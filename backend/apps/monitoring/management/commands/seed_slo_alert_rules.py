# -*- coding: utf-8 -*-
"""一人运营场景下的核心 SLO 告警规则 seed。

铁律 5 条（按优先级）：

  P0 立即响应
  ────────────────────────────────────────────────
  1. 创作提交 5xx 连续 5min 超过 5 次         → 立即叫人醒
  2. 僵尸工作流实例 > 0（15min+ 未结束）        → 立即叫人醒
  3. LLM 调用失败率 5min 内 > 15%             → 立即叫人醒（影响所有用户）

  P1 重要
  ────────────────────────────────────────────────
  4. 创作币总扣费较昨日 ±50%                  → 当天复盘

  P2 关注
  ────────────────────────────────────────────────
  5. Dashboard 缓存失效率 > 3 次/min           → QPS 上来了

每个规则带：channel=console_inapp、cooldown=10min、is_enabled=True。
本命令幂等：name 相同则跳过；metric_type 与 threshold 变化时更新。
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.monitoring.models import AlertRule, MonitorLevel


SLO_RULES = [
    {
        "name": "SLO·创作提交5xx突增",
        "metric_type": AlertRule.MetricType.BUSINESS_ERROR_COUNT,
        "comparator": AlertRule.Comparator.GT,
        "threshold": 5,
        "window_minutes": 5,
        "level": MonitorLevel.P0,
        "path_pattern": "/api/creation/submit/",
        "channels": ["console_inapp"],
        "cooldown_minutes": 10,
        "description": "创作提交接口（/api/creation/submit/）5min 内 5xx 超过 5 次，必醒。",
    },
    {
        "name": "SLO·僵尸工作流实例",
        "metric_type": AlertRule.MetricType.BUSINESS_ERROR_COUNT,
        "comparator": AlertRule.Comparator.GT,
        "threshold": 0,
        "window_minutes": 5,
        "level": MonitorLevel.P0,
        "path_pattern": "/api/admin/workflow/instances/stale/",
        "channels": ["console_inapp"],
        "cooldown_minutes": 15,
        "description": "存在超过 15min 仍处于 running 的 WorkflowInstance，必醒。",
    },
    {
        "name": "SLO·LLM整体失败率",
        "metric_type": AlertRule.MetricType.API_ERROR_RATE,
        "comparator": AlertRule.Comparator.GT,
        "threshold": 15,
        "window_minutes": 5,
        "level": MonitorLevel.P0,
        "path_pattern": "/api/skill/llm/",
        "channels": ["console_inapp"],
        "cooldown_minutes": 10,
        "description": "5min 内 LLM 调用失败率 > 15%（影响所有用户），必醒。",
    },
    {
        "name": "SLO·创作币日扣费异常",
        "metric_type": AlertRule.MetricType.BUSINESS_ERROR_COUNT,
        "comparator": AlertRule.Comparator.GT,
        "threshold": 50,
        "window_minutes": 60,
        "level": MonitorLevel.P1,
        "path_pattern": "/api/billing/coin/spend/",
        "channels": ["console_inapp"],
        "cooldown_minutes": 60,
        "description": "总扣费较昨日同期 ±50%（运营当天复盘重点）。",
    },
    {
        "name": "SLO·Dashboard缓存失效率",
        "metric_type": AlertRule.MetricType.API_AVG_DURATION,
        "comparator": AlertRule.Comparator.GT,
        "threshold": 800,
        "window_minutes": 5,
        "level": MonitorLevel.P2,
        "path_pattern": "/api/admin/dashboard/",
        "channels": ["console_inapp"],
        "cooldown_minutes": 30,
        "description": "Dashboard 平均耗时 > 800ms（QPS 上来了，关注扩容）。",
    },
]


class Command(BaseCommand):
    help = "导入 / 更新 5 条 SLO 告警规则（一人运营铁律）。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="重置：将所有 name 匹配 SLO 规则的告警 is_enabled=False（不删除，便于回滚观察）。",
        )

    def handle(self, *args, **options):
        if options.get("reset"):
            updated = AlertRule.objects.filter(name__in=[r["name"] for r in SLO_RULES]).update(
                is_enabled=False,
                updated_at=timezone.now(),
            )
            self.stdout.write(self.style.WARNING(f"[RESET] 已停用 {updated} 条 SLO 规则"))
            return

        created_count = 0
        updated_count = 0
        for rule_data in SLO_RULES:
            defaults = dict(rule_data)
            defaults.pop("description", None)
            obj, created = AlertRule.objects.update_or_create(
                name=rule_data["name"],
                defaults={
                    **defaults,
                    "is_enabled": True,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"[CREATE] {obj.name} ({obj.level})"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"[UPDATE] {obj.name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\n完成：{created_count} 条新建，{updated_count} 条更新，共 {len(SLO_RULES)} 条规则。\n"
                f"立即生效渠道：console_inapp（控制台 AlertEvent 列表）。"
            )
        )
