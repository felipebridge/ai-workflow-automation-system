from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Process
from app.schemas.schemas import ProcessDetailResponse, ProcessListResponse, ProcessResponse

router = APIRouter()


@router.get("", response_model=ProcessListResponse)
def list_processes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    process_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Process)

    if status:
        query = query.filter(Process.status == status)
    if process_type:
        query = query.filter(Process.process_type == process_type)
    if priority:
        query = query.filter(Process.priority == priority)
    if search:
        term = f"%{search}%"
        query = query.filter(
            Process.title.ilike(term) | Process.raw_input.ilike(term)
        )

    total = query.count()
    items = (
        query.order_by(Process.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return ProcessListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/{process_id}", response_model=ProcessDetailResponse)
def get_process(process_id: int, db: Session = Depends(get_db)):
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return process


@router.delete("/{process_id}", status_code=204)
def delete_process(process_id: int, db: Session = Depends(get_db)):
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    db.delete(process)
    db.commit()
