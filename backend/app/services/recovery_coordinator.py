import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.entities import (
    Customer,
    Payment,
    Subscription,
    RecoveryCase,
    AIDecision,
    PolicyDecision,
    RecoveryAction,
    RecoveryOutcome,
    AuditLog,
)
from backend.app.services.risk_detector import RevenueRiskDetector
from backend.app.services.diagnosis_engine import DiagnosisEngine
from backend.app.services.ai_agent import AIRecoveryAgent
from backend.app.services.policy_engine import DeterministicPolicyEngine
from backend.app.services.execution_adapter import ExecutionAdapter
from backend.app.services.value_model import RecoveryValueModel
from backend.app.config import settings

logger = logging.getLogger(__name__)


class RecoveryCoordinator:
    """
    End-to-end Orchestrator for Revenue Recovery.
    Implements the core pipeline: Ingest -> Detect -> Diagnose -> AI Propose -> Policy Authorize -> Execute -> Audit.
    """

    @classmethod
    async def process_risk_event(
        cls,
        db: AsyncSession,
        event_data: Dict[str, Any],
        auto_execute: bool = True
    ) -> RecoveryCase:
        # 1. Extract or Seed Customer
        customer_id = event_data.get("customer_id") or f"cust_{int(datetime.utcnow().timestamp())}"
        customer_email = event_data.get("customer_email") or f"{customer_id}@example.com"
        customer_phone = event_data.get("customer_phone") or "+919876543210"
        customer_name = event_data.get("customer_name") or "Enterprise Client"
        customer_ltv = float(event_data.get("customer_ltv_inr", 15000.0))

        # Check existing customer
        res = await db.execute(select(Customer).where(Customer.customer_id == customer_id))
        customer = res.scalar_one_or_none()
        if not customer:
            customer = Customer(
                customer_id=customer_id,
                name=customer_name,
                email=customer_email,
                phone=customer_phone,
                ltv_inr=customer_ltv,
                risk_tier="HIGH_VALUE" if customer_ltv > 20000 else "STANDARD"
            )
            db.add(customer)
            await db.flush()

        # 2. Extract Payment / Subscription details
        payment_id = event_data.get("payment_id") or f"pay_{int(datetime.utcnow().timestamp())}"
        subscription_id = event_data.get("subscription_id")
        amount_inr = float(event_data.get("amount_inr", 2999.0))
        payment_method = event_data.get("payment_method", "card")
        error_code = event_data.get("error_code") or "BAD_REQUEST_PAYMENT_DECLINED_BY_BANK"
        error_desc = event_data.get("error_description") or "Bank declined payment transaction"
        retry_count = int(event_data.get("previous_retry_count", 0))
        risk_age_hours = float(event_data.get("risk_age_hours", 0.0))
        is_sub = bool(subscription_id)

        # 3. Deterministic Risk Detection
        risk_assessment = RevenueRiskDetector.evaluate_risk(
            amount_inr=amount_inr,
            customer_ltv_inr=customer.ltv_inr,
            payment_method=payment_method,
            failure_count=retry_count,
            risk_age_hours=risk_age_hours,
            is_subscription=is_sub
        )

        # 4. Deterministic Diagnosis
        diagnosis = DiagnosisEngine.diagnose(
            error_code=error_code,
            error_description=error_desc,
            payment_method=payment_method,
            amount_inr=amount_inr,
            is_subscription=is_sub,
            failure_count=retry_count
        )

        # 5. Create or Find Recovery Case
        case_number = f"CASE-{datetime.utcnow().strftime('%Y%m')}-{int(datetime.utcnow().timestamp() * 1000) % 1000000:06d}"
        recovery_case = RecoveryCase(
            case_number=case_number,
            customer_id=customer.customer_id,
            payment_id=payment_id,
            subscription_id=subscription_id,
            webhook_event_id=event_data.get("webhook_event_id"),
            amount_at_risk_inr=amount_inr,
            customer_ltv_inr=customer.ltv_inr,
            urgency_score=risk_assessment.urgency_score,
            risk_age_hours=risk_assessment.risk_age_hours,
            failure_reason=diagnosis.category,
            error_code=error_code,
            error_description=error_desc,
            payment_method=payment_method,
            status="DETECTED",
            retry_count=retry_count,
            contact_count=0,
            recovery_mode="RAZORPAY_TEST_MODE" if settings.is_razorpay_configured else "SANDBOX_SIMULATION"
        )
        db.add(recovery_case)
        await db.flush()

        # Audit Log: Detection
        db.add(AuditLog(
            case_id=recovery_case.id,
            actor="RISK_DETECTOR",
            action_type="RISK_DETECTED",
            message=f"Detected revenue risk of ₹{amount_inr:,.2f} for {customer.email}. Urgency: {risk_assessment.urgency_score:.2f}.",
            metadata_json=json.dumps(risk_assessment.model_dump())
        ))

        # 6. AI Recovery Agent Proposal
        case_ctx = {
            "amount_at_risk_inr": amount_inr,
            "retry_count": retry_count,
            "contact_count": 0,
            "last_action_timestamp": None,
            "failure_category": diagnosis.category,
            "payment_method": payment_method,
            "is_subscription": is_sub,
        }
        ai_decision = await AIRecoveryAgent.evaluate_case(
            case_context=case_ctx,
            diagnosis=diagnosis,
            risk=risk_assessment
        )

        ai_db = AIDecision(
            case_id=recovery_case.id,
            model_name=settings.GEMINI_MODEL if settings.is_gemini_configured else "ReviveAI-Deterministic-Reasoner",
            diagnosis_category=ai_decision.diagnosis_category,
            diagnosis_reasoning=ai_decision.diagnosis_reasoning,
            recommended_action=ai_decision.recommended_action,
            timing_schedule_minutes=ai_decision.timing_schedule_minutes,
            expected_recovery_probability=ai_decision.expected_recovery_probability,
            confidence_score=ai_decision.confidence_score,
            reasoning_summary=ai_decision.reasoning_summary,
            known_facts_json=json.dumps(ai_decision.known_facts),
            inferred_factors_json=json.dumps(ai_decision.inferred_factors),
            unknown_factors_json=json.dumps(ai_decision.unknown_factors),
            counterfactuals_json=json.dumps([cf.model_dump() for cf in ai_decision.counterfactual_evaluations]),
            requires_human_review=ai_decision.requires_human_review,
            is_fallback=not settings.is_gemini_configured
        )
        db.add(ai_db)
        await db.flush()

        recovery_case.expected_recovery_probability = ai_decision.expected_recovery_probability
        recovery_case.confidence_score = ai_decision.confidence_score

        # Calculate EV of recommended action
        _, _, _, net_ev = RecoveryValueModel.calculate_expected_value(
            action_name=ai_decision.recommended_action,
            amount_at_risk_inr=amount_inr,
            recovery_probability=ai_decision.expected_recovery_probability,
            customer_ltv_inr=customer.ltv_inr
        )
        recovery_case.expected_recovery_value_inr = net_ev
        recovery_case.status = "ACTION_PROPOSED"

        # Audit Log: AI Decision
        db.add(AuditLog(
            case_id=recovery_case.id,
            actor="AI_AGENT",
            action_type="INTERVENTION_PROPOSED",
            message=f"AI Agent recommended '{ai_decision.recommended_action}' with P={ai_decision.expected_recovery_probability:.2f}, EV=₹{net_ev:,.2f}.",
            metadata_json=json.dumps(ai_decision.model_dump())
        ))

        # 7. Deterministic Safety & Policy Engine Check
        policy_res = DeterministicPolicyEngine.evaluate_authorization(
            case_context=case_ctx,
            ai_decision=ai_decision
        )

        policy_db = PolicyDecision(
            case_id=recovery_case.id,
            ai_decision_id=ai_db.id,
            is_authorized=policy_res.is_authorized,
            action_approved=policy_res.action_approved,
            stopping_rule_triggered=policy_res.stopping_rule_triggered,
            rule_evaluations_json=json.dumps([r.model_dump() for r in policy_res.rule_evaluations]),
            rejection_reasons_json=json.dumps(policy_res.rejection_reasons),
            requires_human_review=policy_res.requires_human_review
        )
        db.add(policy_db)
        await db.flush()

        # Audit Log: Policy Evaluation
        db.add(AuditLog(
            case_id=recovery_case.id,
            actor="POLICY_ENGINE",
            action_type="POLICY_EVALUATED",
            message=f"Policy authorization {'APPROVED' if policy_res.is_authorized else 'REJECTED/HELD'}. Approved Action: '{policy_res.action_approved}'.",
            metadata_json=json.dumps(policy_res.model_dump())
        ))

        # 8. Execution or Escalation
        if policy_res.requires_human_review:
            recovery_case.status = "ESCALATED"
        elif not policy_res.is_authorized:
            if policy_res.stopping_rule_triggered:
                recovery_case.status = "STOPPED"
            else:
                recovery_case.status = "POLICY_REJECTED"
        else:
            recovery_case.status = "POLICY_APPROVED"

            if auto_execute and policy_res.action_approved and policy_res.action_approved != "stop_recovery":
                recovery_case.status = "EXECUTING"
                action_to_run = policy_res.action_approved

                # Record Action
                action_db = RecoveryAction(
                    case_id=recovery_case.id,
                    policy_decision_id=policy_db.id,
                    action_type=action_to_run,
                    status="EXECUTING",
                    scheduled_for=datetime.utcnow() + timedelta(minutes=ai_decision.timing_schedule_minutes),
                    execution_mode=recovery_case.recovery_mode
                )
                db.add(action_db)
                await db.flush()

                # Execute via Adapter
                exec_result = await ExecutionAdapter.execute_action(
                    action_type=action_to_run,
                    amount_inr=amount_inr,
                    customer_email=customer.email,
                    customer_phone=customer.phone,
                    payment_id=payment_id,
                    subscription_id=subscription_id,
                    failure_category=diagnosis.category,
                    predicted_prob=ai_decision.expected_recovery_probability,
                    timing_minutes=ai_decision.timing_schedule_minutes
                )

                action_db.status = "SUCCEEDED" if exec_result.success else "FAILED"
                action_db.executed_at = datetime.utcnow()
                action_db.cost_inr = exec_result.cost_inr
                action_db.friction_penalty = exec_result.friction_penalty
                action_db.execution_details_json = json.dumps(exec_result.details)

                # Record Outcome
                outcome_db = RecoveryOutcome(
                    case_id=recovery_case.id,
                    action_id=action_db.id,
                    is_recovered=exec_result.is_recovered,
                    recovered_amount_inr=exec_result.recovered_amount_inr,
                    time_to_recovery_hours=0.5,
                    actual_cost_inr=exec_result.cost_inr,
                    outcome_reason=exec_result.outcome_reason
                )
                db.add(outcome_db)

                recovery_case.status = "RECOVERED" if exec_result.is_recovered else "FAILED"
                if "retry" in action_to_run:
                    recovery_case.retry_count += 1
                if "reminder" in action_to_run or "update_request" in action_to_run:
                    recovery_case.contact_count += 1
                recovery_case.last_action_timestamp = datetime.utcnow()
                if exec_result.is_recovered:
                    recovery_case.resolved_at = datetime.utcnow()

                # Audit Log: Execution Outcome
                db.add(AuditLog(
                    case_id=recovery_case.id,
                    actor="EXECUTOR",
                    action_type="ACTION_EXECUTED",
                    message=f"Executed '{action_to_run}'. Outcome: {'RECOVERED ₹' + f'{exec_result.recovered_amount_inr:,.2f}' if exec_result.is_recovered else 'UNRECOVERED'}.",
                    metadata_json=json.dumps({
                        "is_recovered": exec_result.is_recovered,
                        "recovered_amount": exec_result.recovered_amount_inr,
                        "cost": exec_result.cost_inr,
                        "details": exec_result.details
                    })
                ))

        await db.commit()
        await db.refresh(recovery_case)
        return recovery_case
