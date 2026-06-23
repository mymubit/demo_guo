# -*- coding: utf-8 -*-
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.agent.models import AgentDefinition, AgentKnowledgeBinding, AgentKnowledgeItem

EXTERNAL_DIR_NAMES = ("demo4book", "ai-drama-skills-v2")


class Command(BaseCommand):
    help = "Verify ScriptForge can remove external demo4book/ai-drama-skills-v2 directories safely."

    def add_arguments(self, parser):
        parser.add_argument("--scriptforge-root", default="", help="ScriptForge root path")
        parser.add_argument(
            "--workspace-root",
            default="",
            help="Parent workspace path that must not contain external asset directories",
        )

    def handle(self, *args, **options):
        scriptforge_root = Path(options.get("scriptforge_root") or Path.cwd().parent).resolve()
        workspace_root = Path(
            options.get("workspace_root") or scriptforge_root.parent
        ).resolve()
        blockers: dict = {
            "external_dirs_present": [],
            "agent_binding_gaps": [],
            "runtime_path_references": [],
            "other": [],
        }
        skip_path_parts = {".git", "node_modules", ".idea", "__pycache__", "migrations", "tmp"}
        skip_path_suffixes = (".pyc", ".env", "external_asset_inventory.json")
        skip_path_contains = ("management/commands/", "docs/")

        for dirname in EXTERNAL_DIR_NAMES:
            external_path = workspace_root / dirname
            if external_path.exists():
                blockers["external_dirs_present"].append(str(external_path))

        active_agents = AgentDefinition.objects.filter(
            lifecycle_status=AgentDefinition.LifecycleStatus.ACTIVE,
            is_enabled=True,
        )
        for agent in active_agents:
            if not agent.prompt_versions.filter(is_active=True).exists():
                blockers["other"].append(f"{agent.agent_id}: missing active prompt")
            if not (agent.input_contract and agent.output_contract):
                blockers["other"].append(f"{agent.agent_id}: missing contract")
            binding_count = AgentKnowledgeBinding.objects.filter(
                agent=agent,
                is_enabled=True,
                knowledge__is_enabled=True,
            ).count()
            has_importable = AgentKnowledgeItem.objects.filter(
                applies_to_agents__contains=agent.agent_id,
                is_enabled=True,
            ).exists()
            if binding_count <= 0 and has_importable:
                blockers["agent_binding_gaps"].append(f"{agent.agent_id}: no DB knowledge binding")

        imported = AgentKnowledgeItem.objects.filter(source_origin__in=EXTERNAL_DIR_NAMES).exists()
        if not imported:
            blockers["other"].append("external assets have not been imported into AgentKnowledgeItem")

        runtime_hits = []
        for path in scriptforge_root.rglob("*"):
            if not path.is_file() or any(part in skip_path_parts for part in path.parts):
                continue
            rel = path.relative_to(scriptforge_root).as_posix()
            if rel.endswith(skip_path_suffixes):
                continue
            if any(token in rel for token in skip_path_contains):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if any(token in text for token in ("FUSION_SKILL_ROOT", "demo4book", "ai-drama-skills-v2")):
                runtime_hits.append(rel)
        if runtime_hits:
            blockers["runtime_path_references"] = sorted(runtime_hits)

        has_blockers = any(blockers[key] for key in blockers)
        if has_blockers:
            raise CommandError(json.dumps({"ok": False, "blockers": blockers}, ensure_ascii=False, indent=2))
        self.stdout.write(self.style.SUCCESS(json.dumps({"ok": True}, ensure_ascii=False)))
