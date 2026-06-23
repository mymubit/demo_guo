# -*- coding: utf-8 -*-
"""审计展示层：裸 dict/list、未翻译 snake_case 键、疑似遗漏字段。"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from apps.drama.defaults import DRAMA_ROLE_DEFAULTS
from apps.drama.presentation.labels import FIELD_LABELS
from apps.drama.presentation.presenters import present_artifact

SCHEMA_MAP = {
    role["default_output_artifact_key"]: role["output_contract"]["schema_version"]
    for role in DRAMA_ROLE_DEFAULTS
    if role.get("default_output_artifact_key")
}

RAW_DICT_RE = re.compile(r"^\s*[\[{].*['\"][a-zA-Z_]+['\"]", re.S)
SNAKE_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def collect_output_strings(blocks: list) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for block in blocks:
        block_type = block.get("type")
        for field in ("title", "subtitle", "text", "detail", "summary", "verdict"):
            val = block.get(field)
            if val:
                out.append((block_type, f"{field}", str(val)))
        if block_type == "kv":
            for row in block.get("rows") or []:
                out.append(("kv", "key", str(row.get("key", ""))))
                out.append(("kv", "value", str(row.get("value", ""))))
        elif block_type == "list":
            for item in block.get("items") or []:
                out.append(("list", "item", str(item)))
        elif block_type == "cards":
            for item in block.get("items") or []:
                for field in ("title", "subtitle", "body"):
                    if item.get(field):
                        out.append(("cards", field, str(item[field])))
        elif block_type == "checks":
            for item in block.get("items") or []:
                out.append(("checks", "level", str(item.get("level", ""))))
                out.append(("checks", "detail", str(item.get("detail", ""))))
    return out


def main() -> None:
    issues: list[tuple[str, str, str, str]] = []
    for fixture in sorted((BACKEND_DIR / "scripts").glob("e2e_payloads_*.json")):
        payloads = json.loads(fixture.read_text(encoding="utf-8"))
        for artifact_key, payload in payloads.items():
            schema = SCHEMA_MAP.get(artifact_key)
            if not schema:
                continue
            view = present_artifact(artifact_key, schema, payload)
            for block_type, kind, text in collect_output_strings(view.get("blocks") or []):
                if not text.strip():
                    continue
                if RAW_DICT_RE.match(text):
                    issues.append((artifact_key, f"{block_type}.{kind}", "raw_dict", text[:120]))
                if kind in ("key", "level") and SNAKE_KEY_RE.match(text.strip()):
                    if text.strip() not in FIELD_LABELS and text.strip() not in ("pass", "s"):
                        issues.append((artifact_key, f"{block_type}.{kind}", "snake_key", text))

    print("total issues:", len(issues))
    for cat, count in Counter(i[2] for i in issues).most_common():
        print(f"  {cat}: {count}")
    print("\n--- samples ---")
    seen: set[tuple[str, str, str]] = set()
    for art, kind, cat, text in issues:
        sig = (art, cat, text[:70])
        if sig in seen:
            continue
        seen.add(sig)
        print(f"[{cat}] {art} / {kind}: {text}")
        if len(seen) >= 40:
            break


if __name__ == "__main__":
    main()
