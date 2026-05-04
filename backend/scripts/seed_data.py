
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
import random
from app.db.database import SessionLocal, init_db
from app.db.models import (
    Action, ActionStatus, Approval, AuditLog, Decision,
    Priority, Process, ProcessStatus, ProcessType,
)

SAMPLE_INPUTS = [
    {
        "source": "email",
        "raw_input": (
            "From: John Smith (john.smith@acme.com)\n"
            "Subject: Invoice #INV-2024-0187 — Consulting Services\n\n"
            "Dear Finance Team,\n\n"
            "Please find attached Invoice #INV-2024-0187 for consulting services "
            "rendered in October 2024.\n\n"
            "Amount: $4,500.00\nDue Date: November 15, 2024\n"
            "Company: ACME Corporation\n\n"
            "Please process at your earliest convenience.\n\nBest regards,\nJohn Smith"
        ),
        "process_type": ProcessType.INVOICE,
        "status": ProcessStatus.COMPLETED,
        "priority": Priority.MEDIUM,
        "confidence": 88.5,
        "title": "Invoice #INV-2024-0187 — ACME Corp $4,500",
        "extracted": {
            "name": "John Smith", "email": "john.smith@acme.com",
            "amount": 4500.0, "currency": "USD",
            "date": "November 15, 2024", "order_number": "INV-2024-0187",
            "priority": "medium", "urgency_indicators": [],
            "key_entities": {"company": "ACME Corporation"},
            "summary": "Invoice #INV-2024-0187 for consulting services rendered in October 2024",
        },
        "requires_human": False,
        "action_type": "create_record",
        "action_status": ActionStatus.EXECUTED,
        "action_result": {"status": "created", "record_id": "REC-0001-12345", "crm_synced": True},
        "decision_reasoning": "High confidence (88.5%) — auto-executing action",
    },
    {
        "source": "form",
        "raw_input": (
            "Name: Sarah Johnson\nEmail: sarah.johnson@gmail.com\n"
            "Phone: +1-555-0123\n"
            "Subject: Broken Product — Order #ORD-789\n\n"
            "I purchased your SmartHub Pro 3 weeks ago and it stopped working completely. "
            "The screen won't turn on and the device doesn't respond. "
            "I've tried everything including a factory reset. "
            "I need a replacement or full refund ASAP. This is unacceptable."
        ),
        "process_type": ProcessType.CLAIM,
        "status": ProcessStatus.AWAITING_APPROVAL,
        "priority": Priority.HIGH,
        "confidence": 74.2,
        "title": "Broken product complaint — Sarah Johnson (Order #ORD-789)",
        "extracted": {
            "name": "Sarah Johnson", "email": "sarah.johnson@gmail.com",
            "phone": "+1-555-0123", "amount": None,
            "order_number": "ORD-789",
            "priority": "high", "urgency_indicators": ["asap"],
            "key_entities": {"product": "SmartHub Pro"},
            "summary": "Customer reports broken SmartHub Pro purchased 3 weeks ago, requesting refund or replacement",
        },
        "requires_human": True,
        "action_type": "generate_response",
        "action_status": ActionStatus.PENDING_APPROVAL,
        "action_result": None,
        "decision_reasoning": "Moderate confidence (74.2%) — pending human review",
    },
    {
        "source": "manual",
        "raw_input": (
            "New lead from TechSummit 2024 Conference\n"
            "Name: Carlos Rodriguez\nTitle: CTO\nCompany: TechStart Inc.\n"
            "Email: c.rodriguez@techstart.io\n"
            "Interested in: Enterprise Automation Package\n"
            "Budget: $50,000\nTimeline: Q1 2025\n\n"
            "Notes: Decision maker, very engaged during demo. "
            "Wants to automate invoice processing and customer onboarding. "
            "Schedule discovery call this week."
        ),
        "process_type": ProcessType.LEAD,
        "status": ProcessStatus.COMPLETED,
        "priority": Priority.HIGH,
        "confidence": 91.0,
        "title": "Hot lead — Carlos Rodriguez, CTO at TechStart Inc. ($50K budget)",
        "extracted": {
            "name": "Carlos Rodriguez", "email": "c.rodriguez@techstart.io",
            "amount": 50000.0, "currency": "USD",
            "priority": "high", "urgency_indicators": [],
            "key_entities": {"company": "TechStart Inc.", "title": "CTO", "timeline": "Q1 2025"},
            "summary": "CTO of TechStart Inc. interested in Enterprise Automation Package, $50K budget, Q1 2025",
        },
        "requires_human": False,
        "action_type": "create_record",
        "action_status": ActionStatus.EXECUTED,
        "action_result": {"status": "created", "record_id": "REC-0003-12347", "crm_synced": True, "auto_response_sent": True},
        "decision_reasoning": "High confidence (91.0%) — auto-executing action",
    },
    {
        "source": "email",
        "raw_input": (
            "From: accounts@global-supplies.com\n"
            "Subject: URGENT — Overdue Payment #PO-2024-445 — 30 Days Past Due\n\n"
            "This is a final notice regarding invoice #PO-2024-445 for $15,750.00.\n"
            "This payment is 30 days past due. Immediate payment is required to avoid "
            "service suspension and potential collection proceedings.\n\n"
            "Wire transfer details:\nBank: First National\nAccount: 1234567890\n"
            "Routing: 021000021\n\nContact: billing@global-supplies.com"
        ),
        "process_type": ProcessType.PAYMENT_REQUEST,
        "status": ProcessStatus.AWAITING_APPROVAL,
        "priority": Priority.CRITICAL,
        "confidence": 85.3,
        "title": "URGENT: Overdue payment $15,750 — Global Supplies (30 days past due)",
        "extracted": {
            "name": "Global Supplies", "email": "billing@global-supplies.com",
            "amount": 15750.0, "currency": "USD",
            "order_number": "PO-2024-445",
            "priority": "critical", "urgency_indicators": ["urgent", "overdue", "past due", "final notice", "suspend"],
            "key_entities": {"bank": "First National"},
            "summary": "Final notice for overdue payment of $15,750 — 30 days past due, service suspension threatened",
        },
        "requires_human": True,
        "action_type": "approve_payment",
        "action_status": ActionStatus.PENDING_APPROVAL,
        "action_result": None,
        "decision_reasoning": "Action 'approve_payment' always requires human authorization",
    },
    {
        "source": "api",
        "raw_input": (
            "Ticket Subject: API returning 500 Internal Server Error\n"
            "Reporter: dev@startupxyz.com\n"
            "Severity: High\n\n"
            "Our integration with your REST API started failing at 14:32 UTC today. "
            "All POST requests to /api/orders endpoint return HTTP 500. "
            "Error message: 'Database connection timeout'. "
            "This is blocking our entire checkout flow. We process ~500 orders/hour.\n\n"
            "Request ID: REQ-abc-123\nEnvironment: Production"
        ),
        "process_type": ProcessType.SUPPORT_TICKET,
        "status": ProcessStatus.COMPLETED,
        "priority": Priority.HIGH,
        "confidence": 86.4,
        "title": "API 500 errors blocking checkout — StartupXYZ (500 orders/hour affected)",
        "extracted": {
            "name": None, "email": "dev@startupxyz.com",
            "priority": "high", "urgency_indicators": ["urgent"],
            "order_number": "REQ-ABC-123",
            "key_entities": {"endpoint": "/api/orders", "error": "Database connection timeout"},
            "summary": "POST /api/orders returning 500 — database connection timeout, blocking checkout flow",
        },
        "requires_human": False,
        "action_type": "create_record",
        "action_status": ActionStatus.EXECUTED,
        "action_result": {"status": "created", "record_id": "TKT-0005-12349", "crm_synced": True},
        "decision_reasoning": "High confidence (86.4%) — auto-executing action",
    },
    {
        "source": "form",
        "raw_input": (
            "Department: Human Resources\n"
            "Request Type: Policy Update — Remote Work Policy\n"
            "Submitted by: Maria Chen (hr@company.com)\n\n"
            "We need to update the remote work policy to include the new hybrid schedule "
            "requirements effective January 1, 2025. All employees must be in office "
            "Tuesdays and Thursdays. The updated policy document is attached. "
            "Please route for legal review and executive sign-off before publishing."
        ),
        "process_type": ProcessType.ADMIN_CASE,
        "status": ProcessStatus.COMPLETED,
        "priority": Priority.MEDIUM,
        "confidence": 79.1,
        "title": "HR Policy Update — Remote Work Policy (hybrid schedule effective Jan 2025)",
        "extracted": {
            "name": "Maria Chen", "email": "hr@company.com",
            "date": "January 1, 2025",
            "priority": "medium", "urgency_indicators": [],
            "key_entities": {"department": "Human Resources", "type": "Policy Update"},
            "summary": "Remote work policy update — hybrid schedule Tue/Thu in-office, requires legal review",
        },
        "requires_human": False,
        "action_type": "notify_team",
        "action_status": ActionStatus.EXECUTED,
        "action_result": {"status": "notified", "channel": "#operations", "recipients": ["ops-team"]},
        "decision_reasoning": "High confidence (79.1%) — auto-executing action",
    },
    {
        "source": "email",
        "raw_input": (
            "From: anonymous_user@tempmail.com\n"
            "Subject: Problem\n\n"
            "I am very unhappy. Your service is terrible. I have been waiting for 3 weeks "
            "and nobody has helped me. This is ridiculous. I want my money back.\n\nAnonymous"
        ),
        "process_type": ProcessType.CLAIM,
        "status": ProcessStatus.ESCALATED,
        "priority": Priority.HIGH,
        "confidence": 38.5,
        "title": "Vague complaint — missing details, escalated for human review",
        "extracted": {
            "name": "Anonymous", "email": "anonymous_user@tempmail.com",
            "amount": None,
            "priority": "high", "urgency_indicators": [],
            "key_entities": {},
            "summary": "Customer unhappy with service, waiting 3 weeks, requesting refund — no order details provided",
        },
        "requires_human": True,
        "action_type": "escalate",
        "action_status": ActionStatus.PENDING_APPROVAL,
        "action_result": None,
        "decision_reasoning": "Low confidence (38.5%) — escalated for review",
    },
    {
        "source": "form",
        "raw_input": (
            "Customer: Michael Torres\nEmail: m.torres@enterprise.com\n"
            "Order #: ORD-2024-5521\nProduct: DataSync Pro License (Annual)\n"
            "Purchase Date: September 15, 2024\nAmount: $299.00\n\n"
            "Request: I need to cancel and refund my annual subscription. "
            "I purchased the wrong tier — I need the Enterprise plan, not Standard. "
            "Please process refund to original payment method."
        ),
        "process_type": ProcessType.CLAIM,
        "status": ProcessStatus.AWAITING_APPROVAL,
        "priority": Priority.MEDIUM,
        "confidence": 68.7,
        "title": "Refund request — Michael Torres, DataSync Pro $299 (wrong tier purchased)",
        "extracted": {
            "name": "Michael Torres", "email": "m.torres@enterprise.com",
            "amount": 299.0, "currency": "USD",
            "date": "September 15, 2024", "order_number": "ORD-2024-5521",
            "priority": "medium", "urgency_indicators": [],
            "key_entities": {"product": "DataSync Pro", "reason": "wrong tier"},
            "summary": "Refund request for $299 DataSync Pro Standard — customer needs Enterprise plan instead",
        },
        "requires_human": True,
        "action_type": "generate_response",
        "action_status": ActionStatus.PENDING_APPROVAL,
        "action_result": None,
        "decision_reasoning": "Moderate confidence (68.7%) — pending human review",
    },
    {
        "source": "api",
        "raw_input": (
            "Lead Source: Website Contact Form\n"
            "Name: Priya Sharma\nTitle: VP of Operations\nCompany: RetailChain Global\n"
            "Email: p.sharma@retailchain.com\nPhone: +1-212-555-0198\n\n"
            "Message: We are evaluating automation solutions for our accounts payable "
            "department. We process ~2,000 invoices per month manually and want to "
            "automate 80% of them. Timeline: H1 2025. Budget: $120,000/year.\n"
            "Please have someone contact me to discuss our requirements."
        ),
        "process_type": ProcessType.LEAD,
        "status": ProcessStatus.COMPLETED,
        "priority": Priority.HIGH,
        "confidence": 93.2,
        "title": "Enterprise lead — Priya Sharma (VP Ops), RetailChain Global — $120K/yr, H1 2025",
        "extracted": {
            "name": "Priya Sharma", "email": "p.sharma@retailchain.com",
            "phone": "+1-212-555-0198", "amount": 120000.0, "currency": "USD",
            "priority": "high", "urgency_indicators": [],
            "key_entities": {
                "company": "RetailChain Global", "title": "VP of Operations",
                "invoice_volume": "2,000/month", "timeline": "H1 2025",
            },
            "summary": "VP Ops at RetailChain Global needs invoice automation for 2K/month, $120K budget, H1 2025",
        },
        "requires_human": False,
        "action_type": "create_record",
        "action_status": ActionStatus.EXECUTED,
        "action_result": {"status": "created", "record_id": "REC-0009-12353", "crm_synced": True, "auto_response_sent": True},
        "decision_reasoning": "High confidence (93.2%) — auto-executing action",
    },
    {
        "source": "email",
        "raw_input": (
            "From: cfo@bigcorp.com\nSubject: Invoice #INV-2024-9901 — Software License Renewal\n\n"
            "Please process payment for our annual software license renewal.\n"
            "Invoice #INV-2024-9901\nAmount: $28,500.00\nVendor: CloudSoft Solutions\n"
            "Due Date: December 1, 2024\n\n"
            "This is a critical business system. Please expedite."
        ),
        "process_type": ProcessType.INVOICE,
        "status": ProcessStatus.AWAITING_APPROVAL,
        "priority": Priority.HIGH,
        "confidence": 87.0,
        "title": "Large invoice $28,500 — CloudSoft Solutions license renewal (requires authorization)",
        "extracted": {
            "name": "BigCorp CFO", "email": "cfo@bigcorp.com",
            "amount": 28500.0, "currency": "USD",
            "date": "December 1, 2024", "order_number": "INV-2024-9901",
            "priority": "high", "urgency_indicators": ["urgent"],
            "key_entities": {"vendor": "CloudSoft Solutions", "type": "License Renewal"},
            "summary": "Annual software license renewal $28,500 — CloudSoft Solutions, due December 1",
        },
        "requires_human": True,
        "action_type": "create_record",
        "action_status": ActionStatus.PENDING_APPROVAL,
        "action_result": None,
        "decision_reasoning": "High-value transaction ($28,500.00) requires authorization",
    },
]


def seed(db):
    existing = db.query(Process).count()
    if existing > 0:
        print(f"Database already has {existing} processes. Skipping seed.")
        return

    now = datetime.now(timezone.utc).replace(tzinfo=None) 

    for i, sample in enumerate(SAMPLE_INPUTS):
        offset_hours = (len(SAMPLE_INPUTS) - i) * 6 + random.randint(0, 3)
        created = now - timedelta(hours=offset_hours)
        processed = created + timedelta(seconds=random.randint(2, 8)) if sample["status"] not in (
            ProcessStatus.PENDING, ProcessStatus.PROCESSING
        ) else None

        process = Process(
            source=sample["source"],
            raw_input=sample["raw_input"],
            process_type=sample["process_type"],
            status=sample["status"],
            priority=sample["priority"],
            confidence_score=sample["confidence"],
            extracted_data=sample["extracted"],
            title=sample["title"],
            created_at=created,
            updated_at=processed or created,
            processed_at=processed,
        )
        db.add(process)
        db.flush()

        decision = Decision(
            process_id=process.id,
            classification=sample["process_type"],
            reasoning=sample["decision_reasoning"],
            confidence=sample["confidence"],
            requires_human=sample["requires_human"],
            auto_executable=not sample["requires_human"],
            validation_errors=[],
            missing_fields=[],
            ai_mode="rule_based",
            created_at=created + timedelta(seconds=1),
        )
        db.add(decision)

        action = Action(
            process_id=process.id,
            action_type=sample["action_type"],
            parameters={"record_type": sample["process_type"], "email": sample["extracted"].get("email")},
            status=sample["action_status"],
            result=sample["action_result"],
            executed_at=processed if sample["action_status"] == ActionStatus.EXECUTED else None,
            created_at=created + timedelta(seconds=2),
        )
        db.add(action)

        if sample["requires_human"]:
            approval_status = "pending"
            if sample["status"] in (ProcessStatus.APPROVED, ProcessStatus.REJECTED):
                approval_status = sample["status"]
            approval = Approval(
                process_id=process.id,
                reason=sample["decision_reasoning"],
                status=approval_status,
                created_at=created + timedelta(seconds=3),
            )
            db.add(approval)

        for event in _build_audit_events(process, sample, created):
            db.add(event)

    db.commit()
    print(f"Seeded {len(SAMPLE_INPUTS)} processes successfully.")


def _build_audit_events(process, sample, base_time):
    events = [
        AuditLog(process_id=process.id, event_type="process.received",
                 event_data={"source": sample["source"]}, actor="system",
                 created_at=base_time),
        AuditLog(process_id=process.id, event_type="pipeline.started",
                 event_data={"source": sample["source"]}, actor="system",
                 created_at=base_time + timedelta(milliseconds=200)),
        AuditLog(process_id=process.id, event_type="classification.completed",
                 event_data={"type": sample["process_type"], "confidence": sample["confidence"]},
                 actor="system", created_at=base_time + timedelta(seconds=1)),
        AuditLog(process_id=process.id, event_type="extraction.completed",
                 event_data={"fields_found": list(sample["extracted"].keys())},
                 actor="system", created_at=base_time + timedelta(seconds=2)),
        AuditLog(process_id=process.id, event_type="decision.made",
                 event_data={"requires_human": sample["requires_human"],
                             "reasoning": sample["decision_reasoning"]},
                 actor="system", created_at=base_time + timedelta(seconds=3)),
    ]
    if sample["requires_human"]:
        events.append(AuditLog(
            process_id=process.id, event_type="approval.queued",
            event_data={"reason": sample["decision_reasoning"]},
            actor="system", created_at=base_time + timedelta(seconds=4),
        ))
    else:
        events.append(AuditLog(
            process_id=process.id, event_type="action.executed",
            event_data={"action_type": sample["action_type"], "status": "executed"},
            actor="system", created_at=base_time + timedelta(seconds=4),
        ))
        events.append(AuditLog(
            process_id=process.id, event_type="pipeline.completed",
            event_data={"final_status": sample["status"], "confidence": sample["confidence"]},
            actor="system", created_at=base_time + timedelta(seconds=5),
        ))
    return events


if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
