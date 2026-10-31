"""Authentication routes: first-party sessions in HttpOnly cookies."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_current_user, require_csrf
from app.models import AuthSession, User
from app.schemas import CsrfOut, LoginIn, RegisterIn, UserOut
from app.security import (
    create_signed_token,
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter(
    prefix="/api/auth", tags=["auth"], dependencies=[Depends(require_csrf)]
)


def _set_session_cookie(response: Response, token: str) -> None:
    max_age = settings.session_ttl_days * 24 * 3600
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def _set_csrf_cookie(response: Response) -> str:
    token = create_signed_token()
    max_age = settings.session_ttl_days * 24 * 3600
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=token,
        max_age=max_age,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return token


def _clear_cookies(response: Response) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")


def _open_session(
    db: Session, user: User, request: Request, response: Response
) -> None:
    token = generate_token()
    expires = datetime.now(timezone.utc) + timedelta(days=settings.session_ttl_days)
    db.add(
        AuthSession(
            token_hash=hash_token(token),
            user_id=user.id,
            csrf_token=create_signed_token(),
            user_agent=(request.headers.get("user-agent") or "")[:255],
            expires_at=expires,
        )
    )
    db.commit()
    _set_session_cookie(response, token)
    _set_csrf_cookie(response)


@router.get("/csrf", response_model=CsrfOut)
def csrf(response: Response) -> CsrfOut:
    return CsrfOut(csrf_token=_set_csrf_cookie(response))


@router.post("/register", response_model=UserOut, status_code=201)
def register(
    payload: RegisterIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name.strip() or payload.email.split("@")[0],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _open_session(db, user, request, response)
    return user


@router.post("/login", response_model=UserOut)
def login(
    payload: LoginIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> User:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(user.password_hash, payload.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    _open_session(db, user, request, response)
    return user


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Response:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        record = db.scalar(
            select(AuthSession).where(AuthSession.token_hash == hash_token(token))
        )
        if record is not None:
            db.delete(record)
            db.commit()
    _clear_cookies(response)
    response.status_code = 204
    return response


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
