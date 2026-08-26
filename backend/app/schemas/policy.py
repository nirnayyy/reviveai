from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RuleEvaluation(BaseModel):
    rule_name: str
    passed: bool
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResult(BaseModel):
    is_authorized: bool
    action_approved: Optional[str] = None
    stopping_rule_triggered: Optional[str] = None
    rejection_reasons: List[str] = Field(default_factory=list)
    rule_evaluations: List[RuleEvaluation] = Field(default_factory=list)
    requires_human_review: bool = False
    recommended_fallback_action: Optional[str] = None
