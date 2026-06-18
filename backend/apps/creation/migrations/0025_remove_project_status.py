# 删除 legacy Project.status 列，运营态统一 fusion_status

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0024_backfill_fusion_status"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="project",
            name="status",
        ),
        migrations.AddIndex(
            model_name="project",
            index=models.Index(fields=["fusion_status"], name="creation_pr_fusion_st_idx"),
        ),
        migrations.AddIndex(
            model_name="project",
            index=models.Index(fields=["abandoned_at", "fusion_status"], name="creation_pr_abandon_fus_idx"),
        ),
        migrations.AddIndex(
            model_name="project",
            index=models.Index(fields=["-created_at", "fusion_status"], name="creation_pr_created_fus_idx"),
        ),
    ]
