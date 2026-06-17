"""工单分类默认配置。"""
from django.db import migrations


CATEGORIES = [
    {"code": "billing", "name": "计费/支付", "description": "充值、扣费、订单、退款等计费问题",
     "sla_first_response_minutes": 30, "sla_resolve_minutes": 720, "default_assignee_role": "commerce_ops",
     "auto_reply_template": "您的工单已受理，财务同事会在 30 分钟内联系您。", "sort_order": 1},
    {"code": "skill_issue", "name": "技能/创作异常", "description": "AI 创作出错、生成结果异常、技能调用失败",
     "sla_first_response_minutes": 30, "sla_resolve_minutes": 360, "default_assignee_role": "skill_ops",
     "auto_reply_template": "已记录您反馈的创作异常，技术同事正在排查。", "sort_order": 2},
    {"code": "content_issue", "name": "内容质量", "description": "AI 生成的内容质量不满意、润色需求",
     "sla_first_response_minutes": 60, "sla_resolve_minutes": 720, "default_assignee_role": "content_ops",
     "auto_reply_template": "感谢您的反馈，内容团队会在 1 小时内与您沟通。", "sort_order": 3},
    {"code": "account", "name": "账号问题", "description": "登录、注册、密码、账号申诉",
     "sla_first_response_minutes": 30, "sla_resolve_minutes": 240, "default_assignee_role": "support_ops",
     "auto_reply_template": "您的账号问题已受理，客服会在 30 分钟内联系您。", "sort_order": 4},
    {"code": "suggestion", "name": "建议反馈", "description": "产品建议、Bug 报告",
     "sla_first_response_minutes": 240, "sla_resolve_minutes": 4320, "default_assignee_role": "product_ops",
     "auto_reply_template": "感谢您的建议，已记录并转交产品团队评估。", "sort_order": 5},
    {"code": "compliance", "name": "合规/举报", "description": "内容违规、侵权举报",
     "sla_first_response_minutes": 60, "sla_resolve_minutes": 480, "default_assignee_role": "compliance_ops",
     "auto_reply_template": "已收到您的举报，合规团队会在 1 小时内处理。", "sort_order": 6},
    {"code": "other", "name": "其他", "description": "未分类的工单",
     "sla_first_response_minutes": 240, "sla_resolve_minutes": 1440, "default_assignee_role": "support_ops",
     "auto_reply_template": "已收到您的反馈，客服会尽快与您联系。", "sort_order": 99},
]


def _seed(apps, schema_editor):
    TicketCategoryConfig = apps.get_model("operations", "TicketCategoryConfig")
    for cfg in CATEGORIES:
        TicketCategoryConfig.objects.update_or_create(
            code=cfg["code"],
            defaults={
                "name": cfg["name"],
                "description": cfg["description"],
                "sla_first_response_minutes": cfg["sla_first_response_minutes"],
                "sla_resolve_minutes": cfg["sla_resolve_minutes"],
                "default_assignee_role": cfg["default_assignee_role"],
                "auto_reply_template": cfg["auto_reply_template"],
                "is_active": True,
                "sort_order": cfg["sort_order"],
            },
        )


def _rollback(apps, schema_editor):
    TicketCategoryConfig = apps.get_model("operations", "TicketCategoryConfig")
    TicketCategoryConfig.objects.filter(code__in=[c["code"] for c in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0002_ticket_initial"),
    ]

    operations = [
        migrations.RunPython(_seed, _rollback),
    ]
