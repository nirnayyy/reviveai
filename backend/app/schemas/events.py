from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RazorpayPaymentEntity(BaseModel):
    id: str
    entity: str = "payment"
    amount: int  # in paise (e.g. 500000 = Rs 5000.00)
    currency: str = "INR"
    status: str
    order_id: Optional[str] = None
    invoice_id: Optional[str] = None
    international: bool = False
    method: str  # card, upi, netbanking, emi
    amount_refunded: int = 0
    refund_status: Optional[str] = None
    captured: bool = False
    description: Optional[str] = None
    card_id: Optional[str] = None
    bank: Optional[str] = None
    wallet: Optional[str] = None
    vpa: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None
    customer_id: Optional[str] = None
    token_id: Optional[str] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_source: Optional[str] = None
    error_step: Optional[str] = None
    error_reason: Optional[str] = None
    created_at: int


class RazorpaySubscriptionEntity(BaseModel):
    id: str
    entity: str = "subscription"
    plan_id: str
    customer_id: Optional[str] = None
    status: str  # created, authenticated, active, pending, halted, cancelled, completed
    current_start: Optional[int] = None
    current_end: Optional[int] = None
    ended_at: Optional[int] = None
    quantity: int = 1
    charge_at: Optional[int] = None
    start_at: Optional[int] = None
    end_at: Optional[int] = None
    auth_attempts: int = 0
    total_count: int = 12
    paid_count: int = 0
    remaining_count: int = 12
    customer_notify: int = 1
    created_at: int
    has_scheduled_changes: bool = False
    schedule_change_at: Optional[int] = None
    short_url: Optional[str] = None


class RazorpayWebhookPayload(BaseModel):
    entity: str = "event"
    account_id: str = "acc_test_merchant"
    event: str  # e.g. payment.failed, subscription.halted, subscription.pending, invoice.expired
    contains: list[str] = Field(default_factory=list)
    payload: Dict[str, Any]
    created_at: int


class SyntheticRiskEventCreate(BaseModel):
    event_type: str = "payment.failed"
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_ltv_inr: Optional[float] = 12500.0
    amount_inr: float = 2499.0
    payment_method: str = "card"
    subscription_id: Optional[str] = None
    error_code: Optional[str] = "BAD_REQUEST_PAYMENT_DECLINED_BY_BANK"
    error_description: Optional[str] = "The customer's bank declined the transaction due to insufficient balance"
    risk_age_hours: float = 0.0
    previous_retry_count: int = 0
    custom_scenario: Optional[str] = None
