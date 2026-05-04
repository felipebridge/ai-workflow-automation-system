from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, field_validator


# Ingestion 

class IngestionRequest(BaseModel):
    source: str = "manual"
    raw_input: str

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        allowed = {"email", "pdf", "form", "manual", "api"}
        if v not in allowed:
            raise ValueError(f"source must be one of {allowed}")
        return v

    @field_validator("raw_input")
    @classmethod
    def validate_input(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("raw_input cannot be empty")
        if len(v) > 50_000:
            raise ValueError("raw_input exceeds maximum length of 50,000 characters")
        return v.strip()


class IngestionResponse(BaseModel):
    process_id: int
    uuid: str
    status: str
    message: str


# Extracted Data 

class ExtractedData(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    order_number: Optional[str] = None
    priority: str = "medium"
    urgency_indicators: List[str] = []
    key_entities: Dict[str, Any] = {}
    summary: Optional[str] = None


# Process 

class ProcessBase(BaseModel):
    source: str
    raw_input: str
    process_type: str = "other"
    status: str = "pending"
    priority: str = "medium"
    confidence_score: float = 0.0
    title: Optional[str] = None


class ProcessResponse(ProcessBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    extracted_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


class ProcessListResponse(BaseModel):
    items: List[ProcessResponse]
    total: int
    page: int
    per_page: int
    pages: int


# Decision 

class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    process_id: int
    classification: str
    reasoning: str
    confidence: float
    requires_human: bool
    auto_executable: bool
    validation_errors: List[str] = []
    missing_fields: List[str] = []
    ai_mode: str
    created_at: datetime


# Action 

class ActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    process_id: int
    action_type: str
    parameters: Dict[str, Any] = {}
    status: str
    result: Optional[Dict[str, Any]] = None
    executed_at: Optional[datetime] = None
    created_at: datetime


# Audit Log 

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    process_id: Optional[int] = None
    event_type: str
    event_data: Dict[str, Any] = {}
    actor: str
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    per_page: int


# Approval 

class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    process_id: int
    reason: str
    status: str
    reviewer: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    process: Optional[ProcessResponse] = None


class ApprovalActionRequest(BaseModel):
    reviewer: str = "admin"
    notes: Optional[str] = None


# Process Detail

class ProcessDetailResponse(ProcessResponse):
    decisions: List[DecisionResponse] = []
    actions: List[ActionResponse] = []
    audit_logs: List[AuditLogResponse] = []
    approval: Optional[ApprovalResponse] = None


# Metrics 

class MetricsSummary(BaseModel):
    total_processes: int
    pending: int
    processing: int
    completed: int
    failed: int
    awaiting_approval: int
    approved: int
    rejected: int
    escalated: int
    automated_count: int
    human_reviewed_count: int
    automation_rate: float
    avg_confidence: float
    avg_processing_time_seconds: float


class VolumeDataPoint(BaseModel):
    date: str
    total: int
    automated: int
    human_reviewed: int


class TypeBreakdown(BaseModel):
    process_type: str
    count: int
    percentage: float


class ConfidenceBucket(BaseModel):
    label: str
    min_val: float
    max_val: float
    count: int


class MetricsBreakdownResponse(BaseModel):
    by_type: List[TypeBreakdown]
    by_status: List[Dict[str, Any]]
    confidence_distribution: List[ConfidenceBucket]
