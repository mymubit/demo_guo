import uuid
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0013_llm_usage_cost_split"),
    ]

    operations = [
        migrations.CreateModel(
            name="SkillRuleConfig",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tier", models.PositiveSmallIntegerField(
                    choices=[(2, "Tier2·品类规范"), (3, "Tier3·节点流程")],
                    db_index=True,
                    verbose_name="层级",
                )),
                ("scope_type", models.CharField(
                    choices=[("global", "全局"), ("genre", "题材"), ("node", "节点")],
                    db_index=True,
                    default="global",
                    max_length=16,
                    verbose_name="范围类型",
                )),
                ("scope_key", models.CharField(
                    blank=True,
                    db_index=True,
                    default="",
                    help_text="题材代码（如 family-revenge）或节点 ID（如 node-5-script），全局时留空",
                    max_length=128,
                    verbose_name="范围键",
                )),
                ("section", models.CharField(
                    db_index=True,
                    help_text="规则在 JSON 中的 section 名，如 requirements / rhythm_rules / quantitative_constraints",
                    max_length=64,
                    verbose_name="规则分区",
                )),
                ("content", models.JSONField(
                    help_text="该 section 的完整规则数据（结构对齐 tier JSON 文件中的对应字段）",
                    verbose_name="规则内容",
                )),
                ("version_tag", models.CharField(
                    db_index=True,
                    default="v5.0.0",
                    help_text="如 v5.0.0 / v5.1.0，每次批准新提案时递增",
                    max_length=32,
                    verbose_name="版本标签",
                )),
                ("status", models.CharField(
                    choices=[("active", "已生效"), ("draft", "草稿（待审核）"), ("archived", "已归档")],
                    db_index=True,
                    default="draft",
                    max_length=16,
                    verbose_name="状态",
                )),
                ("source", models.CharField(
                    choices=[("file_import", "JSON文件导入"), ("admin", "后台手动录入"), ("evolve_audit", "进化审计提案")],
                    db_index=True,
                    default="admin",
                    max_length=16,
                    verbose_name="来源",
                )),
                ("note", models.TextField(blank=True, default="", verbose_name="备注/修改说明")),
                ("approved_by", models.CharField(blank=True, default="", max_length=128, verbose_name="审核人")),
                ("approved_at", models.DateTimeField(blank=True, null=True, verbose_name="审核时间")),
                ("trigger_project_ids", models.JSONField(
                    blank=True,
                    default=list,
                    help_text="触发本条规则修改提案的项目 ID（来自 evolve_audit）",
                    verbose_name="触发项目 ID 列表",
                )),
                ("trigger_score_avg", models.FloatField(
                    blank=True,
                    null=True,
                    help_text="触发低分追溯时的平均得分，用于评估修改效果",
                    verbose_name="触发时平均分",
                )),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "技能规则配置",
                "verbose_name_plural": "技能规则配置",
                "db_table": "skill_rule_config",
                "ordering": ["tier", "scope_type", "scope_key", "section", "-created_at"],
                "indexes": [
                    models.Index(
                        fields=["tier", "scope_type", "scope_key", "section", "status"],
                        name="skill_rule_main_idx",
                    ),
                    models.Index(
                        fields=["status", "-updated_at"],
                        name="skill_rule_status_idx",
                    ),
                ],
            },
        ),
    ]
