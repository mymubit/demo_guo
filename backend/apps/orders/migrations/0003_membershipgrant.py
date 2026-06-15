import uuid

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("membership", "0005_feature_matrix_recharge_bonus"),
        ("orders", "0002_order_recharge_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="MembershipGrant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("grant_days", models.PositiveIntegerField(default=0, verbose_name="发放天数")),
                ("grant_coins", models.PositiveIntegerField(default=0, verbose_name="赠送币数")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="创建时间")),
                (
                    "order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="membership_grant",
                        to="orders.order",
                        verbose_name="订单",
                    ),
                ),
                (
                    "user_membership",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_grants",
                        to="membership.usermembership",
                        verbose_name="会员记录",
                    ),
                ),
            ],
            options={
                "verbose_name": "会员权益发放记录",
                "verbose_name_plural": "会员权益发放记录",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="membershipgrant",
            index=models.Index(fields=["user_membership"], name="orders_memb_user_me_a1535d_idx"),
        ),
    ]
