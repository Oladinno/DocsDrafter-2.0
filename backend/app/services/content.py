"""Typed document content model and renderers.

Documents store a Tiptap/ProseMirror-style block JSON structure. Every payload
coming from a client or from an AI provider is validated against these Pydantic
models *before* it is saved or rendered, so malformed model output can never
corrupt a document.
"""

from __future__ import annotations

import html as html_lib
import re
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError

ALLOWED_MARKS = {"bold", "italic", "strike", "code", "link"}
PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


class Mark(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    attrs: dict[str, Any] = Field(default_factory=dict)


class TextNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["text"]
    text: str
    marks: list[Mark] = Field(default_factory=list)


class HardBreakNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["hardBreak"]
    marks: list[Mark] = Field(default_factory=list)


Inline = Annotated[Union[TextNode, HardBreakNode], Field(discriminator="type")]


class ParagraphNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["paragraph"]
    content: list[Inline] = Field(default_factory=list)


class HeadingNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["heading"]
    attrs: dict[str, Any] = Field(default_factory=dict)
    content: list[Inline] = Field(default_factory=list)

    @property
    def level(self) -> int:
        try:
            level = int(self.attrs.get("level", 1))
        except (TypeError, ValueError):
            level = 1
        return min(max(level, 1), 6)


class ListItemNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["listItem"]
    content: list["Block"] = Field(default_factory=list)


class BulletListNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["bulletList"]
    content: list[ListItemNode] = Field(default_factory=list)


class OrderedListNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["orderedList"]
    attrs: dict[str, Any] = Field(default_factory=dict)
    content: list[ListItemNode] = Field(default_factory=list)


class BlockquoteNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["blockquote"]
    content: list["Block"] = Field(default_factory=list)


class CodeBlockNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["codeBlock"]
    attrs: dict[str, Any] = Field(default_factory=dict)
    content: list[Inline] = Field(default_factory=list)

    @property
    def language(self) -> str:
        return str(self.attrs.get("language") or "text")


class HorizontalRuleNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["horizontalRule"]


Block = Annotated[
    Union[
        ParagraphNode,
        HeadingNode,
        BulletListNode,
        OrderedListNode,
        BlockquoteNode,
        CodeBlockNode,
        HorizontalRuleNode,
    ],
    Field(discriminator="type"),
]

# Blocks an AI provider is allowed to emit (validated against a JSON schema).
AIBlock = Annotated[
    Union[ParagraphNode, HeadingNode, BulletListNode, OrderedListNode],
    Field(discriminator="type"),
]


class DocContent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["doc"] = "doc"
    content: list[Block] = Field(default_factory=list)


class AIDocContent(BaseModel):
    """Typed schema handed to the model provider as a JSON schema."""

    model_config = ConfigDict(extra="ignore")

    type: Literal["doc"] = "doc"
    content: list[AIBlock] = Field(default_factory=list)


# Resolve the recursive references now that every node type exists.
for _model in (
    ListItemNode,
    BlockquoteNode,
    ParagraphNode,
    HeadingNode,
    BulletListNode,
    OrderedListNode,
    BlockquoteNode,
    CodeBlockNode,
    HorizontalRuleNode,
    DocContent,
    AIDocContent,
):
    _model.model_rebuild()


class ContentError(ValueError):
    pass


def _strip_empty_text(data: Any) -> Any:
    """Drop empty text nodes and now-empty containers.

    ProseMirror (and therefore Tiptap) rejects ``{"type": "text", "text": ""}``
    with "Empty text nodes are not allowed", which surfaces as a hard failure
    when the editor loads a document. AI output and ``{{placeholder}}`` filling
    can both produce them, so every payload is normalised before validation.
    """
    if isinstance(data, list):
        return [x for x in (_strip_empty_text(i) for i in data) if x is not None]
    if not isinstance(data, dict):
        return data
    if data.get("type") == "text" and not str(data.get("text") or ""):
        return None
    out: dict[str, Any] = {}
    for key, value in data.items():
        cleaned = _strip_empty_text(value)
        if key == "content":
            cleaned = [c for c in cleaned if c is not None] if isinstance(cleaned, list) else cleaned
            if isinstance(cleaned, list) and not cleaned:
                continue
        if cleaned is not None:
            out[key] = cleaned
    return out


def parse_content(data: Any) -> DocContent:
    if isinstance(data, str):
        raise ContentError("content must be an object")
    if not isinstance(data, dict):
        raise ContentError("content must be an object")
    if not data:
        return DocContent(content=[])
    data = _strip_empty_text(data) or {}
    if not data:
        return DocContent(content=[])
    try:
        return DocContent.model_validate(data)
    except ValidationError as exc:  # pragma: no cover - covered via API 422
        raise ContentError(_friendly(exc)) from exc


def parse_ai_content(data: Any) -> DocContent:
    """Validate provider output, then widen it to a full document."""
    if not isinstance(data, dict):
        raise ContentError("model output must be an object")
    data = _strip_empty_text(data) or {}
    try:
        parsed = AIDocContent.model_validate(data)
    except ValidationError as exc:
        raise ContentError(_friendly(exc)) from exc
    return DocContent(content=[block for block in parsed.content])


def _friendly(exc: ValidationError) -> str:
    issues = "; ".join(
        f"{'.'.join(str(p) for p in err['loc']) or 'content'}: {err['msg']}"
        for err in exc.errors()[:5]
    )
    return f"invalid document content: {issues}"


# --- helpers ---------------------------------------------------------------


def text_of(node: Any) -> str:
    if isinstance(node, (ParagraphNode, HeadingNode)):
        return "".join(_inline_text(i) for i in node.content)
    if isinstance(node, CodeBlockNode):
        return "".join(_inline_text(i) for i in node.content)
    if isinstance(node, (BulletListNode, OrderedListNode)):
        return "\n".join(
            " ".join(text_of(inner) for inner in item.content if not isinstance(inner, list))
            for item in node.content
        )
    if isinstance(node, BlockquoteNode):
        return "\n".join(text_of(inner) for inner in node.content if not isinstance(inner, list))
    if isinstance(node, ListItemNode):
        return " ".join(text_of(inner) for inner in node.content if not isinstance(inner, list))
    return ""


def _inline_text(node: Inline) -> str:
    if isinstance(node, HardBreakNode):
        return "\n"
    return node.text


def walk_blocks(blocks: list[Any]):
    for block in blocks:
        yield block
        if isinstance(block, (BlockquoteNode,)):
            yield from walk_blocks([b for b in block.content if not isinstance(b, list)])
        if isinstance(block, ListItemNode):
            yield from walk_blocks([b for b in block.content if not isinstance(b, list)])


def plain_text(content: DocContent) -> str:
    parts: list[str] = []
    for block in walk_blocks(content.content):
        if isinstance(block, (ParagraphNode, HeadingNode, CodeBlockNode)):
            parts.append(text_of(block))
        elif isinstance(block, (BulletListNode, OrderedListNode)):
            for item in block.content:
                for inner in item.content:
                    if isinstance(inner, (ParagraphNode, HeadingNode)):
                        parts.append(text_of(inner))
        elif isinstance(block, HorizontalRuleNode):
            parts.append("")
    return "\n".join(parts)


def word_count(content: DocContent) -> int:
    text = plain_text(content)
    return len([w for w in re.split(r"\s+", text) if w.strip()])


def fill_placeholders(content: DocContent, values: dict[str, Any]) -> DocContent:
    """Replace ``{{key}}`` markers with user-supplied values."""

    def fill_inline(nodes: list[Inline]) -> list[Inline]:
        filled: list[Inline] = []
        for node in nodes:
            if isinstance(node, HardBreakNode):
                filled.append(node)
                continue
            new_text = PLACEHOLDER_RE.sub(
                lambda m: str(values.get(m.group(1), "")), node.text
            )
            if not new_text:
                continue
            filled.append(node.model_copy(update={"text": new_text}))
        return filled

    def fill_block(block: Block) -> Block:
        if isinstance(block, (ParagraphNode, HeadingNode, CodeBlockNode)):
            return block.model_copy(update={"content": fill_inline(block.content)})
        if isinstance(block, (BulletListNode, OrderedListNode)):
            items = []
            for item in block.content:
                inner = [fill_block(b) for b in item.content if not isinstance(b, list)]
                items.append(item.model_copy(update={"content": inner}))
            return block.model_copy(update={"content": items})
        if isinstance(block, BlockquoteNode):
            inner = [fill_block(b) for b in block.content if not isinstance(b, list)]
            return block.model_copy(update={"content": inner})
        return block

    return DocContent(content=[fill_block(b) for b in content.content])


def empty_doc() -> DocContent:
    return DocContent(content=[ParagraphNode(type="paragraph")])


# --- HTML rendering (PDF path) ---------------------------------------------

MARK_OPEN = {
    "bold": "<strong>",
    "italic": "<em>",
    "strike": "<s>",
    "code": "<code>",
}
MARK_CLOSE = {
    "bold": "</strong>",
    "italic": "</em>",
    "strike": "</s>",
    "code": "</code>",
}


def _render_inline(nodes: list[Inline]) -> str:
    out: list[str] = []
    for node in nodes:
        if isinstance(node, HardBreakNode):
            out.append("<br/>")
            continue
        chunk = html_lib.escape(node.text)
        for mark in node.marks:
            if mark.type == "link":
                href = html_lib.escape(str(mark.attrs.get("href", "")), quote=True)
                chunk = f'<a href="{href}">{chunk}</a>'
            elif mark.type in MARK_OPEN:
                chunk = f"{MARK_OPEN[mark.type]}{chunk}{MARK_CLOSE[mark.type]}"
        out.append(chunk)
    return "".join(out)


def _block_html(block: Block, depth: int = 0) -> str:
    if isinstance(block, ParagraphNode):
        inner = _render_inline(block.content) or "<br/>"
        return f"<p>{inner}</p>"
    if isinstance(block, HeadingNode):
        level = block.level
        return f"<h{level}>{_render_inline(block.content)}</h{level}>"
    if isinstance(block, CodeBlockNode):
        body = html_lib.escape(text_of(block))
        return f'<pre class="code" data-lang="{html_lib.escape(block.language)}"><code>{body}</code></pre>'
    if isinstance(block, HorizontalRuleNode):
        return "<hr/>"
    if isinstance(block, BlockquoteNode):
        inner = "".join(
            _block_html(b, depth) for b in block.content if not isinstance(b, list)
        )
        return f"<blockquote>{inner}</blockquote>"
    if isinstance(block, BulletListNode):
        inner = "".join(
            f"<li>{''.join(_block_html(b, depth + 1) for b in item.content if not isinstance(b, list))}</li>"
            for item in block.content
        )
        return f"<ul>{inner}</ul>"
    if isinstance(block, OrderedListNode):
        start = block.attrs.get("start", 1)
        inner = "".join(
            f"<li>{''.join(_block_html(b, depth + 1) for b in item.content if not isinstance(b, list))}</li>"
            for item in block.content
        )
        return f'<ol start="{html_lib.escape(str(start))}">{inner}</ol>'
    return ""


DOCUMENT_CSS = """
  @page { size: A4; margin: 20mm 18mm; }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    font-family: Inter, "Segoe UI", -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif;
    font-size: 11.5pt; line-height: 1.62; color: #171923;
    -webkit-font-smoothing: antialiased;
  }
  h1, h2, h3, h4, h5, h6 {
    font-family: Geist, "Segoe UI", Helvetica, Arial, sans-serif;
    font-weight: 600; letter-spacing: -0.012em; line-height: 1.3;
    margin: 1.4em 0 0.5em; color: #171923;
  }
  h1 { font-size: 24pt; margin-top: 0; }
  h2 { font-size: 17pt; }
  h3 { font-size: 13.5pt; }
  h4, h5, h6 { font-size: 12pt; }
  p { margin: 0 0 0.85em; }
  ul, ol { margin: 0 0 0.9em; padding-left: 1.4em; }
  li { margin-bottom: 0.3em; }
  blockquote {
    margin: 1em 0; padding: 0.2em 0 0.2em 1em;
    border-left: 3px solid #5145cd; color: #474554; font-style: italic;
  }
  code { font-family: "JetBrains Mono", Consolas, "Courier New", monospace; font-size: 0.92em; }
  pre.code {
    background: #f3f2ff; border: 1px solid #e6e8ef; border-radius: 6px;
    padding: 10px 12px; overflow: hidden; white-space: pre-wrap;
    font-family: "JetBrains Mono", Consolas, "Courier New", monospace; font-size: 9.5pt;
    line-height: 1.5; margin: 0 0 1em;
  }
  hr { border: none; border-top: 1px solid #e6e8ef; margin: 1.4em 0; }
  a { color: #5145cd; text-decoration: none; }
  .doc-title { font-size: 26pt; letter-spacing: -0.02em; margin: 0 0 0.4em; }
  .doc-meta { color: #98a2b3; font-size: 9.5pt; margin-bottom: 1.6em;
    border-bottom: 1px solid #e6e8ef; padding-bottom: 1em; }
"""


def to_html(
    content: DocContent,
    *,
    title: str = "Document",
    meta: str | None = None,
    include_document_title: bool = False,
) -> str:
    body = "".join(_block_html(block) for block in content.content) or "<p></p>"
    title_html = ""
    meta_html = ""
    if include_document_title:
        title_html = f'<h1 class="doc-title">{html_lib.escape(title)}</h1>'
        if meta:
            meta_html = f'<div class="doc-meta">{html_lib.escape(meta)}</div>'
    return (
        "<!DOCTYPE html><html><head>"
        '<meta charset="utf-8"/>'
        f"<title>{html_lib.escape(title)}</title>"
        f"<style>{DOCUMENT_CSS}</style>"
        "</head><body>"
        f"{title_html}{meta_html}"
        f'<article class="document">{body}</article>'
        "</body></html>"
    )
