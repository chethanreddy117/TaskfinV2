from app.db import SessionLocal
from app.models import Account

def get_balance(user_id: int) -> int:
    """
    Retrieve the account balance for the specified user.
    
    Parameters:
        user_id (int): ID of the user whose account balance to retrieve.
    
    Returns:
        int: The account balance for the user, or 0 if no account exists.
    """
    db = SessionLocal()
    account = db.query(Account).filter_by(user_id=user_id).first()
    db.close()
    return account.balance if account else 0


def debit(user_id: int, amount: int) -> bool:
    """
    Attempt to subtract an amount from the specified user's account balance and persist the change.
    
    If the account exists and has sufficient balance, the balance is decremented by `amount` and the change is committed; otherwise no change is made.
    
    Parameters:
        user_id (int): ID of the user whose account will be debited.
        amount (int): Amount to subtract from the account balance.
    
    Returns:
        bool: `True` if the amount was debited and committed, `False` if the account does not exist or has insufficient funds.
    """
    db = SessionLocal()
    account = db.query(Account).filter_by(user_id=user_id).first()

    if not account or account.balance < amount:
        db.close()
        return False

    account.balance -= amount
    db.commit()
    db.close()
    return True