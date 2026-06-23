# -*- coding: utf-8 -*-
# Generated manually — LlmModelCatalog + LlmProvider advanced fields

import uuid

from django.db import migrations, models
import django.db.models.deletion


def seed_catalog(apps, schema_editor):
    LlmModelCatalog = apps.get_model("skill", "LlmModelCatalog")
    from apps.skill.config.bootstrap.llm_model_catalog import CATALOG_SEED

    for item in CATALOG_SEED:
        if LlmModelCatalog.objects.filter(preset_key=item["preset_key"]).exists():
            continue
        base_url = (item["base_url"] or "").strip().rstrip("/")
        suffix = "/chat/completions"
        if base_url.endswith(suffix):
            base_url = base_url[: -len(suffix)].rstrip("/")
        LlmModelCatalog.objects.create(
            id=uuid.uuid4(),
            preset_key=item["preset_key"],
            name=item["name"],
            vendor=item["vendor"],
            vendor_label=item.get("vendor_label", ""),
            base_url=base_url,
            model_name=item["model_name"],
            temperature=float(item.get("temperature", 0.7)),
            max_tokens=max(256, int(item.get("max_tokens", 8192))),
            context_window_input=item.get("context_window_input"),
            context_window_output=item.get("context_window_output"),
            tool_call_rounds=item.get("tool_call_rounds"),
            supports_multimodal=bool(item.get("supports_multimodal", False)),
            api_key_hint=str(item.get("api_key_hint") or "")[:255],
            api_key_url=str(item.get("api_key_url") or "")[:512],
            remark=str(item.get("remark") or "")[:512],
            is_enabled=True,
            sort_order=int(item.get("sort_order", 0)),
        )


def link_providers_to_catalog(apps, schema_editor):
    LlmModelCatalog = apps.get_model("skill", "LlmModelCatalog")
    LlmProvider = apps.get_model("skill", "LlmProvider")

    def norm(url):
        u = (url or "").strip().rstrip("/")
        if u.endswith("/chat/completions"):
            u = u[: -len("/chat/completions")].rstrip("/")
        return u

    for catalog in LlmModelCatalog.objects.all():
        LlmProvider.objects.filter(
            catalog__isnull=True,
            model_name=catalog.model_name,
            base_url=norm(catalog.base_url),
        ).update(catalog_id=catalog.id)


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0002_llmprovider"),
    ]

    operations = [
        migrations.CreateModel(
            name="LlmModelCatalog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("preset_key", models.CharField(db_index=True, max_length=64, unique=True, verbose_name="预设键")),
                ("name", models.CharField(max_length=100, verbose_name="展示名称")),
                ("vendor", models.CharField(db_index=True, max_length=64, verbose_name="厂商标识")),
                ("vendor_label", models.CharField(blank=True, default="", max_length=64, verbose_name="厂商名称")),
                ("base_url", models.CharField(max_length=512, verbose_name="Base URL")),
                ("model_name", models.CharField(max_length=128, verbose_name="模型 ID")),
                ("temperature", models.FloatField(default=0.7, verbose_name="默认 Temperature")),
                ("max_tokens", models.PositiveIntegerField(default=8192, verbose_name="默认 Max Tokens")),
                ("context_window_input", models.PositiveIntegerField(blank=True, null=True, verbose_name="上下文窗口-输入")),
                ("context_window_output", models.PositiveIntegerField(blank=True, null=True, verbose_name="上下文窗口-输出")),
                ("tool_call_rounds", models.PositiveIntegerField(blank=True, null=True, verbose_name="工具调用轮次")),
                ("supports_multimodal", models.BooleanField(default=False, verbose_name="支持多模态")),
                ("api_key_hint", models.CharField(blank=True, default="", max_length=255, verbose_name="API Key 提示")),
                ("api_key_url", models.CharField(blank=True, default="", max_length=512, verbose_name="获取 Key 链接")),
                ("remark", models.CharField(blank=True, default="", max_length=512, verbose_name="备注")),
                ("is_enabled", models.BooleanField(db_index=True, default=True, verbose_name="启用")),
                ("sort_order", models.IntegerField(default=0, verbose_name="排序")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "大模型目录",
                "verbose_name_plural": "大模型目录",
                "db_table": "skill_llm_model_catalog",
                "ordering": ["sort_order", "vendor", "name"],
            },
        ),
        migrations.AddField(
            model_name="llmprovider",
            name="catalog",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="providers",
                to="skill.llmmodelcatalog",
                verbose_name="目录模板",
            ),
        ),
        migrations.AddField(
            model_name="llmprovider",
            name="context_window_input",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="上下文窗口-输入"),
        ),
        migrations.AddField(
            model_name="llmprovider",
            name="context_window_output",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="上下文窗口-输出"),
        ),
        migrations.AddField(
            model_name="llmprovider",
            name="tool_call_rounds",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="工具调用轮次"),
        ),
        migrations.AddField(
            model_name="llmprovider",
            name="supports_multimodal",
            field=models.BooleanField(default=False, verbose_name="支持多模态"),
        ),
        migrations.RunPython(seed_catalog, migrations.RunPython.noop),
        migrations.RunPython(link_providers_to_catalog, migrations.RunPython.noop),
    ]
