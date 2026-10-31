import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app.services.content import parse_content, ContentError  # noqa: E402

OUT_PATH = os.path.join(ROOT, "template_import", "templates_import.json")

# The CSV lives at the repo root (parent of backend) in Downloads/templates_rows.csv.
# Use os.path.normpath/abspath so '..' resolves and the path is valid.
DEFAULT_CSV = os.environ.get("TEMPLATE_IMPORT_CSV", "C:/Users/DELL/Downloads/templates_rows.csv")
CSV_PATH = DEFAULT_CSV

cols = ["id", "name", "json_schema", "description", "created_at", "metadata"]
rows = []
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f, fieldnames=cols)
    header = next(reader)
    for raw in reader:
        rec = {}
        for k in cols:
            v = raw.get(k, "")
            if k == "json_schema":
                v = v.strip()
            elif k == "metadata":
                v = v.strip()
            elif k == "created_at":
                v = v.strip()
            rec[k] = v
        rows.append(rec)


def extract_text(block):
    texts = []
    if isinstance(block, dict):
        for node in block.get("content", []) or []:
            if isinstance(node, dict) and node.get("type") == "text":
                texts.append(node.get("text", ""))
    return "".join(texts)


def extract_heading_text(block):
    texts = []
    if isinstance(block, dict):
        for node in block.get("content", []) or []:
            if isinstance(node, dict) and node.get("type") == "text":
                texts.append(node.get("text", ""))
    return texts


def clean_blocks(blocks):
    """Return Tiptap-valid block JSON for a templateConfig.blocks list.

    Drops: table / list / signature blocks (rendered by dedicated UI).

    Empty text nodes are dropped because ProseMirror/Tiptap rejects them.
    """
    out = []
    for b in blocks:
        if not isinstance(b, dict):
            continue
        bt = b.get("type")
        if bt == "keyValueTable":
            for rb in (b.get("rows") or []):
                if isinstance(rb, dict) and "bind" in rb:
                    p = rb["bind"]["path"]
                    out.append({"type": "paragraph", "content": [{"type": "text", "text": "{{" + p + "}}", "marks": []}]})
            continue
        if bt in ("table", "list", "signature"):
            continue
        if bt == "heading":
            out.append({
                "type": "heading",
                "attrs": {"level": b.get("level", 2)},
                "content": [{"type": "text", "text": t, "marks": []} for t in extract_heading_text(b)],
            })
            continue
        if bt == "paragraph":
            text = extract_text(b)
            out.append({"type": "paragraph", "content": [{"type": "text", "text": text, "marks": []}]})
    return out


def _to_camel(snake):
    parts = snake.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def build_fields_from_schema(schema):
    """Rebuild TemplateField list from json_schema.

    The CSV stores snake_case JSON-Schema property keys; the backend stores
    camelCase 'key' on TemplateField.
    """
    props = schema.get("properties", {}) or {}
    required = set(schema.get("required", []) or [])
    fields = []
    for key, prop in props.items():
        kind = "number" if prop.get("type") == "number" else "string"
        fields.append({
            "key": _to_camel(key),
            "label": prop.get("title", key.replace("_", " ").title()),
            "kind": kind,
            "required": key in required,
            "placeholder": prop.get("default", ""),
            "default": prop.get("default", ""),
        })
    return fields


out = []
for r in rows:
    tc = json.loads(r["metadata"])["templateConfig"]
    blocks = tc["blocks"]
    schema = json.loads(r["json_schema"])
    structure = clean_blocks(blocks)
    fields = build_fields_from_schema(schema)
    out.append({
        "id": r["id"],
        "name": r["name"],
        "description": r["description"],
        "created_at": r["created_at"],
        "json_schema": r["json_schema"],
        "metadata": r["metadata"],
        "structure": structure,
        "fields": fields,
    })

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("wrote", len(out), "templates to", OUT_PATH)
for t in out:
    try:
        parse_content({"type": "doc", "content": t["structure"]})
        print("OK   ", t["name"], "| fields:", len(t["fields"]))
    except ContentError as e:
        print("FAIL ", t["name"], "-", e.msg)
