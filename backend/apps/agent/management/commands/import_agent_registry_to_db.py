"""
将 demo4book/agents/registry.json 导入到 AgentRegistryConfig。

用法：
  python manage.py import_agent_registry_to_db
  python manage.py import_agent_registry_to_db --overwrite
  python manage.py import_agent_registry_to_db --dry-run
"""
from django.core.management.base import BaseCommand, CommandError

from apps.agent.registry import AgentRegistryConfigService


class Command(BaseCommand):
    help = "导入 Agent Registry JSON 到后台配置表（DB SSOT）"

    def add_arguments(self, parser):
        parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的 default 配置")
        parser.add_argument("--dry-run", action="store_true", help="仅预览，不写入数据库")
        parser.add_argument("--config-key", default="default", help="配置键，默认 default")

    def handle(self, *args, **options):
        if options["config_key"] != "default":
            raise CommandError("当前仅支持 config_key=default")

        overwrite = options["overwrite"]
        dry_run = options["dry_run"]

        try:
            file_registry = AgentRegistryConfigService._load_file_registry()
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        agents_count = len(file_registry.get("agents") or [])
        workspace_count = len((file_registry.get("_meta") or {}).get("workspace_modules") or [])
        self.stdout.write(
            f"[preview] agents={agents_count}, workspace_modules={workspace_count}, "
            f"source={file_registry.get('_registry_path')}"
        )

        if dry_run:
            self.stdout.write("[dry-run] 未写入数据库")
            return

        existing = AgentRegistryConfigService.get_active_row()
        if existing and not overwrite:
            self.stdout.write(
                self.style.WARNING("[skip] default 已存在；如需覆盖请加 --overwrite")
            )
            return

        AgentRegistryConfigService.import_from_file(overwrite=True)
        self.stdout.write(self.style.SUCCESS("[ok] 已导入并启用 AgentRegistryConfig: default"))
