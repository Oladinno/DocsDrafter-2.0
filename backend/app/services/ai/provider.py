"""Provider-neutral AI adapter.

The provider is chosen by environment variables only; keys never leave the
server. Every provider returns a ``dict`` which callers validate against a
typed Pydantic schema before anything is saved or rendered.
"""

from __future__ import annotations

import json
import re
from typing import Any, Protocol

import httpx

from app.config import settings

FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class AIError(RuntimeError):
    """Raised when the provider cannot return usable structured output."""


class AIProvider(Protocol):
    name: str

    def complete_json(
        self, *, system: str, user: str, schema: dict[str, Any]
    ) -> dict[str, Any]: ...


class OpenAICompatibleProvider:
    """Works with OpenAI, OpenRouter, Groq, Together, Ollama, vLLM, ..."""

    name = "openai-compatible"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        max_tokens: int = 4096,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:  # network / timeout
            raise AIError(f"AI provider request failed: {exc}") from exc
        if response.status_code >= 400:
            raise AIError(
                f"AI provider returned {response.status_code}: {response.text[:400]}"
            )
        return response.json()

    def complete_json(
        self, *, system: str, user: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        base: dict[str, Any] = {
            "model": self.model,
            "temperature": 0.4,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        # Preferred: explicit JSON schema output. Fall back to JSON mode for
        # endpoints that do not implement response_format.json_schema.
        payload = dict(base)
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "document_content",
                "strict": False,
                "schema": schema,
            },
        }
        try:
            data = self._post(payload)
        except AIError as exc:
            if "response_format" not in str(exc) and "400" not in str(exc):
                raise
            payload = dict(base)
            payload["response_format"] = {"type": "json_object"}
            payload["messages"] = [
                {
                    "role": "system",
                    "content": (
                        f"{system}\n\nRespond with a single JSON object only. "
                        "It must match this JSON schema:\n"
                        f"{json.dumps(schema)}"
                    ),
                },
                {"role": "user", "content": user},
            ]
            data = self._post(payload)

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIError(f"unexpected provider response shape: {data}") from exc
        return _loads_json(content)


def _loads_json(text: str) -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise AIError("model returned an empty response")
    candidate = text.strip()
    fence = FENCE_RE.search(candidate)
    if fence:
        candidate = fence.group(1).strip()
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start == -1 or end <= start:
            raise AIError(f"model did not return JSON: {candidate[:200]}")
        try:
            parsed = json.loads(candidate[start : end + 1])
        except json.JSONDecodeError as exc:
            raise AIError(f"model returned invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise AIError("model returned a non-object JSON value")
    return parsed


class MockProvider:
    """Deterministic provider for local development and tests (no API key)."""

    name = "mock"

    def __init__(self, *, model: str = "mock-1") -> None:
        self.model = model

    def complete_json(
        self, *, system: str, user: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        from app.services.ai.mock_payload import build_mock_payload

        return build_mock_payload(system=system, user=user)


def get_provider() -> AIProvider:
    if settings.ai_provider == "mock" or not settings.ai_api_key:
        return MockProvider()
    return OpenAICompatibleProvider(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        model=settings.ai_model,
        max_tokens=settings.ai_max_tokens,
        timeout=settings.ai_timeout_seconds,
    )
