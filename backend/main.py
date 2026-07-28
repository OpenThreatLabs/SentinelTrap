import csv
import datetime
import io
import json
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import database
import models

# Create database tables automatically on launch
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="SentinelTrap Threat Intelligence Backend")

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
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

def mock_geolocate(ip: str):
    """Simple IP geolocation helper with local network fallbacks."""
    if ip in ["127.0.0.1", "localhost", "::1"] or ip.startswith("192.168.") or ip.startswith("10."):
        return {"country": "Local Network", "city": "Internal Node", "lat": 0.0, "lon": 0.0}
    return {"country": "Unknown", "city": "Unknown", "lat": 0.0, "lon": 0.0}

# --- REST Endpoints ---

@app.post("/api/sessions")
async def create_session(payload: dict, db: Session = Depends(database.get_db)):
    ip = payload.get("ip_address", "127.0.0.1")
    geo = mock_geolocate(ip)
    
    session = models.SessionModel(
        ip_address=ip,
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

    # Broadcast new session event to connected dashboards
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
async def create_event(session_id: str, payload: dict, db: Session = Depends(database.get_db)):
    event = models.EventModel(
        session_id=session_id,
        event_type=payload.get("event_type", "command_execution"),
        input_data=payload.get("input_data", ""),
        output_data=payload.get("output_data", ""),
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

@app.get("/api/stats/overview")
def get_stats_overview(db: Session = Depends(database.get_db)):
    total_sessions = db.query(models.SessionModel).count()
    total_events = db.query(models.EventModel).count()

    # Top credentials attempted
    users = db.query(models.SessionModel.username_attempted).all()
    user_counts = {}
    for (u,) in users:
        user_counts[u] = user_counts.get(u, 0) + 1

    top_usernames = [{"username": k, "count": v} for k, v in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

    return {
        "total_sessions": total_sessions,
        "total_events": total_events,
        "top_usernames": top_usernames
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
