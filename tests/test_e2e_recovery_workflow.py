import pytest
import hmac
import hashlib
import json
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.database import init_db
from backend.app.config import settings


@pytest.mark.asyncio
async def test_health_endpoint():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "mode" in data


@pytest.mark.asyncio
async def test_webhook_hmac_and_idempotency():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "id": "evt_test_webhook_12345",
            "entity": "event",
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_001",
                        "amount": 299900,
                        "currency": "INR",
                        "status": "failed",
                        "method": "card",
                        "email": "test_e2e@merchant.com",
                        "contact": "+919876543210",
                        "error_code": "BAD_REQUEST_PAYMENT_DECLINED_BY_BANK",
                        "error_description": "Insufficient funds in bank account",
                        "created_at": 1724670000
                    }
                }
            },
            "created_at": 1724670000
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        signature = hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode(), body_bytes, hashlib.sha256).hexdigest()

        # 1. Send genuine webhook
        resp1 = await client.post(
            "/api/webhooks/razorpay",
            content=body_bytes,
            headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"}
        )
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "accepted"

        # 2. Resend identical webhook -> must return duplicate_ignored (idempotent)
        resp2 = await client.post(
            "/api/webhooks/razorpay",
            content=body_bytes,
            headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"}
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "duplicate_ignored"


@pytest.mark.asyncio
async def test_e2e_batch_simulation_and_metrics():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Reset DB first
        await client.post("/api/simulation/reset")

        # Run small batch simulation of 5 cases
        sim_resp = await client.post(
            "/api/simulation/batch",
            json={"scenario": "mixed_distribution", "count": 5, "auto_process": True}
        )
        assert sim_resp.status_code == 200
        assert sim_resp.json()["simulated_count"] == 5

        # Fetch recovery queue
        cases_resp = await client.get("/api/cases?limit=10")
        assert cases_resp.status_code == 200
        cases = cases_resp.json()
        assert len(cases) == 5

        # Fetch first case detail
        case_id = cases[0]["id"]
        detail_resp = await client.get(f"/api/cases/{case_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert len(detail["ai_decisions"]) >= 1
        assert len(detail["policy_decisions"]) >= 1

        # Fetch metrics overview
        metrics_resp = await client.get("/api/cases/metrics")
        assert metrics_resp.status_code == 200
        metrics = metrics_resp.json()
        assert metrics["total_cases"] == 5
        assert metrics["total_revenue_at_risk_inr"] > 0
