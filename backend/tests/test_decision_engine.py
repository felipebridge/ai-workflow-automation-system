"""Tests for the decision engine business rules."""
import pytest
from app.agent.decision_engine import make_decision
from app.db.models import ActionType


def _decide(
    process_type="invoice",
    amount=None,
    confidence=85.0,
    errors=None,
    missing=None,
):
    extracted = {"amount": amount, "email": "test@test.com", "summary": "test"}
    return make_decision(
        process_type=process_type,
        extracted=extracted,
        confidence=confidence,
        validation_errors=errors or [],
        missing_fields=missing or [],
    )


class TestAutoExecution:
    def test_high_confidence_low_risk_is_auto(self):
        result = _decide(confidence=85.0, amount=500)
        assert result["requires_human"] is False

    def test_invoice_under_threshold_is_auto(self):
        result = _decide(process_type="invoice", confidence=90.0, amount=9999.99)
        assert result["requires_human"] is False

    def test_lead_always_auto_at_high_confidence(self):
        result = _decide(process_type="lead", confidence=93.0, amount=50000)
        assert result["action_type"] == ActionType.CREATE_RECORD


class TestHumanRequired:
    def test_payment_request_always_requires_human(self):
        result = _decide(process_type="payment_request", confidence=95.0, amount=100)
        assert result["requires_human"] is True

    def test_high_value_invoice_requires_human(self):
        result = _decide(process_type="invoice", confidence=90.0, amount=10001)
        assert result["requires_human"] is True

    def test_exact_threshold_does_not_trigger(self):
        result = _decide(process_type="invoice", confidence=90.0, amount=10000)
        assert result["requires_human"] is False

    def test_low_confidence_requires_human(self):
        result = _decide(confidence=40.0)
        assert result["requires_human"] is True

    def test_medium_confidence_requires_human(self):
        result = _decide(confidence=65.0)
        assert result["requires_human"] is True

    def test_multiple_validation_errors_require_human(self):
        result = _decide(errors=["Invalid email", "Amount negative", "Missing date"])
        assert result["requires_human"] is True

    def test_missing_critical_field_requires_human(self):
        result = _decide(missing=["email"], confidence=85.0)
        assert result["requires_human"] is True


class TestActionTypeMapping:
    def test_invoice_maps_to_create_record(self):
        result = _decide(process_type="invoice")
        assert result["action_type"] == ActionType.CREATE_RECORD

    def test_claim_maps_to_generate_response(self):
        result = _decide(process_type="claim")
        assert result["action_type"] == ActionType.GENERATE_RESPONSE

    def test_payment_request_maps_to_approve_payment(self):
        result = _decide(process_type="payment_request")
        assert result["action_type"] == ActionType.APPROVE_PAYMENT

    def test_admin_case_maps_to_notify_team(self):
        result = _decide(process_type="admin_case")
        assert result["action_type"] == ActionType.NOTIFY_TEAM


class TestReasoningField:
    def test_reasoning_is_nonempty_string(self):
        result = _decide()
        assert isinstance(result["reasoning"], str)
        assert len(result["reasoning"]) > 0

    def test_high_value_reasoning_mentions_amount(self):
        result = _decide(amount=25000, confidence=90.0)
        assert "$" in result["reasoning"] or "value" in result["reasoning"].lower()
