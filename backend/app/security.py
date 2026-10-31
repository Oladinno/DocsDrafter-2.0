"""Password hashing, session tokens and CSRF tokens.

Sessions use opaque random tokens stored HttpOnly on the client; only a SHA-256
digest of the token is persisted server-side. CSRF uses a signed double-submit
cookie: the value must be echoed back in the ``X-CSRF-Token`` header, must match
the cookie, and carries an HMAC signature so it cannot be forged without
``SECRET_KEY``.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.config import settings

_hasher = PasswordHasher(time_cost=2, memory_cost=64 * 1024, parallelism=2)

_TOKEN_SEPARATOR = "."


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:  # pragma: no cover - defensive
        return False


# --- tokens ----------------------------------------------------------------


def generate_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _sign(value: str) -> str:
    key = settings.secret_key.encode("utf-8")
    return hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()


def create_signed_token() -> str:
    """Random value + HMAC signature, e.g. ``<random>.<sig>``."""
    raw = secrets.token_urlsafe(24)
    return f"{raw}{TOKEN_SEP}{_sign(raw)}"


def verify_signed_token(token: str | None) -> bool:
    if not token or _TOKEN_SEPARATOR not in token:
        return False
    value, _, signature = token.rpartition(_TOKEN_SEPARATOR)
    if not value or not signature:
        return False
    expected = _sign(value)
    return hmac.compare_digest(expected, signature)


TOKEN_SEP = _TOKEN_SEPARATOR


def tokens_equal(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
