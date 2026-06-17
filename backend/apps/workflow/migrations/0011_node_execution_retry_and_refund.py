# P2-2/3 阶段：为 NodeExecution 补充：
#   1) retry_count —— 节点级重试次数（重试策略由 cfg.runtime_config.retry_policy 控制）
#   2) fallback_skill_id —— 失败时的降级 skill_id（为空时使用 SkillInvoker 的 fallback）
#   3) quota_refunded —— 失败时是否已回补配额
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0010_default_pack_bootstrap"),
    ]

    operations = [
        migrations.AddField(
            model_name="nodeexecution",
            name="retry_count",
            field=models.PositiveSmallIntegerField(
                "重试次数", default=0,
                help_text="节点内部重试次数（含首次执行）。0=一次成功无重试",
            ),
        ),
        migrations.AddField(
            model_name="nodeexecution",
            name="fallback_used",
            field=models.BooleanField(
                "是否触发降级", default=False,
                help_text="节点失败时是否使用了降级 skill 重新执行",
            ),
        ),
        migrations.AddField(
            model_name="nodeexecution",
            name="quota_refunded",
            field=models.BooleanField(
                "是否回补配额", default=False,
                help_text="失败时是否已调用 refund_coins",
            ),
        ),
    ]
