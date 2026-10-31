"""AI operations: draft, rewrite, expand, summarize.

Structured model output is validated against :class:`AIDocContent` before it is
returned to a caller or written to a document; one repair round-trip is issued
when validation fails.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.services.ai.provider import AIError, AIProvider, get_provider
from app.services.content import (
    AIDocContent,
    ContentError,
    DocContent,
    plain_text,
    parse_ai_content,
    parse_content,
)

Operation = Literal["draft", "rewrite", "expand", "summarize"]

OPERATIONS: tuple[Operation, ...] = ("draft", "rewrite", "expand", "summarize")

BASE_RULES = (
    "You are the writing engine of a document editor. Return ONLY a JSON object "
    'of the form {"type":"doc","content":[...]} using these block types: '
    "paragraph, heading (attrs.level 1-6), bulletList, orderedList. "
    "List items must contain paragraph blocks. Plain text only inside blocks - "
    "no markdown syntax, no HTML, no commentary outside the JSON. "
    "Never emit an empty document."
)

PROMPTS: dict[Operation, str] = {
    "draft": (
        "Draft a complete, well-structured document for the request below. "
        "Start with an optional heading only if the document calls for one, then "
        "use clear sections: short paragraphs, and lists where they genuinely help. "
        "Be specific and concrete rather than generic filler."
    ),
    "rewrite": (
        "Rewrite the selection below. Keep its meaning, improve clarity, flow and "
        "precision, and follow any instruction given. Return only the rewritten "
        "blocks - no preamble, no heading unless the original had one."
    ),
    "expand": (
        "Expand the selection below with additional useful detail, examples or "
        "follow-on reasoning, following any instruction given. Return only the new "
        "blocks that should be added, continuing the tone of the selection."
    ),
    "summarize": (
        "Summarize the selection below. Lead with the key point, use short "
        "paragraphs or a bullet list, and keep it substantially shorter than the "
        "source. Return only the summary blocks."
    ),
}


class AIRequest(BaseModel):
    operation: Operation
    prompt: str = Field(default="", max_length=8000)
    selection: str = Field(default="", max_length=20000)
    instructions: str = Field(default="", max_length=2000)
    title: str = Field(default="", max_length=255)
    surrounding: str = Field(default="", max_length=6000)


def available_operations() -> list[dict[str, str]]:
    return [
        {"id": "draft", "label": "Draft document", "hint": "Generate a full draft from a brief"},
        {"id": "rewrite", "label": "Rewrite", "hint": "Rewrite the selected text"},
        {"id": "expand", "label": "Expand", "hint": "Add detail to the selected text"},
        {"id": "summarize", "label": "Summarize", "hint": "Condense the selected text"},
    ]


def _user_message(req: AIRequest) -> str:
    parts: list[str] = []
    if req.operation == "draft":
        parts.append(f"Brief:\n{req.prompt.strip() or 'A general document'}")
        if req.title:
            parts.append(f"Working title: {req.title}")
        if req.surrounding:
            parts.append(f"Existing content to build on:\n{req.surrounding}")
    else:
        if req.selection:
            parts.append(f"Selection:\n{req.selection}")
        if req.prompt:
            parts.append(f"Request:\n{req.prompt}")
        if req.instructions:
            parts.append(f"Instructions:\n{req.instructions}")
        if req.title:
            parts.append(f"Document title: {req.title}")
    return "\n\n".join(parts) or "Nothing supplied."


def _schema() -> dict[str, Any]:
    return AIDocContent.model_json_schema()


def run_operation(
    req: AIRequest, *, provider: AIProvider | None = None, max_repairs: int = 1
) -> dict[str, Any]:
    """Call the provider and return ``{"content": <doc json>, "blocks": [...]}``."""
    provider = provider or get_provider()
    system = (
        f"{BASE_RULES}\n\nOperation: {req.operation}\n\n{PROMPTS[req.operation]}"
    )
    user = _user_message(req)
    schema = _schema()

    last_error: Exception | None = None
    for attempt in range(max_repairs + 1):
        try:
            raw = provider.complete_json(system=system, user=user, schema=schema)
        except AIError as exc:
            last_error = exc
            continue
        try:
            parsed = parse_ai_content(raw)
        except ContentError as exc:
            last_error = exc
            user = (
                f"{_user_message(req)}\n\nYour previous answer was rejected: {exc}. "
                "Return a corrected JSON object only."
            )
            continue
        if not parsed.content:
            last_error = AIError("model returned an empty document")
            user = (
                f"{_user_message(req)}\n\nYour previous answer had an empty "
                "content array. Return a corrected JSON object only."
            )
            continue
        doc = DocContent(content=parsed.content)
        if not plain_text(doc).strip():
            last_error = AIError("model returned a document with no text")
            user = (
                f"{_user_message(req)}\n\nYour previous answer contained no "
                "visible text. Return a corrected JSON object only."
            )
            continue
        return {
            "content": doc.model_dump(exclude_none=True),
            "blocks": [b.model_dump(exclude_none=True) for b in doc.content],
            "provider": provider.name,
            "plainText": plain_text(doc),
        }

    raise AIError(str(last_error) if last_error else "AI generation failed")


def parse_structured(data: Any) -> DocContent:
    """Validate already-known JSON (e.g. saved drafts) into typed content."""
    return parse_content(data)
