# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0029_project_drama_workspace_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="theme",
            field=models.CharField(
                help_text="如 family-revenge / emotion-identity-conflict-world|tag1+tag2",
                max_length=128,
                verbose_name="题材",
            ),
        ),
    ]
