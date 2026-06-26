# -*- coding: utf-8 -*-
"""Drama 工作台枚举常量（原 DramaProject 内嵌 Choices）。"""
from django.db import models


class DramaTrackMode(models.TextChoices):
    FAST = "fast", "标准创作通道（6生产+2裁判）"
    EXPERT = "expert", "专家通道（追加宣发交付）"


class DramaStage(models.TextChoices):
    STRATEGY = "strategy", "选题定调"
    WORLDBUILDING = "worldbuilding", "人物关系"
    PLOT_DESIGN = "plot_design", "全剧架构"
    EPISODE_DESIGN = "episode_design", "分集设计"
    WRITING = "writing", "正文创作"
    REVIEW = "review", "独立评分"
    POLISH = "polish", "返修精修"
    PRODUCTION = "production", "宣发交付"
    COMPLIANCE = "compliance", "合规审查"
    DELIVERED = "delivered", "已交付"


DRAMA_DELIVERY_STATUS_CHOICES = [
    ("pending", "待交付"),
    ("ready", "可交付"),
    ("delivered", "已交付"),
]
