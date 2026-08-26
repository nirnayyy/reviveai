import pytest
from backend.app.services.diagnosis_engine import DiagnosisEngine


def test_hard_decline_stolen_card():
    diag = DiagnosisEngine.diagnose(
        error_code="BAD_REQUEST_PAYMENT_CARD_STOLEN",
        error_description="Card reported lost or stolen",
        payment_method="card",
        amount_inr=5000.0,
        is_subscription=True
    )
    assert diag.category == "bank_decline_hard"
    assert diag.is_hard_decline is True
    assert diag.is_recoverable is False
    assert len(diag.known_facts) >= 3
    assert len(diag.unknown_factors) >= 1


def test_insufficient_funds_diagnosis():
    diag = DiagnosisEngine.diagnose(
        error_code="BAD_REQUEST_PAYMENT_DECLINED_BY_BANK",
        error_description="Insufficient funds in customer account",
        payment_method="card",
        amount_inr=2499.0,
        is_subscription=True
    )
    assert diag.category == "insufficient_funds"
    assert diag.is_hard_decline is False
    assert diag.is_recoverable is True
    assert "salary" in diag.suggested_strategy_hint.lower()


def test_expired_card_diagnosis():
    diag = DiagnosisEngine.diagnose(
        error_code="BAD_REQUEST_PAYMENT_CARD_EXPIRED",
        error_description="Card expired",
        payment_method="card",
        amount_inr=1200.0
    )
    assert diag.category == "expired_payment_method"
    assert diag.is_recoverable is True
