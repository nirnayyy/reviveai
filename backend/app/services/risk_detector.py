from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel


class RiskAssessment(BaseModel):
    amount_at_risk_inr: float
    customer_ltv_inr: float
    customer_tier: str  # VIP, HIGH_VALUE, STANDARD, AT_RISK
    urgency_score: float  # 0.0 (low) to 1.0 (immediate critical)
    risk_age_hours: float
    baseline_recovery_rate_prior: float
    is_high_value: bool
    requires_urgent_action: bool


class RevenueRiskDetector:
    """
    Deterministic Revenue Risk Detector.
    Evaluates financial exposure, customer importance, and time decay without hallucinations.
    """

    @classmethod
    def evaluate_risk(
        cls,
        amount_inr: float,
        customer_ltv_inr: float,
        payment_method: str,
        failure_count: int = 0,
        risk_age_hours: float = 0.0,
        is_subscription: bool = False
    ) -> RiskAssessment:
        # Determine Customer Tier
        if customer_ltv_inr >= 50000.0:
            customer_tier = "VIP"
        elif customer_ltv_inr >= 15000.0:
            customer_tier = "HIGH_VALUE"
        elif customer_ltv_inr < 2000.0 and failure_count >= 2:
            customer_tier = "AT_RISK"
        else:
            customer_tier = "STANDARD"

        is_high_value = customer_tier in ("VIP", "HIGH_VALUE") or amount_inr >= 10000.0

        # Baseline Prior Recovery Probabilities by Method & Failure Count
        method_base = {
            "card": 0.65,
            "upi": 0.58,
            "netbanking": 0.52,
            "emi": 0.45,
            "wallet": 0.50
        }.get(payment_method.lower(), 0.55)

        # Decay prior with repeated failures & age
        decay_factor = max(0.15, 1.0 - (failure_count * 0.22) - (risk_age_hours * 0.01))
        baseline_prior = max(0.05, min(0.95, method_base * decay_factor))

        # Urgency Calculation
        # Subscriptions expiring soon or high amount failures with fresh risk have higher urgency
        urgency = 0.4  # base
        if is_subscription:
            urgency += 0.25
        if is_high_value:
            urgency += 0.20
        if failure_count >= 2:
            urgency += 0.15
        if risk_age_hours > 72.0:
            # Overdue urgency drops because chance of cold churn is high
            urgency = max(0.2, urgency - 0.2)
        
        urgency_score = min(1.0, max(0.1, urgency))
        requires_urgent = urgency_score >= 0.75 or is_high_value

        return RiskAssessment(
            amount_at_risk_inr=amount_inr,
            customer_ltv_inr=customer_ltv_inr,
            customer_tier=customer_tier,
            urgency_score=round(urgency_score, 2),
            risk_age_hours=round(risk_age_hours, 1),
            baseline_recovery_rate_prior=round(baseline_prior, 3),
            is_high_value=is_high_value,
            requires_urgent_action=requires_urgent
        )
