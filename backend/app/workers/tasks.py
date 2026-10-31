"""Celery task definitions."""

from __future__ import annotations

from app.workers.celery_app import celery

EXPORT_TASK = "exports.run"
AI_TASK = "ai.run"


@celery.task(name=EXPORT_TASK)
def run_export(export_id: str) -> dict:
    from app.services.export.service import perform_export

    return perform_export(export_id)


@celery.task(name=AI_TASK)
def run_ai_job(job_id: str) -> dict:
    from app.services.jobs import run_ai_job as _run

    return _run(job_id)
