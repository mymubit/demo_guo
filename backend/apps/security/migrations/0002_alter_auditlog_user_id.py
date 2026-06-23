# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("security", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        'ALTER TABLE "sf_audit_log" '
                        'ALTER COLUMN "user_id" TYPE uuid USING NULL;'
                    ),
                    reverse_sql=(
                        'ALTER TABLE "sf_audit_log" '
                        'ALTER COLUMN "user_id" TYPE bigint USING NULL;'
                    ),
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="auditlog",
                    name="user_id",
                    field=models.UUIDField(
                        blank=True,
                        db_index=True,
                        help_text="关联用户ID，未登录用户为空",
                        null=True,
                        verbose_name="用户ID",
                    ),
                ),
            ],
        ),
    ]
