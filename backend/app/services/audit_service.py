from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.db.models import AuditLog
from app.core.logging_config import get_logger

logger = get_logger("audit")


class AuditService:
    def log(
        self,
        db: Session,
        process_id: Optional[int],
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        actor: str = "system",
    ) -> AuditLog:
        entry = AuditLog(
            process_id=process_id,
            event_type=event_type,
            event_data=event_data or {},
            actor=actor,
            created_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.flush()
        logger.debug("AUDIT [%s] process=%s actor=%s data=%s", event_type, process_id, actor, event_data)
        return entry

    def get_process_trail(self, db: Session, process_id: int) -> list:
        return (
            db.query(AuditLog)
            .filter(AuditLog.process_id == process_id)
            .order_by(AuditLog.created_at.asc())
            .all()
        )


audit_service = AuditService()
