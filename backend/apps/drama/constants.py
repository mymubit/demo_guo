# -*- coding: utf-8 -*-
"""Drama 工作台枚举常量（原 DramaProject 内嵌 Choices）。"""
from django.db import models


class DramaTrackMode(models.TextChoices):
    FAST = "fast", "快速通道（8核心角色）"
    EXPERT = "expert", "专家通道（12角色）"


class DramaStage(models.TextChoices):
    STRATEGY = "strategy", "战略选题"
    WORLDBUILDING = "worldbuilding", "世界构建"
    PLOT_DESIGN = "plot_design", "剧情设计"
    WRITING = "writing", "剧本创作"
    REVIEW = "review", "评审质控"
    POLISH = "polish", "修改润色"
    PRODUCTION = "production", "制作宣发"
    COMPLIANCE = "compliance", "合规审查"
    DELIVERED = "delivered", "已交付"


DRAMA_DELIVERY_STATUS_CHOICES = [
    ("pending", "待交付"),
    ("ready", "可交付"),
    ("delivered", "已交付"),
]
