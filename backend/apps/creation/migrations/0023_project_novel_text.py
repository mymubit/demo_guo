# Generated manually for novel_text field on Project

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0022_script_quality_dimension_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="novel_text",
            field=models.TextField(
                blank=True,
                default="",
                help_text="小说改编入口提交的完整原文，供 adapt Agent 使用",
                verbose_name="小说原文",
            ),
        ),
    ]
