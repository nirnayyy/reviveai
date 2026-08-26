# ReviveAI — Zero-Cost API Keys & Setup Guide

To ensure your submission stands out to hackathon judges, ReviveAI is architected to run **100% free with zero operational costs**.

This guide explains the 2 free keys that give you a live demo experience, plus how to configure them in under 3 minutes.

---

## Quick Summary of Keys

| Service | Key Needed | Cost | Why Judges Value It |
| :--- | :--- | :--- | :--- |
| **Razorpay Test Mode** | `RAZORPAY_KEY_ID`<br/>`RAZORPAY_KEY_SECRET` | **₹0 (Free)** | Allows ReviveAI to call live Razorpay APIs to generate real test payment links (`rzp.io/i/...`) and simulate webhooks directly from the official Razorpay dashboard. |
| **Google Gemini AI** | `GEMINI_API_KEY` | **₹0 (Free)** | Powers live contextual reasoning and counterfactual action scoring with Gemini 3.7 Flash. |
| **Supabase (Optional)** | `DATABASE_URL` | **₹0 (Free)** | Provides persistent cloud PostgreSQL storage. (Local SQLite is already configured if you prefer zero database setup). |

---

## 1. Razorpay Test Mode Keys (Takes 2 Minutes — ₹0 Cost)

Razorpay provides a sandbox environment with test credentials. No business registration or bank verification is required.

### Step-by-Step:
1. Go to **[https://dashboard.razorpay.com/signup](https://dashboard.razorpay.com/signup)** and sign up with any email.
2. Once inside the dashboard, look at the top navigation bar or left sidebar and ensure the toggle is set to **Test Mode** (it should show a yellow/orange **TEST MODE** badge).
3. Navigate to **Account & Settings** &rarr; **API Keys** (or go directly to `https://dashboard.razorpay.com/app/keys`).
4. Click **Generate Test Key**.
5. You will see two values:
   - **Key ID**: Starts with `rzp_test_...`
   - **Key Secret**: A random secret string (copy it immediately).
6. In your `.env` file, paste them:
   ```env
   RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxxx
   RAZORPAY_KEY_SECRET=your_test_key_secret_here
   RAZORPAY_WEBHOOK_SECRET=test_webhook_secret_reviveai
   ```

> **Safety Guarantee**: ReviveAI has a hardcoded startup safety validator that rejects live keys (`rzp_live_...`), ensuring complete financial safety.

---

## 2. Google Gemini API Key (Takes 1 Minute — ₹0 Cost)

Google AI Studio provides free API access for Gemini models with generous rate limits.

### Step-by-Step:
1. Visit **[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)**.
2. Sign in with your Google account.
3. Click **Create API Key** and select **Create API key in new project**.
4. Copy the generated key.
5. In your `.env` file, paste it:
   ```env
   GEMINI_API_KEY=AIzaSy...your_gemini_key_here
   GEMINI_MODEL=gemini-3.7-flash
   AI_ENABLED=true
   ```

---

## 3. Webhook Testing in Razorpay Dashboard (Optional Demo Feature)

To demonstrate live webhook processing to judges:
1. In your Razorpay Dashboard (in **Test Mode**), go to **Account & Settings** &rarr; **Webhooks**.
2. Click **Add New Webhook**.
3. Set **Webhook URL** to your backend URL (or ngrok/tunnel URL if demoing publicly):
   `http://localhost:8000/api/webhooks/razorpay`
4. Set **Secret** to:
   `test_webhook_secret_reviveai`
5. Under **Alert Email**, enter your email.
6. Under **Active Events**, check:
   - `payment.failed`
   - `payment.authorized`
   - `subscription.halted`
   - `subscription.pending`
7. Click **Create Webhook**.

---

## 4. Your Final `.env` Configuration

Here is how your `.env` should look for the complete live demo:

```env
APP_NAME=ReviveAI
APP_ENV=development
LOG_LEVEL=INFO
PORT=8000

# Database (Default: SQLite for local execution)
DATABASE_URL=sqlite+aiosqlite:///./reviveai.db

# Razorpay Test Mode Credentials (₹0 Free Sandbox)
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
RAZORPAY_WEBHOOK_SECRET=test_webhook_secret_reviveai

# Gemini AI Configuration (₹0 Free Google AI Studio)
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.7-flash
AI_ENABLED=true
AI_MODE=DEMO

# Policy Guardrail Defaults
MAX_RETRIES_PER_CASE=3
MIN_HOURS_BETWEEN_RETRIES=24
AUTONOMOUS_AMOUNT_LIMIT_INR=50000.0
MIN_CONFIDENCE_THRESHOLD=0.65
MAX_CONTACT_ATTEMPTS=2
```

---

## 5. Verification Checklist Before Submission

Run these two commands to confirm everything is operational:

1. **Verify Backend Tests**:
   ```bash
   pytest
   ```
   *Expected result: 12 passed in ~1.2s.*

2. **Verify 10,000-Event Benchmark**:
   ```bash
   python evaluation/run_evaluation.py --samples 10000
   ```
   *Expected result: 67.22% recovery rate, +₹23.95M net recovered revenue.*
