import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.models import AgentDefinition, AgentKnowledgeBinding, AgentKnowledgeItem

from .agent_asset_utils import category_for_classification, read_asset


class Command(BaseCommand):
    help = "Import inventoried external assets into AgentKnowledgeItem rows."

    def add_arguments(self, parser):
        parser.add_argument("--inventory", required=True, help="Path to external_asset_inventory.json")
        parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
        parser.add_argument("--commit", action="store_true", help="Write database rows")

    def handle(self, *args, **options):
        if options["dry_run"] == options["commit"]:
            raise CommandError("Pass exactly one of --dry-run or --commit")
        inventory_path = Path(options["inventory"])
        if not inventory_path.exists():
            raise CommandError(f"Inventory not found: {inventory_path}")
        payload = json.loads(inventory_path.read_text(encoding="utf-8"))
        items = payload.get("items") if isinstance(payload, dict) else []
        if not isinstance(items, list):
            raise CommandError("Invalid inventory: items must be a list")

        AgentDefinitionService.ensure_defaults()
        summary = {"create_or_update": 0, "discard": 0, "bind": 0, "missing": 0}
        if options["dry_run"]:
            for item in items:
                action = item.get("import_action")
                if action == "import":
                    summary["create_or_update"] += 1
                    if item.get("suggested_agent"):
                        summary["bind"] += 1
                elif action == "discard":
                    summary["discard"] += 1
                else:
                    summary["missing"] += 1
            self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2))
            return

        with transaction.atomic():
            for item in items:
                if item.get("import_action") != "import":
                    if item.get("import_action") == "discard":
                        summary["discard"] += 1
                    else:
                        summary["missing"] += 1
                    continue
                path = Path(str(item.get("path") or ""))
                if not path.exists():
                    summary["missing"] += 1
                    continue
                classification = str(item.get("classification") or "knowledge")
                content = read_asset(path)
                source_origin = str(item.get("source_origin") or "")
                rel = str(item.get("relative_path") or path.name)
                knowledge_id = f"{source_origin}:{rel}".replace("\\", "/")
                row, _ = AgentKnowledgeItem.objects.update_or_create(
                    knowledge_id=knowledge_id[:128],
                    defaults={
                        "title": path.stem[:255],
                        "category": category_for_classification(classification),
                        "source_origin": source_origin,
                        "source_path": str(path)[:500],
                        "content_text": content["content_text"],
                        "content_json": content["content_json"],
                        "tags": [classification],
                        "applies_to_agents": [item.get("suggested_agent")] if item.get("suggested_agent") else [],
                        "priority": 100,
                        "is_enabled": True,
                        "version": "v1",
                        "checksum": str(item.get("checksum") or "")[:128],
                    },
                )
                summary["create_or_update"] += 1
                agent_id = str(item.get("suggested_agent") or "")
                if agent_id:
                    agent = AgentDefinition.objects.filter(agent_id=agent_id).first()
                    if agent:
                        AgentKnowledgeBinding.objects.get_or_create(
                            agent=agent,
                            knowledge=row,
                            binding_type=(
                                AgentKnowledgeBinding.BindingType.OUTPUT_SCHEMA
                                if row.category == AgentKnowledgeItem.Category.SCHEMA
                                else AgentKnowledgeBinding.BindingType.OPTIONAL
                            ),
                            inject_position=(
                                AgentKnowledgeBinding.InjectPosition.VALIDATOR
                                if row.category == AgentKnowledgeItem.Category.VALIDATOR
                                else AgentKnowledgeBinding.InjectPosition.CONTEXT
                            ),
                            defaults={"order_index": 100, "is_enabled": True},
                        )
                        summary["bind"] += 1
        self.stdout.write(self.style.SUCCESS(json.dumps(summary, ensure_ascii=False, indent=2)))
