"""Pytest fixtures.

The app is configured for a self-contained run: SQLite database, inline task
execution, local storage and the mock AI provider - so the whole API is
exercised without Redis, Postgres or an AI key.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
TEST_DATA = BASE_DIR / ".data" / "pytest"

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{BASE_DIR / '.data' / 'test.db'}")
os.environ.setdefault("TASK_MODE", "inline")
os.environ.setdefault("STORAGE_BACKEND", "local")
os.environ.setdefault("LOCAL_STORAGE_DIR", str(TEST_DATA / "files"))
os.environ.setdefault("AI_PROVIDER", "mock")
os.environ.setdefault("AUTO_CREATE_TABLES", "true")
os.environ.setdefault("COOKIE_SECURE", "false")

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_templates  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    shutil.rmtree(TEST_DATA, ignore_errors=True)
    TEST_DATA.mkdir(parents=True, exist_ok=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_templates(db)
    with TestClient(app) as test_client:
        yield test_client


def csrf_headers(client: TestClient) -> dict[str, str]:
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrfToken"]}


def register(
    client: TestClient,
    email: str = "ada@example.com",
    password: str = "correct-horse-battery",
    name: str = "Ada",
) -> dict:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": name},
        headers=csrf_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()
