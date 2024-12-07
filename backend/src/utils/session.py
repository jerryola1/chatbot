import uuid
from datetime import datetime
from typing import Optional, Dict
from fastapi import Request
from sqlalchemy.orm import Session as DBSession
from src.models.session import Session
import json

def create_or_get_session(
    db: DBSession,
    request: Request,
    cookie_id: Optional[str] = None
) -> Session:
    """Create a new session or retrieve existing one based on cookie"""
    
    if cookie_id:
        # Try to find existing session
        existing_session = db.query(Session).filter(Session.cookie_id == cookie_id).first()
        if existing_session:
            # Update last activity
            existing_session.last_activity = datetime.utcnow()
            db.commit()
            return existing_session

    # Create new session
    device_info = {
        "user_agent": request.headers.get("user-agent", ""),
        "platform": request.headers.get("sec-ch-ua-platform", ""),
        "mobile": request.headers.get("sec-ch-ua-mobile", ""),
    }

    new_session = Session(
        session_id=str(uuid.uuid4()),
        cookie_id=cookie_id or str(uuid.uuid4()),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        device_info=device_info,
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session

def update_session_analytics(db: DBSession, session: Session):
    """Update session analytics"""
    session.messages_count += 1
    session.total_interactions += 1
    session.last_activity = datetime.utcnow()
    db.commit() 