from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.ai import CounterfactualEvaluation


class ActionSummary(BaseModel):
    id: str
    action_type: str
    status: str
    scheduled_for: datetime
    executed_at: Optional[datetime] = None
    cost_inr: float
    friction_penalty: float
    execution_mode: str


class AIDecisionSummary(BaseModel):
    id: str
    model_name: str
    diagnosis_category: str
    diagnosis_reasoning: str
    recommended_action: str
    timing_schedule_minutes: int
    expected_recovery_probability: float
    confidence_score: float
    reasoning_summary: str
    known_facts: List[str]
    inferred_factors: List[str]
    unknown_factors: List[str]
    counterfactuals: List[CounterfactualEvaluation]
    requires_human_review: bool
    is_fallback: bool
    created_at: datetime


class PolicyDecisionSummary(BaseModel):
    id: str
    is_authorized: bool
    action_approved: Optional[str]
    stopping_rule_triggered: Optional[str]
    rejection_reasons: List[str]
    rule_evaluations: List[Dict[str, Any]]
    requires_human_review: bool
    created_at: datetime


class RecoveryCaseListItem(BaseModel):
    id: str
    case_number: str
    customer_id: str
    customer_name: Optional[str] = "Customer"
    customer_email: Optional[str] = None
    payment_id: Optional[str] = None
    subscription_id: Optional[str] = None
    amount_at_risk_inr: float
    customer_ltv_inr: float
    urgency_score: float
    risk_age_hours: float
    failure_reason: str
    error_code: Optional[str] = None
    payment_method: str
    status: str
    retry_count: int
    expected_recovery_probability: float
    expected_recovery_value_inr: float
    confidence_score: float
    recommended_action: Optional[str] = None
    recovery_mode: str
    created_at: datetime


class RecoveryCaseDetail(RecoveryCaseListItem):
    error_description: Optional[str] = None
    contact_count: int
    last_action_timestamp: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    ai_decisions: List[AIDecisionSummary] = Field(default_factory=list)
    policy_decisions: List[PolicyDecisionSummary] = Field(default_factory=list)
    actions: List[ActionSummary] = Field(default_factory=list)


class ManualActionRequest(BaseModel):
    action: str = Field(description="Action to manually approve: delayed_retry, smart_timing_retry, payment_method_update_request, customer_reminder_email, customer_reminder_whatsapp, stop_recovery, resolve_manually")
    timing_schedule_minutes: int = 0
    notes: Optional[str] = None


class BatchSimulationRequest(BaseModel):
    scenario: str = Field(default="mixed_distribution", description="One of: mixed_distribution, high_failure_spike, subscription_churn, high_ltv_vip, hard_declines_heavy")
    count: int = Field(default=20, ge=1, le=500, description="Number of risk events to simulate")
    auto_process: bool = Field(default=True, description="Automatically run AI diagnosis, policy authorization, and execution")


class MetricsOverview(BaseModel):
    total_cases: int
    active_cases: int
    recovered_cases: int
    failed_cases: int
    escalated_cases: int
    stopped_cases: int
    total_revenue_at_risk_inr: float
    total_recovered_revenue_inr: float
    recovery_rate_pct: float
    baseline_recovery_rate_pct: float
    net_revenue_lift_inr: float
    avg_confidence_score: float
    prevented_friction_events_count: int
    total_intervention_cost_inr: float
