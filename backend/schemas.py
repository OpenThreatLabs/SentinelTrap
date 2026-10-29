from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- Session Schemas ---

class SessionCreate(BaseModel):
    ip_address: str = Field(default="127.0.0.1", description="IP address of the attacker")
    username_attempted: Optional[str] = Field(default="root", description="Target username tried during SSH auth")
    password_attempted: Optional[str] = Field(default="", description="Password tried during SSH auth")
    protocol: Optional[str] = Field(default="SSH", description="Honeypot protocol that captured this session")

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
    protocol: Optional[str] = Field(default=None, description="Protocol associated with this event")
    vulnerability_code: Optional[str] = Field(default=None, description="Vulnerability classification code")

class EventResponse(BaseModel):
    id: int
    session_id: str
    timestamp: datetime
    protocol: Optional[str] = "SSH"
    event_type: str
    vulnerability_code: Optional[str] = None
    input_data: Optional[str] = None
    output_data: Optional[str] = None

    class Config:
        from_attributes = True

class DirectEventCreate(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Existing session ID if known")
    ip_address: Optional[str] = Field(default="127.0.0.1", description="IP address of the attacker")
    protocol: Optional[str] = Field(default="HTTP", description="Protocol of the honeypot event")
    event_type: str = Field(default="honeypot_event", description="Type of honeypot event")
    input_data: Optional[str] = Field(default="", description="Command or ingress payload")
    output_data: Optional[str] = Field(default="", description="Honeypot or deception response")
    vulnerability_code: Optional[str] = Field(default=None, description="Vulnerability classification code")
    username_attempted: Optional[str] = Field(default="Unknown", description="Username attempted")
    password_attempted: Optional[str] = Field(default="", description="Password attempted")


# --- Threat Intelligence Summary Schemas ---

class TopItem(BaseModel):
    name: str
    count: int

class ThreatStatsOverview(BaseModel):
    total_sessions: int
    total_events: int
    top_usernames: List[TopItem]
    top_commands: List[TopItem]
