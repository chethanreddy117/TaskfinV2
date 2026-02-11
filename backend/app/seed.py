from app.db import SessionLocal, engine, Base
from app.models import User
from app.models import Bill
from app.models import Account
from app.security import hash_password


def seed_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # ---- USER ----
    user = db.query(User).filter_by(username="chethan").first()
    if not user:
        user = User(
            username="chethan",
            password=hash_password("1234"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # ---- ACCOUNT ----
    existing_account = db.query(Account).filter_by(user_id=user.id).first()
    if not existing_account:
        account = Account(
            user_id=user.id,
            balance=5000,
            type="primary",
        )
        db.add(account)
        db.commit()

    # ---- BILLS ----
    existing_bills = db.query(Bill).count()
    if existing_bills == 0:
        bills = [
            Bill(
                user_id=user.id,
                name="Credit Card",
                amount=2500,
                status="unpaid",
            ),
            Bill(
                user_id=user.id,
                name="Electricity",
                amount=1200,
                status="unpaid",
            ),
        ]
        db.add_all(bills)
        db.commit()

    db.close()
