💧 AquaSwarm AI

🤖 Autonomous Water Supply & Shortage Coordination Network

AquaSwarm AI is a smart water management system that helps monitor water usage, identify possible shortages, detect unusual consumption, coordinate available water supply, and verify deliveries.

🌊 How it works
👀 Observe → 🔮 Predict → 🚨 Diagnose → 📦 Allocate → 👤 Approve → 🚚 Deliver → ✅ Verify → 🔄 Re-plan

✨ Main Features

💧 Water tank monitoring
📊 Consumption tracking
🔮 Shortage prediction
🚨 Abnormal consumption detection
🚚 Supplier evaluation
📦 Delivery request management
👤 Manager approval for critical actions
🔍 Delivery verification
🔄 Re-planning when delivery problems occur

🤖 AI Agents

🎯 Orchestrator Agent
🔮 Demand Agent
🚨 Anomaly Agent
💧 Supply Agent
📦 Allocation Agent
🚚 Delivery Agent
🔍 Verification Agent

🗂️ Data

🏢 Sites / Buildings
🚰 Water Tanks
📊 Consumption
🚚 Suppliers
🚨 Alerts
📦 Delivery Requests
🤖 Agent Runs
👤 Approvals
🔍 Verification

🧪 MVP Demo

The MVP uses simulated water data for demonstration.

For example, when a site's water consumption suddenly increases, AquaSwarm AI can detect the abnormal usage, identify a possible shortage, check available suppliers, create a delivery plan, request manager approval, and verify the delivery result.

🛠️ Technology

🐍 Python
🎨 Streamlit
🐼 Pandas
🗄️ SQLite
🤖 CrewAI
📊 Plotly
🔗 GitHub

📁 Project Structure

AquaSwarm-AI/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── agents/
├── backend/
├── data/
├── ui/
└── workflows/

🔐 Safety

AquaSwarm AI keeps humans involved in critical physical actions.

The MVP uses synthetic/demo data and does not automatically dispatch real-world water deliveries.

🔮 Future Ideas

📡 Real sensor integration
📱 Mobile notifications
☁️ Cloud deployment
🧠 Advanced forecasting
🌐 Supplier integrations
📊 Advanced analytics
🔔 Real-time alerts

💙 Built as a University + Hackathon Project

🌊 AquaSwarm AI
Smarter Water. Better Coordination. Less Waste. 💧🤖
```markdown
# AquaSwarm-AI

### AI-Powered Multi-Agent Water Operations System

AquaSwarm-AI is a multi-agent AI system designed to support intelligent water resource management through demand analysis, anomaly detection, supplier selection, water allocation, human approval, delivery coordination, and verification.

The system combines specialized AI agents, deterministic water-management tools, and an interactive Streamlit dashboard to provide an end-to-end water operations workflow.

---

## 🚀 Key Features

- 🤖 Multi-agent water operations
- 📊 Water demand and shortage analysis
- ⚠️ Anomaly detection
- 🚚 Supplier evaluation and selection
- 💧 Intelligent water allocation
- 👨‍💼 Human-in-the-loop approval
- 📦 Delivery coordination
- 🔍 Delivery verification
- 🔄 Replanning after rejection
- 🖥️ Interactive Streamlit dashboard
- 🔐 Login interface
- 📋 Structured agent outputs using Pydantic

---

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
              Manager Approval
                 ┌──────┴──────┐
                 │             │
              APPROVE        REJECT
                 │             │
                 ▼             ▼
          Delivery Agent   Replanning Agent
                 │
                 ▼
        Verification Agent
```

The workflow pauses at the **Manager Approval** stage. The proposed allocation is not executed until the manager approves it.

---

## 🤖 Multi-Agent System

| Agent | Responsibility |
|---|---|
| **Demand Agent** | Analyzes water demand, shortage, and priority |
| **Anomaly Agent** | Detects abnormal water conditions |
| **Supply Agent** | Evaluates available suppliers |
| **Allocation Agent** | Proposes water quantity and supplier |
| **Approval** | Handles the manager's decision |
| **Delivery Agent** | Coordinates the approved delivery |
| **Verification Agent** | Verifies delivery quantity and status |
| **Replanning Agent** | Generates an alternative action after rejection |

---

## 🧠 How It Works

1. **Analyze** — Water data is evaluated to identify demand and potential shortages.
2. **Detect** — The system checks for abnormal water conditions.
3. **Select** — Available suppliers are evaluated.
4. **Allocate** — The system proposes the required quantity and supplier.
5. **Approve** — A manager reviews and approves or rejects the recommendation.
6. **Execute** — Approved allocations proceed to delivery coordination.
7. **Verify** — Delivery quantity and status are checked.
8. **Replan** — Rejected allocations are sent to the replanning stage.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python 3.11+** | Core development |
| **CrewAI** | Multi-agent orchestration |
| **Groq** | LLM inference |
| **Pydantic** | Data validation and structured outputs |
| **Streamlit** | Web dashboard |
| **Pandas** | Data processing |
| **Plotly** | Data visualization |
| **python-dotenv** | Environment configuration |

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
├── data/
├── models/
├── tools/
├── ui/
├── workflows/
│
├── app.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Calipha-Rayyan/AquaSwarm-AI.git
cd AquaSwarm-AI
```

### 2. Create a Virtual Environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

### 5. Run the Application

```bash
streamlit run app.py
```

The Streamlit dashboard will open in your browser.

---

## 👨‍💼 Human-in-the-Loop

AquaSwarm-AI keeps the final water allocation decision under human control.

After the AI agents generate an allocation recommendation, the manager can:

### Approve

```text
Manager Approval
       ↓
Delivery
       ↓
Verification
```

### Reject

```text
Manager Rejection
       ↓
Replanning
```

This approach combines AI-driven operational analysis with human oversight for critical decisions.

---

## 📋 Documentation

Detailed product requirements, system scope, functional requirements, workflows, and product specifications are documented separately in the project's **Product Requirements Document (PRD)**.

The README provides a high-level technical and operational overview, while the PRD contains the detailed product definition.

---

## 📌 Project Status

**Current Status: Working Prototype**

The current prototype includes:

- Multi-agent water operations workflow
- Streamlit dashboard
- Login interface
- Demand and anomaly analysis
- Supplier selection
- Water allocation
- Human manager approval
- Delivery coordination
- Verification
- Replanning

---

## 👥 Team

### AquaSwarm-AI

**Multi-Agent AI for Intelligent Water Operations**
```
