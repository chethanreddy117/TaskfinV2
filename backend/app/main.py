from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError
import time
from app.models import User, Account, Bill, Transaction

from app.config import settings
from app.db import SessionLocal
from app.security import verify_password, create_access_token
from app.seed import seed_db

from app.agents.auth_agent import resolve_user_id
from app.agents.orchestrator import handle_message

# APP
app = FastAPI(title="TaskFin Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# STARTUP
@app.on_event("startup")
def startup_event():
    retries = 5
    while retries:
        try:
            seed_db()
            print("Database ready")
            break
        except OperationalError:
            retries -= 1
            print("Waiting for database...")
            time.sleep(2)

# AUTH API
class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(req: LoginRequest):
    db = SessionLocal()
    user = db.query(User).filter(User.username == req.username).first()
    db.close()

    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}

# HEALTH

@app.get("/health")
def health():
    return {"status": "healthy"}

# CHAT API 

class ChatRequest(BaseModel):
    message: str

@app.post("/agent/chat")
def agent_chat(
    req: ChatRequest,
    authorization: str = Header(...)
):
    user_id = resolve_user_id(authorization)
    response = handle_message(user_id, req.message)
    return {"response": response}

# ME
@app.get("/me")
def me(authorization: str = Header(...)):
    user_id = resolve_user_id(authorization)
    return {"user_id": user_id}

#Test 2.o
