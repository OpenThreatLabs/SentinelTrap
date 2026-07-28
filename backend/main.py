#!/usr/bin/env python3
"""
SentinelTrap - Threat Intelligence Backend API
FastAPI Application Running on Port 8000 with Real-Time WebSockets
"""

import csv
import datetime
import io
import json
import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
import database
import models

# Create database tables automatically on startup
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="SentinelTrap Threat Intelligence Backend",
    description="Multi-Layer Honeypot Telemetry, Real-Time WebSockets & SIEM Analytics API",
    version="1.0.0"
)

# Enable CORS for Frontend SIEM Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

def mock_geolocate(ip: str):
    """Simple IP geolocation helper with local network fallbacks."""
    if ip in ["127.0.0.1", "localhost", "::1"] or ip.startswith("192.168.") or ip.startswith("10."):
        return {"country": "Local Network", "city": "Internal Node", "lat": 28.6139, "lon": 77.2090}
    return {"country": "Unknown", "city": "Unknown", "lat": 0.0, "lon": 0.0}

# --- REST Endpoints ---

@app.get("/")
def root_status():
    return {
        "status": "online",
        "service": "SentinelTrap Threat Intelligence Backend API",
        "port": 8000,
        "version": "1.0.0",
        "websocket": "/ws"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}

@app.post("/api/events")
async def receive_telemetry_event(payload: dict, db: Session = Depends(database.get_db)):
    """
    Central Telemetry Receiver endpoint used by all protocol honeypots
    (FTP, SMTP, Telnet, SSH, Web, DB, Redis, Fake Ports).
    """
    session_id = payload.get("session_id")
    ip_address = payload.get("ip_address", "127.0.0.1")
    protocol = payload.get("protocol", "SSH")
    
    # Locate or create the session
    session = None
    if session_id:
        session = db.query(models.SessionModel).filter(models.SessionModel.id == session_id).first()
        
    if not session:
        geo = mock_geolocate(ip_address)
        session = models.SessionModel(
            id=session_id if session_id else None,
            ip_address=ip_address,
            protocol=protocol,
            country=geo["country"],
            city=geo["city"],
            latitude=geo["lat"],
            longitude=geo["lon"],
            username_attempted=payload.get("username_attempted", "Unknown"),
            password_attempted=payload.get("password_attempted", ""),
            started_at=datetime.datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    else:
        if payload.get("username_attempted"):
            session.username_attempted = payload.get("username_attempted")
        if payload.get("password_attempted"):
            session.password_attempted = payload.get("password_attempted")
        db.commit()

    # Create event record
    event = models.EventModel(
        session_id=session.id,
        protocol=protocol,
        event_type=payload.get("event_type", "general_activity"),
        vulnerability_code=payload.get("vulnerability_code"),
        input_data=payload.get("input_data", ""),
        output_data=payload.get("output_data", ""),
        timestamp=datetime.datetime.utcnow()
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Broadcast event payload to real-time WebSockets SIEM Dashboard
    broadcast_data = {
        "event_type": "honeypot_telemetry",
        "session_id": session.id,
        "protocol": protocol,
        "ip_address": ip_address,
        "event": {
            "id": event.id,
            "event_type": event.event_type,
            "vulnerability_code": event.vulnerability_code,
            "input_data": event.input_data,
            "output_data": event.output_data,
            "timestamp": event.timestamp.isoformat()
        }
    }
    await manager.broadcast(json.dumps(broadcast_data))
    return {"status": "success", "session_id": session.id, "event_id": event.id}

@app.post("/api/sessions")
async def create_session(payload: dict, db: Session = Depends(database.get_db)):
    ip = payload.get("ip_address", "127.0.0.1")
    protocol = payload.get("protocol", "SSH")
    geo = mock_geolocate(ip)
    
    session = models.SessionModel(
        ip_address=ip,
        protocol=protocol,
        country=geo["country"],
        city=geo["city"],
        latitude=geo["lat"],
        longitude=geo["lon"],
        username_attempted=payload.get("username_attempted", "root"),
        password_attempted=payload.get("password_attempted", ""),
        started_at=datetime.datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

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
async def create_session_event(session_id: str, payload: dict, db: Session = Depends(database.get_db)):
    event = models.EventModel(
        session_id=session_id,
        protocol=payload.get("protocol", "SSH"),
        event_type=payload.get("event_type", "command_execution"),
        vulnerability_code=payload.get("vulnerability_code"),
        input_data=payload.get("input_data", ""),
        output_data=payload.get("output_data", ""),
        timestamp=datetime.datetime.utcnow()
    )
    db.add(event)
    db.commit()

    await manager.broadcast(json.dumps({
        "event_type": "new_event",
        "session_id": session_id,
        "event": {
            "id": event.id,
            "event_type": event.event_type,
            "vulnerability_code": event.vulnerability_code,
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

@app.get("/api/stats/overview")
def get_stats_overview(db: Session = Depends(database.get_db)):
    total_sessions = db.query(models.SessionModel).count()
    total_events = db.query(models.EventModel).count()

    # Protocol Breakdown
    sessions = db.query(models.SessionModel).all()
    protocol_counts = {}
    user_counts = {}
    for s in sessions:
        proto = s.protocol or "SSH"
        protocol_counts[proto] = protocol_counts.get(proto, 0) + 1
        if s.username_attempted and s.username_attempted != "Unknown":
            user_counts[s.username_attempted] = user_counts.get(s.username_attempted, 0) + 1

    top_usernames = [{"username": k, "count": v} for k, v in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

    # Vulnerability Breakdown
    events = db.query(models.EventModel).filter(models.EventModel.vulnerability_code.isnot(None)).all()
    vuln_counts = {}
    for e in events:
        v = e.vulnerability_code
        vuln_counts[v] = vuln_counts.get(v, 0) + 1

    return {
        "total_sessions": total_sessions,
        "total_events": total_events,
        "protocol_breakdown": protocol_counts,
        "vulnerability_breakdown": vuln_counts,
        "top_usernames": top_usernames
    }

@app.get("/api/reports/export")
def export_logs(format: str = "json", db: Session = Depends(database.get_db)):
    events = db.query(models.EventModel).all()
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Session ID", "Protocol", "Timestamp", "Event Type", "Vuln Code", "Input Data", "Output Data"])
        for e in events:
            writer.writerow([e.id, e.session_id, e.protocol, e.timestamp, e.event_type, e.vulnerability_code, e.input_data, e.output_data])
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=sentinel_attack_logs.csv"}
        )
    else:
        return [{
            "id": e.id,
            "session_id": e.session_id,
            "protocol": e.protocol,
            "timestamp": e.timestamp.isoformat(),
            "event_type": e.event_type,
            "vulnerability_code": e.vulnerability_code,
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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"[*] Launching SentinelTrap Backend API on http://0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
