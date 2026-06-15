from django.core.management.base import BaseCommand

from apps.monitoring.services.retention import cleanup_expired_monitoring_data


class Command(BaseCommand):
    help = "清理过期监控数据"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=None, help="保留天数，默认读取 MONITORING_RETENTION_DAYS")

    def handle(self, *args, **options):
        deleted = cleanup_expired_monitoring_data(options.get("days"))
        for key, count in deleted.items():
            self.stdout.write(f"{key}: {count}")
        self.stdout.write(self.style.SUCCESS("监控数据清理完成"))
