# ReviveAI

## Adaptive AI Revenue Recovery Agent

ReviveAI is an intelligent, bounded revenue recovery engine for Razorpay merchants. When recurring subscriptions fail, checkout payments are declined, or invoices become overdue, ReviveAI diagnoses the root cause, calculates expected recovery values across candidate interventions, enforces deterministic policy guardrails, and executes bounded recovery workflows in Razorpay Test Mode or Sandbox Simulation.

---

## Problem

Merchants experience significant revenue leakage from failed payments, expired cards, UPI AutoPay mandate revocations, and checkout abandonments. Standard industry recovery mechanisms suffer from two major flaws:
1. **Blind Naive Retries**: Re-attempting failed charges on arbitrary 24-hour schedules without diagnosing the decline cause wastes gateway fees, irritates cardholders, and incurs risk penalties on hard declines (e.g., lost or stolen cards).
2. **Customer Friction & Churn**: Bombarding users with intrusive communications without timing optimization increases churn and customer dissatisfaction.

---

## Solution

ReviveAI introduces an adaptive recovery paradigm centered on the principle: **"LLM Proposes, Deterministic Policy Authorizes, Executor Executes"**.

1. **Revenue Risk Detection**: Evaluates financial exposure, customer lifetime value (LTV), urgency, and risk decay.
2. **Epistemic Root Cause Diagnosis**: Distinguishes verified data facts from statistical inferences and unobservables to prevent hallucinations.
3. **Expected Recovery Value ($EV$) Optimization**: Selects actions that maximize net recovered revenue:
   $$EV = P(\text{recovery} \mid \text{context}, \text{action}) \times \text{Amount} - \text{InterventionCost} - \text{FrictionPenalty}$$
4. **Deterministic Policy Gate**: Enforces hardcoded limits on retry counts ($\le 3$), minimum cooldown intervals (24h), hard decline rejections, and stopping rules ($EV \le 0$).
5. **Bounded Execution**: Integrates with official Razorpay Test Mode APIs (`rzp_test_...`) and high-fidelity sandbox simulation.
6. **Immutable Audit Trail**: Append-only event tracking for compliance, governance, and model evaluation.

---

## Why AI?

### Where AI Adds Value
* **Contextual Diagnosis**: Multi-factor synthesis across customer history, payment method, gateway error codes, and temporal patterns.
* **Counterfactual Intervention Scoring**: Reasoning through trade-offs across 8 candidate recovery actions to formulate recovery probabilities.
* **Operational Explainability**: Providing plain-language rationale for merchant risk teams without speculative hallucinations.

### Where Deterministic Logic Is Intentionally Used
* **Arithmetic & Financial Equations**: LLMs are never trusted with arithmetic.
* **Policy Authorizations & Stopping Rules**: Rate limits, cooldowns, and stopping rules are hardcoded in deterministic Python.
* **Cryptographic Signatures & Idempotency**: HMAC-SHA256 verification and event deduplication remain strictly deterministic.
* **10,000-Event Benchmark Runs**: Large-scale evaluation uses statistical scoring (Layer 2) to eliminate unnecessary LLM rate limits and token costs.

---

## Core Workflow

```
Revenue at Risk → Epistemic Diagnosis → Candidate Actions → AI Proposal → Policy Gate → Execution → Outcome Tracking → Audit Log
```

---

## Architecture

```
                                    +-----------------------------------------+
                                    |     Razorpay Webhook / Synthetic Ingest |
                                    +-----------------------------------------+
                                                         |
                                                         v
                                    +-----------------------------------------+
                                    |      Webhook Ingestion & Idempotency    |
                                    |   (HMAC-SHA256 Signature + Event Dedupe)|
                                    +-----------------------------------------+
                                                         |
                                                         v
                                    +-----------------------------------------+
                                    |         Revenue Risk Detector           |
                                    |  (Amount at Risk, Customer LTV, Urgency)|
                                    +-----------------------------------------+
                                                         |
                                                         v
                                    +-----------------------------------------+
                                    |            Diagnosis Engine             |
                                    |     (Known Facts vs Inferences vs Unk)  |
                                    +-----------------------------------------+
                                                         |
                                                         v
                                    +-----------------------------------------+
                                    |            AI Recovery Agent            |
                                    |     (Gemini 3.7 Flash / Reasoner)       |
                                    |  Structured Proposal + Counterfactuals  |
                                    +-----------------------------------------+
                                                         |
                                                         v
                                    +-----------------------------------------+
                                    |    Deterministic Policy & Safety Engine |
                                    |   - Max 3 Retries                       |
                                    |   - Min 24h Cooldown                    |
                                    |   - Hard Decline Rejection (0% Retries) |
                                    |   - Autonomous Amount Limit (<= ₹50,000)|
                                    |   - Stopping Rules (EV <= 0)            |
                                    +-----------------------------------------+
                                        /                                 \
                         [Authorized]  /                                   \ [Rejected / Held]
                                      v                                     v
                 +--------------------------+                      +-----------------------+
                 |    Execution Adapter     |                      | Human Review / Stopped|
                 | - Razorpay Test Mode SDK |                      | (Operator Sign-off)   |
                 | - Sandbox Simulator      |                      +-----------------------+
                 +--------------------------+                                   |
                              |                                                  |
                              +--------------------+-----------------------------+
                                                   |
                                                   v
                                    +-----------------------------------------+
                                    |      Outcome Tracker & Audit Log        |
                                    |    (Append-Only Event Store / SQLite)   |
                                    +-----------------------------------------+
                                                   |
                                                   v
                                    +-----------------------------------------+
                                    |     Razorpay-Inspired Operations UI     |
                                    |      (React 18 + Vite + TypeScript)     |
                                    +-----------------------------------------+
```

---

## Key Engineering Decisions

1. **Decoupled Proposal & Authorization**: The AI recommends actions via Pydantic structured schemas; the policy engine enforces deterministic legal and business bounds.
2. **Epistemic Fact vs. Inference vs. Unknown Separation**: Prevents financial hallucinations by categorizing data before LLM reasoning.
3. **Tiered AI Cost Architecture**: Large batches (10k+ cases) run on lightweight statistical decision layers, preserving Gemini quotas for ambiguous and high-value edge cases.
4. **Idempotent Deduplication**: Rejects duplicate webhook payloads by checking stored unique event identifiers.
5. **Heuristic Offline Fallback**: Guarantees 100% operational availability if Gemini encounters rate limits or network degradation.

---

## Razorpay Integration

* **Test Mode Only**: Integrates directly with official Razorpay Test Mode APIs (`rzp_test_...`) for creating payment links and managing subscriptions.
* **Safety Lockout**: The application validates API keys at startup and terminates immediately if live credentials (`rzp_live_...`) are detected.
* **Sandbox Simulator**: Provides high-fidelity stochastic simulation for local unit testing and reproducible benchmark generation.

---

## Evaluation Results (10,000 Payment Events)

Reproducible command: `python evaluation/run_evaluation.py --samples 10000`

| Metric | Baseline (Fixed Naive Retry) | ReviveAI (Adaptive Agent) | Net Difference / Lift |
| :--- | :--- | :--- | :--- |
| **Evaluated Events** | 10,000 | 10,000 | Identical Test Split |
| **Total Revenue at Risk** | ₹89,646,925.57 | ₹89,646,925.57 | - |
| **Recovered Events** | 4,107 | **6,722** | **+2,615 (+63.7%)** |
| **Recovery Rate (%)** | 41.07% | **67.22%** | **+26.15% Absolute Lift** |
| **Total Recovered Revenue** | ₹37,439,603.18 | **₹61,399,308.00** | **+₹23,959,704.82 (+64.0%)** |
| **Direct Intervention Cost** | ₹91,990.00 | **₹26,990.00** | **-₹65,000.00 (Saved)** |
| **Net Economic Benefit Lift** | ₹0.00 | **+₹23,984,419.82** | **+₹23.98M Net Uplift** |
| **Avg Attempts per Case** | 1.84 | **1.00** | **-0.84 (Friction reduced)** |
| **Hard Declines Intercepted** | 0 (Wasted retries) | **100% Intercepted (19 cases)** | **Zero gateway penalty** |
| **Human Review Escalations** | 0 (Unchecked) | **272 high-value cases** | **Safety bounded** |

---

## Failure Analysis

* **Unrecoverable Cases (7%)**: Closed bank accounts or revoked mandates cannot be recovered on the existing token. ReviveAI intercepts these early and requests new payment methods.
* **Policy Rejections**: Actions proposing retries on hard declines or violating cooldown periods are automatically rejected by policy.
* **Human Escalations**: Transactions exceeding ₹50,000 are escalated to human operators to mitigate high-value tail risk.

---

## Tech Stack

* **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2, aiosqlite / asyncpg
* **AI & LLM**: Google Gemini 3.7 Flash (`google-genai` SDK), Structured JSON Schema output, In-memory Decision Caching
* **Payment Integration**: Razorpay Python SDK (`razorpay`), HMAC-SHA256 Webhook Verification
* **Frontend**: React 18, Vite, TypeScript, Lucide Icons, Vanilla CSS (Razorpay Design Tokens)
* **Testing & Evaluation**: Pytest, Pytest-Asyncio, HTTPX

---

## Local Setup

### 1. Clone & Configure
```bash
git clone <repo-url>
cd reviveai
copy .env.example .env
```

### 2. Start Backend Server
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows (.venv/bin/activate on Linux/macOS)
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --port 8000 --reload
```
*API documentation available at `http://127.0.0.1:8000/docs`.*

### 3. Start Frontend Operations UI
```bash
cd frontend
npm install
npm run dev
```
*UI accessible at `http://127.0.0.1:5173/`.*

---

## Database Setup

* **SQLite (Default)**: Initialized automatically on startup for zero-friction local execution.
* **PostgreSQL / Supabase**: Apply migrations located in `backend/migrations/`:
  ```bash
  # In Supabase SQL Editor:
  # 1. Run backend/migrations/001_initial_schema.sql
  # 2. Run backend/migrations/002_seed_data.sql
  ```

---

## Evaluation Reproduction

To execute the 10,000-event benchmark and reproduce all metrics:
```bash
python evaluation/run_evaluation.py --samples 10000
```
Results are saved to `evaluation/evaluation_results.json`.

---

## Project Structure

```
reviveai/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI REST endpoints
│   │   ├── models/          # SQLAlchemy ORM entities
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── services/        # Core business & AI services
│   │   ├── config.py        # Settings with Test Mode validation
│   │   ├── database.py      # Async database connection
│   │   └── main.py          # App entrypoint & CORS
│   ├── migrations/          # PostgreSQL / Supabase SQL DDL & Seed scripts
│   └── requirements.txt
├── evaluation/
│   ├── synthetic_generator.py # 10k realistic dataset generator
│   ├── baseline_engine.py     # Naive retry baseline comparator
│   ├── run_evaluation.py      # Reproducible evaluation runner
│   └── evaluation_results.json # Measured benchmark data
├── frontend/
│   ├── src/
│   │   ├── components/      # Operations UI views & modals
│   │   ├── services/api.ts  # Typed API client
│   │   ├── types/index.ts   # TypeScript interfaces
│   │   └── index.css        # Razorpay design tokens
│   └── package.json
├── tests/                   # 12 automated unit, integration, and E2E tests
├── FINAL_SUBMISSION_AND_EVALUATION_REPORT.md
├── pytest.ini
└── README.md
```

---

## Limitations & Future Work

* **Distributed Queueing**: Current asynchronous processing uses FastAPI background tasks; future versions will introduce Celery/Redis for multi-worker scale.
* **Online Contextual Bandits**: Extending the statistical scoring layer with online Thompson Sampling for continuous learning from merchant outcomes.
