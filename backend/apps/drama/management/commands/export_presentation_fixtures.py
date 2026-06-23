# -*- coding: utf-8 -*-
"""从 DramaRoleExecution 导出 presentation fixture（每 schema 一份真实 JSON）。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from apps.drama.defaults import DRAMA_ROLE_DEFAULTS
from apps.drama.models import DramaRoleExecution

FIXTURE_DIR = Path(__file__).resolve().parents[4] / "scripts" / "fixtures" / "presentation"
OVERRIDE_DIR = FIXTURE_DIR / "overrides"


def _top_level_keys(payload: Any) -> list[str]:
    if isinstance(payload, dict):
        return sorted(str(k) for k in payload.keys())
    return []


class Command(BaseCommand):
    help = "导出 presentation fixtures 至 scripts/fixtures/presentation/"

    def add_arguments(self, parser):
        parser.add_argument(
            "--project-id",
            type=str,
            default="",
            help="限定 drama 项目 UUID；默认取全库最新成功执行",
        )

    def handle(self, *args, **options):
        FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
        OVERRIDE_DIR.mkdir(parents=True, exist_ok=True)

        schema_map: dict[str, dict[str, Any]] = {}
        for role in DRAMA_ROLE_DEFAULTS:
            artifact_key = role.get("default_output_artifact_key")
            schema_version = (role.get("output_contract") or {}).get("schema_version")
            agent_id = role.get("agent_id")
            if not artifact_key or not schema_version:
                continue
            if schema_version not in schema_map:
                schema_map[schema_version] = {
                    "artifact_key": artifact_key,
                    "agent_id": agent_id,
                    "role_name_zh": role.get("name_zh") or "",
                }

        exported = 0
        manifest_entries = []

        for schema_version, meta in sorted(schema_map.items()):
            artifact_key = meta["artifact_key"]
            payload = self._load_override(schema_version, artifact_key)
            source = "override"
            exec_row = None
            if payload is None:
                payload, exec_row = self._load_from_db(
                    artifact_key,
                    meta["agent_id"],
                    project_id=options.get("project_id") or "",
                )
                source = "database" if payload is not None else "missing"

            if payload is None:
                self.stdout.write(self.style.WARNING(f"SKIP {schema_version} ({artifact_key}): no data"))
                manifest_entries.append(
                    {
                        **meta,
                        "schema_version": schema_version,
                        "source": "missing",
                        "top_level_keys": [],
                    }
                )
                continue

            exec_id = exec_row if source == "database" else None
            out_path = FIXTURE_DIR / f"{schema_version}.json"
            out_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            exported += 1
            manifest_entries.append(
                {
                    **meta,
                    "schema_version": schema_version,
                    "source": source,
                    "top_level_keys": _top_level_keys(payload),
                    "execution_id": exec_id,
                }
            )
            self.stdout.write(self.style.SUCCESS(f"OK {schema_version} <- {source}"))

        manifest = {
            "fixture_count": exported,
            "schema_count": len(schema_map),
            "entries": manifest_entries,
        }
        (FIXTURE_DIR / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.stdout.write(self.style.SUCCESS(f"Exported {exported}/{len(schema_map)} fixtures"))

    def _load_override(self, schema_version: str, artifact_key: str) -> Any | None:
        for name in (f"{schema_version}.json", f"{artifact_key}.json"):
            path = OVERRIDE_DIR / name
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        return None

    def _load_from_db(
        self,
        artifact_key: str,
        agent_id: str,
        *,
        project_id: str,
    ) -> tuple[Any | None, str | None]:
        qs = DramaRoleExecution.objects.filter(status=DramaRoleExecution.Status.SUCCESS)
        if project_id:
            qs = qs.filter(drama_project_id=project_id)
        qs = qs.filter(agent_id=agent_id).order_by("-finished_at", "-created_at")
        for row in qs[:20]:
            artifacts = row.output_artifacts or {}
            payload = artifacts.get(artifact_key)
            if payload not in (None, {}, []):
                return payload, str(row.id)
        qs2 = DramaRoleExecution.objects.filter(status=DramaRoleExecution.Status.SUCCESS)
        if project_id:
            qs2 = qs2.filter(drama_project_id=project_id)
        qs2 = qs2.order_by("-finished_at", "-created_at")
        for row in qs2[:100]:
            payload = (row.output_artifacts or {}).get(artifact_key)
            if payload not in (None, {}, []):
                return payload, str(row.id)
        return None, None
