from typing import Tuple, List
from pydantic import BaseModel


class DiagnosisResult(BaseModel):
    category: str
    is_hard_decline: bool
    is_recoverable: bool
    known_facts: List[str]
    inferred_factors: List[str]
    unknown_factors: List[str]
    suggested_strategy_hint: str


class DiagnosisEngine:
    """
    Deterministic Diagnosis Layer for Razorpay Payment & Subscription Failure Events.
    Categorizes root causes and separates verified Facts from Inferences and Unknowns.
    """

    HARD_DECLINE_CODES = {
        "BAD_REQUEST_PAYMENT_CARD_STOLEN",
        "BAD_REQUEST_PAYMENT_CARD_LOST",
        "BAD_REQUEST_PAYMENT_ACCOUNT_CLOSED",
        "BAD_REQUEST_PAYMENT_BLOCKED",
        "BAD_REQUEST_PAYMENT_FRAUDULENT",
        "BAD_REQUEST_PAYMENT_CARD_NOT_SUPPORTED",
    }

    INSUFFICIENT_FUNDS_CODES = {
        "BAD_REQUEST_PAYMENT_DECLINED_BY_BANK",
        "BAD_REQUEST_PAYMENT_INSUFFICIENT_FUNDS",
        "BAD_REQUEST_PAYMENT_LIMIT_EXCEEDED",
        "BAD_REQUEST_PAYMENT_DECLINED_DUE_TO_LOW_BALANCE",
    }

    EXPIRED_OR_INVALID_METHOD_CODES = {
        "BAD_REQUEST_PAYMENT_CARD_EXPIRED",
        "BAD_REQUEST_PAYMENT_CARD_INVALID",
        "BAD_REQUEST_PAYMENT_TOKEN_INVALID",
        "BAD_REQUEST_PAYMENT_MANDATE_EXPIRED",
    }

    TEMPORARY_GATEWAY_CODES = {
        "GATEWAY_ERROR",
        "SERVER_ERROR",
        "BAD_REQUEST_PAYMENT_TIMED_OUT",
        "BAD_REQUEST_PAYMENT_NETWORK_FAILURE",
        "BAD_REQUEST_PAYMENT_BANK_DOWNTIME",
    }

    AUTH_OR_ABANDON_CODES = {
        "BAD_REQUEST_PAYMENT_OTP_VALIDATION_FAILED",
        "BAD_REQUEST_PAYMENT_CANCELLED_BY_USER",
        "BAD_REQUEST_PAYMENT_AUTHENTICATION_FAILED",
        "BAD_REQUEST_PAYMENT_USER_DROPPED_OUT",
    }

    UPI_MANDATE_CODES = {
        "BAD_REQUEST_UPI_MANDATE_REVOKED",
        "BAD_REQUEST_UPI_DECLINED",
        "BAD_REQUEST_UPI_LIMIT_EXCEEDED",
        "BAD_REQUEST_PAYMENT_VPA_INVALID",
    }

    @classmethod
    def diagnose(
        cls,
        error_code: str,
        error_description: str,
        payment_method: str,
        amount_inr: float,
        is_subscription: bool = False,
        subscription_status: str = "active",
        failure_count: int = 0
    ) -> DiagnosisResult:
        code = (error_code or "").upper().strip()
        desc = error_description or ""

        known_facts: List[str] = [
            f"Payment Method: {payment_method.upper()}",
            f"Amount at Risk: ₹{amount_inr:,.2f}",
            f"Previous Consecutive Failures: {failure_count}",
        ]
        if error_code:
            known_facts.append(f"Razorpay Error Code: {error_code}")
        if error_description:
            known_facts.append(f"Gateway Error Description: '{error_description}'")
        if is_subscription:
            known_facts.append(f"Subscription Status: {subscription_status.upper()}")

        inferred_factors: List[str] = []
        unknown_factors: List[str] = [
            "Customer current account balance or credit limit availability",
            "Customer subjective willingness or intent to continue subscription",
            "Device network speed or connectivity state during payment attempt",
        ]

        # 1. Hard Decline Check
        if any(h in code for h in cls.HARD_DECLINE_CODES) or "stolen" in desc.lower() or "account closed" in desc.lower():
            category = "bank_decline_hard"
            is_hard_decline = True
            is_recoverable = False
            inferred_factors.append("Payment instrument is permanently blocked or closed by issuing bank; automated retries will 100% fail and damage gateway standing.")
            strategy_hint = "Require customer to provide a completely new payment method or stop recovery."

        # 2. Insufficient Funds
        elif any(inf in code for inf in cls.INSUFFICIENT_FUNDS_CODES) or "insufficient" in desc.lower() or "balance" in desc.lower():
            category = "insufficient_funds"
            is_hard_decline = False
            is_recoverable = True
            inferred_factors.append("Temporary liquidity shortfall. Highly sensitive to retry timing (e.g. salary cycle / morning bank settlement hours).")
            strategy_hint = "Schedule delayed smart retry aligned with standard salary cycles (1st-5th of month) or morning window (9:00-11:00 AM)."

        # 3. Expired Payment Method
        elif any(exp in code for exp in cls.EXPIRED_OR_INVALID_METHOD_CODES) or "expired" in desc.lower():
            category = "expired_payment_method"
            is_hard_decline = False
            is_recoverable = True
            inferred_factors.append("Card or mandate expired. Retrying current token will repeatedly fail without customer updating credentials.")
            strategy_hint = "Send automated payment method update link (via email/SMS/WhatsApp)."

        # 4. Temporary Gateway / Network Failure
        elif any(gw in code for gw in cls.TEMPORARY_GATEWAY_CODES) or "gateway" in desc.lower() or "timeout" in desc.lower() or "downtime" in desc.lower():
            category = "bank_decline_temporary"
            is_hard_decline = False
            is_recoverable = True
            inferred_factors.append("Transient infrastructure or gateway timeout. Likely resolved once bank network recovers.")
            strategy_hint = "Execute short-delay retry (e.g. 2 to 4 hours) without bothering the customer."

        # 5. Auth / 3DS Abandonment
        elif any(ab in code for ab in cls.AUTH_OR_ABANDON_CODES) or "otp" in desc.lower() or "cancel" in desc.lower():
            category = "auth_abandonment"
            is_hard_decline = False
            is_recoverable = True
            inferred_factors.append("Customer dropped off during 3DS OTP step or authentication window expired.")
            strategy_hint = "Send single polite reminder with direct 1-click checkout recovery link."

        # 6. UPI Mandate
        elif any(upi in code for upi in cls.UPI_MANDATE_CODES) or payment_method.lower() == "upi" and is_subscription:
            category = "upi_mandate_failed"
            is_hard_decline = False
            is_recoverable = True
            inferred_factors.append("UPI AutoPay mandate failure. Often caused by UPI daily limit reached or mandate authorization pause.")
            strategy_hint = "Send UPI intent notification or prompt mandate re-authorization."

        # 7. Subscription Halted
        elif is_subscription and subscription_status.lower() in ("halted", "pending"):
            category = "subscription_halted"
            is_hard_decline = False
            is_recoverable = True
            inferred_factors.append("Razorpay recurring subscription has exhausted standard auto-charge retries and entered halted status.")
            strategy_hint = "Deploy high-priority customer reminder with instant payment link to resume subscription."

        else:
            category = "unknown_ambiguous"
            is_hard_decline = False
            is_recoverable = True
            inferred_factors.append("Generic or unclassified decline response from issuing bank.")
            strategy_hint = "Attempt single conservative delayed retry; if failed, request payment method update."

        return DiagnosisResult(
            category=category,
            is_hard_decline=is_hard_decline,
            is_recoverable=is_recoverable,
            known_facts=known_facts,
            inferred_factors=inferred_factors,
            unknown_factors=unknown_factors,
            suggested_strategy_hint=strategy_hint
        )
