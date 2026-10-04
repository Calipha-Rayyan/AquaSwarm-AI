```markdown
# AquaSwarm-AI

## AI-Powered Multi-Agent Water Operations System

AquaSwarm-AI is a multi-agent AI system designed to improve water resource management through intelligent demand analysis, anomaly detection, supplier selection, water allocation, human approval, delivery coordination, and verification.

The system combines specialized AI agents with deterministic water-management tools and a Streamlit dashboard to provide an end-to-end operational workflow.

---

## Key Features

- Multi-agent water operations workflow
- Water demand and shortage analysis
- Water anomaly detection
- Supplier evaluation and selection
- Intelligent water allocation
- Human-in-the-loop manager approval
- Delivery coordination
- Delivery verification
- Replanning after rejected allocations
- Interactive Streamlit dashboard
- Login interface
- Structured agent outputs using Pydantic

---

## System Workflow

```text
Water Data
    ↓
Demand Agent
    ↓
Anomaly Agent
    ↓
Supply Agent
    ↓
Allocation Agent
    ↓
Manager Approval
   ↙       ↘
Approve   Reject
   ↓        ↓
Delivery  Replanning
   ↓
Verification
```

The system pauses at the allocation stage until a human manager approves or rejects the proposed operation.

---

## Multi-Agent System

| Agent | Responsibility |
|---|---|
| Demand Agent | Analyzes demand, shortage, and priority |
| Anomaly Agent | Detects abnormal water conditions |
| Supply Agent | Evaluates available suppliers |
| Allocation Agent | Proposes water quantity and supplier |
| Approval | Handles human manager decision |
| Delivery Agent | Coordinates the approved delivery |
| Verification Agent | Verifies delivery quantity and status |
| Replanning Agent | Generates an alternative plan after rejection |

---

## Technology Stack

- **Python 3.11+**
- **CrewAI** – Multi-agent orchestration
- **Groq** – LLM inference
- **Pydantic** – Structured data validation
- **Streamlit** – Web dashboard
- **Pandas** – Data processing
- **Plotly** – Data visualization
- **python-dotenv** – Environment configuration

---

## Project Structure

```text
AquaSwarm-AI/
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
├── config/
├── data/
├── models/
├── tools/
├── ui/
├── workflows/
├── app.py
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Calipha-Rayyan/AquaSwarm-AI.git
cd AquaSwarm-AI
```

### 2. Create and activate virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

### 5. Run the application

```bash
streamlit run app.py
```

---

## Human-in-the-Loop

AquaSwarm-AI keeps the final water allocation decision under human control.

After the AI agents generate an allocation recommendation, the manager can:

- **Approve** → Delivery and verification proceed.
- **Reject** → The Replanning Agent generates the next operational action.

This provides human oversight while allowing AI agents to automate analysis and operational coordination.

---

## Documentation

The project's detailed product requirements, functional requirements, system scope, user workflows, and product specifications are documented separately in the **Product Requirements Document (PRD)**.

---

## Project Status

AquaSwarm-AI currently provides a working prototype of the multi-agent water operations workflow, including the Streamlit dashboard, login interface, agent pipeline, human approval mechanism, delivery coordination, verification, and replanning.

---

## Team

**AquaSwarm-AI**

Multi-Agent AI for Intelligent Water Operations
```

