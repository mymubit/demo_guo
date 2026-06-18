# -*- coding: utf-8 -*-
"""Absorb external drama assets into ScriptForge DB/assets once.

External folders are migration sources only. Runtime code must not read them.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable

from django.core.management.base import BaseCommand, CommandError

from apps.skill.models import (
    AgentSkillDefinition,
    ReferenceLibraryConfig,
    SkillConfigEntry,
    SkillRuleConfig,
)
from apps.workflow.models import FusionJsonSchema


ASSET_ROOT = Path(__file__).resolve().parents[3] / "assets"
TEMPLATE_ROOT = ASSET_ROOT / "templates"
REFERENCE_CONFIG = "default"
MAIN_SKILLS = {
    "creation.brief",
    "creation.structure",
    "creation.character",
    "creation.outline",
    "creation.script",
    "creation.review",
    "creation.score",
    "creation.polish",
    "creation.marketing",
    "creation.insight",
}


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[6]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_key(path: Path) -> str:
    return path.stem.replace(".schema", "").replace("-", "_")


class Command(BaseCommand):
    help = "Absorb demo4book/ai-drama-skills-v2 assets into ScriptForge DB/assets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            action="append",
            choices=["demo4book", "ai-drama-skills-v2"],
            help="Source folder name. Repeatable. Defaults to both.",
        )
        parser.add_argument("--write", action="store_true", help="Write changes. Without this it is a dry-run.")
        parser.add_argument("--overwrite", action="store_true", help="Overwrite existing DB rows/assets.")

    def handle(self, *args, **options):
        sources = options.get("source") or ["demo4book", "ai-drama-skills-v2"]
        write = bool(options.get("write"))
        overwrite = bool(options.get("overwrite"))
        workspace = _workspace_root()
        roots = self._resolve_sources(workspace, sources)

        report = {
            "schemas": 0,
            "references": 0,
            "rules": 0,
            "configs": 0,
            "templates": 0,
            "skills": 0,
            "skipped": 0,
            "errors": 0,
            "dry_run": not write,
        }
        for source, root in roots.items():
            self.stdout.write(f"{'[WRITE]' if write else '[DRY]'} absorbing {source}: {root}")
            self._absorb_source(source, root, write=write, overwrite=overwrite, report=report)
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))

    def _resolve_sources(self, workspace: Path, sources: Iterable[str]) -> Dict[str, Path]:
        roots: Dict[str, Path] = {}
        for source in sources:
            if source == "demo4book":
                root = workspace / "demo4book" / "short-drama-script-creator"
            else:
                root = workspace / "ai-drama-skills-v2"
            if not root.exists():
                raise CommandError(f"source not found: {root}")
            roots[source] = root
        return roots

    def _absorb_source(self, source: str, root: Path, *, write: bool, overwrite: bool, report: dict) -> None:
        if source == "demo4book":
            self._schemas(root / "schemas", write=write, overwrite=overwrite, report=report)
            self._references(root / "references", write=write, overwrite=overwrite, report=report)
            self._rules(root / "config" / "skill-rules", write=write, overwrite=overwrite, report=report)
            self._configs(root / "config", "demo4book", write=write, overwrite=overwrite, report=report)
            self._templates(root / "templates", "demo4book", write=write, overwrite=overwrite, report=report)
            self._skills(root, "demo4book", write=write, overwrite=overwrite, report=report)
        else:
            self._references(root / "drama-knowledge-base" / "config", write=write, overwrite=overwrite, report=report)
            self._rules(root / "config", write=write, overwrite=overwrite, report=report)
            self._configs(root / "config", "ai-drama-skills-v2", write=write, overwrite=overwrite, report=report)
            self._templates(root / "templates", "ai-drama-skills-v2", write=write, overwrite=overwrite, report=report)
            self._skills(root, "ai-drama-skills-v2", write=write, overwrite=overwrite, report=report)

    def _schemas(self, directory: Path, *, write: bool, overwrite: bool, report: dict) -> None:
        if not directory.is_dir():
            return
        for path in sorted(directory.glob("*.json")):
            try:
                data = _load_json(path)
                report["schemas"] += 1
                if write:
                    row, created = FusionJsonSchema.objects.get_or_create(
                        schema_key=_safe_key(path),
                        defaults={"filename": path.name, "schema_json": data},
                    )
                    if not created and overwrite:
                        row.filename = path.name
                        row.schema_json = data
                        row.save(update_fields=["filename", "schema_json", "updated_at"])
            except Exception as exc:  # noqa: BLE001
                report["errors"] += 1
                self.stderr.write(f"schema failed {path}: {exc}")

    def _references(self, directory: Path, *, write: bool, overwrite: bool, report: dict) -> None:
        if not directory.is_dir():
            return
        content: Dict[str, Any] = {}
        if write:
            row, _ = ReferenceLibraryConfig.objects.get_or_create(
                config_key=REFERENCE_CONFIG,
                defaults={"content": {}},
            )
            content = dict(row.content or {})
        else:
            row = None
        for path in sorted(directory.glob("*.json")):
            try:
                data = _load_json(path)
                report["references"] += 1
                if write and (overwrite or path.name not in content):
                    content[path.name] = data
            except Exception as exc:  # noqa: BLE001
                report["errors"] += 1
                self.stderr.write(f"reference failed {path}: {exc}")
        if write and row is not None:
            row.content = content
            row.save(update_fields=["content", "updated_at"])

    def _rules(self, directory: Path, *, write: bool, overwrite: bool, report: dict) -> None:
        if not directory.is_dir():
            return
        for path in sorted(directory.glob("*.json")):
            try:
                data = _load_json(path)
                report["rules"] += 1
                if not write:
                    continue
                tier = self._infer_tier(path.name)
                section = path.stem[:64]
                defaults = {
                    "content": data if isinstance(data, dict) else {"value": data},
                    "version_tag": str((data or {}).get("version") if isinstance(data, dict) else "v1.0.0")[:32],
                    "status": SkillRuleConfig.STATUS_ACTIVE,
                    "source": SkillRuleConfig.SOURCE_FILE,
                    "note": f"absorbed:{path.as_posix()}",
                }
                row, created = SkillRuleConfig.objects.get_or_create(
                    tier=tier,
                    scope_type=SkillRuleConfig.SCOPE_GLOBAL,
                    scope_key="",
                    section=section,
                    status=SkillRuleConfig.STATUS_ACTIVE,
                    defaults=defaults,
                )
                if not created and overwrite:
                    for key, value in defaults.items():
                        setattr(row, key, value)
                    row.save(update_fields=[*defaults.keys(), "updated_at"])
            except Exception as exc:  # noqa: BLE001
                report["errors"] += 1
                self.stderr.write(f"rule failed {path}: {exc}")

    def _configs(self, directory: Path, edition: str, *, write: bool, overwrite: bool, report: dict) -> None:
        if not directory.is_dir():
            return
        for path in sorted(directory.glob("*.json")):
            if "skill-rules" in path.name:
                continue
            try:
                data = _load_json(path)
                report["configs"] += 1
                if write:
                    obj, created = SkillConfigEntry.objects.get_or_create(
                        config_key=path.stem,
                        defaults={"edition": edition, "version": str((data or {}).get("version", "1.0.0")), "content": data},
                    )
                    if not created and overwrite:
                        obj.edition = edition
                        obj.version = str((data or {}).get("version", "1.0.0"))
                        obj.content = data
                        obj.save(update_fields=["edition", "version", "content", "updated_at"])
            except Exception as exc:  # noqa: BLE001
                report["errors"] += 1
                self.stderr.write(f"config failed {path}: {exc}")

    def _templates(self, directory: Path, source: str, *, write: bool, overwrite: bool, report: dict) -> None:
        if not directory.is_dir():
            return
        for path in sorted(directory.glob("*.md")):
            report["templates"] += 1
            if not write:
                continue
            dest = TEMPLATE_ROOT / source / path.name
            if dest.exists() and not overwrite:
                report["skipped"] += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)

    def _skills(self, root: Path, source: str, *, write: bool, overwrite: bool, report: dict) -> None:
        for path in sorted(root.rglob("SKILL.md")):
            skill_id = self._skill_id_for(path)
            if skill_id not in MAIN_SKILLS:
                report["skipped"] += 1
                continue
            content = path.read_text(encoding="utf-8")
            report["skills"] += 1
            if not write:
                continue
            obj, created = AgentSkillDefinition.objects.get_or_create(
                skill_id=skill_id,
                defaults={
                    "name": skill_id,
                    "version": "1.0.0",
                    "category": self._skill_category(skill_id),
                    "content": content,
                    "system_hint": content[:12000],
                    "source_file": f"{source}/{path.relative_to(root).as_posix()}",
                    "lifecycle_status": AgentSkillDefinition.LIFECYCLE_ACTIVE,
                    "is_active": True,
                },
            )
            if not created and overwrite:
                obj.content = content
                obj.system_hint = content[:12000]
                obj.source_file = f"{source}/{path.relative_to(root).as_posix()}"
                obj.save(update_fields=["content", "system_hint", "source_file", "updated_at"])

    def _infer_tier(self, name: str) -> int:
        for tier in (1, 2, 3, 4):
            if f"tier{tier}" in name.lower():
                return tier
        return 1

    def _skill_id_for(self, path: Path) -> str:
        dirname = path.parent.name
        mapping = {
            "short-drama-script-creator": "creation.script",
            "drama-creator-core": "creation.script",
            "drama-from-outline": "creation.script",
            "drama-world-setting-builder": "creation.structure",
            "drama-world-character-builder": "creation.structure",
            "drama-character-designer": "creation.character",
            "drama-character-manager": "creation.character",
            "drama-quality-suite": "creation.review",
            "drama-evaluation-scorer": "creation.score",
            "drama-polisher-text": "creation.polish",
            "drama-polisher-creative": "creation.polish",
            "drama-marketing-kit": "creation.marketing",
            "drama-info-extractor": "creation.insight",
        }
        return mapping.get(dirname, dirname)

    def _skill_category(self, skill_id: str) -> str:
        if skill_id in {"creation.review", "creation.score"}:
            return AgentSkillDefinition.CATEGORY_QUALITY
        if skill_id == "creation.marketing":
            return AgentSkillDefinition.CATEGORY_SHARED
        return AgentSkillDefinition.CATEGORY_CREATOR
