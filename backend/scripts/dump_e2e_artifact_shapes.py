# -*- coding: utf-8 -*-
"""导出 Drama E2E 项目各产物真实 payload 结构，供 presenter 对齐。"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from typing import Any

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from apps.creation.models import ProjectFusionArtifact
from apps.drama.defaults import DRAMA_ROLE_DEFAULTS
from apps.drama.models import DramaProject
from apps.drama.presentation.normalize import normalize_payload


def _shape(value: Any, depth: int = 0, max_depth: int = 3) -> Any:
    if depth >= max_depth:
        if isinstance(value, dict):
            return {"__dict__": len(value)}
        if isinstance(value, list):
            return [f"__list[{len(value)}]__"]
        if isinstance(value, str):
            return value[:80] + ("…" if len(value) > 80 else "")
        return type(value).__name__

    if isinstance(value, dict):
        return {k: _shape(v, depth + 1, max_depth) for k, v in list(value.items())[:20]}
    if isinstance(value, list):
        if not value:
            return []
        sample = value[0]
        return [_shape(sample, depth + 1, max_depth), f"…共{len(value)}项"]
    if isinstance(value, str):
        return value[:120] + ("…" if len(value) > 120 else "")
    return value


def main() -> None:
    titles = sys.argv[1:] if len(sys.argv) > 1 else ["e2e-drama-expert", "e2e-drama-fast"]
    schema_by_key = {}
    for role in DRAMA_ROLE_DEFAULTS:
        key = role.get("default_output_artifact_key")
        schema = (role.get("output_contract") or {}).get("schema_version")
        if key:
            schema_by_key[key] = schema

    report: dict[str, Any] = {}
    for title in titles:
        dp = DramaProject.objects.filter(title=title).first()
        if not dp:
            print(f"skip: {title} not found")
            continue
        project_report = {}
        for artifact in ProjectFusionArtifact.objects.filter(project_id=dp.project_id).order_by("artifact_key"):
            body = normalize_payload(artifact.payload)
            project_report[artifact.artifact_key] = {
                "schema_version": schema_by_key.get(artifact.artifact_key),
                "top_keys": list(body.keys()) if isinstance(body, dict) else type(body).__name__,
                "shape": _shape(body),
            }
        report[title] = project_report

    out_path = os.path.join(os.path.dirname(__file__), "e2e_artifact_shapes.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"written: {out_path}")
    for title, arts in report.items():
        print(f"\n=== {title} ({len(arts)} artifacts) ===")
        for key, info in sorted(arts.items()):
            print(f"  {key} [{info['schema_version']}] keys={info['top_keys']}")


if __name__ == "__main__":
    main()
