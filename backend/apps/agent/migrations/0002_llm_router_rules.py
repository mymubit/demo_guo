# -*- coding: utf-8 -*-
"""LLM 路由规则字段扩展 — 为 AgentLlmRouteConfig 添加 routing_rules JSONField。"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agent", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentllmrouteconfig",
            name="routing_rules",
            field=models.JSONField(
                "路由规则 JSON",
                default=dict,
                blank=True,
                help_text=(
                    "多维路由规则配置，格式："
                    '{"rules":[{"priority":1,'
                    '"conditions":{"theme":[],"node_type":[],"user_tier":[],"time_window":{}},'
                    '"model_name":"gpt-4o-mini","provider_id":"xxx","cost_score":0}]}'
                ),
            ),
        ),
    ]
