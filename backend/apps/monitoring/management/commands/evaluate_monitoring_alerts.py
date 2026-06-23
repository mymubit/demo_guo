# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from apps.monitoring.services.alerts import evaluate_alert_rules


class Command(BaseCommand):
    help = "评估监控告警规则"

    def handle(self, *args, **options):
        triggered = evaluate_alert_rules()
        self.stdout.write(self.style.SUCCESS(f"告警评估完成，触发 {triggered} 条"))
