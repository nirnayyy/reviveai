from typing import Dict, Tuple
from backend.app.config import settings


class RecoveryValueModel:
    """
    Computes Expected Recovery Value (EV) and economic trade-offs:
    EV = (P_recovery * Amount_At_Risk) - Intervention_Cost - Friction_Penalty
    """

    ACTION_COSTS: Dict[str, float] = {
        "delayed_retry": settings.COST_PER_RETRY_INR,
        "smart_timing_retry": settings.COST_PER_RETRY_INR,
        "payment_method_update_request": settings.COST_PER_EMAIL_INR,
        "customer_reminder_email": settings.COST_PER_EMAIL_INR,
        "customer_reminder_whatsapp": settings.COST_PER_WHATSAPP_INR,
        "incentive_grace_period": 50.0,
        "escalate_to_human_review": settings.COST_HUMAN_REVIEW_INR,
        "stop_recovery": 0.0,
    }

    ACTION_FRICTION: Dict[str, float] = {
        "delayed_retry": settings.FRICTION_PENALTY_RETRY,
        "smart_timing_retry": settings.FRICTION_PENALTY_RETRY * 0.5,  # Less friction because timed smartly
        "payment_method_update_request": settings.FRICTION_PENALTY_EMAIL * 0.8,
        "customer_reminder_email": settings.FRICTION_PENALTY_EMAIL,
        "customer_reminder_whatsapp": settings.FRICTION_PENALTY_WHATSAPP,
        "incentive_grace_period": 0.0,  # Positive delight, zero friction
        "escalate_to_human_review": 10.0,
        "stop_recovery": 0.0,
    }

    @classmethod
    def calculate_expected_value(
        cls,
        action_name: str,
        amount_at_risk_inr: float,
        recovery_probability: float,
        customer_ltv_inr: float = 0.0
    ) -> Tuple[float, float, float, float]:
        """
        Calculates:
        - gross_expected_inr: P * Amount
        - cost_inr: Direct cost
        - friction_penalty_inr: Customer fatigue / churn risk scaled by customer LTV
        - net_expected_value_inr: gross - cost - friction
        """
        prob = max(0.0, min(1.0, recovery_probability))
        gross_expected = prob * amount_at_risk_inr
        
        base_cost = cls.ACTION_COSTS.get(action_name, 5.0)
        base_friction = cls.ACTION_FRICTION.get(action_name, 10.0)
        
        # High LTV customers have a higher penalty for intrusive communications
        if customer_ltv_inr > 25000 and "whatsapp" in action_name:
            base_friction *= 1.5
        elif customer_ltv_inr > 50000 and "retry" in action_name:
            base_friction *= 1.2

        net_ev = gross_expected - base_cost - base_friction

        return gross_expected, base_cost, base_friction, net_ev
