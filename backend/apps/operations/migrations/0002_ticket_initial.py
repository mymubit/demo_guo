"""Ticket 模块初始迁移。"""
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0001_campaign_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TicketCategoryConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(
                    choices=[("billing", "计费/支付"), ("skill_issue", "技能/创作异常"),
                             ("content_issue", "内容质量"), ("account", "账号问题"),
                             ("suggestion", "建议反馈"), ("compliance", "合规/举报"),
                             ("other", "其他")],
                    max_length=32, unique=True,
                )),
                ("name", models.CharField(max_length=64)),
                ("description", models.TextField(blank=True, default="")),
                ("sla_first_response_minutes", models.PositiveIntegerField(default=60)),
                ("sla_resolve_minutes", models.PositiveIntegerField(default=1440)),
                ("default_assignee_role", models.CharField(blank=True, default="", max_length=64)),
                ("auto_reply_template", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "ops_ticket_category", "ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="Ticket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ticket_no", models.CharField(help_text="工单编号（用户可见）", max_length=32, unique=True)),
                ("category", models.CharField(
                    choices=[("billing", "计费/支付"), ("skill_issue", "技能/创作异常"),
                             ("content_issue", "内容质量"), ("account", "账号问题"),
                             ("suggestion", "建议反馈"), ("compliance", "合规/举报"),
                             ("other", "其他")],
                    max_length=32,
                )),
                ("priority", models.CharField(
                    choices=[("P0", "紧急"), ("P1", "高"), ("P2", "中"), ("P3", "低")],
                    default="P2", max_length=8,
                )),
                ("status", models.CharField(
                    choices=[("pending", "待受理"), ("processing", "处理中"),
                             ("waiting_user", "等待用户"), ("resolved", "已解决"),
                             ("closed", "已关闭"), ("rejected", "已驳回")],
                    default="pending", max_length=16,
                )),
                ("subject", models.CharField(max_length=255)),
                ("content", models.TextField()),
                ("contact", models.CharField(blank=True, default="", max_length=128)),
                ("attachments", models.JSONField(default=list)),
                ("context", models.JSONField(default=dict)),
                ("assignee_role", models.CharField(blank=True, default="", max_length=64)),
                ("first_response_at", models.DateTimeField(blank=True, null=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("sla_first_response_breached", models.BooleanField(default=False)),
                ("sla_resolve_breached", models.BooleanField(default=False)),
                ("satisfaction", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("satisfaction_comment", models.TextField(blank=True, default="")),
                ("operator", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assignee", models.ForeignKey(
                    blank=True, null=True, on_delete=models.deletion.SET_NULL,
                    related_name="assigned_tickets", to=settings.AUTH_USER_MODEL,
                )),
                ("user", models.ForeignKey(
                    blank=True, null=True, on_delete=models.deletion.SET_NULL,
                    related_name="tickets", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"db_table": "ops_ticket", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(fields=["status", "-created_at"], name="ops_tk_idx_status_created"),
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(fields=["category", "status"], name="ops_tk_idx_cat_status"),
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(fields=["assignee", "status"], name="ops_tk_idx_asg_status"),
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(fields=["priority", "status"], name="ops_tk_idx_pri_status"),
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(fields=["-created_at"], name="ops_tk_idx_created"),
        ),
        migrations.CreateModel(
            name="TicketReply",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("author_role", models.CharField(default="user", help_text="user/ops/system", max_length=16)),
                ("content", models.TextField()),
                ("attachments", models.JSONField(default=list)),
                ("is_internal_note", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("author", models.ForeignKey(
                    blank=True, null=True, on_delete=models.deletion.SET_NULL,
                    related_name="ticket_replies", to=settings.AUTH_USER_MODEL,
                )),
                ("ticket", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="replies", to="operations.ticket",
                )),
            ],
            options={"db_table": "ops_ticket_reply", "ordering": ["created_at"]},
        ),
        migrations.AddIndex(
            model_name="ticketreply",
            index=models.Index(fields=["ticket", "-created_at"], name="ops_tkr_idx_ticket_created"),
        ),
        migrations.CreateModel(
            name="TicketEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=32)),
                ("operator", models.CharField(blank=True, default="", max_length=64)),
                ("from_value", models.CharField(blank=True, default="", max_length=64)),
                ("to_value", models.CharField(blank=True, default="", max_length=64)),
                ("note", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ticket", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="events", to="operations.ticket",
                )),
            ],
            options={"db_table": "ops_ticket_event", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="ticketevent",
            index=models.Index(fields=["ticket", "-created_at"], name="ops_tke_idx_ticket_created"),
        ),
        migrations.CreateModel(
            name="TicketMacro",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=64)),
                ("category", models.CharField(blank=True, default="", max_length=32)),
                ("content", models.TextField()),
                ("is_active", models.BooleanField(default=True)),
                ("operator", models.CharField(blank=True, default="", max_length=64)),
                ("usage_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "ops_ticket_macro", "ordering": ["-usage_count", "-created_at"]},
        ),
    ]
