"""Celery application.

Used by the ``worker`` Railway service. Local development and tests default to
``TASK_MODE=inline``, which runs the same task functions in-process.
"""

from __future__ import annotations

from celery import Celery

from app.config import settings

celery = Celery(
    "docsdrafter",
    broker=settings.broker_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_soft_time_limit=15 * 60,
    task_time_limit=20 * 60,
)

# Importing the tasks module registers them on this app.
from app.workers import tasks  # noqa: E402,F401

__all__ = ["celery"]
