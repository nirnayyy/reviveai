from typing import List, Optional
from pydantic import BaseModel, Field


class CounterfactualEvaluation(BaseModel):
    action_name: str = Field(description="Name of the candidate intervention")
    recovery_probability: float = Field(ge=0.0, le=1.0, description="Estimated recovery probability")
    expected_recovered_inr: float = Field(description="Gross expected recovered amount (P * Amount)")
    intervention_cost_inr: float = Field(description="Operational direct cost of this intervention")
    friction_penalty_inr: float = Field(description="Estimated penalty for customer irritation or churn risk")
    expected_net_value_inr: float = Field(description="Net expected recovery value (P * Amount - Cost - Friction)")
    tradeoff_summary: str = Field(description="Pros and cons of choosing this alternative")


class AIDecisionSchema(BaseModel):
    diagnosis_category: str = Field(
        description="Root cause category: insufficient_funds, expired_payment_method, bank_decline_temporary, bank_decline_hard, auth_abandonment, upi_mandate_failed, subscription_halted, overdue_receivable, unknown_ambiguous"
    )
    diagnosis_reasoning: str = Field(
        description="Detailed technical diagnosis of why the payment or subscription entered a risk state"
    )
    known_facts: List[str] = Field(
        description="List of verified, data-backed facts strictly present in the payment metadata and Razorpay error codes"
    )
    inferred_factors: List[str] = Field(
        description="Plausible contextual or statistical inferences drawn from customer history, failure patterns, or timing"
    )
    unknown_factors: List[str] = Field(
        description="Explicitly identified unobservable variables or missing data points to prevent hallucination"
    )
    recommended_action: str = Field(
        description="One of: delayed_retry, smart_timing_retry, payment_method_update_request, customer_reminder_email, customer_reminder_whatsapp, incentive_grace_period, escalate_to_human_review, stop_recovery"
    )
    timing_schedule_minutes: int = Field(
        default=0,
        description="Optimal delay in minutes before executing the action (e.g. 0 for immediate, 1440 for 24h, 7200 for salary cycle)"
    )
    expected_recovery_probability: float = Field(
        ge=0.0, le=1.0,
        description="Estimated probability of successful recovery for the recommended action"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Model confidence in this assessment based on data completeness and pattern clarity"
    )
    reasoning_summary: str = Field(
        description="Clear, operational explanation of why this specific action and timing was chosen over alternatives"
    )
    counterfactual_evaluations: List[CounterfactualEvaluation] = Field(
        description="Comparative analysis of alternative interventions and their expected value trade-offs"
    )
    requires_human_review: bool = Field(
        default=False,
        description="Flag indicating if edge-case ambiguity or extreme sensitivity warrants human operator sign-off"
    )
