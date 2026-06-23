# -*- coding: utf-8 -*-
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.models import AgentDefinition, AgentKnowledgeItem


class Command(BaseCommand):
    help = "Verify imported agent assets and active Agent configuration health."

    def add_arguments(self, parser):
        parser.add_argument("--inventory", required=True, help="Path to external_asset_inventory.json")
        parser.add_argument(
            "--require-healthy-routes",
            action="store_true",
            help="Also fail when active agents have no LLM provider route",
        )

    def handle(self, *args, **options):
        inventory_path = Path(options["inventory"])
        if not inventory_path.exists():
            raise CommandError(f"Inventory not found: {inventory_path}")
        payload = json.loads(inventory_path.read_text(encoding="utf-8"))
        items = payload.get("items") if isinstance(payload, dict) else []
        missing = []
        for item in items:
            if item.get("import_action") != "import":
                continue
            source_origin = str(item.get("source_origin") or "")
            rel = str(item.get("relative_path") or "")
            knowledge_id = f"{source_origin}:{rel}".replace("\\", "/")[:128]
            checksum = str(item.get("checksum") or "")
            exists = AgentKnowledgeItem.objects.filter(
                knowledge_id=knowledge_id,
                checksum=checksum,
            ).exists()
            if not exists:
                missing.append(knowledge_id)

        unhealthy = []
        if options.get("require_healthy_routes"):
            for agent in AgentDefinition.objects.filter(
                lifecycle_status=AgentDefinition.LifecycleStatus.ACTIVE,
                is_enabled=True,
            ):
                health = AgentDefinitionService.health(agent)
                if not health["healthy"]:
                    unhealthy.append(health)

        result = {"missing_assets": missing, "unhealthy_agents": unhealthy}
        if missing or unhealthy:
            raise CommandError(json.dumps(result, ensure_ascii=False, indent=2))
        self.stdout.write(self.style.SUCCESS(json.dumps({"ok": True}, ensure_ascii=False)))
