# TaskfinV2

# TaskFin – Agent-Based Bill Payment System (Backend)

TaskFin is an agent-based backend system that enables users to manage and pay bills through a conversational interface.  
It demonstrates clean separation of concerns, payment correctness, risk controls, and auditability.

---

## 🚀 Features

- Secure user authentication (JWT)
- Account balance management
- Unpaid bill listing
- Bill payment with confirmation flow
- Transaction lifecycle (PENDING / SUCCESS / FAILED)
- Risk controls using Redis
- Immutable audit logging
- Mock banking service (no real money involved)
- Agent-based architecture
- Dockerized setup

---

## 🏗 Architecture Overview

- **FastAPI** – API layer
- **PostgreSQL** – Persistent storage
- **Redis** – State, rate limiting, risk tracking
- **LLM (Claude)** – Intent detection only
- **Agents** – Orchestrator, Financial, Risk, Audit, Auth

The LLM is strictly limited to intent detection.  
All business logic is deterministic and handled by agents.

---

## 📦 Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Docker & Docker Compose
- LangChain + Claude (Haiku)

---

## 🧠 Agent Responsibilities

- **Orchestrator Agent** – Interprets user intent and coordinates flow
- **Financial Agent** – Handles bills, payments, balances, transactions
- **Risk Agent** – Enforces limits and prevents misuse
- **Audit Agent** – Records immutable audit logs
- **Auth Agent** – Resolves user identity from JWT

---

## 🔐 Payment Lifecycle

1. User requests bill payment
2. System creates a `PENDING` transaction
3. User confirms payment
4. Balance is validated
5. Transaction becomes `SUCCESS` or `FAILED`
6. Bill status updated
7. Audit log recorded

Idempotency and duplicate prevention are enforced.

---

## 🗄 Database Tables

- users
- accounts
- bills
- transactions
- audit_logs

---

## ▶️ Running the Project

```bash
docker-compose up --build
