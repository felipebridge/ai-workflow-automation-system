from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Action, ActionStatus, Approval, Decision, Process
from app.schemas.schemas import (
    ConfidenceBucket, MetricsBreakdownResponse,
    MetricsSummary, TypeBreakdown, VolumeDataPoint,
)

router = APIRouter()


@router.get("/summary", response_model=MetricsSummary)
def get_summary(db: Session = Depends(get_db)):
    status_counts = dict(
        db.query(Process.status, func.count(Process.id))
        .group_by(Process.status)
        .all()
    )
    total = sum(status_counts.values())

    automated = (
        db.query(func.count(Action.id))
        .filter(Action.status == ActionStatus.EXECUTED)
        .join(Decision, Decision.process_id == Action.process_id)
        .filter(Decision.auto_executable.is_(True))
        .scalar() or 0
    )
    human_reviewed = (
        db.query(func.count(Approval.id))
        .filter(Approval.status.in_(["approved", "rejected"]))
        .scalar() or 0
    )

    avg_confidence = db.query(func.avg(Process.confidence_score)).scalar() or 0.0

    completed_with_time = (
        db.query(Process.created_at, Process.processed_at)
        .filter(Process.status.in_(["completed", "approved", "rejected"]))
        .filter(Process.processed_at.isnot(None))
        .all()
    )
    avg_time = 0.0
    if completed_with_time:
        durations = [(p - c).total_seconds() for c, p in completed_with_time if p]
        avg_time = sum(durations) / len(durations) if durations else 0.0

    automation_rate = round((automated / total * 100) if total > 0 else 0.0, 1)

    return MetricsSummary(
        total_processes=total,
        pending=status_counts.get("pending", 0),
        processing=status_counts.get("processing", 0),
        completed=status_counts.get("completed", 0),
        failed=status_counts.get("failed", 0),
        awaiting_approval=status_counts.get("awaiting_approval", 0),
        approved=status_counts.get("approved", 0),
        rejected=status_counts.get("rejected", 0),
        escalated=status_counts.get("escalated", 0),
        automated_count=automated,
        human_reviewed_count=human_reviewed,
        automation_rate=automation_rate,
        avg_confidence=round(avg_confidence, 1),
        avg_processing_time_seconds=round(avg_time, 1),
    )


@router.get("/volume", response_model=List[VolumeDataPoint])
def get_volume(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    result = []
    now = datetime.now(timezone.utc)

    for i in range(days - 1, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        total = (
            db.query(func.count(Process.id))
            .filter(Process.created_at >= day_start, Process.created_at < day_end)
            .scalar() or 0
        )
        automated = (
            db.query(func.count(Action.id))
            .filter(Action.status == ActionStatus.EXECUTED)
            .join(Decision, Decision.process_id == Action.process_id)
            .filter(Decision.auto_executable.is_(True))
            .filter(Action.executed_at >= day_start, Action.executed_at < day_end)
            .scalar() or 0
        )
        human_reviewed = (
            db.query(func.count(Approval.id))
            .filter(Approval.reviewed_at >= day_start, Approval.reviewed_at < day_end)
            .scalar() or 0
        )

        result.append(VolumeDataPoint(
            date=day_start.strftime("%Y-%m-%d"),
            total=total,
            automated=automated,
            human_reviewed=human_reviewed,
        ))

    return result


@router.get("/breakdown", response_model=MetricsBreakdownResponse)
def get_breakdown(db: Session = Depends(get_db)):
    total = db.query(func.count(Process.id)).scalar() or 1

    type_rows = (
        db.query(Process.process_type, func.count(Process.id))
        .group_by(Process.process_type)
        .all()
    )
    by_type = [
        TypeBreakdown(
            process_type=pt,
            count=count,
            percentage=round(count / total * 100, 1),
        )
        for pt, count in sorted(type_rows, key=lambda r: r[1], reverse=True)
    ]

    status_rows = (
        db.query(Process.status, func.count(Process.id))
        .group_by(Process.status)
        .all()
    )
    by_status = [{"status": s, "count": c} for s, c in status_rows]

    buckets = [
        ConfidenceBucket(label="Very Low (0-25)", min_val=0, max_val=25, count=0),
        ConfidenceBucket(label="Low (25-50)", min_val=25, max_val=50, count=0),
        ConfidenceBucket(label="Medium (50-75)", min_val=50, max_val=75, count=0),
        ConfidenceBucket(label="High (75-90)", min_val=75, max_val=90, count=0),
        ConfidenceBucket(label="Very High (90-100)", min_val=90, max_val=100, count=0),
    ]
    scores = db.query(Process.confidence_score).all()
    for (score,) in scores:
        for bucket in buckets:
            if bucket.min_val <= (score or 0) < bucket.max_val or (bucket.max_val == 100 and score == 100):
                bucket.count += 1
                break

    return MetricsBreakdownResponse(
        by_type=by_type,
        by_status=by_status,
        confidence_distribution=buckets,
    )
