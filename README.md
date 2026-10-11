# 💧 AquaSwarm AI

<div align="center">

### Autonomous Water Operations & Multi-Agent Logistics Swarm

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B.svg)](https://streamlit.io/)
[![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-orange.svg)](https://crewai.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Flash--Lite-4E86F7.svg)](https://ai.google.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL--Mode-003B57.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*An enterprise-grade multi-agent autonomous coordination platform for facility water storage, real-time sensor telemetry, shortage mitigation, dynamic supplier dispatching, and digital meter verification.*

[Overview](#-overview) •
[Architecture](#-architecture) •
[Agent Swarm](#-authoritative-8-agent-swarm) •
[Sensor Ingestion API](#-sensor-ingestion-api) •
[Quickstart](#-quickstart--installation) •
[Testing](#-testing--verification)

</div>

---

## 🌊 Overview

**AquaSwarm AI** is an autonomous water operations management system designed for industrial facilities, commercial real estate, campuses, and municipal infrastructure. It combines deterministic water physics and strict accounting rules with specialized **CrewAI** agents powered by **Google Gemini** (`gemini-3.5-flash-lite`).

The platform continuously monitors reservoir volumes, predicts drawdown, detects abnormal consumption spikes, discovers eligible tanker suppliers, proposes optimized allocation plans, enforces human authorization, dispatches suppliers, and verifies physical deliveries with digital flow evidence.

### Core Capabilities
- **Deterministic Core + Cognitive Layer**: Mathematical calculations (shortage volume, days of cover, cost, fill percentage) are calculated strictly by deterministic formulas. AI agents provide operational reasoning, anomaly diagnosis, risk assessment, and adaptive replanning.
- **Human-in-the-Loop Governance**: Physical water dispatches and expenditure require explicit approval from an authenticated Operations Manager. AI cannot initiate physical deliveries autonomously.
- **Hardware Telemetry Ready**: High-throughput `POST /readings` ingestion endpoint protected by `X-API-Key` authentication, boundary validation, and real-time fill tracking.
- **Idempotent Delivery Lifecycle**: Deduplicated request pipeline backed by stable operation run identifiers (`operation_run_id`), preventing duplicate orders across dashboard interactions and reruns.
- **Contingency Replanning**: Dynamic recovery branches triggered automatically upon manager allocation rejection or flow meter verification discrepancies.
- **Multi-Channel Alerting**: Integrated SMTP email and modular WhatsApp messaging (Twilio / Meta Cloud API) with automated 10-minute alert deduplication.

---

## 🔄 Architecture & Closed-Loop Workflow

```
                          ┌───────────────────────────┐
                          │  IoT Sensors & Telemetry  │
                          │   (ESP32 / Ultrasonic)    │
                          └─────────────┬─────────────┘
                                        │ HTTP POST /readings (X-API-Key)
                                        ▼
                          ┌───────────────────────────┐
                          │    Backend SQLite Engine  │
                          │   (Tanks, Readings, Sites)│
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │    Demand Analysis Agent  │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │ Consumption Anomaly Agent │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                                 [Shortage > 0?]
                                  /            \
                       NO (Healthy)            YES (Shortage)
                            /                    \
                           ▼                      ▼
               ┌──────────────────────┐   ┌──────────────────────┐
               │ Procurement Skipped  │   │  Water Supply Agent  │
               │ (Reserve Sufficient) │   └──────────┬───────────┘
               └──────────────────────┘              │
                                                     ▼
                                          ┌──────────────────────┐
                                          │Dynamic Allocation Agt│
                                          └──────────┬───────────┘
                                                     │
                                                     ▼
                                          ┌──────────────────────┐
                                          │ Approval Review Agt  │
                                          └──────────┬───────────┘
                                                     │
                                                     ▼
                                       ╔════════════════════════════╗
                                       ║   HUMAN MANAGER APPROVAL   ║
                                       ╚═════════════╤══════════════╝
                                                    / \
                                         REJECTED  /   \  APPROVED
                                                  /     \
                                                 ▼       ▼
                             ┌──────────────────────┐  ┌──────────────────────┐
                             │ Replanning Agent     │  │ Delivery Agent       │
                             │ (Alternative Action) │  │ (Dispatch & ETA)     │
                             └──────────────────────┘  └──────────┬───────────┘
                                                                  │
                                                                  ▼
                                                       ┌──────────────────────┐
                                                       │  Physical Delivery   │
                                                       └──────────┬───────────┘
                                                                  │
                                                                  ▼
                                                       ┌──────────────────────┐
                                                       │ Verification Agent   │
                                                       │ (Digital Meter Slip) │
                                                       └──────────┬───────────┘
                                                                  │
                                                        [Discrepancy == 0?]
                                                          /             \
                                               YES (Verified)         NO (Discrepancy)
                                                      /                     \
                                                     ▼                       ▼
                                         ┌──────────────────────┐   ┌──────────────────────┐
                                         │ Tank Volume Updated  │   │ Replanning Agent     │
                                         │ Operation Completed  │   │ (Review Discrepancy) │
                                         └──────────────────────┘   └──────────────────────┘
```

---

## 🤖 Authoritative 8-Agent Swarm

AquaSwarm AI unifies its cognitive intelligence into an authoritative registry of **8 specialist AI agents** (`agents.registry`):

| # | Agent Name | Pipeline Stage | Primary Responsibility | Execution Type |
|---|---|---|---|---|
| **1** | **Demand Agent** | `Demand` | Computes reservoir deficit, net daily drawdown, target reserve, and days of cover. | Standard |
| **2** | **Anomaly Agent** | `Anomaly` | Detects abnormal drawoff, sudden leaks, and consumption spikes vs. rolling historical baselines. | Standard |
| **3** | **Supply Agent** | `Supply` | Discovers eligible tanker suppliers, filters by capacity, and ranks by price, distance, and ETA. | Conditional (on shortage) |
| **4** | **Allocation Agent** | `Allocation` | Optimizes delivery quantity against supplier limits and formulates the multi-site allocation quota. | Conditional (on shortage) |
| **5** | **Approval Review Agent** | `Approval` | Synthesizes operational urgency and risk to brief the human manager prior to dispatch. | Conditional (on shortage) |
| **6** | **Delivery Agent** | `Delivery` | Coordinates tanker dispatch, creates delivery orders, and tracks transit logistics. | Post-Approval |
| **7** | **Verification Agent** | `Verification` | Audits delivered volume against approved quota, calculates discrepancies, and verifies delivery notes. | Post-Delivery |
| **8** | **Replanning Agent** | `Replanning` | Formulates autonomous recovery plans when an allocation is rejected or delivery fails. | Contingency Branch |

> **Human Governance Boundary**: The **Operations Manager** is explicitly an external human authorization gate, not an agent. Physical delivery and supplier payment dispatches require manager approval.

---

## 📡 Sensor & Hardware Ingestion API

The backend exposes an asynchronous RESTful API for field telemetry (ESP32, Raspberry Pi Pico W, ultrasonic depth sensors, digital pulse flow meters).

### Endpoint: `POST /readings`
Records live water levels and hourly/daily consumption increments.

#### Network Endpoints & Addressing
- **Local Testing (Host Machine Only)**: `http://127.0.0.1:8000/readings`  
  *(Loopback address for local testing with curl, PowerShell, or Python scripts. Not reachable by external Wi-Fi microcontrollers).*
- **Physical Devices (ESP32 / Pico W on Local Wi-Fi)**: `http://<HOST_LAN_IP>:8000/readings` (e.g. `http://192.168.1.6:8000/readings`)  
  *(Reachable by microcontrollers connected to the same local network).*
- **Production Deployments**: `https://<YOUR_DOMAIN>/readings`

#### Headers
```http
Content-Type: application/json
X-API-Key: <AQUASWARM_API_KEY>
```

#### Request Payload
```json
{
  "tank_code": "TANK-001",
  "current_level": 7500.0,
  "consumption": 250.0,
  "source": "SENSOR",
  "timestamp": "2026-10-10T14:30:00Z"
}
```

#### Response (`200 OK`)
```json
{
  "status": "RECORDED",
  "message": "Reading recorded successfully for TANK-001.",
  "tank_code": "TANK-001",
  "tank_id": 1,
  "site_id": 1,
  "current_level": 7500.0,
  "capacity": 10000.0,
  "fill_percentage": 75.0,
  "consumption": 250.0,
  "source": "SENSOR",
  "timestamp": "2026-10-10T14:30:00Z",
  "updated_at": "2026-10-10T14:30:00Z"
}
```

#### Hardware Wiring Reference
- **ESP32**:
  - **JSN-SR04T Waterproof Ultrasonic**: VCC $\rightarrow$ 5V, GND $\rightarrow$ GND, TRIG $\rightarrow$ GPIO 5, ECHO $\rightarrow$ GPIO 18 *(via 1kΩ/2kΩ voltage divider to 3.3V)*.
  - **YF-S201 Flow Meter**: VCC $\rightarrow$ 5V, GND $\rightarrow$ GND, Yellow Pulse $\rightarrow$ GPIO 19 *(with 4.7kΩ pull-up resistor)*.
- **Raspberry Pi Pico W**:
  - **JSN-SR04T**: TRIG $\rightarrow$ GP3, ECHO $\rightarrow$ GP2 *(via voltage divider)*.
  - **YF-S201**: Yellow Pulse $\rightarrow$ GP4 *(with pull-up resistor)*.

#### Validation & Status
- **Authentication**: Constant-time HMAC comparison on `X-API-Key`. Missing or invalid keys return `HTTP 401 Unauthorized`.
- **Tank Verification**: Unknown tank codes return `HTTP 404 Not Found`.
- **Capacity Overflow Guard**: Submitting a `current_level` greater than the tank's maximum capacity returns `HTTP 400 Bad Request`.
- **Negative Value Guard**: Negative `consumption` or `current_level` values return `HTTP 422 Unprocessable Entity` or `HTTP 400 Bad Request`.
- **Readiness Truthfulness**: The REST ingestion API, validation guards, and simulation testbench are verified with automated test suites. Physical microcontroller deployment requires on-site enclosure mounting and bench calibration.

---

## ⚙️ Quickstart & Installation

### Prerequisites
- **Python**: Version 3.10, 3.11, 3.12, or 3.13.
- **Operating System**: Windows 10/11, macOS, or Linux.
- **API Key**: A valid [Google Gemini API Key](https://ai.google.dev/).

### 1. Clone & Set Up Virtual Environment

```powershell
# Clone the repository
git clone https://github.com/Calipha-Rayyan/AquaSwarm-AI.git
cd AquaSwarm-AI

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```powershell
cp .env.example .env
```

Edit `.env` and provide your credentials:

```ini
# Google Gemini Configuration (CrewAI cognitive provider)
GEMINI_API_KEY=AIzaSy...your_real_gemini_key_here
GEMINI_MODEL=gemini-3.5-flash-lite

# Backend Mode
# "inprocess" = Embedded database connection (recommended for local/Streamlit)
# "http"      = Separate FastAPI server (needed for external ESP32 sensor posting)
AQUASWARM_BACKEND_MODE=inprocess
AQUASWARM_API_URL=http://127.0.0.1:8000
AQUASWARM_API_KEY=generate_a_secure_token_here

# E-mail Notifications (Optional)
AQUASWARM_SMTP_HOST=smtp.gmail.com
AQUASWARM_SMTP_PORT=587
AQUASWARM_SMTP_USER=alerts@yourdomain.com
AQUASWARM_SMTP_PASSWORD=your_app_password
AQUASWARM_SMTP_FROM=AquaSwarm <alerts@yourdomain.com>

# WhatsApp Notifications (Optional: Twilio or Meta Cloud API)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=
```

> **Security Note**: Never commit `.env` to Git. The repository includes strict `.gitignore` rules protecting credentials, databases, and local video captures.

---

### 3. Launch the Application

#### Option A: Streamlit Control Center (Single-Command Run)
In standard in-process mode, running Streamlit initializes the database and backend automatically:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

#### Option B: Dual Service Architecture (Streamlit + FastAPI Ingestion Server)
If external IoT microcontrollers or sensors will post telemetry over HTTP:

**Terminal 1 (FastAPI Sensor Service):**
```powershell
.\.venv\Scripts\uvicorn.exe backend.api:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Streamlit Control Center):**
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

---

## 🔐 First-Time Administrator Setup & Account Recovery

AquaSwarm AI does not ship with hardcoded credentials. On the initial launch:
1. Navigate to `http://localhost:8501`.
2. The **Setup AquaSwarm** screen will prompt you to create the initial Administrator account.
3. **Password Security Policy**: Minimum 10 characters, containing both letters and numbers.
4. Subsequent staff (Operations Managers and Field Operators) can request access from the sign-in portal; administrators approve or reject accounts from the **Team Access** console.

### Account Recovery & CLI Tools
If you ever lock an account (triggered after 5 failed login attempts) or forget your credentials:

- **Web Reset**: Use the **Reset password** tab on the sign-in page.
  - If SMTP email is configured, a verification code is emailed to you.
  - In local development without SMTP, the one-time code is displayed immediately on-screen and printed to the terminal console.
- **Terminal CLI**: Use the built-in user management tool from PowerShell:
  ```powershell
  # List all accounts and their lockout status
  .\.venv\Scripts\python.exe -m backend.users list

  # Unlock a locked account
  .\.venv\Scripts\python.exe -m backend.users unlock <email>

  # Directly set a new password
  .\.venv\Scripts\python.exe -m backend.users reset-password <email> <new_password>
  ```

---

## 🧪 Testing & Verification

The project includes an automated test suite verifying database migrations, API authentication, validation boundaries, delivery deduplication, and AI workflows:

```powershell
# Run the complete test suite
.\.venv\Scripts\python.exe -m pytest -v tests/test_audit_fixes.py backend/test_database.py
```

### Test Coverage Highlights:
- **`test_agent_registry_count_and_roles`**: Validates authoritative 8-agent registration and role contracts.
- **`test_active_agents_lifecycle`**: Validates deterministic tracking of active agents during pipeline runs.
- **`test_readings_api_security`**: Tests constant-time `X-API-Key` authentication and 401 rejection.
- **`test_readings_api_validation_bounds`**: Verifies rejection of negative consumption, capacity overflow, and invalid tanks.
- **`test_delivery_request_deduplication_and_lifecycle`**: Confirms idempotent requests matching `operation_run_id` without database row duplication.
- **`test_supplier_constraints_and_validation`**: Validates supplier availability flags and volume capacity caps.
- **`test_delivery_rejection_and_exception_transitions`**: Tests `APPROVED`, `REJECTED`, `DISPATCHED`, `DELIVERED`, and `DELIVERY_EXCEPTION` states.
- **`test_forecasting_readiness_evaluation`**: Tests rolling averages, variance, and the 30-reading dataset ML readiness threshold.
- **`test_allocation_with_routing`**: Validates sequential multi-site route ordering by priority and proximity.
- **`test_password_strength_validation`**: Validates password length and alphanumeric requirements.

---

## 📁 Repository Structure

```text
AquaSwarm-AI/
├── agents/                      # Specialist CrewAI agent definitions
│   ├── allocation/              # Dynamic Allocation Agent
│   ├── anomaly/                 # Consumption Anomaly Agent
│   ├── approval/                # Approval Review Agent
│   ├── delivery/                # Dispatch & Delivery Agent
│   ├── demand/                  # Water Demand Agent
│   ├── replanning/              # Contingency Replanning Agent
│   ├── supply/                  # Water Supply Agent
│   ├── verification/            # Digital Meter Verification Agent
│   └── registry.py              # [Authoritative] 8-agent registry & active tracker
│
├── backend/                     # High-performance data layer & API
│   ├── __init__.py              # Windows asyncio socket stability patch
│   ├── api.py                   # FastAPI REST service & /readings telemetry endpoint
│   ├── database.py              # SQLite connection pool, schema, & auto-migration
│   ├── notify.py                # Email & WhatsApp (Twilio/Meta) notification engine
│   ├── operations.py            # Business logic, tank records, & guarded deletion
│   ├── security.py              # Constant-time API key verification & CORS rules
│   └── users.py                 # RBAC user accounts, bcrypt hashing, & sessions
│
├── config/                      # Application configuration & policy
│   └── settings.py              # Gemini LLM initialization, timeouts, & policies
│
├── data/                        # Initial seed data for facilities
│   ├── sites.csv                # Site locations and population data
│   ├── tanks.csv                # Water tanks, capacities, and baseline levels
│   ├── suppliers.csv            # Water tanker suppliers, capacity, and rates
│   └── consumption.csv          # Verified historical consumption observations
│
├── tests/                       # Automated test suites
│   └── test_audit_fixes.py      # End-to-end API, agent, & integration tests
│
├── tools/                       # Deterministic water physics tools
│   └── water_tools.py           # Shortage formulas, ML readiness, & route sequencer
│
├── ui/                          # Streamlit user interface components
│   ├── auth_pages.py            # Authentication, registration, & password validation
│   ├── dashboard.py             # Live operations dashboard & agent progress rail
│   ├── data_admin.py            # Tank metadata profiles, readings, & sensor console
│   ├── pages.py                 # Network overview, deliveries, alerts, & suppliers
│   └── theme.py                 # Aquatic dark design system & CSS styling
│
├── workflows/                   # Multi-agent flow coordinator
│   └── aquaswarm_flow.py        # CrewAI Flow orchestration & state management
│
├── app.py                       # Main Streamlit application entry point
├── aquaswarm.db                 # Local SQLite database (WAL mode)
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment configuration template
└── README.md                    # Project documentation
```

---

## 🛡️ Security & Operational Principles

- **Human-in-the-Loop Safeguards**: Critical physical logistics and financial approvals require human manager authorization.
- **Fail-Safe Fallbacks**: If external LLM calls experience latency or rate limits, the deterministic water engineering baseline safely governs tank monitoring without interruption.
- **Non-Destructive Operations**: Production data deletion controls are guarded at the code level (`developer_override=True`).
- **Platform Stability**: Includes built-in socket cleanup handlers on Windows to suppress `WinError 10054` socket resets during browser tab refreshes.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
