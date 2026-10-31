"""Deterministic structured output for the mock provider.

Used when no AI API key is configured (local development, CI). It returns the
same *shape* a real model would, so schema validation, the repair loop and the
renderers are all exercised without network access.
"""

from __future__ import annotations

import re
from typing import Any


def _paragraph(text: str) -> dict[str, Any]:
    # Never emit an empty text node - ProseMirror rejects it outright.
    if not text:
        return {"type": "paragraph", "content": []}
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


def _heading(text: str, level: int = 2) -> dict[str, Any]:
    if not text:
        return {"type": "heading", "attrs": {"level": level}, "content": []}
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}],
    }


def _bullets(items: list[str]) -> dict[str, Any]:
    return {
        "type": "bulletList",
        "content": [
            {"type": "listItem", "content": [_paragraph(item)]} for item in items
        ],
    }


def _field(user: str, label: str) -> str:
    match = re.search(rf"{label}:\s*(.+)", user, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _sentences(text: str, limit: int = 3) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()][:limit]


def build_mock_payload(*, system: str, user: str) -> dict[str, Any]:
    operation = "draft"
    match = re.search(r"Operation:\s*(\w+)", system)
    if match:
        operation = match.group(1)

    if operation == "draft":
        brief = _field(user, "Brief") or "your document"
        title_line = _field(user, "Working title")
        title = title_line or _title_from(brief)
        return {
            "type": "doc",
            "content": [
                _heading(title, 1),
                _paragraph(
                    f"This draft was generated for the following brief: {brief} "
                    "It opens with the core context a reader needs before the detail begins."
                ),
                _heading("Background", 2),
                _paragraph(
                    "The background section frames the problem, states who it affects, "
                    "and explains why it matters now."
                ),
                _heading("Key points", 2),
                _bullets(
                    [
                        "The primary requirement and the constraint it places on the work.",
                        "The measurable outcome the document is trying to achieve.",
                        "The next decision a reader is being asked to make.",
                    ]
                ),
                _heading("Recommendation", 2),
                _paragraph(
                    "Close with a concrete recommendation and the immediate next step, "
                    "so the document ends on an action rather than a summary."
                ),
            ],
        }

    if operation == "rewrite":
        selection = _field(user, "Selection") or user
        instructions = _field(user, "Instructions")
        suffix = f" ({instructions})" if instructions else ""
        sentences = _sentences(selection, 3) or [selection[:240]]
        return {
            "type": "doc",
            "content": [
                _paragraph(
                    "Rewritten: " + " ".join(sentences) + suffix
                )
            ],
        }

    if operation == "expand":
        selection = _field(user, "Selection") or user
        sentences = _sentences(selection, 2) or [selection[:160]]
        return {
            "type": "doc",
            "content": [
                _paragraph(
                    "Building on the point above: "
                    + (sentences[0] if sentences else "the idea")
                ),
                _paragraph(
                    "In practice this means the surrounding process, the people "
                    "affected, and the trade-offs involved are made explicit."
                ),
            ],
        }

    # summarize
    selection = _field(user, "Selection") or user
    sentences = _sentences(selection, 3)
    if not sentences:
        sentences = [selection[:200] or "Nothing to summarize."]
    return {
        "type": "doc",
        "content": [_bullets(sentences)],
    }


def _title_from(brief: str) -> str:
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", brief)[:7]
    if not words:
        return "Untitled draft"
    title = " ".join(words)
    return title[0].upper() + title[1:]
