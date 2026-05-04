from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Process
from app.schemas.schemas import IngestionRequest, IngestionResponse
from app.agent.pipeline import run_pipeline_task
from app.services.audit_service import audit_service
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger("routes.ingestion")


@router.post("/submit", response_model=IngestionResponse, status_code=202)
def submit_process(
    payload: IngestionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    process = Process(source=payload.source, raw_input=payload.raw_input)
    db.add(process)
    db.flush()

    audit_service.log(db, process.id, "process.received", {
        "source": payload.source,
        "input_length": len(payload.raw_input),
    })
    db.commit()

    background_tasks.add_task(run_pipeline_task, process.id)

    logger.info("Accepted process id=%d source=%s", process.id, payload.source)
    return IngestionResponse(
        process_id=process.id,
        uuid=process.uuid,
        status=process.status,
        message="Process accepted and queued for analysis",
    )
