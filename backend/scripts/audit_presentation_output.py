# -*- coding: utf-8 -*-
"""扫描 E2E payload 展示结果中的英文/裸 JSON 问题。"""
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
from apps.drama.presentation.presenters import present_artifact

SCHEMA_MAP = {
    role["default_output_artifact_key"]: role["output_contract"]["schema_version"]
    for role in DRAMA_ROLE_DEFAULTS
    if role.get("default_output_artifact_key")
}

EPISODE_RE = re.compile(r"\bEpisode\s+\d+", re.I)
RAW_DICT_RE = re.compile(r"^\s*\{'[a-zA-Z_]+'")
SNAKE_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def collect_strings(blocks: list, artifact: str, out: list[tuple[str, str, str]]) -> None:
    for block in blocks:
        block_type = block.get("type")
        for field in ("title", "subtitle", "text", "detail", "summary", "verdict"):
            val = block.get(field)
            if val:
                out.append((artifact, f"{block_type}.{field}", str(val)))
        if block_type == "kv":
            for row in block.get("rows") or []:
                out.append((artifact, "kv.key", str(row.get("key", ""))))
                out.append((artifact, "kv.value", str(row.get("value", ""))))
        elif block_type == "cards":
            for item in block.get("items") or []:
                for field in ("title", "subtitle", "body"):
                    if item.get(field):
                        out.append((artifact, f"cards.{field}", str(item[field])))
        elif block_type == "list":
            for item in block.get("items") or []:
                out.append((artifact, "list.item", str(item)))
        elif block_type == "metrics":
            for item in block.get("items") or []:
                out.append((artifact, "metrics.label", str(item.get("label", ""))))
        elif block_type == "score_board":
            for dim in block.get("dimensions") or []:
                out.append((artifact, "score.name", str(dim.get("name", ""))))
            if block.get("summary"):
                out.append((artifact, "score.summary", str(block["summary"])))


def main() -> None:
    issues: list[tuple[str, str, str, str]] = []
    for fixture in sorted((BACKEND_DIR / "scripts").glob("e2e_payloads_*.json")):
        payloads = json.loads(fixture.read_text(encoding="utf-8"))
        for artifact_key, payload in payloads.items():
            schema = SCHEMA_MAP.get(artifact_key)
            if not schema:
                continue
            strings: list[tuple[str, str, str]] = []
            view = present_artifact(artifact_key, schema, payload)
            collect_strings(view.get("blocks") or [], artifact_key, strings)
            if view.get("summary"):
                strings.append((artifact_key, "view.summary", str(view["summary"])))
            for art, kind, text in strings:
                if not text:
                    continue
                if EPISODE_RE.search(text):
                    issues.append((art, kind, "episode_en", text[:100]))
                if RAW_DICT_RE.match(text):
                    issues.append((art, kind, "raw_dict", text[:120]))
                if kind.endswith(".key") or kind.endswith(".label") or kind.endswith(".name"):
                    if SNAKE_KEY_RE.match(text.strip()) and text.strip() not in ("pass", "S"):
                        issues.append((art, kind, "snake_key", text))

    print("total issues:", len(issues))
    for cat, count in Counter(i[2] for i in issues).most_common():
        print(f"  {cat}: {count}")
    print("\n--- unique samples ---")
    seen: set[tuple[str, str, str]] = set()
    for art, kind, cat, text in issues:
        key = (art, cat, text[:70])
        if key in seen:
            continue
        seen.add(key)
        print(f"[{cat}] {art} / {kind}: {text}")
        if len(seen) >= 35:
            break


if __name__ == "__main__":
    main()
