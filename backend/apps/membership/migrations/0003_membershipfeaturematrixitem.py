# Generated manually for MembershipFeatureMatrixItem

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("membership", "0002_membershipplan_grant_coins"),
    ]

    operations = [
        migrations.CreateModel(
            name="MembershipFeatureMatrixItem",
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
                ("feature_key", models.CharField(max_length=64, unique=True, verbose_name="权益键")),
                ("label", models.CharField(max_length=128, verbose_name="展示名称")),
                ("free", models.BooleanField(default=False, verbose_name="普通用户")),
                ("member", models.BooleanField(default=True, verbose_name="会员")),
                ("coming_soon", models.BooleanField(default=False, verbose_name="即将上线")),
                ("member_only", models.BooleanField(default=False, verbose_name="仅会员")),
                ("is_active", models.BooleanField(default=True, verbose_name="启用")),
                ("sort_order", models.IntegerField(default=0, verbose_name="排序")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "会员权益矩阵",
                "verbose_name_plural": "会员权益矩阵",
                "db_table": "membership_feature_matrix_item",
                "ordering": ["sort_order", "feature_key"],
            },
        ),
    ]
