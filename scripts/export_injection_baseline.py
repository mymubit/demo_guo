#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出脱敏 injection 基线 JSON 到 docs/superpowers/baselines/。

在 Django 环境运行（backend 容器工作目录通常为 /app）：
  python scripts/export_injection_baseline.py
  python scripts/export_injection_baseline.py --agent drama.story-bible
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "drama-skills").is_dir() and (parent / "backend").is_dir():
            return parent
        if (parent / "manage.py").is_file() and (parent.parent / "drama-skills").is_dir():
            return parent.parent
    return here.parents[1]


def _minimal_settings() -> dict:
    return {
        "title": "baseline-export",
        "entry_type": "original_track",
        "core_idea": "基线导出用短梗概，禁止含真实用户隐私",
        "genre_matrix": {
            "emotion": "revenge",
            "identity": "reborn",
            "conflict": "family",
            "world": "modern",
            "audience_channel": "female",
        },
        "episode_count": 30,
        "creation_preferences": {
            "batch_episode_max": 5,
            "outline_mode": "full",
            "scoring_preset": "standard",
            "compliance_check_mode": "standard",
            "enable_delivery": False,
        },
    }


def _slim_manifest(manifest: dict, bundle_version: str) -> dict:
    knowledge_included = (manifest.get("knowledge") or {}).get("included") or []
    slim_knowledge = []
    for item in knowledge_included:
        if isinstance(item, dict):
            slim_knowledge.append(
                {
                    "path": item.get("path"),
                    "chars": item.get("chars"),
                }
            )
        if len(slim_knowledge) >= 20:
            break
    return {
        "agent_id": manifest.get("agent_id"),
        "bundle_version": manifest.get("bundle_version") or bundle_version,
        "system_chars": manifest.get("system_chars"),
        "user_chars": manifest.get("user_chars"),
        "checksum": manifest.get("checksum"),
        "layers": manifest.get("layers"),
        "modules": {
            "included": (manifest.get("modules") or {}).get("included"),
            "skipped": (manifest.get("modules") or {}).get("skipped"),
        },
        "knowledge": {"included": slim_knowledge},
        "rules": {
            "sections_included": (manifest.get("rules") or {}).get("sections_included"),
            "truncated": (manifest.get("rules") or {}).get("truncated"),
        },
        "exported_on": date.today().isoformat(),
        "note": "desensitized baseline; no full prompts",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", default="drama.topic-director")
    parser.add_argument(
        "--out-dir",
        default="",
        help="默认 <repo>/docs/superpowers/baselines",
    )
    args = parser.parse_args()

    repo = _repo_root()
    backend = repo / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))

    import django
    from django.conf import settings as dj_settings

    if not dj_settings.configured:
        import os

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
        django.setup()

    from apps.drama.services.prompt_builder import PromptBuilder
    from apps.drama.services.skills_loader import get_skills_loader

    _system, _user, manifest = PromptBuilder().build(
        args.agent,
        settings=_minimal_settings(),
        workflow_state={},
        artifacts={},
    )
    loader = get_skills_loader()
    snap = _slim_manifest(manifest, str(getattr(loader, "bundle_version", "") or ""))

    out_dir = Path(args.out_dir) if args.out_dir else repo / "docs" / "superpowers" / "baselines"
    out_dir.mkdir(parents=True, exist_ok=True)
    short = args.agent.replace("drama.", "").replace(".", "-")
    out_path = out_dir / f"{date.today().isoformat()}-{short}.json"
    out_path.write_text(
        json.dumps(snap, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out_path} system_chars={snap.get('system_chars')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
