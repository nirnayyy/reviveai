# ReviveAI

Autonomous revenue recovery and intelligent dunning engine built for Razorpay merchants.

When subscriptions fail, card transactions decline, or UPI AutoPay mandates bounce, ReviveAI diagnoses the root cause, calculates net expected recovery values ($EV$) across candidate actions, enforces deterministic safety guardrails, and executes bounded recovery actions through Razorpay Test Mode or sandbox simulation.

```
LLM Proposes → Deterministic Policy Authorizes → Executor Executes
```

## System Architecture

```mermaid
flowchart LR
    A["1. Ingestion<br/>Razorpay Webhook<br/>+ HMAC Verification"] --> B["2. Diagnosis & AI<br/>Root Cause Analysis<br/>+ Gemini 3.7 EV Scoring"]
    B --> C{"3. Policy Gate<br/>Retry Limits & Cooldowns<br/>Hard Decline Block"}
    C -->|Approved| D["4. Bounded Execution<br/>Razorpay Test SDK<br/>/ Sandbox Simulator"]
    C -->|High Risk| E["Human Review<br/>Operator Sign-off"]
    D --> F[("5. Audit & UI<br/>Append-Only Event Store<br/>+ React Dashboard")]
    E --> F
```

## Recovery Lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant Gateway as Razorpay Gateway
    participant Revive as ReviveAI Engine
    participant Policy as Policy Gate
    participant Exec as Execution & Audit

    Gateway->>Revive: Payment Fails (`payment.failed` webhook)
    Revive->>Revive: Diagnose root cause & calculate Expected Value ($EV$)
    Revive->>Policy: Propose optimal action (e.g. smart retry, payment link)
    Policy->>Policy: Validate safety bounds (retry count ≤ 3, cooldown ≥ 24h)
    Policy->>Exec: Dispatch approved action & record in audit log
```

## Core Engineering Principles

### 1. Separation of AI Proposals and Policy Authorization
Probabilistic models should not have unconstrained execution authority over financial transactions. Gemini analyzes the failure context and proposes an action with counterfactual probabilities, while the deterministic Python policy engine holds sole authority to authorize, reject, or escalate the action.

### 2. Epistemic Separation of Facts, Inferences, and Unknowns
To prevent hallucinations regarding customer balances or bank conditions, input context is categorized before reasoning:
* **Known Facts**: Verified data (error codes, failure timestamps, consecutive retry count).
* **Inferences**: Behavioral likelihoods (salary liquidity windows, renewal history).
* **Unknowns**: Unobservable state (live bank account balance).

### 3. Net Expected Recovery Value ($EV$) Optimization
Actions are scored by balancing gross recovery probability against operational intervention costs and customer relationship friction:

$$EV = P(\text{recovery} \mid \text{context}, \text{action}) \times \text{Amount} - \text{InterventionCost} - \text{FrictionPenalty}$$

* Low-friction delayed retries are scheduled for temporary banking timeouts.
* WhatsApp and email update links are sent when customer action is required (expired cards, failed UPI mandates).
* Hard declines (stolen cards, closed accounts) trigger zero retries, saving gateway fees and protecting merchant reputation.

## Benchmark Evaluation Results (10,000 Payment Events)

ReviveAI was evaluated against a standard baseline (fixed 24-hour naive retry) on an identical test split of 10,000 heterogeneous payment failure events.

```bash
python evaluation/run_evaluation.py --samples 10000
```

| Metric | Baseline (Fixed Retry) | ReviveAI (Adaptive Agent) | Net Difference / Lift |
| :--- | :--- | :--- | :--- |
| **Evaluated Events** | 10,000 | 10,000 | Identical Test Split |
| **Total Revenue at Risk** | ₹89,646,925.57 | ₹89,646,925.57 | Baseline parity |
| **Recovered Events** | 4,107 | **6,722** | **+2,615 (+63.7%)** |
| **Recovery Rate (%)** | 41.07% | **67.22%** | **+26.15% Absolute Lift** |
| **Total Recovered Revenue** | ₹37,439,603.18 | **₹61,399,308.00** | **+₹23,959,704.82 (+64.0%)** |
| **Direct Intervention Cost** | ₹91,990.00 | **₹26,990.00** | **-₹65,000.00 (Saved)** |
| **Customer Friction Penalty** | ₹221,980.00 | **₹262,265.00** | Balanced trade-off |
| **Net Economic Benefit Lift** | ₹0.00 | **+₹23,984,419.82** | **+₹23.98M Net Uplift** |
| **Avg Attempts per Case** | 1.84 | **1.00** | **-0.84 (Reduced friction)** |
| **Hard Declines Intercepted** | 0 (Wasted retries) | **100% Intercepted (19 cases)** | **Zero gateway penalty** |
| **Human Review Escalations** | 0 (Unchecked) | **272 high-value cases** | **Safety bounded** |

### Breakdown by Failure Scenario

| Scenario | Baseline Rate | ReviveAI Rate | Recovered Revenue (₹) | Absolute Lift |
| :--- | :--- | :--- | :--- | :--- |
| `expired_payment_method` | 0.0% | 63.3% | ₹10,805,066.19 | **+63.3%** |
| `upi_mandate_failed` | 33.6% | 66.4% | ₹6,896,694.09 | **+32.8%** |
| `auth_abandonment` | 35.5% | 62.7% | ₹2,300,811.86 | **+27.2%** |
| `bank_decline_hard` | 0.0% | 29.6% | ₹2,631,720.07 | **+29.6%** |
| `insufficient_funds` | 60.2% | 70.9% | ₹20,351,110.69 | **+10.7%** |
| `bank_decline_temporary` | 77.4% | 86.4% | ₹18,413,905.10 | **+9.0%** |

## Configuration & Free API Keys Setup

ReviveAI runs **100% free with zero cost**. You can run entirely in local sandbox mode or add free API keys for live integration:

### 1. Razorpay Test Mode Key (Optional — ₹0 Free)
* Sign up at [https://dashboard.razorpay.com/signup](https://dashboard.razorpay.com/signup) (no bank verification needed).
* Switch the toggle to **Test Mode** (orange badge).
* Go to **Account & Settings** &rarr; **API Keys** and generate a test key.
* Add to `.env`:
  ```env
  RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxxx
  RAZORPAY_KEY_SECRET=your_test_secret_here
  RAZORPAY_WEBHOOK_SECRET=test_webhook_secret_reviveai
  ```

### 2. Google Gemini API Key (Optional — ₹0 Free)
* Get a free API key at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).
* Add to `.env`:
  ```env
  GEMINI_API_KEY=your_gemini_api_key
  GEMINI_MODEL=gemini-3.7-flash
  AI_ENABLED=true
  ```

### 3. Database (Default: SQLite local, Zero setup)
* Local SQLite runs out of the box with zero configuration: `DATABASE_URL=sqlite+aiosqlite:///./reviveai.db`.
* For Supabase PostgreSQL, set `DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.ahufzfapqdjmwctwgcku.supabase.co:5432/postgres` and run the migration files in `backend/migrations/`.

## Quickstart

### 1. Clone & Setup Environment
```bash
git clone https://github.com/nirnayyy/reviveai.git
cd reviveai
copy .env.example .env
```

### 2. Run Backend
```bash
python -m venv .venv
.venv\Scripts\activate  # On Linux/macOS: source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --port 8000 --reload
```
OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Run Frontend
```bash
cd frontend
npm install
npm run dev
```
Dashboard is available at `http://127.0.0.1:5173/`.

### 4. Run Tests & Evaluation
```bash
# Run unit & integration test suite
pytest

# Run 10k event benchmark
python evaluation/run_evaluation.py --samples 10000
```

## Repository Structure

```
reviveai/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI REST routes (cases, webhooks, simulation, audit)
│   │   ├── models/          # SQLAlchemy async ORM models
│   │   ├── schemas/         # Pydantic schemas (AI decisions, events, policies)
│   │   ├── services/        # AI agent, diagnosis, value model, policy engine, execution adapter
│   │   ├── config.py        # Central configuration & test mode validation
│   │   ├── database.py      # Async database connection & session maker
│   │   └── main.py          # FastAPI application entrypoint & middleware
│   ├── migrations/          # PostgreSQL / Supabase schema (001) & seed data (002)
│   └── requirements.txt     # Python dependencies
├── evaluation/
│   ├── synthetic_generator.py # 10k heterogeneous dataset generator
│   ├── baseline_engine.py     # Naive retry baseline comparator
│   ├── run_evaluation.py      # Benchmark runner & metric calculator
│   └── evaluation_results.json # Verified benchmark output
├── frontend/
│   ├── src/
│   │   ├── components/      # Metrics, RecoveryQueue, CaseDetailModal, SimulationRunner
│   │   ├── services/api.ts  # Typed API client
│   │   ├── types/index.ts   # TypeScript interfaces
│   │   └── index.css        # Razorpay design tokens & glassmorphic theme
│   └── package.json
├── tests/                   # 12 automated unit, integration, and E2E test suites
├── FINAL_SUBMISSION_AND_EVALUATION_REPORT.md
├── pytest.ini
└── README.md
```

## License

Apache 2.0 License. Built for the Razorpay AI Revenue Recovery Buildathon.
