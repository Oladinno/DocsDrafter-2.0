"""Authentication, session and CSRF tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import csrf_headers, register


def test_register_sets_httponly_session_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "grace@example.com", "password": "secure-password", "name": "Grace"},
        headers=csrf_headers(client),
    )
    assert response.status_code == 201, response.text
    set_cookie = ";".join(response.headers.get_list("set-cookie")).lower()
    assert "dd_session=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "grace@example.com"


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    register(client, email="dup@example.com")
    response = client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "password": "secure-password"},
        headers=csrf_headers(client),
    )
    assert response.status_code == 409


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "short@example.com", "password": "short"},
        headers=csrf_headers(client),
    )
    assert response.status_code == 422


def test_login_logout_roundtrip(client: TestClient) -> None:
    register(client, email="login@example.com", password="trust-no-one")

    client.post("/api/auth/logout", headers=csrf_headers(client))
    assert client.get("/api/auth/me").status_code == 401

    bad = client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "wrong-password"},
        headers=csrf_headers(client),
    )
    assert bad.status_code == 401

    good = client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "trust-no-one"},
        headers=csrf_headers(client),
    )
    assert good.status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_state_changing_request_requires_csrf(client: TestClient) -> None:
    register(client)
    response = client.post("/api/documents", json={"title": "No token"})
    assert response.status_code == 403
    assert "CSRF" in response.json()["detail"]


def test_csrf_token_must_match_cookie(client: TestClient) -> None:
    register(client)
    response = client.post(
        "/api/documents",
        json={"title": "Forged"},
        headers={"X-CSRF-Token": "not-a-valid-token"},
    )
    assert response.status_code == 403


def test_unauthenticated_requests_are_rejected(client: TestClient) -> None:
    assert client.get("/api/documents").status_code == 401
    assert client.get("/api/templates").status_code == 401
