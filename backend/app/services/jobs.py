"""Background AI job execution."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db import SessionLocal
from app.models import Job
from app.services.ai import run_operation
from app.services.ai.operations import AIRequest
from app.services.ai.provider import AIError


def run_ai_job(job_id: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            raise ValueError(f"job {job_id} not found")
        job.status = "running"
        db.commit()

        request = AIRequest.model_validate(job.payload or {})
        try:
            result = run_operation(request)
        except AIError as exc:
            job = db.get(Job, job_id)
            job.status = "failed"
            job.error = str(exc)[:2000]
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            return {"id": job_id, "status": "failed", "error": str(exc)}

        job = db.get(Job, job_id)
        job.status = "succeeded"
        job.result = result
        job.error = None
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        return {"id": job_id, "status": "succeeded"}
    finally:
        db.close()
