import random
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.app.database import get_db, init_db
from backend.app.schemas.cases import BatchSimulationRequest
from backend.app.schemas.events import SyntheticRiskEventCreate
from backend.app.services.recovery_coordinator import RecoveryCoordinator

router = APIRouter(prefix="/api/simulation", tags=["Simulation"])

PRESET_SCENARIOS = {
    "insufficient_funds_spike": {
        "error_code": "BAD_REQUEST_PAYMENT_DECLINED_BY_BANK",
        "error_description": "Payment declined due to insufficient balance in account",
        "payment_method": "card",
        "amounts": [999.0, 1999.0, 3499.0, 4999.0, 8999.0],
    },
    "subscription_mandate_churn": {
        "error_code": "BAD_REQUEST_UPI_MANDATE_REVOKED",
        "error_description": "UPI recurring mandate auto-charge failed or revoked",
        "payment_method": "upi",
        "amounts": [499.0, 999.0, 1499.0, 2499.0],
    },
    "expired_cards_wave": {
        "error_code": "BAD_REQUEST_PAYMENT_CARD_EXPIRED",
        "error_description": "The card has expired. Please use a valid card",
        "payment_method": "card",
        "amounts": [1299.0, 2999.0, 5999.0],
    },
    "temporary_gateway_outage": {
        "error_code": "GATEWAY_ERROR",
        "error_description": "Bank network connection timed out during capture",
        "payment_method": "netbanking",
        "amounts": [3500.0, 7500.0, 12000.0, 25000.0],
    },
    "hard_declines_stolen": {
        "error_code": "BAD_REQUEST_PAYMENT_CARD_STOLEN",
        "error_description": "Card reported lost or stolen by customer",
        "payment_method": "card",
        "amounts": [1999.0, 4500.0, 9999.0],
    },
    "high_value_enterprise": {
        "error_code": "BAD_REQUEST_PAYMENT_LIMIT_EXCEEDED",
        "error_description": "Corporate card single-transaction credit limit exceeded",
        "payment_method": "card",
        "amounts": [55000.0, 85000.0, 120000.0],
    }
}


@router.post("/batch")
async def run_batch_simulation(
    req: BatchSimulationRequest,
    db: AsyncSession = Depends(get_db)
):
    created_cases = []
    scenario_keys = list(PRESET_SCENARIOS.keys())

    for i in range(req.count):
        if req.scenario == "mixed_distribution":
            # Weighted distribution: 40% insufficient funds, 20% expired, 15% gateway, 15% UPI, 10% hard declines
            sc_key = random.choices(
                population=[
                    "insufficient_funds_spike",
                    "subscription_mandate_churn",
                    "expired_cards_wave",
                    "temporary_gateway_outage",
                    "hard_declines_stolen",
                    "high_value_enterprise"
                ],
                weights=[0.40, 0.20, 0.15, 0.12, 0.08, 0.05],
                k=1
            )[0]
        else:
            sc_key = req.scenario if req.scenario in PRESET_SCENARIOS else "insufficient_funds_spike"

        sc = PRESET_SCENARIOS[sc_key]
        amt = random.choice(sc["amounts"])
        cust_num = random.randint(1000, 9999)
        ltv = amt * random.choice([2.5, 4.0, 6.5, 12.0])

        event_data = {
            "customer_id": f"cust_sim_{cust_num}",
            "customer_name": f"Merchant Client {cust_num}",
            "customer_email": f"client_{cust_num}@fintech-corp.in",
            "customer_phone": f"+9198{random.randint(10000000, 99999999)}",
            "customer_ltv_inr": round(ltv, 2),
            "amount_inr": amt,
            "payment_id": f"pay_sim_{int(datetime.utcnow().timestamp())}_{i}",
            "subscription_id": f"sub_sim_{cust_num}" if "mandate" in sc_key or random.random() < 0.4 else None,
            "payment_method": sc["payment_method"],
            "error_code": sc["error_code"],
            "error_description": sc["error_description"],
            "previous_retry_count": 0 if random.random() > 0.3 else 1,
            "risk_age_hours": random.choice([0.5, 2.0, 8.0, 24.0, 48.0]),
        }

        case = await RecoveryCoordinator.process_risk_event(db, event_data, auto_execute=req.auto_process)
        created_cases.append({
            "case_number": case.case_number,
            "amount": case.amount_at_risk_inr,
            "failure_reason": case.failure_reason,
            "status": case.status
        })

    return {
        "status": "success",
        "simulated_count": len(created_cases),
        "scenario": req.scenario,
        "sample_cases": created_cases[:5]
    }


@router.post("/event")
async def inject_custom_event(
    event: SyntheticRiskEventCreate,
    db: AsyncSession = Depends(get_db)
):
    event_dict = event.model_dump()
    case = await RecoveryCoordinator.process_risk_event(db, event_dict, auto_execute=True)
    return {
        "status": "success",
        "case_id": case.id,
        "case_number": case.case_number,
        "amount_at_risk_inr": case.amount_at_risk_inr,
        "status": case.status,
        "failure_reason": case.failure_reason,
        "expected_recovery_value_inr": case.expected_recovery_value_inr
    }


@router.post("/reset")
async def reset_simulation_data(db: AsyncSession = Depends(get_db)):
    """
    Clears all cases and logs for a fresh, clean demonstration.
    """
    await db.execute(text("DELETE FROM audit_logs"))
    await db.execute(text("DELETE FROM recovery_outcomes"))
    await db.execute(text("DELETE FROM recovery_actions"))
    await db.execute(text("DELETE FROM policy_decisions"))
    await db.execute(text("DELETE FROM ai_decisions"))
    await db.execute(text("DELETE FROM recovery_cases"))
    await db.execute(text("DELETE FROM webhook_events"))
    await db.commit()

    return {"status": "success", "message": "Simulation environment reset clean."}
