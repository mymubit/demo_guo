# -*- coding: utf-8 -*-
"""对比展示层假设字段 vs E2E 真实 payload 字段。"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from apps.drama.presentation.labels import FIELD_LABELS

PRESENTER_FILES = [
    BACKEND_DIR / "apps/drama/presentation/base.py",
    BACKEND_DIR / "apps/drama/presentation/schema_presenters.py",
    BACKEND_DIR / "apps/drama/presentation/blocks_builder.py",
    BACKEND_DIR / "apps/drama/presentation/text_localize.py",
]


def all_payload_keys(obj) -> set[str]:
    keys: set[str] = set()
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key.startswith("_"):
                continue
            keys.add(key)
            keys |= all_payload_keys(val)
    elif isinstance(obj, list):
        for item in obj[:5]:
            keys |= all_payload_keys(item)
    return keys


def collect_assumed_keys() -> set[str]:
    code = "\n".join(path.read_text(encoding="utf-8") for path in PRESENTER_FILES)
    keys = set(re.findall(r"""\.get\(['"]([a-zA-Z_]+)['"]""", code))
    keys |= set(re.findall(r"""body\.get\(['"]([a-zA-Z_]+)['"]""", code))
    keys |= set(re.findall(r"""item\.get\(['"]([a-zA-Z_]+)['"]""", code))
    keys |= set(re.findall(r"""char\.get\(['"]([a-zA-Z_]+)['"]""", code))
    keys |= set(re.findall(r"""space\.get\(['"]([a-zA-Z_]+)['"]""", code))
    from apps.drama.presentation.base import CHARACTER_PROFILE_FIELD_GROUPS, CHARACTER_ROLE_KEYS

    for group in CHARACTER_PROFILE_FIELD_GROUPS:
        keys.update(group)
    keys.update(CHARACTER_ROLE_KEYS)
    keys.update(
        {
            "main_characters",
            "core_supporting_characters",
            "relationship_map",
            "relationship_network",
            "surface_desire",
            "character_flaw",
            "core_fear",
            "voice_tag",
            "initial",
            "final",
        }
    )
    return {k for k in keys if k.islower() or "_" in k}


def main() -> None:
    real: set[str] = set()
    by_artifact: dict[str, set[str]] = {}
    for fixture in sorted((BACKEND_DIR / "scripts").glob("e2e_payloads_*.json")):
        payloads = json.loads(fixture.read_text(encoding="utf-8"))
        for artifact_key, payload in payloads.items():
            keys = all_payload_keys(payload)
            real |= keys
            by_artifact.setdefault(artifact_key, set()).update(keys)

    assumed = collect_assumed_keys()
    never_in_e2e = sorted(k for k in assumed if k not in real)

    print("=== 展示层假设但 E2E 真实 payload 从未出现的字段 ===")
    for key in never_in_e2e:
        print(f"  {key}")

    print("\n=== 各产物真实顶层结构（E2E）===")
    for fp in sorted((BACKEND_DIR / "scripts").glob("e2e_payloads_*.json")):
        payloads = json.loads(fp.read_text(encoding="utf-8"))
        print(f"\n[{fp.name}]")
        for artifact_key, payload in sorted(payloads.items()):
            if isinstance(payload, dict):
                top = [k for k in payload if not k.startswith("_")]
                print(f"  {artifact_key}: {top}")

    print("\n=== character_bible 三种真实形态 ===")
    shapes = {
        "expert": {"characters", "relationship_network"},
        "fast": {"main_characters", "core_supporting_characters", "relationship_network"},
        "demo1(user)": {"characters", "relationship_network"},
    }
    for name, expected in shapes.items():
        print(f"  {name}: {sorted(expected)}")

    print("\n=== relationship 条目真实字段对比 ===")
    for fp in sorted((BACKEND_DIR / "scripts").glob("e2e_payloads_*.json")):
        payloads = json.loads(fp.read_text(encoding="utf-8"))
        cb = payloads.get("character_bible")
        if not cb:
            continue
        rel = cb.get("relationship_network") or []
        if rel:
            print(f"  {fp.name}: {sorted(rel[0].keys())}")

    char_keys: set[str] = set()
    for fp in (BACKEND_DIR / "scripts").glob("e2e_payloads_*.json"):
        cb = json.loads(fp.read_text(encoding="utf-8")).get("character_bible") or {}
        for group in ("characters", "main_characters", "core_supporting_characters"):
            for char in cb.get(group) or []:
                if isinstance(char, dict):
                    char_keys |= set(char.keys())

    print("\n=== 人物条目真实字段并集（E2E）===")
    print(" ", sorted(char_keys))

    print("\n=== 展示层 CHARACTER 字段组 vs 真实 ===")
    from apps.drama.presentation.base import CHARACTER_PROFILE_FIELD_GROUPS

    profile_aliases = {a for group in CHARACTER_PROFILE_FIELD_GROUPS for a in group}
    unused_aliases = sorted(a for a in profile_aliases if a not in char_keys)
    missing_real = sorted(k for k in char_keys if k not in profile_aliases and k not in {
        "name", "character_id", "role_position", "role_type", "identity",
    })
    print("  别名组里 E2E 未出现的:", unused_aliases)
    print("  真实有但展示未专门处理的:", missing_real)


if __name__ == "__main__":
    main()
