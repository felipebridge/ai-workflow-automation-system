from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import (
    Action, ActionStatus, Approval, Decision,
    Process, ProcessStatus, Priority
)
from app.services.ai_service import ai_service
from app.services.audit_service import audit_service
from app.agent.validator import validate_data, calculate_confidence
from app.agent.decision_engine import make_decision
from app.agent.action_executor import execute_action
from app.core.logging_config import get_logger

logger = get_logger("pipeline")


def run_pipeline(process_id: int, db: Session) -> None:
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        logger.error("Pipeline: process %d not found", process_id)
        return

    logger.info("Pipeline START — process=%d source=%s", process_id, process.source)

    try:
        _set_status(db, process, ProcessStatus.PROCESSING)
        audit_service.log(db, process_id, "pipeline.started", {"source": process.source})
        db.commit()

        # 1: Classify 
        classification = ai_service.classify(process.raw_input)
        process.process_type = classification["process_type"]
        audit_service.log(db, process_id, "classification.completed", {
            "type": classification["process_type"],
            "confidence": classification["confidence"],
            "reasoning": classification.get("reasoning", ""),
            "mode": ai_service.get_mode(),
        })
        db.commit()

        # 2: Extract 
        extracted = ai_service.extract(process.raw_input, process.process_type)
        process.extracted_data = extracted

        if extracted.get("priority") in (Priority.HIGH, Priority.CRITICAL):
            process.priority = extracted["priority"]
        elif extracted.get("urgency_indicators"):
            process.priority = Priority.HIGH

        process.title = _derive_title(process, extracted)

        audit_service.log(db, process_id, "extraction.completed", {
            "fields_found": [k for k, v in extracted.items() if v not in (None, [], {})],
            "has_amount": extracted.get("amount") is not None,
        })
        db.commit()

        # 3: Validate 
        validation_errors, missing_fields = validate_data(extracted, process.process_type)
        audit_service.log(db, process_id, "validation.completed", {
            "errors": validation_errors,
            "missing": missing_fields,
        })

        # 4: Confidence 
        confidence = calculate_confidence(
            classification["confidence"], extracted,
            process.process_type, validation_errors, missing_fields
        )
        process.confidence_score = confidence

        # 5: Decide 
        decision_result = make_decision(
            process.process_type, extracted, confidence, validation_errors, missing_fields
        )
        audit_service.log(db, process_id, "decision.made", {
            "requires_human": decision_result["requires_human"],
            "action_type": decision_result["action_type"],
            "reasoning": decision_result["reasoning"],
        })

        # 6: Persist decision 
        decision = Decision(
            process_id=process_id,
            classification=process.process_type,
            reasoning=decision_result["reasoning"],
            confidence=confidence,
            requires_human=decision_result["requires_human"],
            auto_executable=not decision_result["requires_human"],
            validation_errors=validation_errors,
            missing_fields=missing_fields,
            ai_mode=ai_service.get_mode(),
        )
        db.add(decision)

        action = Action(
            process_id=process_id,
            action_type=decision_result["action_type"],
            parameters=decision_result["action_params"],
            status=ActionStatus.PENDING,
        )
        db.add(action)
        db.flush()

        # 7: Execute or queue for approval 
        if decision_result["requires_human"]:
            approval = Approval(
                process_id=process_id,
                reason=decision_result["reasoning"],
            )
            db.add(approval)
            action.status = ActionStatus.PENDING_APPROVAL
            _set_status(db, process, ProcessStatus.AWAITING_APPROVAL)
            audit_service.log(db, process_id, "approval.queued", {
                "reason": decision_result["reasoning"],
                "action_type": decision_result["action_type"],
            })
        else:
            result = execute_action(action.action_type, action.parameters, process)
            action.status = ActionStatus.EXECUTED
            action.result = result
            action.executed_at = datetime.now(timezone.utc)
            process.processed_at = datetime.now(timezone.utc)
            _set_status(db, process, ProcessStatus.COMPLETED)
            audit_service.log(db, process_id, "action.executed", {
                "action_type": action.action_type,
                "status": result.get("status"),
            })

        db.commit()
        audit_service.log(db, process_id, "pipeline.completed", {
            "final_status": process.status,
            "confidence": confidence,
            "auto_executed": not decision_result["requires_human"],
        })
        db.commit()
        logger.info("Pipeline DONE — process=%d status=%s confidence=%.1f", process_id, process.status, confidence)

    except Exception as exc:
        logger.error("Pipeline FAILED — process=%d error=%s", process_id, exc, exc_info=True)
        db.rollback()
        try:
            process = db.query(Process).filter(Process.id == process_id).first()
            if process:
                process.status = ProcessStatus.FAILED
                audit_service.log(db, process_id, "pipeline.failed", {"error": str(exc)})
                db.commit()
        except Exception:
            pass


def run_pipeline_task(process_id: int) -> None:
    """Background task entrypoint — creates its own DB session."""
    db = SessionLocal()
    try:
        run_pipeline(process_id, db)
    finally:
        db.close()


def _set_status(db: Session, process: Process, status: str) -> None:
    process.status = status
    process.updated_at = datetime.now(timezone.utc)


def _derive_title(process: Process, extracted: dict) -> str:
    if extracted.get("summary"):
        return extracted["summary"][:250]
    if extracted.get("order_number"):
        return f"{process.process_type.replace('_', ' ').title()} — {extracted['order_number']}"
    if extracted.get("name"):
        return f"{process.process_type.replace('_', ' ').title()} from {extracted['name']}"
    return f"{process.process_type.replace('_', ' ').title()} via {process.source}"
