"""为已完成项目补写 ScriptWork 与展示 HTML。"""
from django.core.management.base import BaseCommand

from apps.creation.models import Project
from apps.creation.script_delivery import persist_script_works


class Command(BaseCommand):
    help = "为已完成项目从 fusion artifact 重建剧本文件与 rendered_result_html"

    def add_arguments(self, parser):
        parser.add_argument("--project-id", type=str, default="", help="仅处理指定 project UUID")
        parser.add_argument("--limit", type=int, default=50, help="最多处理条数")

    def handle(self, *args, **options):
        qs = Project.objects.filter(fusion_status=Project.FUSION_READY).order_by("-completed_at")
        if options["project_id"]:
            qs = qs.filter(id=options["project_id"])
        qs = qs[: options["limit"]]

        ok = 0
        for project in qs:
            persist_script_works(project)
            ok += 1
            self.stdout.write(self.style.SUCCESS(f"OK {project.id} · {project.title}"))

        self.stdout.write(self.style.NOTICE(f"已处理 {ok} 个项目"))
