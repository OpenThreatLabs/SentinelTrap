from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- Session Schemas ---

class SessionCreate(BaseModel):
    ip_address: str = Field(default="127.0.0.1", description="IP address of the attacker")
    username_attempted: Optional[str] = Field(default="root", description="Target username tried during SSH auth")
    password_attempted: Optional[str] = Field(default="", description="Password tried during SSH auth")

class SessionResponse(BaseModel):
    id: str
    ip_address: str
    country: Optional[str] = "Unknown"
    city: Optional[str] = "Unknown"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    username_attempted: str
    password_attempted: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Event Schemas ---

class EventCreate(BaseModel):
    event_type: str = Field(default="command_execution", description="Type of honeypot event")
    input_data: Optional[str] = Field(default="", description="Raw command entered by attacker")
    output_data: Optional[str] = Field(default="", description="Response or deception output generated")

class EventResponse(BaseModel):
    id: int
    session_id: str
    timestamp: datetime
    event_type: str
    input_data: Optional[str] = None
    output_data: Optional[str] = None

    class Config:
        from_attributes = True

# --- Threat Intelligence Summary Schemas ---

class TopItem(BaseModel):
    name: str
    count: int

class ThreatStatsOverview(BaseModel):
    total_sessions: int
    total_events: int
    top_usernames: List[TopItem]
    top_commands: List[TopItem]
