from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base


class ProcessType:
    INVOICE = "invoice"
    CUSTOMER_REQUEST = "customer_request"
    CLAIM = "claim"
    LEAD = "lead"
    SUPPORT_TICKET = "support_ticket"
    ADMIN_CASE = "admin_case"
    PAYMENT_REQUEST = "payment_request"
    OTHER = "other"

    ALL = [INVOICE, CUSTOMER_REQUEST, CLAIM, LEAD, SUPPORT_TICKET, ADMIN_CASE, PAYMENT_REQUEST, OTHER]


class ProcessStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class Priority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType:
    SEND_EMAIL = "send_email"
    CREATE_RECORD = "create_record"
    UPDATE_RECORD = "update_record"
    GENERATE_RESPONSE = "generate_response"
    ESCALATE = "escalate"
    REQUEST_INFORMATION = "request_information"
    APPROVE_PAYMENT = "approve_payment"
    CLOSE_CASE = "close_case"
    NOTIFY_TEAM = "notify_team"


class ActionStatus:
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Process(Base):
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid4()))
    source = Column(String(50), nullable=False)
    raw_input = Column(Text, nullable=False)
    process_type = Column(String(50), default=ProcessType.OTHER)
    status = Column(String(50), default=ProcessStatus.PENDING, index=True)
    priority = Column(String(20), default=Priority.MEDIUM)
    confidence_score = Column(Float, default=0.0)
    extracted_data = Column(JSON, nullable=True)
    title = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)

    decisions = relationship("Decision", back_populates="process", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="process", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="process", cascade="all, delete-orphan")
    approval = relationship("Approval", back_populates="process", uselist=False, cascade="all, delete-orphan")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False)
    classification = Column(String(50))
    reasoning = Column(Text)
    confidence = Column(Float)
    requires_human = Column(Boolean, default=False)
    auto_executable = Column(Boolean, default=False)
    validation_errors = Column(JSON, default=list)
    missing_fields = Column(JSON, default=list)
    ai_mode = Column(String(20), default="rule_based")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    process = relationship("Process", back_populates="decisions")


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False)
    action_type = Column(String(50), nullable=False)
    parameters = Column(JSON, default=dict)
    status = Column(String(50), default=ActionStatus.PENDING)
    result = Column(JSON, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    process = relationship("Process", back_populates="actions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, default=dict)
    actor = Column(String(100), default="system")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    process = relationship("Process", back_populates="audit_logs")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), unique=True, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default="pending")
    reviewer = Column(String(100), nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime, nullable=True)

    process = relationship("Process", back_populates="approval")
