import pytest
from datetime import datetime, timedelta
from backend.app.services.policy_engine import DeterministicPolicyEngine
from backend.app.schemas.ai import AIDecisionSchema, CounterfactualEvaluation


def create_sample_ai_decision(action: str, conf: float = 0.85, human: bool = False, net_ev: float = 500.0) -> AIDecisionSchema:
    return AIDecisionSchema(
        diagnosis_category="insufficient_funds",
        diagnosis_reasoning="Balance low",
        known_facts=["Fact 1"],
        inferred_factors=["Inference 1"],
        unknown_factors=["Unknown 1"],
        recommended_action=action,
        timing_schedule_minutes=0,
        expected_recovery_probability=0.70,
        confidence_score=conf,
        reasoning_summary="Optimal intervention",
        counterfactual_evaluations=[
            CounterfactualEvaluation(
                action_name=action,
                recovery_probability=0.70,
                expected_recovered_inr=700.0,
                intervention_cost_inr=5.0,
                friction_penalty_inr=10.0,
                expected_net_value_inr=net_ev,
                tradeoff_summary="Optimal"
            )
        ],
        requires_human_review=human
    )


def test_max_retries_rejection():
    ai_dec = create_sample_ai_decision("delayed_retry")
    ctx = {
        "amount_at_risk_inr": 2500.0,
        "retry_count": 3,  # Reached limit 3
        "contact_count": 0,
        "last_action_timestamp": None,
        "failure_category": "insufficient_funds"
    }
    res = DeterministicPolicyEngine.evaluate_authorization(ctx, ai_dec)
    assert res.is_authorized is False
    assert res.stopping_rule_triggered == "MAX_RETRIES_EXCEEDED"
    assert "payment_method_update_request" in res.recommended_fallback_action


def test_hard_decline_retry_rejection():
    ai_dec = create_sample_ai_decision("delayed_retry")
    ctx = {
        "amount_at_risk_inr": 3000.0,
        "retry_count": 0,
        "contact_count": 0,
        "last_action_timestamp": None,
        "failure_category": "bank_decline_hard"
    }
    res = DeterministicPolicyEngine.evaluate_authorization(ctx, ai_dec)
    assert res.is_authorized is False
    assert any("HARD DECLINE" in r for r in res.rejection_reasons)
    assert res.recommended_fallback_action == "payment_method_update_request"


def test_high_amount_escalation_to_human():
    ai_dec = create_sample_ai_decision("delayed_retry")
    ctx = {
        "amount_at_risk_inr": 75000.0,  # Exceeds 50,000 limit
        "retry_count": 0,
        "contact_count": 0,
        "last_action_timestamp": None,
        "failure_category": "insufficient_funds"
    }
    res = DeterministicPolicyEngine.evaluate_authorization(ctx, ai_dec)
    assert res.is_authorized is False
    assert res.requires_human_review is True


def test_negative_expected_value_stopping_rule():
    ai_dec = create_sample_ai_decision("delayed_retry", net_ev=-15.0)
    ctx = {
        "amount_at_risk_inr": 50.0,
        "retry_count": 0,
        "contact_count": 0,
        "last_action_timestamp": None,
        "failure_category": "insufficient_funds"
    }
    res = DeterministicPolicyEngine.evaluate_authorization(ctx, ai_dec)
    assert res.is_authorized is False
    assert res.stopping_rule_triggered == "NEGATIVE_EXPECTED_VALUE"
    assert res.recommended_fallback_action == "stop_recovery"
    assert res.action_approved is None
