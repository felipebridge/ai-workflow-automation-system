"""Tests for the rule-based process classifier."""
import pytest
from app.agent.classifier import rule_classify


@pytest.mark.parametrize("text,expected_type", [
    # Invoice signals
    (
        "Please process Invoice #INV-2024-001 for $4,500 due November 15.",
        "invoice",
    ),
    (
        "From: vendor@co.com\nSubject: Bill for consulting services rendered. Amount due: $2,000. Net 30.",
        "invoice",
    ),
    # Payment request signals
    (
        "This is a final notice. Your account is 30 days past due. "
        "Immediate payment of $15,750 required to avoid service suspension.",
        "payment_request",
    ),
    # Claim / complaint signals
    (
        "I bought your product 2 weeks ago and it arrived broken. "
        "The screen doesn't work. I need a refund ASAP. Order #ORD-123.",
        "claim",
    ),
    (
        "I am very dissatisfied. The product is defective and I want my money back.",
        "claim",
    ),
    # Lead signals
    (
        "Hi, I'm the CTO at TechCorp. We're interested in your enterprise package. "
        "Budget: $50,000. Timeline: Q1 2025.",
        "lead",
    ),
    # Support ticket signals
    (
        "Our API is returning a 500 error on all POST requests. "
        "Please help troubleshoot this technical issue.",
        "support_ticket",
    ),
    # Admin case signals
    (
        "HR Policy Update: Please review the attached contract and NDA "
        "for compliance before the onboarding meeting.",
        "admin_case",
    ),
    # Other — no strong signal
    (
        "Hello, just wanted to say hi.",
        "other",
    ),
])
def test_classify_returns_correct_type(text, expected_type):
    process_type, confidence, reasoning = rule_classify(text)
    assert process_type == expected_type, (
        f"Expected '{expected_type}', got '{process_type}'. Reasoning: {reasoning}"
    )


def test_classify_returns_confidence_in_range():
    _, confidence, _ = rule_classify("Invoice #INV-001 for $1,000 due December 1.")
    assert 0.0 <= confidence <= 100.0


def test_classify_returns_nonempty_reasoning():
    _, _, reasoning = rule_classify("Please process this invoice for $500.")
    assert isinstance(reasoning, str)
    assert len(reasoning) > 0


def test_classify_high_confidence_for_strong_signal():
    _, confidence, _ = rule_classify(
        "Invoice #INV-2024-001 billing amount due payment remittance net 30 payable."
    )
    assert confidence >= 60.0


def test_classify_low_confidence_for_vague_input():
    _, confidence, _ = rule_classify("Hello, I have a question.")
    assert confidence < 60.0


def test_payment_request_outranks_invoice_on_overdue():
    """Overdue/urgent signals should beat generic invoice signals."""
    process_type, _, _ = rule_classify(
        "This is a final notice. Invoice #INV-001 is 30 days past due. "
        "Immediate wire transfer required or service will be suspended."
    )
    assert process_type == "payment_request"
