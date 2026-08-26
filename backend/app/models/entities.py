import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    customer_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(128), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ltv_inr: Mapped[float] = mapped_column(Float, default=0.0)
    risk_tier: Mapped[str] = mapped_column(String(32), default="STANDARD")  # VIP, HIGH_VALUE, STANDARD, AT_RISK
    payment_methods_count: Mapped[int] = mapped_column(Integer, default=1)
    historical_recovery_rate: Mapped[float] = mapped_column(Float, default=0.65)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cases: Mapped[list["RecoveryCase"]] = relationship("RecoveryCase", back_populates="customer")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    payment_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.customer_id"), index=True)
    amount_inr: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    method: Mapped[str] = mapped_column(String(32))  # card, upi, netbanking, emi
    status: Mapped[str] = mapped_column(String(32))  # created, authorized, captured, failed
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    subscription_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    plan_id: Mapped[str] = mapped_column(String(64))
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.customer_id"), index=True)
    amount_inr: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32))  # active, pending, halted, cancelled, completed
    total_count: Mapped[int] = mapped_column(Integer, default=12)
    paid_count: Mapped[int] = mapped_column(Integer, default=0)
    current_cycle_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    current_cycle_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    signature: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PROCESSED")  # PROCESSED, DUPLICATE, FAILED
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # CASE-2026-XXXXXX
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.customer_id"), index=True)
    payment_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    subscription_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    webhook_event_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Risk Metrics
    amount_at_risk_inr: Mapped[float] = mapped_column(Float)
    customer_ltv_inr: Mapped[float] = mapped_column(Float, default=0.0)
    urgency_score: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 to 1.0
    risk_age_hours: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Classification & Diagnostics
    failure_reason: Mapped[str] = mapped_column(String(64))  # insufficient_funds, bank_decline, etc.
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_method: Mapped[str] = mapped_column(String(32), default="card")
    
    # State & Counters
    status: Mapped[str] = mapped_column(String(32), default="DETECTED", index=True)
    # DETECTED, DIAGNOSED, ACTION_PROPOSED, POLICY_APPROVED, POLICY_REJECTED, EXECUTING, RECOVERED, FAILED, ESCALATED, STOPPED
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    contact_count: Mapped[int] = mapped_column(Integer, default=0)
    last_action_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Economic Metrics
    expected_recovery_probability: Mapped[float] = mapped_column(Float, default=0.0)
    expected_recovery_value_inr: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Mode & Lifecycle
    recovery_mode: Mapped[str] = mapped_column(String(32), default="SANDBOX_SIMULATION")  # TEST_MODE, SANDBOX_SIMULATION
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="cases")
    ai_decisions: Mapped[list["AIDecision"]] = relationship("AIDecision", back_populates="case")
    policy_decisions: Mapped[list["PolicyDecision"]] = relationship("PolicyDecision", back_populates="case")
    actions: Mapped[list["RecoveryAction"]] = relationship("RecoveryAction", back_populates="case")
    outcomes: Mapped[list["RecoveryOutcome"]] = relationship("RecoveryOutcome", back_populates="case")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="case")


class AIDecision(Base):
    __tablename__ = "ai_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_cases.id"), index=True)
    model_name: Mapped[str] = mapped_column(String(64), default="gemini-2.5-flash")
    
    diagnosis_category: Mapped[str] = mapped_column(String(64))
    diagnosis_reasoning: Mapped[str] = mapped_column(Text)
    recommended_action: Mapped[str] = mapped_column(String(64))
    timing_schedule_minutes: Mapped[int] = mapped_column(Integer, default=0)
    expected_recovery_probability: Mapped[float] = mapped_column(Float)
    confidence_score: Mapped[float] = mapped_column(Float)
    reasoning_summary: Mapped[str] = mapped_column(Text)
    
    # Structured Fact / Inference / Unknown Breakdown (Stored as JSON text)
    known_facts_json: Mapped[str] = mapped_column(Text, default="[]")
    inferred_factors_json: Mapped[str] = mapped_column(Text, default="[]")
    unknown_factors_json: Mapped[str] = mapped_column(Text, default="[]")
    counterfactuals_json: Mapped[str] = mapped_column(Text, default="[]")
    
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["RecoveryCase"] = relationship("RecoveryCase", back_populates="ai_decisions")


class PolicyDecision(Base):
    __tablename__ = "policy_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_cases.id"), index=True)
    ai_decision_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("ai_decisions.id"), nullable=True)
    
    is_authorized: Mapped[bool] = mapped_column(Boolean, default=False)
    action_approved: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    stopping_rule_triggered: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    rule_evaluations_json: Mapped[str] = mapped_column(Text, default="[]")  # Detailed checks breakdown
    rejection_reasons_json: Mapped[str] = mapped_column(Text, default="[]")
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["RecoveryCase"] = relationship("RecoveryCase", back_populates="policy_decisions")


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_cases.id"), index=True)
    policy_decision_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("policy_decisions.id"), nullable=True)
    
    action_type: Mapped[str] = mapped_column(String(64))  # delayed_retry, smart_timing_retry, payment_link_email, etc.
    status: Mapped[str] = mapped_column(String(32), default="SCHEDULED")  # SCHEDULED, EXECUTING, SUCCEEDED, FAILED, CANCELLED
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    cost_inr: Mapped[float] = mapped_column(Float, default=0.0)
    friction_penalty: Mapped[float] = mapped_column(Float, default=0.0)
    execution_mode: Mapped[str] = mapped_column(String(32), default="SANDBOX_SIMULATION")
    execution_details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["RecoveryCase"] = relationship("RecoveryCase", back_populates="actions")


class RecoveryOutcome(Base):
    __tablename__ = "recovery_outcomes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_cases.id"), index=True)
    action_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("recovery_actions.id"), nullable=True)
    
    is_recovered: Mapped[bool] = mapped_column(Boolean, default=False)
    recovered_amount_inr: Mapped[float] = mapped_column(Float, default=0.0)
    time_to_recovery_hours: Mapped[float] = mapped_column(Float, default=0.0)
    actual_cost_inr: Mapped[float] = mapped_column(Float, default=0.0)
    outcome_reason: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["RecoveryCase"] = relationship("RecoveryCase", back_populates="outcomes")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("recovery_cases.id"), nullable=True, index=True)
    actor: Mapped[str] = mapped_column(String(32))  # INGESTION, RISK_DETECTOR, DIAGNOSIS_ENGINE, AI_AGENT, POLICY_ENGINE, EXECUTOR, HUMAN_ADMIN
    action_type: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    case: Mapped[Optional["RecoveryCase"]] = relationship("RecoveryCase", back_populates="audit_logs")
