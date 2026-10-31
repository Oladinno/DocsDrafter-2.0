"""AI generation tests (mock provider, structured-output validation)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.ai.operations import AIRequest, run_operation
from app.services.ai.provider import AIError
from app.services.content import parse_content
from tests.conftest import csrf_headers, register


def _generate(client: TestClient, **payload) -> dict:
    response = client.post(
        "/api/ai/generate",
        json=payload,
        headers=csrf_headers(client),
    )
    assert response.status_code == 202, response.text
    job = response.json()
    polled = client.get(f"/api/jobs/{job['id']}").json()
    return {**job, **polled}


def test_draft_generates_a_valid_document(client: TestClient) -> None:
    register(client)
    job = _generate(client, operation="draft", prompt="A memo about on-call rotations")
    assert job["status"] == "succeeded", job.get("error")
    content = job["result"]["content"]
    parsed = parse_content(content)  # must satisfy the typed schema
    assert parsed.content
    assert job["result"]["plainText"]
    assert job["result"]["provider"] == "mock"


def test_rewrite_returns_replacement_blocks(client: TestClient) -> None:
    register(client)
    job = _generate(
        client,
        operation="rewrite",
        selection="The system is kinda slow sometimes and users notice.",
        instructions="Make it professional",
    )
    assert job["status"] == "succeeded", job.get("error")
    text = job["result"]["plainText"].lower()
    assert "rewritten" in text or "system" in text
    assert "{{" not in text


def test_summarize_returns_bullets(client: TestClient) -> None:
    register(client)
    job = _generate(
        client,
        operation="summarize",
        selection=(
            "Revenue grew 12% this quarter. Churn increased slightly in the SMB "
            "segment. Enterprise renewals closed above forecast."
        ),
    )
    assert job["status"] == "succeeded", job.get("error")
    kinds = [b["type"] for b in job["result"]["blocks"]]
    assert kinds == ["bulletList"]


def test_ai_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/ai/generate",
        json={"operation": "draft", "prompt": "x"},
        headers=csrf_headers(client),
    )
    assert response.status_code == 401


def test_jobs_are_private_to_the_owner(client: TestClient) -> None:
    register(client, email="first@example.com")
    job = _generate(client, operation="draft", prompt="Private brief")
    client.post("/api/auth/logout", headers=csrf_headers(client))

    register(client, email="second@example.com")
    assert client.get(f"/api/jobs/{job['id']}").status_code == 404


class FlakyProvider:
    """Returns invalid output first, then a valid document."""

    name = "flaky"

    def __init__(self) -> None:
        self.calls = 0

    def complete_json(self, *, system: str, user: str, schema: dict) -> dict:
        self.calls += 1
        if self.calls == 1:
            return {"type": "doc", "content": [{"type": "paragraph", "text": "no content key"}]}
        return {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "repaired"}]}
            ],
        }


class AlwaysBadProvider:
    name = "always-bad"

    def complete_json(self, *, system: str, user: str, schema: dict) -> dict:
        return {"type": "not-a-doc", "content": "oops"}


def test_invalid_model_output_is_repaired_once() -> None:
    provider = FlakyProvider()
    result = run_operation(
        AIRequest(operation="draft", prompt="anything"), provider=provider
    )
    assert provider.calls == 2, "one repair round-trip should be issued"
    assert "repaired" in result["plainText"]


def test_output_fails_after_repairs_are_exhausted() -> None:
    with pytest.raises(AIError):
        run_operation(
            AIRequest(operation="draft", prompt="anything"),
            provider=AlwaysBadProvider(),
            max_repairs=1,
        )
