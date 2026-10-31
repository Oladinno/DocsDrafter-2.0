"""Process-wide logging configuration.

Uvichon's own handlers cover startup/shutdown ``uvicorn.error`` lines; this
module reconfigures everything else onto one plain-text format that reads well
in Railway's log viewer:

    2026-10-31 09:14:02 INFO  app.main: GET /api/documents 200 14ms

``uvicorn.access`` is neutralised because the request middleware in
``app.main`` already emits richer lines (with duration and request id).
"""

from __future__ import annotations

import logging

from app.config import settings

_LEVELS = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}


def configure_logging() -> None:
    level = _LEVELS.get(settings.log_level.lower(), logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # The request middleware produces the access line, so drop uvicorn's.
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("uvicorn.error").setLevel(level)

    # Keep noisy framework loggers at a sane level unless debugging.
    if level > logging.DEBUG:
        for name in ("httpx", "httpcore", "watchfiles"):
            logging.getLogger(name).setLevel(logging.WARNING)
