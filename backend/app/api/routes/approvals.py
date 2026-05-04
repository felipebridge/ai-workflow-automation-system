from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.db.database import get_db
from app.db.models import (
    Action, ActionStatus, Approval, Process, ProcessStatus
)
from app.schemas.schemas import ApprovalActionRequest, ApprovalResponse
from app.services.audit_service import audit_service
from app.agent.action_executor import execute_action

router = APIRouter()


@router.get("", response_model=List[ApprovalResponse])
def list_approvals(
    status: Optional[str] = Query("pending"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Approval)
        .options(joinedload(Approval.process))
        .order_by(Approval.created_at.desc())
    )
    if status:
        query = query.filter(Approval.status == status)
    return query.all()


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve(
    approval_id: int,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail=f"Approval already {approval.status}")

    process = db.query(Process).filter(Process.id == approval.process_id).first()
    action = (
        db.query(Action)
        .filter(Action.process_id == approval.process_id, Action.status == ActionStatus.PENDING_APPROVAL)
        .first()
    )

    if action and process:
        result = execute_action(action.action_type, action.parameters, process)
        action.status = ActionStatus.EXECUTED
        action.result = result
        action.executed_at = datetime.now(timezone.utc)
        process.status = ProcessStatus.APPROVED
        process.processed_at = datetime.now(timezone.utc)

    approval.status = "approved"
    approval.reviewer = payload.reviewer
    approval.review_notes = payload.notes
    approval.reviewed_at = datetime.now(timezone.utc)
    db.flush()

    audit_service.log(db, approval.process_id, "approval.approved", {
        "reviewer": payload.reviewer,
        "notes": payload.notes,
        "action_executed": action.action_type if action else None,
    }, actor=payload.reviewer)
    db.commit()

    return db.query(Approval).options(joinedload(Approval.process)).filter(Approval.id == approval_id).first()


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def reject(
    approval_id: int,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail=f"Approval already {approval.status}")

    action = (
        db.query(Action)
        .filter(Action.process_id == approval.process_id, Action.status == ActionStatus.PENDING_APPROVAL)
        .first()
    )
    if action:
        action.status = ActionStatus.CANCELLED

    process = db.query(Process).filter(Process.id == approval.process_id).first()
    if process:
        process.status = ProcessStatus.REJECTED

    approval.status = "rejected"
    approval.reviewer = payload.reviewer
    approval.review_notes = payload.notes
    approval.reviewed_at = datetime.now(timezone.utc)
    db.flush()

    audit_service.log(db, approval.process_id, "approval.rejected", {
        "reviewer": payload.reviewer,
        "notes": payload.notes,
    }, actor=payload.reviewer)
    db.commit()

    return db.query(Approval).options(joinedload(Approval.process)).filter(Approval.id == approval_id).first()
