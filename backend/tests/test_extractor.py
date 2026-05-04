"""Tests for the rule-based data extractor."""
import pytest
from app.agent.extractor import rule_extract


INVOICE_TEXT = """From: john.smith@acme.com
Subject: Invoice #INV-2024-0187

Dear Finance,
Please process Invoice #INV-2024-0187 for consulting services.
Amount: $4,500.00
Due Date: November 15, 2024
Company: ACME Corporation
"""

LEAD_TEXT = """Name: Carlos Rodriguez
Email: c.rodriguez@techstart.io
Title: CTO
Company: TechStart Inc.
Budget: $50,000
Timeline: Q1 2025
"""

CLAIM_TEXT = """From: unhappy@email.com
Subject: Broken product - Order #ORD-789

I purchased Order #ORD-789 and it stopped working.
I need a refund ASAP. This is urgent!
"""


class TestEmailExtraction:
    def test_extracts_email(self):
        result = rule_extract(INVOICE_TEXT, "invoice")
        assert result["email"] == "john.smith@acme.com"

    def test_extracts_email_from_plain_text(self):
        result = rule_extract("Contact us at support@company.com for help.", "support_ticket")
        assert result["email"] == "support@company.com"

    def test_no_email_returns_none(self):
        result = rule_extract("No contact information here.", "other")
        assert result["email"] is None


class TestAmountExtraction:
    def test_extracts_dollar_amount(self):
        result = rule_extract(INVOICE_TEXT, "invoice")
        assert result["amount"] == 4500.0

    def test_extracts_currency(self):
        result = rule_extract(INVOICE_TEXT, "invoice")
        assert result["currency"] == "USD"

    def test_large_amount_with_commas(self):
        result = rule_extract("Total amount: $15,750.00 is overdue.", "payment_request")
        assert result["amount"] == 15750.0

    def test_no_amount_returns_none(self):
        result = rule_extract("I have a question about your service.", "customer_request")
        assert result["amount"] is None


class TestOrderNumberExtraction:
    def test_extracts_inv_number(self):
        result = rule_extract(INVOICE_TEXT, "invoice")
        assert result["order_number"] is not None
        assert "INV-2024-0187" in result["order_number"]

    def test_extracts_ord_number(self):
        result = rule_extract(CLAIM_TEXT, "claim")
        assert result["order_number"] is not None
        assert "ORD-789" in result["order_number"]


class TestPriorityExtraction:
    def test_urgent_text_sets_high_priority(self):
        result = rule_extract(CLAIM_TEXT, "claim")
        assert result["priority"] == "high"
        assert "urgent" in result["urgency_indicators"]

    def test_no_urgency_defaults_to_medium(self):
        result = rule_extract(INVOICE_TEXT, "invoice")
        assert result["priority"] == "medium"
        assert result["urgency_indicators"] == []


class TestReturnStructure:
    def test_all_expected_keys_present(self):
        result = rule_extract("Some text.", "other")
        expected = {
            "name", "email", "phone", "date", "amount", "currency",
            "description", "order_number", "priority", "urgency_indicators",
            "key_entities", "summary",
        }
        assert expected.issubset(result.keys())

    def test_urgency_indicators_is_list(self):
        result = rule_extract("Hello.", "other")
        assert isinstance(result["urgency_indicators"], list)

    def test_key_entities_is_dict(self):
        result = rule_extract("Hello.", "other")
        assert isinstance(result["key_entities"], dict)
