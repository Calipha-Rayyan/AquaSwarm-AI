# 💧 AquaSwarm AI

### Autonomous Water Supply & Shortage Coordination Network

AquaSwarm AI is a multi-agent water-operations prototype that monitors tank conditions, analyzes shortages, detects abnormal conditions, evaluates suppliers, proposes allocations, obtains human approval, coordinates delivery, verifies the delivered quantity, and recommends replanning when an operation fails.

> **MVP safety note:** the project uses synthetic/demo data. It does not automatically control real-world water infrastructure.

## 🔄 System Workflow

```text
Water Data
    │
    ▼
Demand Agent
    │
    ▼
Anomaly Agent
    │
    ▼
Supply Agent
    │
    ▼
Allocation Agent
    │
    ▼
Human Manager Approval
    ├───────────────┐
    │ APPROVE      │ REJECT
    ▼              ▼
Delivery Agent   Replanning Agent
    │
    ▼
DISPATCHED
    │
    ▼
Physical Delivery Completed
    │
    ▼
DELIVERED
    │
    ▼
Verification Agent
    │
    ├── VERIFIED
    │
    └── REVIEW_REQUIRED → Replanning
```

The manager approval step is the safety boundary for critical actions. AI may recommend an allocation, but the human manager authorizes delivery.

## 🤖 Agent Responsibilities

| Agent | Responsibility |
|---|---|
| Demand | Calculates shortage and operational priority |
| Anomaly | Identifies abnormal water conditions |
| Supply | Filters and ranks available suppliers |
| Allocation | Proposes quantity and supplier |
| Delivery | Coordinates an approved delivery |
| Verification | Checks tank/supplier identity, status, and quantity |
| Replanning | Recommends recovery after rejection or failed verification |
| Orchestrator | Summarizes workflow state and recommends the next action |

## 🧠 Deterministic vs AI Logic

Deterministic application logic handles:
- shortage calculation
- tank fill percentage
- operational priority
- supplier eligibility and ranking
- approval state
- delivery state transitions
- delivery discrepancy
- verification result

CrewAI agents interpret those deterministic results, explain them, and recommend actions. They are instructed not to invent operational measurements.

## 🗂️ Data

```text
data/
├── sites.csv
├── tanks.csv
├── consumption.csv
├── suppliers.csv
└── sample_water_data.csv
```

The SQLite database is generated locally by the backend and is intentionally ignored by Git.

## 🏗️ Project Structure

```text
AquaSwarm-AI/
│
├── agents/
│   ├── allocation/
│   ├── anomaly/
│   ├── approval/
│   ├── delivery/
│   ├── demand/
│   ├── orchestrator/
│   ├── replanning/
│   ├── supply/
│   └── verification/
│
├── backend/
├── config/
├── data/
├── models/
├── tools/
├── ui/
│   ├── components/
│   │   ├── auth.py
│   │   └── network.py
│   └── dashboard.py
├── workflows/
│
├── app.py
├── requirements.txt
├── .env.example
└── README.md
```

## ⚙️ Windows Setup

```powershell
cd D:\AquaSwarm-AI
python -m venv .venv
.venv\Scriptsctivate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your real API key:

```env
GROQ_API_KEY=your_real_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Never commit `.env`.

### Initialize the database

```powershell
python -m backend.database
```

### Start the backend

```powershell
uvicorn backend.api:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

### Start Streamlit

In another terminal:

```powershell
cd D:\AquaSwarm-AI
.venv\Scriptsctivate
streamlit run app.py
```

## 🔐 Prototype Login

The demo credentials are environment configurable:

```env
AQUASWARM_DEMO_EMAIL=demo@aquaswarm.ai
AQUASWARM_DEMO_PASSWORD=AquaSwarm@123
```

Change them before any non-local demonstration.

## 🚚 Delivery Lifecycle

A Delivery Agent run creates a `DISPATCHED` state. It does not automatically mean that water has arrived.

```text
APPROVED
   ↓
DISPATCHED
   ↓
physical receipt
   ↓
DELIVERED
   ↓
VERIFICATION
```

The dashboard therefore has a separate **Confirm Delivery Received** control that records the physically measured quantity before verification.

## 🧪 Testing

Run the individual agent smoke tests:

```powershell
python -m agents.demand.test_run
python -m agents.anomaly.test_run
python -m agents.supply.test_run
python -m agents.allocation.test_run
python -m agents.approval.test_run
python -m agents.delivery.test_run
python -m agents.verification.test_run
python -m agents.replanning.test_run
python -m agents.orchestrator.test_run
```

Backend:

```powershell
python -m backend.test_database
```

## 🛡️ Security

- `.env` is ignored by Git.
- `.streamlit/secrets.toml` is ignored by Git.
- SQLite databases are ignored by Git.
- Critical physical delivery actions require human approval.
- Verification is based on recorded operational values.
- Prototype authentication is not production-grade identity management.

## 📌 Status

**Working Hackathon Prototype**

The project demonstrates a closed-loop water operations workflow using deterministic water-management logic, CrewAI specialist agents, a FastAPI/SQLite backend, and a Streamlit manager control center.
