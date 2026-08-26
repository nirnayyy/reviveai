from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from backend.app.config import settings
from backend.app.schemas.ai import AIDecisionSchema
from backend.app.schemas.policy import PolicyEvaluationResult, RuleEvaluation


class DeterministicPolicyEngine:
    """
    Deterministic Safety & Policy Guardrails Engine.
    Strictly guarantees that AI proposals cannot execute unauthorized, unsafe,
    excessive, or financially negative actions.
    """

    @classmethod
    def evaluate_authorization(
        cls,
        case_context: Dict[str, Any],
        ai_decision: AIDecisionSchema
    ) -> PolicyEvaluationResult:
        rule_evals: List[RuleEvaluation] = []
        rejection_reasons: List[str] = []
        requires_human = ai_decision.requires_human_review
        stopping_rule: Optional[str] = None
        action_to_approve: Optional[str] = ai_decision.recommended_action
        fallback_action: Optional[str] = None

        retry_count = case_context.get("retry_count", 0)
        contact_count = case_context.get("contact_count", 0)
        amount_inr = case_context.get("amount_at_risk_inr", 0.0)
        last_action_ts = case_context.get("last_action_timestamp")
        failure_category = case_context.get("failure_category", "")
        proposed_action = ai_decision.recommended_action
        confidence = ai_decision.confidence_score

        # ----------------------------------------------------
        # Rule 1: Maximum Retries Limit
        # ----------------------------------------------------
        is_retry_action = "retry" in proposed_action
        if is_retry_action and retry_count >= settings.MAX_RETRIES_PER_CASE:
            rejection_reasons.append(
                f"Maximum retry limit ({settings.MAX_RETRIES_PER_CASE}) reached. Proposed retry rejected."
            )
            rule_evals.append(RuleEvaluation(
                rule_name="max_retry_limit",
                passed=False,
                reason=f"Current retries ({retry_count}) >= limit ({settings.MAX_RETRIES_PER_CASE})",
                details={"current_retries": retry_count, "limit": settings.MAX_RETRIES_PER_CASE}
            ))
            stopping_rule = "MAX_RETRIES_EXCEEDED"
            action_to_approve = None
            fallback_action = "payment_method_update_request"
        else:
            rule_evals.append(RuleEvaluation(
                rule_name="max_retry_limit",
                passed=True,
                reason=f"Retry count ({retry_count}) is within limit ({settings.MAX_RETRIES_PER_CASE})"
            ))

        # ----------------------------------------------------
        # Rule 2: Minimum Cooldown Between Retries
        # ----------------------------------------------------
        if is_retry_action and last_action_ts:
            if isinstance(last_action_ts, str):
                try:
                    last_action_ts = datetime.fromisoformat(last_action_ts)
                except Exception:
                    last_action_ts = None

            if last_action_ts:
                hours_since = (datetime.utcnow() - last_action_ts).total_seconds() / 3600.0
                if hours_since < settings.MIN_HOURS_BETWEEN_RETRIES and ai_decision.timing_schedule_minutes == 0:
                    rejection_reasons.append(
                        f"Cooldown active ({hours_since:.1f}h < {settings.MIN_HOURS_BETWEEN_RETRIES}h). Immediate retry rejected."
                    )
                    rule_evals.append(RuleEvaluation(
                        rule_name="cooldown_interval",
                        passed=False,
                        reason=f"Action too soon after previous attempt ({hours_since:.1f}h < {settings.MIN_HOURS_BETWEEN_RETRIES}h)"
                    ))
                    # Adjust timing to enforce remaining cooldown
                    remaining_hours = max(1.0, settings.MIN_HOURS_BETWEEN_RETRIES - hours_since)
                    ai_decision.timing_schedule_minutes = int(remaining_hours * 60)
                else:
                    rule_evals.append(RuleEvaluation(
                        rule_name="cooldown_interval",
                        passed=True,
                        reason=f"Cooldown satisfied ({hours_since:.1f}h >= {settings.MIN_HOURS_BETWEEN_RETRIES}h)"
                    ))
            else:
                rule_evals.append(RuleEvaluation(rule_name="cooldown_interval", passed=True, reason="No previous action timestamp"))
        else:
            rule_evals.append(RuleEvaluation(rule_name="cooldown_interval", passed=True, reason="Not a retry or no previous action"))

        # ----------------------------------------------------
        # Rule 3: Maximum Contact Attempts
        # ----------------------------------------------------
        is_contact_action = "reminder" in proposed_action or "update_request" in proposed_action
        if is_contact_action and contact_count >= settings.MAX_CONTACT_ATTEMPTS:
            rejection_reasons.append(
                f"Maximum contact frequency ({settings.MAX_CONTACT_ATTEMPTS}) reached. Customer contact rejected to prevent churn."
            )
            rule_evals.append(RuleEvaluation(
                rule_name="max_contact_frequency",
                passed=False,
                reason=f"Contact attempts ({contact_count}) >= limit ({settings.MAX_CONTACT_ATTEMPTS})"
            ))
            stopping_rule = "MAX_CONTACT_LIMIT_REACHED"
            action_to_approve = "stop_recovery"
        else:
            rule_evals.append(RuleEvaluation(
                rule_name="max_contact_frequency",
                passed=True,
                reason=f"Contact attempts ({contact_count}) within limit ({settings.MAX_CONTACT_ATTEMPTS})"
            ))

        # ----------------------------------------------------
        # Rule 4: Autonomous Amount Threshold (Human Review Sign-off)
        # ----------------------------------------------------
        if amount_inr > settings.AUTONOMOUS_AMOUNT_LIMIT_INR:
            requires_human = True
            rule_evals.append(RuleEvaluation(
                rule_name="autonomous_amount_threshold",
                passed=False,
                reason=f"Amount ₹{amount_inr:,.2f} exceeds autonomous limit ₹{settings.AUTONOMOUS_AMOUNT_LIMIT_INR:,.2f}; human review mandatory"
            ))
        else:
            rule_evals.append(RuleEvaluation(
                rule_name="autonomous_amount_threshold",
                passed=True,
                reason=f"Amount ₹{amount_inr:,.2f} within autonomous limit ₹{settings.AUTONOMOUS_AMOUNT_LIMIT_INR:,.2f}"
            ))

        # ----------------------------------------------------
        # Rule 5: Confidence Threshold
        # ----------------------------------------------------
        if confidence < settings.MIN_CONFIDENCE_THRESHOLD:
            requires_human = True
            rejection_reasons.append(
                f"Confidence score ({confidence:.2f}) is below minimum safe threshold ({settings.MIN_CONFIDENCE_THRESHOLD:.2f})."
            )
            rule_evals.append(RuleEvaluation(
                rule_name="confidence_threshold",
                passed=False,
                reason=f"Confidence {confidence:.2f} < {settings.MIN_CONFIDENCE_THRESHOLD:.2f}"
            ))
        else:
            rule_evals.append(RuleEvaluation(
                rule_name="confidence_threshold",
                passed=True,
                reason=f"Confidence {confidence:.2f} >= {settings.MIN_CONFIDENCE_THRESHOLD:.2f}"
            ))

        # ----------------------------------------------------
        # Rule 6: Hard Decline Rejection
        # ----------------------------------------------------
        if failure_category == "bank_decline_hard" and is_retry_action:
            rejection_reasons.append(
                "HARD DECLINE: Card is blocked, lost, or account closed. Gateway retries strictly prohibited."
            )
            rule_evals.append(RuleEvaluation(
                rule_name="hard_decline_guard",
                passed=False,
                reason="Hard bank decline prevents automated retry"
            ))
            action_to_approve = "payment_method_update_request"
        else:
            rule_evals.append(RuleEvaluation(
                rule_name="hard_decline_guard",
                passed=True,
                reason="No hard decline constraint violated"
            ))

        # ----------------------------------------------------
        # Rule 7: Negative Expected Value Stopping Rule
        # ----------------------------------------------------
        best_cf = next((cf for cf in ai_decision.counterfactual_evaluations if cf.action_name == proposed_action), None)
        if best_cf and best_cf.expected_net_value_inr <= 0 and proposed_action != "stop_recovery":
            rejection_reasons.append(
                f"Expected Net Value is negative (₹{best_cf.expected_net_value_inr:.2f} <= 0). Action economically unviable."
            )
            rule_evals.append(RuleEvaluation(
                rule_name="positive_expected_value",
                passed=False,
                reason=f"Expected net recovery value <= ₹0.00"
            ))
            stopping_rule = "NEGATIVE_EXPECTED_VALUE"
            action_to_approve = "stop_recovery"
        else:
            rule_evals.append(RuleEvaluation(
                rule_name="positive_expected_value",
                passed=True,
                reason="Action has positive or break-even expected value"
            ))

        # Final Authorization Logic
        is_authorized = len(rejection_reasons) == 0 and not requires_human

        return PolicyEvaluationResult(
            is_authorized=is_authorized,
            action_approved=action_to_approve if is_authorized else None,
            stopping_rule_triggered=stopping_rule,
            rejection_reasons=rejection_reasons,
            rule_evaluations=rule_evals,
            requires_human_review=requires_human,
            recommended_fallback_action=fallback_action or action_to_approve
        )
