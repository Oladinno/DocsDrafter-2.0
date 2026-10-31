"""Task dispatch: Celery in production, in-process for dev and tests."""

from __future__ import annotations

from typing import Any

from app.config import settings
from app.workers.tasks import AI_TASK, EXPORT_TASK


def dispatch(task_name: str, *args: Any) -> str | None:
    """Queue a background job. Returns the Celery task id when queued."""
    if settings.task_mode != "celery":
        _run_inline(task_name, *args)
        return None

    from app.workers.celery_app import celery

    return celery.send_task(task_name, args=list(args)).id


def _run_inline(task_name: str, *args: Any) -> None:
    if task_name == EXPORT_TASK:
        from app.services.export.service import perform_export

        perform_export(*args)
        return
    if task_name == AI_TASK:
        from app.services.jobs import run_ai_job

        run_ai_job(*args)
        return
    raise ValueError(f"unknown task: {task_name}")
