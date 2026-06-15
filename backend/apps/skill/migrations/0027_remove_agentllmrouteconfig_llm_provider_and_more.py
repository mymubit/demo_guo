# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0026_strip_pipeline_skill_fields"),
        ("workflow", "0001_initial"),
        ("agent", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="AgentRegistryConfig"),
                migrations.DeleteModel(name="ReviewScoringConfig"),
                migrations.DeleteModel(name="AgentLlmRouteConfig"),
                migrations.DeleteModel(name="FusionPipelinePack"),
                migrations.DeleteModel(name="FusionJsonSchema"),
                migrations.DeleteModel(name="FusionPipelineNode"),
            ],
        ),
        migrations.AlterField(
            model_name="dialoguetemplate",
            name="template_text",
            field=models.TextField(verbose_name="模板文本"),
        ),
        migrations.AlterField(
            model_name="hooklibrary",
            name="content",
            field=models.TextField(verbose_name="钩子内容"),
        ),
        migrations.AlterField(
            model_name="hooklibrary",
            name="tags",
            field=models.CharField(blank=True, default="", max_length=256, verbose_name="标签"),
        ),
        migrations.AlterField(
            model_name="themetemplate",
            name="character_archetypes",
            field=models.JSONField(blank=True, default=list, verbose_name="角色原型"),
        ),
        migrations.AlterField(
            model_name="themetemplate",
            name="hook_templates",
            field=models.JSONField(blank=True, default=dict, verbose_name="钩子模板配置"),
        ),
        migrations.AlterField(
            model_name="themetemplate",
            name="params",
            field=models.JSONField(blank=True, default=dict, verbose_name="参数配置"),
        ),
        migrations.AlterField(
            model_name="themetemplate",
            name="sort_order",
            field=models.IntegerField(default=0, verbose_name="排序"),
        ),
        migrations.AlterField(
            model_name="themetemplate",
            name="theme_code",
            field=models.CharField(db_index=True, max_length=64, unique=True, verbose_name="题材代码"),
        ),
        migrations.AlterField(
            model_name="themetemplate",
            name="theme_name",
            field=models.CharField(max_length=64, verbose_name="题材名称"),
        ),
    ]
