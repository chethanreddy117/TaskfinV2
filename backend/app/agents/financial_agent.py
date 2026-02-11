from datetime import date
from zoneinfo import ZoneInfo

from app.db import SessionLocal
from app.models import Bill
from app.models import Transaction
from app.services.redis_service import redis_client
from app.services.mock_banking import debit
from app.agents.audit_agent import log_event


def list_bills(user_id: int) -> str:
    db = SessionLocal()
    bills = (
        db.query(Bill)
        .filter(Bill.user_id == user_id, Bill.status == "unpaid")
        .all()
    )
    db.close()

    if not bills:
        return "No unpaid bills."

    return "Unpaid bills:\n" + "\n".join(
        f"{b.name} – {b.amount}" for b in bills
    )


def pay_bill_by_name(user_id: int, text: str, amount: int | None = None) -> str:
    lock_key = f"payment_lock:{user_id}:{text.lower()}"

    # ---- Prevent double execution ----
    if not redis_client.set(lock_key, "1", nx=True, ex=10):
        return "Payment already in progress. Please wait."

    if not text:
        redis_client.delete(lock_key)
        return "Please specify which bill you want to pay."

    db = SessionLocal()
    try:
        text = text.lower().strip()

        bills = (
            db.query(Bill)
            .filter(Bill.user_id == user_id, Bill.status == "unpaid")
            .all()
        )

        for b in bills:
            if b.name.lower() in text:

                # ---- BANK CHECK (CRITICAL) ----
                if not debit(user_id, b.amount):
                    redis_client.delete(lock_key)

                    log_event(
                        user_id,
                        action="PAYMENT_FAILED",
                        status="INSUFFICIENT_FUNDS",
                        message=f"Insufficient balance for {b.name} ₹{b.amount}",
                    )

                    return "Insufficient account balance."

                # ---- Mark bill paid ----
                b.status = "paid"

                txn = Transaction(
                    user_id=user_id,
                    bill_name=b.name,
                    amount=b.amount,
                    status="success",
                )

                db.add(txn)
                db.commit()

                # ---- Update risk counters ----
                today = date.today().isoformat()

                redis_client.incrby(f"risk:amount:{user_id}:{today}", b.amount)
                redis_client.incr(f"risk:count:{user_id}:{today}")
                redis_client.expire(f"risk:amount:{user_id}:{today}", 86400)
                redis_client.expire(f"risk:count:{user_id}:{today}", 86400)

                # ---- Audit log ----
                log_event(
                    user_id,
                    action="PAYMENT_EXECUTED",
                    status="SUCCESS",
                    message=f"{b.name} ₹{b.amount} paid successfully",
                )

                redis_client.delete(lock_key)
                return f"{b.name} bill paid successfully."

        redis_client.delete(lock_key)
        return "Bill not found."

    finally:
        db.close()


def list_transactions(user_id: int) -> str:
    db = SessionLocal()
    txns = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .all()
    )
    db.close()

    if not txns:
        return "No transactions found."

    ist = ZoneInfo("Asia/Kolkata")
    result = "Payment history:\n"

    for t in txns:
        ist_time = t.created_at.replace(
            tzinfo=ZoneInfo("UTC")
        ).astimezone(ist)

        result += (
            f"{t.bill_name} – {t.amount} – "
            f"{ist_time.strftime('%Y-%m-%d %H:%M')}\n"
        )

    return result.strip()
