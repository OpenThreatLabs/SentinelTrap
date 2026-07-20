from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from database import Base
import datetime
import uuid

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address = Column(String, index=True)
    country = Column(String, default="Unknown")
    city = Column(String, default="Unknown")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    username_attempted = Column(String, default="Unknown")
    password_attempted = Column(String, default="Unknown")
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    events = relationship("EventModel", back_populates="session", cascade="all, delete-orphan")

class EventModel(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    event_type = Column(String)  # login_attempt, command_execution, deception_triggered, etc.
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)

    session = relationship("SessionModel", back_populates="events")

class DecoyModel(Base):
    __tablename__ = "decoys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)  # port, file
    status = Column(String, default="inactive")  # active, inactive
    triggered_by_session = Column(String, ForeignKey("sessions.id"), nullable=True)
    activated_at = Column(DateTime, nullable=True)
