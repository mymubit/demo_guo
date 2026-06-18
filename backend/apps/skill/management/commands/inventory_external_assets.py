import json
from pathlib import Path

from django.core.management.base import BaseCommand

from .agent_asset_utils import iter_inventory


class Command(BaseCommand):
    help = "Inventory external ScriptForge agent assets without writing database rows."

    def add_arguments(self, parser):
        parser.add_argument("--roots", nargs="+", required=True, help="External asset roots")
        parser.add_argument(
            "--output",
            default="",
            help="Output JSON path (default: backend/tmp/external_asset_inventory.json)",
        )

    def handle(self, *args, **options):
        rows = iter_inventory(options["roots"])
        payload = {"items": rows, "count": len(rows)}
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        output = options.get("output") or ""
        if not output:
            output = str(Path.cwd() / "tmp" / "external_asset_inventory.json")
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"inventory written: {out_path} ({len(rows)} files)"))
