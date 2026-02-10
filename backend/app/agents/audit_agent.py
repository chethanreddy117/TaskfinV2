from zoneinfo import ZoneInfo
from datetime import datetime
from app.db import SessionLocal
from app.models_audit import AuditLog

def log_event(
    user_id: int,
    action: str,
    status: str,
    message: str,
):
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
