import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.models.entities import (
    RecoveryCase,
    Customer,
    AIDecision,
    PolicyDecision,
    RecoveryAction,
    RecoveryOutcome,
    AuditLog,
)
from backend.app.schemas.cases import (
    RecoveryCaseListItem,
    RecoveryCaseDetail,
    AIDecisionSummary,
    PolicyDecisionSummary,
    ActionSummary,
    ManualActionRequest,
    MetricsOverview,
)
from backend.app.services.execution_adapter import ExecutionAdapter

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.get("", response_model=List[RecoveryCaseListItem])
async def list_recovery_cases(
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search case number or customer"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(RecoveryCase)
        .options(selectinload(RecoveryCase.customer), selectinload(RecoveryCase.ai_decisions))
        .order_by(desc(RecoveryCase.created_at))
    )

    if status and status != "ALL":
        query = query.where(RecoveryCase.status == status)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    cases = result.scalars().all()

    items = []
    for c in cases:
        rec_action = c.ai_decisions[-1].recommended_action if c.ai_decisions else None
        items.append(RecoveryCaseListItem(
            id=c.id,
            case_number=c.case_number,
            customer_id=c.customer_id,
            customer_name=c.customer.name if c.customer else "Customer",
            customer_email=c.customer.email if c.customer else None,
            payment_id=c.payment_id,
            subscription_id=c.subscription_id,
            amount_at_risk_inr=c.amount_at_risk_inr,
            customer_ltv_inr=c.customer_ltv_inr,
            urgency_score=c.urgency_score,
            risk_age_hours=c.risk_age_hours,
            failure_reason=c.failure_reason,
            error_code=c.error_code,
            payment_method=c.payment_method,
            status=c.status,
            retry_count=c.retry_count,
            expected_recovery_probability=c.expected_recovery_probability,
            expected_recovery_value_inr=c.expected_recovery_value_inr,
            confidence_score=c.confidence_score,
            recommended_action=rec_action,
            recovery_mode=c.recovery_mode,
            created_at=c.created_at
        ))
    return items


@router.get("/metrics", response_model=MetricsOverview)
async def get_recovery_metrics(db: AsyncSession = Depends(get_db)):
    total_res = await db.execute(select(func.count(RecoveryCase.id)))
    total_cases = total_res.scalar() or 0

    if total_cases == 0:
        return MetricsOverview(
            total_cases=0,
            active_cases=0,
            recovered_cases=0,
            failed_cases=0,
            escalated_cases=0,
            stopped_cases=0,
            total_revenue_at_risk_inr=0.0,
            total_recovered_revenue_inr=0.0,
            recovery_rate_pct=0.0,
            baseline_recovery_rate_pct=38.5,
            net_revenue_lift_inr=0.0,
            avg_confidence_score=0.0,
            prevented_friction_events_count=0,
            total_intervention_cost_inr=0.0
        )

    active_res = await db.execute(select(func.count(RecoveryCase.id)).where(RecoveryCase.status.in_(["DETECTED", "ACTION_PROPOSED", "POLICY_APPROVED", "EXECUTING"])))
    active_cases = active_res.scalar() or 0

    recovered_res = await db.execute(select(func.count(RecoveryCase.id)).where(RecoveryCase.status == "RECOVERED"))
    recovered_cases = recovered_res.scalar() or 0

    failed_res = await db.execute(select(func.count(RecoveryCase.id)).where(RecoveryCase.status.in_(["FAILED", "POLICY_REJECTED"])))
    failed_cases = failed_res.scalar() or 0

    escalated_res = await db.execute(select(func.count(RecoveryCase.id)).where(RecoveryCase.status == "ESCALATED"))
    escalated_cases = escalated_res.scalar() or 0

    stopped_res = await db.execute(select(func.count(RecoveryCase.id)).where(RecoveryCase.status == "STOPPED"))
    stopped_cases = stopped_res.scalar() or 0

    risk_sum_res = await db.execute(select(func.sum(RecoveryCase.amount_at_risk_inr)))
    total_risk = risk_sum_res.scalar() or 0.0

    recovered_sum_res = await db.execute(select(func.sum(RecoveryOutcome.recovered_amount_inr)))
    total_recovered = recovered_sum_res.scalar() or 0.0

    cost_sum_res = await db.execute(select(func.sum(RecoveryAction.cost_inr)))
    total_cost = cost_sum_res.scalar() or 0.0

    conf_avg_res = await db.execute(select(func.avg(RecoveryCase.confidence_score)))
    avg_conf = conf_avg_res.scalar() or 0.85

    recovery_rate = (recovered_cases / total_cases * 100.0) if total_cases > 0 else 0.0
    baseline_rate = 38.5  # Standard naive retry baseline
    baseline_estimated_recovered = total_risk * (baseline_rate / 100.0)
    net_lift = max(0.0, total_recovered - baseline_estimated_recovered - total_cost)

    return MetricsOverview(
        total_cases=total_cases,
        active_cases=active_cases,
        recovered_cases=recovered_cases,
        failed_cases=failed_cases,
        escalated_cases=escalated_cases,
        stopped_cases=stopped_cases,
        total_revenue_at_risk_inr=round(total_risk, 2),
        total_recovered_revenue_inr=round(total_recovered, 2),
        recovery_rate_pct=round(recovery_rate, 1),
        baseline_recovery_rate_pct=baseline_rate,
        net_revenue_lift_inr=round(net_lift, 2),
        avg_confidence_score=round(avg_conf, 2),
        prevented_friction_events_count=stopped_cases + (total_cases - recovered_cases),
        total_intervention_cost_inr=round(total_cost, 2)
    )


@router.get("/{case_id}", response_model=RecoveryCaseDetail)
async def get_case_detail(case_id: str, db: AsyncSession = Depends(get_db)):
    query = (
        select(RecoveryCase)
        .options(
            selectinload(RecoveryCase.customer),
            selectinload(RecoveryCase.ai_decisions),
            selectinload(RecoveryCase.policy_decisions),
            selectinload(RecoveryCase.actions),
            selectinload(RecoveryCase.audit_logs)
        )
        .where((RecoveryCase.id == case_id) | (RecoveryCase.case_number == case_id))
    )
    result = await db.execute(query)
    c = result.scalar_one_or_none()

    if not c:
        raise HTTPException(status_code=404, detail="Recovery Case not found")

    ai_summaries = []
    for ai in c.ai_decisions:
        try:
            facts = json.loads(ai.known_facts_json)
            inferences = json.loads(ai.inferred_factors_json)
            unknowns = json.loads(ai.unknown_factors_json)
            cfs = json.loads(ai.counterfactuals_json)
        except Exception:
            facts, inferences, unknowns, cfs = [], [], [], []

        ai_summaries.append(AIDecisionSummary(
            id=ai.id,
            model_name=ai.model_name,
            diagnosis_category=ai.diagnosis_category,
            diagnosis_reasoning=ai.diagnosis_reasoning,
            recommended_action=ai.recommended_action,
            timing_schedule_minutes=ai.timing_schedule_minutes,
            expected_recovery_probability=ai.expected_recovery_probability,
            confidence_score=ai.confidence_score,
            reasoning_summary=ai.reasoning_summary,
            known_facts=facts,
            inferred_factors=inferences,
            unknown_factors=unknowns,
            counterfactuals=cfs,
            requires_human_review=ai.requires_human_review,
            is_fallback=ai.is_fallback,
            created_at=ai.created_at
        ))

    policy_summaries = []
    for p in c.policy_decisions:
        try:
            rules = json.loads(p.rule_evaluations_json)
            rejections = json.loads(p.rejection_reasons_json)
        except Exception:
            rules, rejections = [], []

        policy_summaries.append(PolicyDecisionSummary(
            id=p.id,
            is_authorized=p.is_authorized,
            action_approved=p.action_approved,
            stopping_rule_triggered=p.stopping_rule_triggered,
            rejection_reasons=rejections,
            rule_evaluations=rules,
            requires_human_review=p.requires_human_review,
            created_at=p.created_at
        ))

    action_summaries = []
    for a in c.actions:
        action_summaries.append(ActionSummary(
            id=a.id,
            action_type=a.action_type,
            status=a.status,
            scheduled_for=a.scheduled_for,
            executed_at=a.executed_at,
            cost_inr=a.cost_inr,
            friction_penalty=a.friction_penalty,
            execution_mode=a.execution_mode
        ))

    return RecoveryCaseDetail(
        id=c.id,
        case_number=c.case_number,
        customer_id=c.customer_id,
        customer_name=c.customer.name if c.customer else "Customer",
        customer_email=c.customer.email if c.customer else None,
        payment_id=c.payment_id,
        subscription_id=c.subscription_id,
        amount_at_risk_inr=c.amount_at_risk_inr,
        customer_ltv_inr=c.customer_ltv_inr,
        urgency_score=c.urgency_score,
        risk_age_hours=c.risk_age_hours,
        failure_reason=c.failure_reason,
        error_code=c.error_code,
        error_description=c.error_description,
        payment_method=c.payment_method,
        status=c.status,
        retry_count=c.retry_count,
        contact_count=c.contact_count,
        expected_recovery_probability=c.expected_recovery_probability,
        expected_recovery_value_inr=c.expected_recovery_value_inr,
        confidence_score=c.confidence_score,
        recommended_action=ai_summaries[-1].recommended_action if ai_summaries else None,
        recovery_mode=c.recovery_mode,
        created_at=c.created_at,
        last_action_timestamp=c.last_action_timestamp,
        resolved_at=c.resolved_at,
        ai_decisions=ai_summaries,
        policy_decisions=policy_summaries,
        actions=action_summaries
    )


@router.post("/{case_id}/override")
async def override_case_action(
    case_id: str,
    req: ManualActionRequest,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(RecoveryCase)
        .options(selectinload(RecoveryCase.customer))
        .where((RecoveryCase.id == case_id) | (RecoveryCase.case_number == case_id))
    )
    result = await db.execute(query)
    c = result.scalar_one_or_none()

    if not c:
        raise HTTPException(status_code=404, detail="Recovery Case not found")

    # Record Operator Audit Log
    db.add(AuditLog(
        case_id=c.id,
        actor="HUMAN_ADMIN",
        action_type="OPERATOR_OVERRIDE",
        message=f"Operator manually approved action '{req.action}'. Notes: {req.notes or 'None'}",
        metadata_json=json.dumps(req.model_dump())
    ))

    if req.action == "stop_recovery":
        c.status = "STOPPED"
        await db.commit()
        return {"status": "success", "message": "Case stopped by human operator", "case_status": c.status}

    # Execute action
    action_db = RecoveryAction(
        case_id=c.id,
        action_type=req.action,
        status="EXECUTING",
        scheduled_for=datetime.utcnow(),
        execution_mode=c.recovery_mode
    )
    db.add(action_db)
    await db.flush()

    exec_result = await ExecutionAdapter.execute_action(
        action_type=req.action,
        amount_inr=c.amount_at_risk_inr,
        customer_email=c.customer.email if c.customer else "customer@example.com",
        customer_phone=c.customer.phone if c.customer else "+919876543210",
        payment_id=c.payment_id,
        subscription_id=c.subscription_id,
        failure_category=c.failure_reason,
        predicted_prob=c.expected_recovery_probability or 0.65,
        timing_minutes=req.timing_schedule_minutes
    )

    action_db.status = "SUCCEEDED" if exec_result.success else "FAILED"
    action_db.executed_at = datetime.utcnow()
    action_db.cost_inr = exec_result.cost_inr
    action_db.friction_penalty = exec_result.friction_penalty
    action_db.execution_details_json = json.dumps(exec_result.details)

    outcome_db = RecoveryOutcome(
        case_id=c.id,
        action_id=action_db.id,
        is_recovered=exec_result.is_recovered,
        recovered_amount_inr=exec_result.recovered_amount_inr,
        time_to_recovery_hours=0.2,
        actual_cost_inr=exec_result.cost_inr,
        outcome_reason=f"Manual Override: {exec_result.outcome_reason}"
    )
    db.add(outcome_db)

    c.status = "RECOVERED" if exec_result.is_recovered else "FAILED"
    if exec_result.is_recovered:
        c.resolved_at = datetime.utcnow()

    await db.commit()
    return {
        "status": "success",
        "case_status": c.status,
        "is_recovered": exec_result.is_recovered,
        "recovered_amount_inr": exec_result.recovered_amount_inr,
        "outcome_reason": exec_result.outcome_reason
    }
