"""运营中心常量。"""
from __future__ import annotations

from django.db import models


# ──────────────────────────────────────────────
# 角色 / 权限
# ──────────────────────────────────────────────
ROLE_CONTENT_OPS = "content_ops"          # 内容运营
ROLE_GROWTH_OPS = "growth_ops"            # 增长运营
ROLE_COMMERCE_OPS = "commerce_ops"        # 商业化运营
ROLE_SKILL_OPS = "skill_ops"              # 技能运营
ROLE_SUPPORT_OPS = "support_ops"          # 客服
ROLE_DATA_OPS = "data_ops"                # 数据分析
ROLE_SUPER = "super_ops"                  # 运营总监

OPS_ROLES = (
    ROLE_CONTENT_OPS,
    ROLE_GROWTH_OPS,
    ROLE_COMMERCE_OPS,
    ROLE_SKILL_OPS,
    ROLE_SUPPORT_OPS,
    ROLE_DATA_OPS,
    ROLE_SUPER,
)


# ──────────────────────────────────────────────
# 活动 / 卡券
# ──────────────────────────────────────────────
class CampaignType(models.TextChoices):
    NEW_USER = "new_user", "拉新活动"
    RETENTION = "retention", "留存活动"
    CONVERSION = "conversion", "付费转化"
    BRAND = "brand", "品牌活动"
    LIMITED = "limited", "限时活动"
    INTERNAL = "internal", "内部活动"


class CampaignStatus(models.TextChoices):
    DRAFT = "draft", "草稿"
    SCHEDULED = "scheduled", "待生效"
    RUNNING = "running", "进行中"
    PAUSED = "paused", "已暂停"
    ENDED = "ended", "已结束"
    ARCHIVED = "archived", "已归档"


class CouponType(models.TextChoices):
    COIN = "coin", "创作币"
    TOKEN = "token", "Token"
    DISCOUNT = "discount", "折扣"
    TRIAL = "trial", "会员试用"
    FEATURE = "feature", "权益赠送"
    PHYSICAL = "physical", "实物（占位）"


class CouponStatus(models.TextChoices):
    ACTIVE = "active", "可领取"
    PAUSED = "paused", "暂停发放"
    EXHAUSTED = "exhausted", "已发完"
    EXPIRED = "expired", "已过期"


class RedemptionCodeStatus(models.TextChoices):
    UNCLAIMED = "unclaimed", "未领取"
    CLAIMED = "claimed", "已领取"
    EXPIRED = "expired", "已过期"
    DISABLED = "disabled", "已作废"


# ──────────────────────────────────────────────
# 工单
# ──────────────────────────────────────────────
class TicketCategory(models.TextChoices):
    BILLING = "billing", "计费/支付"
    SKILL_ISSUE = "skill_issue", "技能/创作异常"
    CONTENT_ISSUE = "content_issue", "内容质量"
    ACCOUNT = "account", "账号问题"
    SUGGESTION = "suggestion", "建议反馈"
    COMPLIANCE = "compliance", "合规/举报"
    OTHER = "other", "其他"


class TicketStatus(models.TextChoices):
    PENDING = "pending", "待受理"
    PROCESSING = "processing", "处理中"
    WAITING_USER = "waiting_user", "等待用户"
    RESOLVED = "resolved", "已解决"
    CLOSED = "closed", "已关闭"
    REJECTED = "rejected", "已驳回"


class TicketPriority(models.TextChoices):
    P0 = "P0", "紧急"
    P1 = "P1", "高"
    P2 = "P2", "中"
    P3 = "P3", "低"


# ──────────────────────────────────────────────
# 实验
# ──────────────────────────────────────────────
class ExperimentStatus(models.TextChoices):
    DRAFT = "draft", "草稿"
    RUNNING = "running", "进行中"
    PAUSED = "paused", "暂停"
    CONCLUDED = "concluded", "已结束"
    ABANDONED = "abandoned", "废弃"


class ExperimentBucket(models.TextChoices):
    SKILL = "skill", "技能"
    PIPELINE = "pipeline", "工作流"
    CONFIG = "config", "配置项"
    COPY = "copy", "文案"
    PRICING = "pricing", "定价"


# ──────────────────────────────────────────────
# 模板沉淀 / UGC
# ──────────────────────────────────────────────
class TemplatePromotionStatus(models.TextChoices):
    CANDIDATE = "candidate", "候选"
    REVIEWING = "reviewing", "审核中"
    APPROVED = "approved", "已通过"
    PUBLISHED = "published", "已上架"
    REJECTED = "rejected", "已驳回"
    ARCHIVED = "archived", "已归档"


class UgcTemplateStatus(models.TextChoices):
    DRAFT = "draft", "草稿"
    PENDING = "pending", "待审核"
    PUBLISHED = "published", "已发布"
    REJECTED = "rejected", "已驳回"
    OFFLINE = "offline", "已下架"


# ──────────────────────────────────────────────
# 创作者激励
# ──────────────────────────────────────────────
class PointsReason(models.TextChoices):
    PROJECT_COMPLETED = "project_completed", "完成项目"
    SCRIPT_ADOPTED = "script_adopted", "剧本被采纳"
    TEMPLATE_USED = "template_used", "模板被使用"
    TEMPLATE_RATED = "template_rated", "模板被评分"
    DAILY_LOGIN = "daily_login", "每日登录"
    SHARE = "share", "分享"
    EXCHANGE = "exchange", "兑换消耗"
    ADMIN_ADJUST = "admin_adjust", "运营调整"


# ──────────────────────────────────────────────
# 合规
# ──────────────────────────────────────────────
class ComplianceLevel(models.TextChoices):
    P0 = "P0", "硬熔断"
    P1 = "P1", "提示告警"
    P2 = "P2", "仅记录"


class ComplianceCategory(models.TextChoices):
    SENSITIVE_WORD = "sensitive_word", "敏感词"
    TOPIC_RISK = "topic_risk", "题材风险"
    IP_RISK = "ip_risk", "IP 侵权"
    POLITICS = "politics", "政治安全"
    VIOLENCE = "violence", "暴力血腥"
    ADULT = "adult", "成人内容"
    OTHER = "other", "其他"
