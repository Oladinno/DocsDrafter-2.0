"""Client log ingestion endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _post_log(client: TestClient, payload: dict):
    """POST through the same CSRF flow the browser uses."""
    csrf = client.get("/api/auth/csrf").json()["csrfToken"]
    return client.post(
        "/api/logs",
        json=payload,
        headers={"X-CSRF-Token": csrf},
    )


def test_client_log_accepted(client: TestClient) -> None:
    response = _post_log(
        client,
        {
            "message": "TypeError: x is not a function",
            "stack": "at foo (main.js:1:1)",
            "url": "https://app.example.com/documents/123",
            "userAgent": "test-agent",
        },
    )
    assert response.status_code == 204


def test_client_log_rejects_oversized_message(client: TestClient) -> None:
    response = _post_log(client, {"message": "x" * 5000})
    assert response.status_code == 422


def test_client_log_requires_csrf(client: TestClient) -> None:
    response = client.post("/api/logs", json={"message": "no token"})
    assert response.status_code == 403
