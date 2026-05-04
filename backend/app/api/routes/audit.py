from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import AuditLog
from app.schemas.schemas import AuditLogListResponse, AuditLogResponse

router = APIRouter()


@router.get("/logs", response_model=AuditLogListResponse)
def get_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    process_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)

    if process_id is not None:
        query = query.filter(AuditLog.process_id == process_id)
    if event_type:
        query = query.filter(AuditLog.event_type.ilike(f"%{event_type}%"))

    total = query.count()
    items = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return AuditLogListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/process/{process_id}", response_model=list)
def get_process_audit(process_id: int, db: Session = Depends(get_db)):
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.process_id == process_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )
    return [AuditLogResponse.model_validate(log) for log in logs]
