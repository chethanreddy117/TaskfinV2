from app.db import SessionLocal
from app.models import Account

def get_balance(user_id: int) -> int:
    db = SessionLocal()
    account = db.query(Account).filter_by(user_id=user_id).first()
    db.close()
    return account.balance if account else 0


def debit(user_id: int, amount: int) -> bool:
    db = SessionLocal()
    account = db.query(Account).filter_by(user_id=user_id).first()

    if not account or account.balance < amount:
        db.close()
        return False

    account.balance -= amount
    db.commit()
    db.close()
    return True
