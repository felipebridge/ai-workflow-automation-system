import re
from typing import Any, Dict, List, Optional


def rule_extract(text: str, process_type: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "name": _extract_name(text),
        "email": _extract_email(text),
        "phone": _extract_phone(text),
        "date": _extract_date(text),
        "amount": _extract_amount(text),
        "currency": _extract_currency(text),
        "description": None,
        "order_number": _extract_order_number(text),
        "priority": "medium",
        "urgency_indicators": [],
        "key_entities": {},
        "summary": None,
    }

    urgency = _extract_urgency(text)
    result["urgency_indicators"] = urgency
    if urgency:
        result["priority"] = "critical" if len(urgency) >= 3 else "high"

    result["summary"] = _extract_summary(text)
    result["description"] = _extract_description(text)
    result["key_entities"] = _extract_entities(text, process_type)

    return result


def _extract_email(text: str) -> Optional[str]:
    match = re.search(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", text)
    return match.group() if match else None


def _extract_phone(text: str) -> Optional[str]:
    match = re.search(
        r"(\+?1?\s?)?(\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})", text
    )
    return match.group().strip() if match else None


def _extract_amount(text: str) -> Optional[float]:
    patterns = [
        r"\$\s*([\d,]+(?:\.\d{1,2})?)",
        r"([\d,]+(?:\.\d{1,2})?)\s*(?:USD|EUR|GBP)",
        r"amount[:\s]+\$?([\d,]+(?:\.\d{1,2})?)",
        r"total[:\s]+\$?([\d,]+(?:\.\d{1,2})?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                continue
    return None


def _extract_currency(text: str) -> Optional[str]:
    if re.search(r"\$|USD", text):
        return "USD"
    if re.search(r"€|EUR", text):
        return "EUR"
    if re.search(r"£|GBP", text):
        return "GBP"
    return "USD" if _extract_amount(text) else None


def _extract_date(text: str) -> Optional[str]:
    patterns = [
        (r"\b(\d{4}-\d{2}-\d{2})\b", "%Y-%m-%d"),
        (r"\b(\d{1,2}/\d{1,2}/\d{4})\b", "%m/%d/%Y"),
        (r"\b(\d{1,2}-\d{1,2}-\d{4})\b", "%m-%d-%Y"),
        (
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)"
            r"\s+\d{1,2},?\s+\d{4}\b",
            None,
        ),
    ]
    for pattern, _ in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group().strip()
    return None


def _extract_name(text: str) -> Optional[str]:
    patterns = [
        r"(?:Name|From|Contact|Client|Customer|Sender)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)",
        r"^From:\s*([A-Z][a-z]+ [A-Z][a-z]+)",
        r"(?:Hi|Hello|Dear)\s+([A-Z][a-z]+ [A-Z][a-z]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1).strip()

    company_match = re.search(
        r"(?:Company|Organization|Corp|LLC|Inc)[:\s]+([A-Z][A-Za-z\s&,]+?)(?:\n|\.|\,|$)",
        text,
    )
    if company_match:
        return company_match.group(1).strip()

    return None


def _extract_order_number(text: str) -> Optional[str]:
    match = re.search(
        r"\b(?:INV|ORD|PO|TKT|CASE|REF|TICKET|ORDER)(?![a-z])[-#]?\s*[\dA-Z-]+",
        text,
        re.IGNORECASE,
    )
    return match.group().upper().replace(" ", "") if match else None


def _extract_urgency(text: str) -> List[str]:
    indicators = ["urgent", "asap", "immediately", "critical", "emergency", "overdue",
                  "past due", "final notice", "suspend", "escalate"]
    lower = text.lower()
    return [i for i in indicators if i in lower]


def _extract_summary(text: str) -> Optional[str]:
    lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 25]
    for line in lines:
        if not re.match(r"^(From|To|Subject|Date|CC):", line, re.IGNORECASE):
            return line[:200]
    return text[:150].strip() if text.strip() else None


def _extract_description(text: str) -> Optional[str]:
    clean = re.sub(r"^(From|To|Subject|Date|CC):.*$", "", text, flags=re.MULTILINE)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:500] if clean else None


def _extract_entities(text: str, process_type: str) -> Dict[str, str]:
    entities: Dict[str, str] = {}

    if process_type == "invoice":
        due_match = re.search(r"due\s+(?:date)?[:\s]+([\w\s,/]+?)(?:\n|$)", text, re.IGNORECASE)
        if due_match:
            entities["due_date"] = due_match.group(1).strip()

    if process_type in ("claim", "support_ticket"):
        order_match = re.search(r"order\s+#?([\w-]+)", text, re.IGNORECASE)
        if order_match:
            entities["related_order"] = order_match.group(1)

    if process_type == "lead":
        budget_match = re.search(r"budget[:\s]+\$?([\d,kK]+)", text, re.IGNORECASE)
        if budget_match:
            entities["budget"] = budget_match.group(1)
        timeline_match = re.search(r"(Q[1-4]\s+\d{4}|H[12]\s+\d{4})", text)
        if timeline_match:
            entities["timeline"] = timeline_match.group()

    return entities
