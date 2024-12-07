from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.config.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)  # UUID for anonymous sessions
    cookie_id = Column(String, unique=True, index=True)   # For cookie-based tracking
    ip_address = Column(String)                          # Store user's IP
    user_agent = Column(String)                          # Browser/device info
    device_info = Column(JSON)                           # Detailed device information
    
    # Session timing
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Analytics
    messages_count = Column(Integer, default=0)
    total_interactions = Column(Integer, default=0)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="session")