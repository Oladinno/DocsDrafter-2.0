"""Content model and renderer tests."""

from __future__ import annotations

import pytest

from app.services.content import (
    ContentError,
    empty_doc,
    fill_placeholders,
    parse_content,
    plain_text,
    to_html,
    word_count,
)

SAMPLE = {
    "type": "doc",
    "content": [
        {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Intro"}]},
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Hello "},
                {"type": "text", "text": "world", "marks": [{"type": "bold"}]},
            ],
        },
        {
            "type": "bulletList",
            "content": [
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "one"}]}]}
            ],
        },
        {"type": "codeBlock", "attrs": {"language": "python"}, "content": [{"type": "text", "text": "print(1)"}]},
    ],
}


def test_valid_content_round_trips() -> None:
    parsed = parse_content(SAMPLE)
    dumped = parsed.model_dump(exclude_none=True)
    assert dumped["content"][0]["attrs"]["level"] == 2
    assert word_count(parsed) == 5
    assert "Hello world" in plain_text(parsed).replace("\n", " ")


def test_unknown_block_types_are_rejected() -> None:
    with pytest.raises(ContentError):
        parse_content({"type": "doc", "content": [{"type": "iframe"}]})


def test_text_without_a_content_array_is_rejected() -> None:
    with pytest.raises(ContentError):
        parse_content({"type": "doc", "content": [{"type": "paragraph", "content": "oops"}]})


def test_empty_payload_is_treated_as_empty_document() -> None:
    assert parse_content({}).content == []
    assert empty_doc().model_dump(exclude_none=True) == {
        "type": "doc",
        "content": [{"type": "paragraph", "content": []}],
    }


def test_fill_placeholders() -> None:
    doc = {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Dear {{name}}, welcome to {{company}}."}]}
        ],
    }
    filled = fill_placeholders(parse_content(doc), {"name": "Ada", "company": "Northwind"})
    assert plain_text(filled) == "Dear Ada, welcome to Northwind."


def test_empty_text_nodes_are_stripped() -> None:
    """ProseMirror rejects empty text nodes, so they never reach a document."""
    doc = {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": ""}]},
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Hi "},
                    {"type": "text", "text": ""},
                    {"type": "text", "text": "there"},
                ],
            },
            {"type": "heading", "attrs": {"level": 2}, "content": []},
        ],
    }
    parsed = parse_content(doc)
    dumped = parsed.model_dump(exclude_none=True)

    def empty_text_nodes(node):
        hits = []
        if isinstance(node, dict):
            if node.get("type") == "text" and not node.get("text"):
                hits.append(node)
            for value in node.values():
                hits.extend(empty_text_nodes(value))
        elif isinstance(node, list):
            for item in node:
                hits.extend(empty_text_nodes(item))
        return hits

    assert empty_text_nodes(dumped) == []
    assert [t["text"] for t in dumped["content"][1]["content"]] == ["Hi ", "there"]
    assert plain_text(parsed).strip() == "Hi there"
    assert word_count(parsed) == 2


def test_empty_placeholder_value_drops_the_text_node() -> None:
    doc = {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "{{name}}"}]}],
    }
    filled = fill_placeholders(parse_content(doc), {"name": ""})
    dumped = filled.model_dump(exclude_none=True)
    assert dumped["content"][0]["content"] == []
    assert plain_text(filled) == ""


def test_html_escapes_unsafe_input() -> None:
    doc = parse_content(
        {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "<script>alert(1)</script>"}]}
            ],
        }
    )
    html = to_html(doc, title="T")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "<strong>" in to_html(parse_content(SAMPLE), title="T")
