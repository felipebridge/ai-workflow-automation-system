import re
from typing import List, Tuple


_PATTERNS: List[Tuple[str, List[str], float]] = [
    (
        "payment_request",
        [
            r"urgent.*payment", r"overdue", r"past due", r"outstanding balance",
            r"wire transfer", r"ach payment", r"immediate payment",
            r"\d+\s*days\s*(overdue|past due)", r"suspend.*service",
            r"final notice", r"collection",
        ],
        1.4,
    ),
    (
        "invoice",
        [
            r"\binvoice\b", r"\bfactura\b", r"\binv[-#]?\s*\d+", r"\bbill\b",
            r"billing", r"payment due", r"net\s+\d{2}", r"remittance",
            r"amount due", r"payable to", r"consulting.*fee", r"services rendered",
        ],
        1.1,
    ),
    (
        "claim",
        [
            r"\bcomplaint\b", r"\bclaim\b", r"dissatisfied", r"\bunhappy\b",
            r"\bbroken\b", r"\bdamaged\b", r"\bdefective\b", r"not working",
            r"doesn.t work", r"\brefund\b", r"\breturn\b", r"\bwarranty\b",
            r"\bdispute\b", r"won.t turn on", r"stopped working",
        ],
        1.0,
    ),
    (
        "lead",
        [
            r"interested in", r"would like.*demo", r"sales.*opportunity",
            r"budget.*\$", r"\bcto\b", r"\bceo\b", r"\bvp\b",
            r"decision maker", r"enterprise.*package", r"pricing.*inquiry",
            r"potential.*client", r"partnership", r"Q[1-4]\s+\d{4}",
        ],
        1.0,
    ),
    (
        "support_ticket",
        [
            r"\bsupport\b", r"\berror\b", r"\bbug\b", r"not working",
            r"technical.*issue", r"troubleshoot", r"\bcrash", r"\bfix\b",
            r"assistance", r"screen.*won.t", r"api.*fail", r"500.*error",
            r"404.*error",
        ],
        1.0,
    ),
    (
        "admin_case",
        [
            r"\bcontract\b", r"\bagreement\b", r"\bhr\b", r"\bpolicy\b",
            r"compliance", r"\blegal\b", r"administrative", r"onboarding",
            r"offboarding", r"regulatory", r"\bnda\b", r"employment",
        ],
        1.0,
    ),
    (
        "customer_request",
        [
            r"requesting", r"would like to request", r"please.*provide",
            r"i need\b", r"can you.*send", r"require.*information",
            r"please.*update", r"kindly", r"request.*information",
        ],
        0.7,
    ),
]


def rule_classify(text: str) -> Tuple[str, float, str]:
    lower = text.lower()
    scores: dict = {}
    all_matched: dict = {}

    for process_type, patterns, weight in _PATTERNS:
        score = 0.0
        matched = []
        for pattern in patterns:
            hits = re.findall(pattern, lower)
            if hits:
                score += len(hits) * weight
                matched.extend(hits[:2])
        if score > 0:
            scores[process_type] = score
            all_matched[process_type] = matched

    if not scores:
        return "other", 38.0, "No specific patterns matched"

    best_type = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]
    total_score = sum(scores.values())
    dominance = best_score / total_score

    matched_count = min(len(all_matched[best_type]), 6)
    confidence = min(92.0, 42.0 + (dominance * 38.0) + (matched_count * 3.5))

    reasoning = f"Matched: {', '.join(set(all_matched[best_type][:4]))}"
    return best_type, round(confidence, 1), reasoning
