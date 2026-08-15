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
def get_session_events(session_id: str, db: Session = Depends(database.get_db)):
    return db.query(models.EventModel).filter(models.EventModel.session_id == session_id).order_by(models.EventModel.timestamp.asc()).all()

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

# --- WebSocket Endpoint ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
