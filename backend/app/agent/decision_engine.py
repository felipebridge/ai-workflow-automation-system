from typing import Any, Dict, List
from app.core.config import settings
from app.db.models import ActionType, ProcessType


_TYPE_TO_ACTION: Dict[str, str] = {
    ProcessType.INVOICE: ActionType.CREATE_RECORD,
    ProcessType.CUSTOMER_REQUEST: ActionType.GENERATE_RESPONSE,
    ProcessType.CLAIM: ActionType.GENERATE_RESPONSE,
    ProcessType.LEAD: ActionType.CREATE_RECORD,
    ProcessType.SUPPORT_TICKET: ActionType.CREATE_RECORD,
    ProcessType.ADMIN_CASE: ActionType.NOTIFY_TEAM,
    ProcessType.PAYMENT_REQUEST: ActionType.APPROVE_PAYMENT,
    ProcessType.OTHER: ActionType.CREATE_RECORD,
}

_ALWAYS_HUMAN_ACTIONS = {ActionType.APPROVE_PAYMENT}

_ALWAYS_HUMAN_TYPES = {ProcessType.PAYMENT_REQUEST}


def make_decision(
    process_type: str,
    extracted: Dict[str, Any],
    confidence: float,
    validation_errors: List[str],
    missing_fields: List[str],
) -> Dict[str, Any]:
    action_type = _TYPE_TO_ACTION.get(process_type, ActionType.CREATE_RECORD)
    action_params = _build_action_params(action_type, process_type, extracted)

    requires_human, reason = _evaluate_human_need(
        action_type, process_type, confidence, extracted, validation_errors, missing_fields
    )

    return {
        "action_type": action_type,
        "action_params": action_params,
        "requires_human": requires_human,
        "reasoning": reason,
    }


def _evaluate_human_need(
    action_type: str,
    process_type: str,
    confidence: float,
    extracted: Dict[str, Any],
    validation_errors: List[str],
    missing_fields: List[str],
) -> tuple:
    if action_type in _ALWAYS_HUMAN_ACTIONS or process_type in _ALWAYS_HUMAN_TYPES:
        return True, f"Action '{action_type}' always requires human authorization"

    amount = _parse_amount(extracted.get("amount"))
    if amount and amount > settings.HIGH_VALUE_THRESHOLD:
        return True, f"High-value transaction (${amount:,.2f}) requires authorization"

    if len(validation_errors) >= 2:
        return True, f"Multiple validation errors detected: {'; '.join(validation_errors[:2])}"

    critical_missing = [f for f in missing_fields if f in ("email", "amount")]
    if critical_missing:
        return True, f"Critical fields missing: {', '.join(critical_missing)}"

    if confidence < settings.CONFIDENCE_REVIEW_THRESHOLD:
        return True, f"Low confidence ({confidence:.0f}%) — escalated for review"

    if confidence < settings.CONFIDENCE_AUTO_THRESHOLD:
        return True, f"Moderate confidence ({confidence:.0f}%) — pending human review"

    return False, f"High confidence ({confidence:.0f}%) — auto-executing action"


def _parse_amount(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def _build_action_params(
    action_type: str,
    process_type: str,
    extracted: Dict[str, Any],
) -> Dict[str, Any]:
    name = extracted.get("name") or "Unknown"
    email = extracted.get("email") or "no-reply@domain.com"
    amount = extracted.get("amount")
    order_number = extracted.get("order_number")
    summary = extracted.get("summary") or "No description"

    if action_type == ActionType.SEND_EMAIL:
        return {
            "to": email,
            "subject": f"Re: Your {process_type.replace('_', ' ').title()}",
            "body": f"Dear {name},\n\nThank you for reaching out. We have received your {process_type.replace('_', ' ')} and are processing it.\n\nBest regards,\nAutomation Team",
        }

    if action_type == ActionType.CREATE_RECORD:
        return {
            "record_type": process_type,
            "name": name,
            "email": email,
            "amount": amount,
            "order_number": order_number,
            "summary": summary,
            "auto_response_sent": True,
        }

    if action_type == ActionType.GENERATE_RESPONSE:
        return {
            "to": email,
            "template": f"{process_type}_response",
            "name": name,
            "order_number": order_number,
            "amount": amount,
        }

    if action_type == ActionType.APPROVE_PAYMENT:
        return {
            "requester_email": email,
            "requester_name": name,
            "amount": amount,
            "currency": extracted.get("currency", "USD"),
            "order_number": order_number,
            "requires_two_factor": True,
        }

    if action_type == ActionType.NOTIFY_TEAM:
        return {
            "channel": "#operations",
            "message": f"New {process_type.replace('_', ' ')} from {name}: {summary[:100]}",
            "priority": extracted.get("priority", "medium"),
        }

    return {"process_type": process_type, "summary": summary}
