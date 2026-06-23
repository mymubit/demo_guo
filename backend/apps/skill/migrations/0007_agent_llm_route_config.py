# -*- coding: utf-8 -*-
# Generated manually — Agent LLM 路由与节点 max_tokens

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0006_fusion_node_llm_provider"),
    ]

    operations = [
        migrations.AddField(
            model_name="fusionnodellmpromptconfig",
            name="max_tokens",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="本节点 LLM 输出上限；留空则读 Agent 路由表",
                null=True,
                verbose_name="Max Tokens",
            ),
        ),
        migrations.CreateModel(
            name="AgentLlmRouteConfig",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "route_key",
                    models.CharField(
                        db_index=True,
                        max_length=64,
                        unique=True,
                        verbose_name="路由键",
                    ),
                ),
                (
                    "display_name",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=128,
                        verbose_name="展示名称",
                    ),
                ),
                ("max_tokens", models.PositiveIntegerField(blank=True, null=True, verbose_name="Max Tokens")),
                ("is_active", models.BooleanField(default=True, verbose_name="启用")),
                ("sort_order", models.IntegerField(default=0, verbose_name="排序")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "llm_provider",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agent_llm_routes",
                        to="skill.llmprovider",
                        verbose_name="指定大模型",
                    ),
                ),
            ],
            options={
                "verbose_name": "Agent LLM 路由",
                "verbose_name_plural": "Agent LLM 路由",
                "db_table": "skill_agent_llm_route",
                "ordering": ["sort_order", "route_key"],
            },
        ),
    ]
