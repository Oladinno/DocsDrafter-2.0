"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from http.cookies import SimpleCookie
from starlette.datastructures import Headers

from app.config import settings
from app.db import Base, SessionLocal, engine
from app.routes import ai, auth, documents, exports, templates
from app.schemas import HealthOut
from app.security import verify_signed_token
from app.seed import seed_templates
from app.services.storage import get_storage

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class CSRFMiddleware:
    """Signed double-submit CSRF protection for state-changing API requests."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET").upper()
        path = scope.get("path", "")
        if method in SAFE_METHODS or not path.startswith("/api"):
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        header_token = headers.get("x-csrf-token", "")
        cookie_token = ""
        raw_cookie = headers.get("cookie", "")
        if raw_cookie:
            jar = SimpleCookie()
            try:
                jar.load(raw_cookie)
            except Exception:  # noqa: BLE001 - malformed cookies simply fail the check
                jar = {}
            if settings.csrf_cookie_name in jar:
                cookie_token = jar[settings.csrf_cookie_name].value

        if not header_token or not cookie_token or header_token != cookie_token:
            await self._forbidden(send, "CSRF token missing")
            return
        if not verify_signed_token(cookie_token):
            await self._forbidden(send, "CSRF token invalid")
            return
        await self.app(scope, receive, send)

    @staticmethod
    async def _forbidden(send, detail: str) -> None:
        body = JSONResponse({"detail": detail}).body
        await send(
            {
                "type": "http.response.start",
                "status": 403,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


def _init_database() -> None:
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_templates(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_database()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="DocsDrafter API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url=None,
    )

    # CSRF first (inner), CORS last (outer) so every API response - including
    # a 403 - carries the CORS headers.
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        # Local dev servers bind to arbitrary ports; production stays restricted
        # to CORS_ORIGINS.
        allow_origin_regex=None
        if settings.is_production
        else r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(templates.router)
    app.include_router(documents.router)
    app.include_router(ai.router)
    app.include_router(exports.router)

    @app.get("/health", response_model=HealthOut, tags=["health"])
    def health() -> HealthOut:
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            database = "ok"
        except Exception as exc:  # noqa: BLE001
            database = f"error: {exc}"[:120]
        return HealthOut(
            status="ok" if database == "ok" else "degraded",
            database=database,
            storage=get_storage().name,
            tasks=settings.task_mode,
            environment=settings.environment,
        )

    @app.get("/api/health", response_model=HealthOut, tags=["health"])
    def health_alias() -> HealthOut:
        return health()

    return app


app = create_app()
