```markdown
# 🌊 AquaSwarm AI

> **An AI-powered multi-agent system for intelligent water resource management.**

AquaSwarm AI uses specialized AI agents to analyze water demand, detect anomalies, evaluate suppliers, allocate water resources, obtain manager approval, coordinate delivery, verify delivery, and replan rejected allocations.

---

## 🚀 AquaSwarm AI Workflow

```text
                         ┌──────────────────┐
                         │    Water Data    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Demand Agent    │
                         │    Analysis      │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Anomaly Agent   │
                         │    Detection     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   Supply Agent   │
                         │    Analysis      │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Allocation Agent │
                         │ Water Allocation │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Manager Approval │
                         └────────┬─────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
              Approved                          Rejected
                 │                                 │
                 ▼                                 ▼
        ┌──────────────────┐              ┌──────────────────┐
        │  Delivery Agent  │              │ Replanning Agent │
        │    Delivery      │              │    Replanning    │
        └────────┬─────────┘              └──────────────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Verification     │
        │      Agent       │
        │   Verification   │
        └──────────────────┘
```

---

## 🤖 Multi-Agent System

| Agent | Responsibility |
|---|---|
| **Demand Agent** | Analyzes water demand, shortage, and priority |
| **Anomaly Agent** | Detects abnormal water conditions |
| **Supply Agent** | Evaluates available water suppliers |
| **Allocation Agent** | Determines allocation quantity and supplier |
| **Manager Approval Agent** | Reviews and approves or rejects allocations |
| **Delivery Agent** | Coordinates approved water deliveries |
| **Verification Agent** | Verifies delivered quantity and discrepancies |
| **Replanning Agent** | Reassesses rejected allocations |

---

## 🛠️ Technology Stack

- **Python 3.11**
- **CrewAI**
- **CrewAI Flow**
- **Groq**
- **Pydantic**
- **Streamlit**
- **Pandas**
- **Plotly**

---

## 📁 Project Structure

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
├── config/
│   └── settings.py
│
├── data/
│   └── sample_water_data.csv
│
├── models/
│   └── schemas.py
│
├── tools/
│   └── water_tools.py
│
├── ui/
│   └── dashboard.py
│
├── workflows/
│   └── aquaswarm_flow.py
│
├── app.py
├── .gitignore
└── README.md
```

---

## 📊 Current Workflow

The system currently supports an end-to-end simulated water management workflow:

1. **Water Data Initialization**
2. **Demand Analysis**
3. **Anomaly Detection**
4. **Supply Analysis**
5. **Water Allocation**
6. **Manager Approval**
7. **Delivery Coordination**
8. **Delivery Verification**
9. **Replanning for Rejected Allocations**

---

## 🔄 Decision Routing

```text
Manager Approval
       │
       ├── Approved ──→ Delivery ──→ Verification
       │
       └── Rejected ──→ Replanning
```

---

## 📌 Current Status

### Completed

- [x] Multi-agent architecture
- [x] Pydantic data schemas
- [x] Water management tools
- [x] CrewAI Flow orchestration
- [x] Demand analysis
- [x] Anomaly detection
- [x] Supply analysis
- [x] Water allocation
- [x] Manager approval and rejection
- [x] Approval routing
- [x] Delivery coordination
- [x] Delivery verification
- [x] Replanning branch
- [x] End-to-end workflow testing

### Next Development

- [ ] Streamlit manager dashboard integration
- [ ] Interactive manager approval controls
- [ ] Real-time water monitoring interface
- [ ] Agent activity visualization
- [ ] Alerts and exception handling
- [ ] Persistent workflow data
- [ ] Real supplier/backend integration
- [ ] Improved delivery and verification lifecycle

---

## ▶️ Installation

Clone the repository:

```bash
git clone https://github.com/Calipha-Rayyan/AquaSwarm-AI.git
cd AquaSwarm-AI
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment on Windows:

```cmd
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install streamlit crewai groq pydantic pandas plotly python-dotenv litellm
```

---

## 🔐 Environment Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

> **Never commit `.env` or API keys to GitHub.**

---

## ▶️ Run the Workflow

From the project root:

```cmd
python -m workflows.aquaswarm_flow
```

---

## 🎯 Project Goal

AquaSwarm AI aims to provide an intelligent and coordinated platform for **water resource monitoring, decision-making, allocation, delivery, verification, and adaptive replanning** using a collaborative multi-agent AI architecture.
```