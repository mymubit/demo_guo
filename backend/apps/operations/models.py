# -*- coding: utf-8 -*-
"""【运营 M4-M5】运营监控中心模型。

本 app 是「一人运营」场景下的核心 SSOT：
  • CreationFeedback      - 用户主动反馈（功能建议/BUG/咨询/其它）
  • OperationsDailyCache  - 运营 Dashboard 聚合缓存（避免每页请求都重算）

所有模型都使用 UUID 主键；时间字段统一 use_tz=True。
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


# ============================================================
# CreationFeedback - 用户主动反馈
# ============================================================
class CreationFeedback(models.Model):
    """用户主动反馈（功能建议 / BUG / 咨询 / 表扬 / 其它）。

    来自：
      • 工作台 / 作品详情页的反馈入口
      • 运营后台手动录入（来自电话/微信群反馈）
      • 抽样回访：is_quality_sampled=true 的项目，运营可主动回访并录入

    字段：
      category       - 反馈大类（功能建议/BUG/咨询/表扬/其它）
      severity       - 严重程度（一人运营：标记 P0/P1/P2/P3 处理优先级）
      title          - 一句话标题
      content        - 反馈正文
      contact        - 联系方式（手机/微信/邮箱）
      project        - 关联创作项目（可空）
      source         - 提交来源（workspace/portal/admin_import/quality_sample）
      status         - 处理状态（open/in_progress/resolved/wont_fix）
      handler        - 处理人（一人运营时 = 运营本人）
      handled_at     - 处理时间
      handler_note   - 处理备注
      tags           - 标签 JSON 数组（按需扩展）
    """

    class Category(models.TextChoices):
        FEATURE_REQUEST = "feature_request", "功能建议"
        BUG = "bug", "BUG 报告"
        CONSULT = "consult", "使用咨询"
        PRAISE = "praise", "表扬"
        COMPLAINT = "complaint", "投诉"
        OTHER = "other", "其它"

    class Severity(models.TextChoices):
        P0 = "P0", "P0 紧急（影响创作主链路）"
        P1 = "P1", "P1 高（影响 1 个节点）"
        P2 = "P2", "P2 中（体验问题）"
        P3 = "P3", "P3 低（建议性）"

    class Source(models.TextChoices):
        WORKSPACE = "workspace", "工作台"
        PORTAL = "portal", "C 端门户"
        ADMIN_IMPORT = "admin_import", "后台导入"
        QUALITY_SAMPLE = "quality_sample", "运营抽样"
        WECHAT = "wechat", "微信群"
        PHONE = "phone", "电话"

    class Status(models.TextChoices):
        OPEN = "open", "待处理"
        IN_PROGRESS = "in_progress", "处理中"
        RESOLVED = "resolved", "已处理"
        WONT_FIX = "wont_fix", "不处理"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="creation_feedbacks",
        verbose_name="提交人",
    )
    project = models.ForeignKey(
        "creation.Project",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="feedbacks",
        verbose_name="关联项目",
    )

    category = models.CharField(
        "分类", max_length=24, choices=Category.choices, default=Category.FEATURE_REQUEST,
        db_index=True,
    )
    severity = models.CharField(
        "严重程度", max_length=4, choices=Severity.choices, default=Severity.P2, db_index=True,
    )
    source = models.CharField(
        "来源", max_length=24, choices=Source.choices, default=Source.WORKSPACE, db_index=True,
    )
    status = models.CharField(
        "状态", max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True,
    )

    title = models.CharField("标题", max_length=200)
    content = models.TextField("反馈正文", blank=True, default="")
    contact = models.CharField("联系方式", max_length=120, blank=True, default="")
    tags = models.JSONField("标签", default=list, blank=True)

    # 处理信息
    handler = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="handled_creation_feedbacks",
        verbose_name="处理人",
    )
    handled_at = models.DateTimeField("处理时间", null=True, blank=True)
    handler_note = models.TextField("处理备注", blank=True, default="")

    # 抽样标记：与 Project.is_quality_sampled 配合，避免重复回访
    is_from_sample = models.BooleanField("来自抽样", default=False, db_index=True)

    created_at = models.DateTimeField("提交时间", default=timezone.now, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "operations_creation_feedback"
        verbose_name = "用户反馈"
        verbose_name_plural = "用户反馈"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["category", "-created_at"]),
            models.Index(fields=["severity", "status"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"[{self.get_severity_display()}] {self.title}"


# ============================================================
# OperationsDailyCache - 运营 Dashboard 聚合缓存
# ============================================================
class OperationsDailyCache(models.Model):
    """运营 Dashboard 聚合缓存（按天分桶，避免冷启动时全表扫描）。

    每天凌晨由 management command 预计算，写入当天的 bucket；
    Dashboard 读取时取「最新 bucket + 今日实时累计」。
    """

    class MetricType(models.TextChoices):
        DASHBOARD = "dashboard", "总 Dashboard"
        CONTENT_QUALITY = "content_quality", "内容质量"
        FEEDBACK = "feedback", "反馈汇总"
        CONFIG_HIT = "config_hit", "配置命中率"
        FUNNEL = "funnel", "用户漏斗"

    id = models.BigAutoField(primary_key=True)
    cache_date = models.DateField("缓存日期", db_index=True)
    metric_type = models.CharField("指标类型", max_length=32, choices=MetricType.choices, db_index=True)
    payload = models.JSONField("聚合数据", default=dict, blank=True)
    extra = models.JSONField("扩展", default=dict, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "operations_daily_cache"
        verbose_name = "运营聚合缓存"
        verbose_name_plural = "运营聚合缓存"
        ordering = ["-cache_date", "metric_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["cache_date", "metric_type"],
                name="uniq_ops_daily_cache",
            ),
        ]
        indexes = [
            models.Index(fields=["metric_type", "-cache_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.cache_date} · {self.metric_type}"


# ============================================================
# UserBehaviorEvent - 用户行为埋点（6 个核心事件）
# ============================================================
class UserBehaviorEvent(models.Model):
    """用户行为埋点（一人运营场景下的 6 个核心事件）。

    6 个核心事件（C 端主链路上的关键节点）：
      1. landing_view           - 用户进入落地页
      2. creation_form_open     - 打开创作表单
      3. creation_submitted     - 提交创作
      4. node_edited            - 编辑工作台节点
      5. script_exported        - 导出最终剧本
      6. share_link_generated   - 生成分享链接

    数据源：
      • 前端 trackEvent 工具主动上报
      • 后端关键业务路径自动写入（如 creation_submitted、script_exported）

    字段：
      event_name  - 事件名（6 个核心值之一）
      source      - 上报端（frontend / backend）
      user        - 关联用户（可空：未登录访问也算）
      session_id  - 前端会话 ID（前端 generate）
      project_id  - 关联项目（可空）
      page        - 当前页面/路由
      payload     - 扩展 JSON
    """

    class EventName(models.TextChoices):
        LANDING_VIEW = "landing_view", "落地页访问"
        CREATION_FORM_OPEN = "creation_form_open", "打开创作表单"
        CREATION_SUBMITTED = "creation_submitted", "提交创作"
        NODE_EDITED = "node_edited", "编辑节点"
        SCRIPT_EXPORTED = "script_exported", "导出剧本"
        SHARE_LINK_GENERATED = "share_link_generated", "生成分享链接"

    class Source(models.TextChoices):
        FRONTEND = "frontend", "前端"
        BACKEND = "backend", "后端"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_name = models.CharField(
        "事件名", max_length=48, choices=EventName.choices, db_index=True,
    )
    source = models.CharField(
        "来源", max_length=16, choices=Source.choices, default=Source.FRONTEND, db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="behavior_events",
        verbose_name="用户",
    )
    session_id = models.CharField("会话ID", max_length=64, blank=True, default="", db_index=True)
    project_id = models.CharField("项目ID", max_length=64, blank=True, default="", db_index=True)
    page = models.CharField("页面/路由", max_length=200, blank=True, default="")
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("User-Agent", max_length=512, blank=True, default="")
    payload = models.JSONField("载荷", default=dict, blank=True)
    created_at = models.DateTimeField("发生时间", default=timezone.now, db_index=True)

    class Meta:
        db_table = "operations_user_behavior_event"
        verbose_name = "用户行为事件"
        verbose_name_plural = "用户行为事件"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_name", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["session_id", "-created_at"]),
            models.Index(fields=["project_id", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_name} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
