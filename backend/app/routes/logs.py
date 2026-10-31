"""Browser-side log ingestion so client errors reach the same log stream.

Unauthenticated by design: errors can happen on the login/register pages
before any session exists. Payload sizes are hard-capped in the schema and
CSRF still applies (the frontend logger sends the token like every other
POST), so this is not an open write surface.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Response

from app.schemas import ClientLogIn

_logger = logging.getLogger("app.client")

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.post("", status_code=204)
def create_client_log(payload: ClientLogIn) -> Response:
    level = {"error": logging.ERROR, "warn": logging.WARNING, "info": logging.INFO}[
        payload.level
    ]
    suffix = []
    if payload.url:
        suffix.append(f"url={payload.url}")
    if payload.user_agent:
        suffix.append(f"ua={payload.user_agent}")
    _logger.log(
        level,
        "%s | %s%s",
        payload.message,
        " ".join(suffix),
        "",
    )
    if payload.stack:
        _logger.log(level, "stack: %s", payload.stack)
    return Response(status_code=204)
