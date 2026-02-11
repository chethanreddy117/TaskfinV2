from app.db import SessionLocal
from app.models import AuditLog

def log_event(user_id, action, status, message):
    """
    Record an audit event in the database.
    
    Parameters:
    	user_id: Identifier of the user performing the action.
    	action (str): Short name or description of the action performed.
    	status (str): Outcome or status of the action (e.g., "success", "failure").
    	message (str): Additional context or details about the event.
    """
    db = SessionLocal()
    db.add(AuditLog(
        user_id=user_id,
        action=action,
        status=status,
        message=message,
    ))
    db.commit()
    db.close()