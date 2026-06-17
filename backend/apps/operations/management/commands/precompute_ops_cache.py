# -*- coding: utf-8 -*-
"""【运营 M5】预计算并写入运营聚合缓存。

建议每日凌晨 0:30 执行（避开 0 点 hit_24h 重置）。
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.operations.models import OperationsDailyCache
from apps.operations.services import (
    content_quality_dashboard,
    config_hit_dashboard,
    dashboard_slo_cards,
    feedback_summary,
    full_dashboard,
    node_duration_dashboard,
)


class Command(BaseCommand):
    help = "预计算运营 Dashboard 聚合并写入 OperationsDailyCache"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="聚合窗口（默认 30 天）",
        )
        parser.add_argument(
            "--date",
            type=str,
            default="",
            help="指定缓存日期 YYYY-MM-DD（默认 = 今天）",
        )

    def handle(self, *args, **options):
        if options["date"]:
            from datetime import date
            cache_date = date.fromisoformat(options["date"])
        else:
            cache_date = timezone.now().date()
        days = options["days"]

        payloads = {
            OperationsDailyCache.MetricType.DASHBOARD: full_dashboard(days=days),
            OperationsDailyCache.MetricType.CONTENT_QUALITY: content_quality_dashboard(days=days),
            OperationsDailyCache.MetricType.FEEDBACK: feedback_summary(days=days),
            OperationsDailyCache.MetricType.CONFIG_HIT: config_hit_dashboard(),
            OperationsDailyCache.MetricType.FUNNEL: full_dashboard(days=days).get("content_quality", {}).get("funnel", {}),
        }
        # 节点耗时（7d 固定）
        node_payload = node_duration_dashboard(days=7)

        written = 0
        for metric_type, payload in payloads.items():
            obj, _ = OperationsDailyCache.objects.update_or_create(
                cache_date=cache_date,
                metric_type=metric_type,
                defaults={"payload": payload, "extra": {"days": days}},
            )
            written += 1
            self.stdout.write(self.style.SUCCESS(
                f"[{cache_date}] {metric_type}: {len(payload) if isinstance(payload, (list, dict)) else 0} 项"
            ))

        # 节点耗时作为 dashboard 缓存的 extra
        OperationsDailyCache.objects.filter(
            cache_date=cache_date, metric_type=OperationsDailyCache.MetricType.DASHBOARD,
        ).update(extra={"days": days, "node_duration": node_payload})

        self.stdout.write(self.style.SUCCESS(
            f"完成：{written} 个 metric 已写入 cache_date={cache_date}"
        ))
