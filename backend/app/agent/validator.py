import re
from typing import Any, Dict, List, Tuple

_REQUIRED_FIELDS: Dict[str, List[str]] = {
    "invoice": ["amount", "email"],
    "customer_request": ["email"],
    "claim": ["email"],
    "lead": ["name", "email"],
    "support_ticket": ["email"],
    "admin_case": [],
    "payment_request": ["amount"],
    "other": [],
}

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def validate_data(
    extracted: Dict[str, Any], process_type: str
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    missing: List[str] = []

    required = _REQUIRED_FIELDS.get(process_type, [])
    for field in required:
        if not extracted.get(field):
            missing.append(field)

    if extracted.get("email") and not _EMAIL_RE.match(str(extracted["email"])):
        errors.append(f"Invalid email format: {extracted['email']}")

    amount = extracted.get("amount")
    if amount is not None:
        if isinstance(amount, (int, float)):
            if amount < 0:
                errors.append(f"Amount cannot be negative: {amount}")
            if amount > 10_000_000:
                errors.append(f"Amount unusually large, possible extraction error: {amount}")
        else:
            errors.append(f"Amount is not numeric: {amount}")

    description = extracted.get("description") or extracted.get("summary") or ""
    if len(description.strip()) < 10:
        errors.append("Description is too short or missing")

    return errors, missing


def calculate_confidence(
    classifier_confidence: float,
    extracted: Dict[str, Any],
    process_type: str,
    validation_errors: List[str],
    missing_fields: List[str],
) -> float:
    score = classifier_confidence * 0.6

    required = _REQUIRED_FIELDS.get(process_type, [])
    all_fields = ["name", "email", "amount", "date", "order_number", "description", "summary"]
    present = sum(1 for f in all_fields if extracted.get(f))
    completeness = present / len(all_fields)
    score += completeness * 35.0

    score -= len(validation_errors) * 6.0
    score -= len(missing_fields) * 8.0

    if process_type != "other":
        score += 5.0

    if extracted.get("urgency_indicators"):
        score += 3.0

    return round(max(5.0, min(99.0, score)), 1)
