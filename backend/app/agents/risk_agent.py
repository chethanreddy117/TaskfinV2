from datetime import date
from app.services.redis_service import redis_client

# ---- Policy constants (easy to tune) ----
DAILY_LIMIT = 5000  # INR
MAX_PAYMENTS_PER_DAY = 5

def assess_payment_risk(
    user_id: int,
    bill_name: str,
    amount: int
) -> tuple[bool, str]:
    """
    Returns:
      (True, "approved") OR
      (False, reason)
    """

    today = date.today().isoformat()

    # ---- Daily amount limit ----
    amount_key = f"risk:amount:{user_id}:{today}"
    current_amount = redis_client.get(amount_key)
    current_amount = int(current_amount) if current_amount else 0

    if current_amount + amount > DAILY_LIMIT:
        return False, "Daily payment limit exceeded."

    # ---- Payment count limit ----
    count_key = f"risk:count:{user_id}:{today}"
    count = redis_client.get(count_key)
    count = int(count) if count else 0

    if count >= MAX_PAYMENTS_PER_DAY:
        return False, "Too many payments today."

    return True, "approved"
