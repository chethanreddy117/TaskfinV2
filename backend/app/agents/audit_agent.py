from zoneinfo import ZoneInfo
from datetime import datetime
from app.db import SessionLocal
from app.agents.logger import log_event
from app.models import AuditLog


def log_event(
    user_id: int,
    action: str,
    status: str,
    message: str,
):
    """
    Create and persist an audit log entry in the database with a UTC timestamp.
    
    Parameters:
        user_id (int): ID of the user who performed the action.
        action (str): Short identifier or name of the action performed.
        status (str): Outcome or status of the action (e.g., 'success', 'failure').
        message (str): Human-readable details about the event.
    """
    db = SessionLocal()
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            status=status,
            message=message,
            created_at=datetime.now(ZoneInfo("UTC")),
        )
        db.add(log)
        db.commit()
    finally:
        db.close()