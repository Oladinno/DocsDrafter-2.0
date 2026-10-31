"""Shared dependencies: current user and CSRF enforcement."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import AuthSession, User
from app.security import hash_token, verify_signed_token


def _session_from_request(request: Request, db: Session) -> tuple[User, AuthSession] | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    record = db.scalar(
        select(AuthSession).where(AuthSession.token_hash == hash_token(token))
    )
    if record is None:
        return None
    expires = record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        db.delete(record)
        db.commit()
        return None
    user = db.get(User, record.user_id)
    if user is None:
        return None
    return user, record


def get_current_session(
    request: Request, db: Session = Depends(get_db)
) -> tuple[User, AuthSession]:
    result = _session_from_request(request, db)
    if result is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return result


def get_current_user(
    session: tuple[User, AuthSession] = Depends(get_current_session),
) -> User:
    return session[0]


def require_csrf(request: Request) -> None:
    """Signed double-submit check for state-changing API requests."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    header = request.headers.get("x-csrf-token")
    cookie = request.cookies.get(settings.csrf_cookie_name)
    if not header or not cookie:
        raise HTTPException(status_code=403, detail="CSRF token missing")
    if not verify_signed_token(cookie) or header != cookie:
        raise HTTPException(status_code=403, detail="CSRF token invalid")
