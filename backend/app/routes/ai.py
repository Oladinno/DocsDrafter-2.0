"""AI generation endpoints (background jobs, polled by the client)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_csrf
from app.models import Document, Job, User
from app.schemas import AIGenerateIn, AIOperationsOut, JobOut
from app.services.ai import available_operations
from app.services.ai.operations import AIRequest
from app.services.ai.provider import get_provider
from app.workers.dispatch import dispatch
from app.workers.tasks import AI_TASK

router = APIRouter(prefix="/api", tags=["ai"], dependencies=[Depends(require_csrf)])


@router.get("/ai/operations", response_model=AIOperationsOut)
def operations() -> AIOperationsOut:
    return AIOperationsOut(items=available_operations())


@router.get("/ai/status", response_model=dict)
def ai_status() -> dict:
    provider = get_provider()
    return {"provider": provider.name}


@router.post("/ai/generate", response_model=JobOut, status_code=202)
def generate(
    payload: AIGenerateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobOut:
    if payload.document_id:
        document = db.get(Document, payload.document_id)
        if document is None or document.owner_id != user.id:
            raise HTTPException(status_code=404, detail="Document not found")

    request = AIRequest.model_validate(payload.model_dump())
    job = Job(
        owner_id=user.id,
        kind=f"ai.{payload.operation}",
        status="pending",
        payload=request.model_dump(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    dispatch(AI_TASK, job.id)

    db.expire(job)
    return JobOut.model_validate(job)


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobOut:
    job = db.scalar(select(Job).where(Job.id == job_id, Job.owner_id == user.id))
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobOut.model_validate(job)
