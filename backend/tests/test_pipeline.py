"""Integration tests for the agent pipeline using an in-memory SQLite database."""
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import (
    Action, ActionStatus, Approval, Decision,
    Process, ProcessStatus, ProcessType,
)
from app.agent.pipeline import run_pipeline


@pytest.fixture(scope="function")
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _create_process(db, raw_input: str, source: str = "manual") -> Process:
    p = Process(source=source, raw_input=raw_input)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


class TestPipelineBasicFlow:
    def test_pipeline_completes_for_clear_invoice(self, db):
        p = _create_process(
            db,
            "From: vendor@acme.com\nSubject: Invoice #INV-001\n"
            "Amount: $500.00. Due: December 1. Please process payment.",
        )
        run_pipeline(p.id, db)
        db.refresh(p)
        assert p.status == ProcessStatus.COMPLETED
        assert p.process_type == ProcessType.INVOICE
        assert p.confidence_score > 0

    def test_pipeline_sets_process_type(self, db):
        p = _create_process(
            db,
            "CTO at Enterprise Corp interested in automation package. "
            "Budget $30,000. Email: cto@enterprise.com",
        )
        run_pipeline(p.id, db)
        db.refresh(p)
        assert p.process_type == ProcessType.LEAD

    def test_pipeline_populates_extracted_data(self, db):
        p = _create_process(
            db,
            "Invoice for $1,200. Contact: billing@corp.com. Ref: INV-2024-500",
        )
        run_pipeline(p.id, db)
        db.refresh(p)
        assert p.extracted_data is not None
        assert p.extracted_data.get("email") == "billing@corp.com"
        assert p.extracted_data.get("amount") == 1200.0

    def test_pipeline_sets_confidence_score(self, db):
        p = _create_process(db, "Invoice #INV-001 for $500 from vendor@co.com due Dec 1.")
        run_pipeline(p.id, db)
        db.refresh(p)
        assert 0.0 < p.confidence_score <= 100.0

    def test_pipeline_creates_decision_record(self, db):
        p = _create_process(db, "Invoice #INV-001 for $500. Contact: a@b.com")
        run_pipeline(p.id, db)
        decisions = db.query(Decision).filter(Decision.process_id == p.id).all()
        assert len(decisions) == 1
        assert decisions[0].classification == ProcessType.INVOICE

    def test_pipeline_creates_action_record(self, db):
        p = _create_process(db, "Invoice #INV-001 for $500. Contact: a@b.com")
        run_pipeline(p.id, db)
        actions = db.query(Action).filter(Action.process_id == p.id).all()
        assert len(actions) == 1

    def test_pipeline_creates_audit_log(self, db):
        from app.db.models import AuditLog
        p = _create_process(db, "Invoice #INV-001 for $500. Contact: a@b.com")
        run_pipeline(p.id, db)
        logs = db.query(AuditLog).filter(AuditLog.process_id == p.id).all()
        assert len(logs) >= 3
        event_types = {log.event_type for log in logs}
        assert "pipeline.started" in event_types
        assert "classification.completed" in event_types


class TestPipelineEscalation:
    def test_high_value_invoice_queued_for_approval(self, db):
        p = _create_process(
            db,
            "Invoice #INV-001 for $25,000.00 from cfo@bigcorp.com due December 1.",
        )
        run_pipeline(p.id, db)
        db.refresh(p)
        assert p.status == ProcessStatus.AWAITING_APPROVAL

    def test_high_value_creates_approval_record(self, db):
        p = _create_process(
            db,
            "Invoice #INV-001 for $25,000.00 from cfo@bigcorp.com due December 1.",
        )
        run_pipeline(p.id, db)
        approval = db.query(Approval).filter(Approval.process_id == p.id).first()
        assert approval is not None
        assert approval.status == "pending"

    def test_payment_request_always_escalated(self, db):
        p = _create_process(
            db,
            "URGENT: Invoice #PO-001 is 30 days past due. "
            "Wire transfer of $5,000 required immediately or service suspended. "
            "Contact: billing@vendor.com",
        )
        run_pipeline(p.id, db)
        db.refresh(p)
        assert p.status == ProcessStatus.AWAITING_APPROVAL

    def test_low_confidence_requires_human(self, db):
        p = _create_process(db, "I have a problem. Please help.")
        run_pipeline(p.id, db)
        db.refresh(p)
        decision = db.query(Decision).filter(Decision.process_id == p.id).first()
        assert decision is not None
        if decision.confidence < 50.0:
            assert decision.requires_human is True


class TestPipelineErrorHandling:
    def test_pipeline_handles_nonexistent_process(self, db):
        """Should not raise — just log and return."""
        run_pipeline(99999, db)  # no exception

    def test_failed_process_has_failed_status(self, db, monkeypatch):
        """If the AI service crashes mid-pipeline, process status becomes 'failed'."""
        from app.services import ai_service as ai_module

        def boom(*args, **kwargs):
            raise RuntimeError("Simulated AI failure")

        monkeypatch.setattr(ai_module.ai_service, "classify", boom)

        p = _create_process(db, "Invoice for $500")
        run_pipeline(p.id, db)
        db.refresh(p)
        assert p.status == ProcessStatus.FAILED
