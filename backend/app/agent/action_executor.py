import time
from datetime import datetime, timezone
from typing import Any, Dict
from app.db.models import ActionType, Process
from app.core.logging_config import get_logger

logger = get_logger("action_executor")

_SIMULATED_DELAY_MS = 120


def execute_action(
    action_type: str,
    parameters: Dict[str, Any],
    process: Process,
) -> Dict[str, Any]:
    logger.info("Executing action '%s' for process %d", action_type, process.id)

    handlers = {
        ActionType.SEND_EMAIL: _send_email,
        ActionType.CREATE_RECORD: _create_record,
        ActionType.UPDATE_RECORD: _update_record,
        ActionType.GENERATE_RESPONSE: _generate_response,
        ActionType.ESCALATE: _escalate,
        ActionType.REQUEST_INFORMATION: _request_information,
        ActionType.APPROVE_PAYMENT: _approve_payment,
        ActionType.NOTIFY_TEAM: _notify_team,
        ActionType.CLOSE_CASE: _close_case,
    }

    handler = handlers.get(action_type, _default_action)
    result = handler(parameters, process)
    result["executed_at"] = datetime.now(timezone.utc).isoformat()
    result["action_type"] = action_type
    result["simulated"] = True
    return result


def _send_email(params: Dict[str, Any], process: Process) -> Dict[str, Any]:
    return {
        "status": "sent",
        "to": params.get("to", ""),
        "subject": params.get("subject", ""),
        "message_id": f"msg_{int(time.time() * 1000)}",
        "provider": "mock-smtp",
    }


def _create_record(params: Dict[str, Any], process: Process) -> Dict[str, Any]:
    record_id = f"REC-{process.id:04d}-{int(time.time()) % 100000}"
    return {
        "status": "created",
        "record_id": record_id,
        "record_type": params.get("record_type", "generic"),
        "crm_synced": True,
        "auto_response_sent": params.get("auto_response_sent", False),
    }


def _update_record(params: Dict[str, Any], process: Process) -> Dict[str, Any]:
    return {
        "status": "updated",
        "record_id": params.get("record_id", f"REC-{process.id:04d}"),
        "fields_updated": list(params.keys()),
    }


def _generate_response(params: Dict[str, Any], process: Process) -> Dict[str, Any]:
    name = params.get("name", "Customer")
    template = params.get("template", "generic_response")
    body = _render_template(template, params)
    return {
        "status": "generated",
        "to": params.get("to", ""),
        "template_used": template,
        "response_length": len(body),
        "email_sent": True,
        "preview": body[:200],
    }


def _escalate(params: Dict[str, Any], process: Process) -> Dict[str, Any]:
    return {
        "status": "escalated",
        "assigned_to": params.get("assigned_to", "operations-team"),
        "ticket_id": f"ESC-{process.id:04d}",
        "notification_sent": True,
    }


def _request_information(params: Dict[str, Any], process: Process) -> Dict[str, Any]:
    return {
        "status": "info_requested",
        "to": params.get("to", ""),
        "missing_fields": params.get("missing_fields", []),
        "email_sent": True,
    }


def _approve_payment(params: Dict[str, Any], process: Process) -> Dict[str, Any]:
    return {
        "status": "approved",
        "requester_email": params.get("requester_email", ""),
        "requester_name": params.get("requester_name", "Unknown"),
        "amount": params.get("amount"),
        "currency": params.get("currency", "USD"),
        "order_number": params.get("order_number"),
        "authorization_code": f"AUTH-{process.id:04d}-{int(time.time()) % 100000}",
        "two_factor_verified": True,
        "notification_sent": True,
    }


def _notify_team(params: Dict[str, Any], process: Process) -> Dict[str, Any]:
    return {
        "status": "notified",
        "channel": params.get("channel", "#general"),
        "message_preview": str(params.get("message", ""))[:100],
        "recipients": params.get("recipients", ["ops-team"]),
    }


def _close_case(params: Dict[str, Any], process: Process) -> Dict[str, Any]:
    return {
        "status": "closed",
        "resolution": params.get("resolution", "resolved"),
        "closed_by": "system",
        "notification_sent": True,
    }


def _default_action(params: Dict[str, Any], process: Process) -> Dict[str, Any]:
    return {"status": "executed", "params": params}


def _render_template(template: str, params: Dict[str, Any]) -> str:
    name = params.get("name", "Customer")
    order = params.get("order_number") or ""
    order_ref = f" (Ref: {order})" if order else ""

    templates = {
        "invoice_response": (
            f"Dear {name},\n\nThank you for submitting invoice{order_ref}. "
            "Our finance team has received it and will process payment within 5-7 business days. "
            "You will receive a confirmation once the payment has been issued.\n\nBest regards,\nFinance Team"
        ),
        "claim_response": (
            f"Dear {name},\n\nWe have received your claim{order_ref} and sincerely apologize for the inconvenience. "
            "Our customer success team will review your case within 24 hours and contact you with a resolution.\n\n"
            "Best regards,\nCustomer Success Team"
        ),
        "lead_response": (
            f"Dear {name},\n\nThank you for your interest in our solutions. "
            "A member of our sales team will reach out to you within 24 hours to discuss your requirements "
            "and schedule a personalized demo.\n\nBest regards,\nSales Team"
        ),
        "support_ticket_response": (
            f"Dear {name},\n\nYour support ticket{order_ref} has been created successfully. "
            "Our technical team will review your issue and respond within 4 business hours.\n\n"
            "Best regards,\nSupport Team"
        ),
        "customer_request_response": (
            f"Dear {name},\n\nThank you for contacting us. "
            "We have received your request and will process it shortly.\n\n"
            "Best regards,\nCustomer Service Team"
        ),
    }

    process_type = template.replace("_response", "")
    return templates.get(template, templates.get(f"{process_type}_response",
        f"Dear {name},\n\nThank you for your message. We will process your request shortly.\n\nBest regards,\nAutomation Team"
    ))
