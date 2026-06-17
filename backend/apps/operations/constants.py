"""运营中心常量（精简版）。

个人站只保留：活动 / 卡券 / 工单 / 敏感词 4 类枚举。
"""
from __future__ import annotations

from django.db import models


class CampaignStatus(models.TextChoices):
    DRAFT = "draft", "草稿"
    RUNNING = "running", "进行中"
    PAUSED = "paused", "已暂停"
    ENDED = "ended", "已结束"


class CouponType(models.TextChoices):
    COIN = "coin", "创作币"
    TRIAL = "trial", "会员试用"
    DISCOUNT = "discount", "折扣"


class TicketStatus(models.TextChoices):
    OPEN = "open", "待处理"
    REPLIED = "replied", "已回复"
    CLOSED = "closed", "已关闭"


class TicketPriority(models.TextChoices):
    P0 = "P0", "紧急"
    P1 = "P1", "高"
    P2 = "P2", "中"
    P3 = "P3", "低"
