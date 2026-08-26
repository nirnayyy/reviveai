import pytest
from backend.app.services.risk_detector import RevenueRiskDetector


def test_vip_customer_risk_evaluation():
    risk = RevenueRiskDetector.evaluate_risk(
        amount_inr=15000.0,
        customer_ltv_inr=75000.0,
        payment_method="card",
        failure_count=0,
        risk_age_hours=1.0,
        is_subscription=True
    )
    assert risk.customer_tier == "VIP"
    assert risk.is_high_value is True
    assert risk.urgency_score >= 0.7
    assert risk.amount_at_risk_inr == 15000.0


def test_standard_customer_repeated_failure():
    risk = RevenueRiskDetector.evaluate_risk(
        amount_inr=1999.0,
        customer_ltv_inr=4500.0,
        payment_method="upi",
        failure_count=3,
        risk_age_hours=48.0,
        is_subscription=False
    )
    assert risk.customer_tier == "STANDARD"
    # Prior should decay with repeated failures
    assert risk.baseline_recovery_rate_prior < 0.40
