import json
from rapidfuzz import fuzz

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.services.redis_service import redis_client
from app.db import SessionLocal
from app.models import Bill

from app.agents.risk_agent import assess_payment_risk
from app.agents.audit_agent import log_event
from app.services.mock_banking import get_balance

from app.agents.financial_agent import (
    list_bills,
    pay_bill_by_name,
    list_transactions,
)

# ---------------- LLM ----------------

llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    anthropic_api_key=settings.ANTHROPIC_API_KEY,
    temperature=0.2,
)

SYSTEM_PROMPT = (
    "You are TaskFin, a bill payment assistant.\n"
    "\n"
    "You must respond with ONE internal action keyword ONLY when a system action is required.\n"
    "\n"
    "Internal actions (NEVER mention these to the user):\n"
    "- LIST_BILLS\n"
    "- PAY_BILL <bill name>\n"
    "- SHOW_HISTORY\n"
    "- SHOW_BALANCE\n"
    "\n"
    "Rules:\n"
    "- If the user greets you (hi, hello, hey), respond with a friendly greeting in natural language.\n"
    "- If the user asks to see or list bills, respond ONLY with LIST_BILLS.\n"
    "- If the user asks to pay a bill, respond ONLY with PAY_BILL followed by the bill name.\n"
    "- If the user asks about payment history, respond ONLY with SHOW_HISTORY.\n"
    "- If the user asks about balance, respond ONLY with SHOW_BALANCE.\n"
    "- Do NOT create internal actions for greetings or small talk.\n"
    "-If the request is unclear or unrelated, respond with a friendly message explaining that you can help with: viewing unpaid bills, paying a bill, checking account balance, or viewing payment history.\nSuggest example phrases like “show my bills”, “pay electricity”, or “show balance”.\nDo NOT say you lack context.\n"
    "- NEVER mention internal actions or system commands.\n"
)


# ---------------- Helpers ----------------

def normalize(text: str) -> str:
    synonyms = {
        "power": "electricity",
        "current": "electricity",
        "light": "electricity",
        "cc": "credit card",
        "card": "credit card",
    }

    text = text.lower()
    for word, replacement in synonyms.items():
        text = text.replace(word, replacement)

    return (
        text.replace("my", "")
        .replace("bill", "")
        .replace("payment", "")
        .strip()
    )


def find_best_bill(bills, query: str, threshold: int = 70):
    query = normalize(query)

    best_bill = None
    best_score = 0

    for bill in bills:
        score = fuzz.partial_ratio(query, normalize(bill.name))
        if score > best_score:
            best_score = score
            best_bill = bill

    return best_bill if best_score >= threshold else None


# ---------------- Orchestrator ----------------

def handle_message(user_id: int, message: str) -> str:
    # ---- Redis availability ----
    try:
        redis_client.ping()
    except Exception:
        return "System temporarily unavailable. Please try later."

    # ---- Rate limiting ----
    rate_key = f"rate_limit:{user_id}"
    count = redis_client.incr(rate_key)
    if count == 1:
        redis_client.expire(rate_key, 60)
    if count > 10:
        return "Too many requests. Please slow down."

    # ---- Confirmation handling ----
    confirm_key = f"confirm:payment:{user_id}"
    pending = redis_client.get(confirm_key)

    if pending:
        pending_data = json.loads(pending)
        user_reply = message.lower().strip()

        if user_reply in ("yes", "confirm", "ok"):
            redis_client.delete(confirm_key)

            log_event(
                user_id,
                action="PAYMENT_CONFIRMED",
                status="APPROVED",
                message=f"Confirmed payment for {pending_data['bill_name']} ₹{pending_data['amount']}",
            )

            return pay_bill_by_name(
                user_id,
                pending_data["bill_name"],
                pending_data["amount"],
            )

        if user_reply in ("no", "cancel"):
            redis_client.delete(confirm_key)

            log_event(
                user_id,
                action="PAYMENT_CANCELLED",
                status="CANCELLED",
                message="User cancelled payment",
            )

            return "Payment cancelled."

        return (
            f"Please confirm payment of ₹{pending_data['amount']} "
            f"for {pending_data['bill_name']} (yes/no)."
        )

    # ---- Intent detection ----
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=message),
    ]

    try:
        ai_response = llm.invoke(messages).content.strip()
    except Exception:
        return "AI service temporarily unavailable. Please try again."

    # ---- Simple intents ----
    if ai_response == "LIST_BILLS":
        return list_bills(user_id)

    if ai_response == "SHOW_HISTORY":
        return list_transactions(user_id)

    if ai_response == "SHOW_BALANCE":
        balance = get_balance(user_id)

        log_event(
            user_id,
            action="BALANCE_VIEWED",
            status="SUCCESS",
            message=f"Balance checked: ₹{balance}",
        )

        return f"Your current account balance is ₹{balance}."

    # ---- Payment intent ----
    if ai_response.startswith("PAY_BILL"):
        bill_text = ai_response.split(" ", 1)[1] if " " in ai_response else ""

        if not bill_text:
            return "Please specify which bill you want to pay."

        db = SessionLocal()
        bills = (
            db.query(Bill)
            .filter(Bill.user_id == user_id, Bill.status == "unpaid")
            .all()
        )
        bill = find_best_bill(bills, bill_text)
        db.close()

        if not bill:
            return "Bill not found."

        allowed, reason = assess_payment_risk(
            user_id=user_id,
            bill_name=bill.name,
            amount=bill.amount,
        )

        if not allowed:
            log_event(
                user_id,
                action="PAYMENT_BLOCKED",
                status="REJECTED",
                message=reason,
            )
            return reason

        log_event(
            user_id,
            action="PAYMENT_REQUESTED",
            status="PENDING",
            message=f"Requested payment for {bill.name} ₹{bill.amount}",
        )

        redis_client.setex(
            confirm_key,
            60,
            json.dumps(
                {
                    "bill_id": bill.id,
                    "bill_name": bill.name,
                    "amount": bill.amount,
                }
            ),
        )

        return f"Confirm payment of ₹{bill.amount} for {bill.name}? (yes/no)"

    return ai_response
