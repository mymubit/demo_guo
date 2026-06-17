"""A/B 实验模型。

设计要点：
  ① Experiment：实验定义（目标 / 假设 / 指标）
  ② Variant：实验变体（control + 1~n 个 treatment）
  ③ Assignment：用户-实验-变体的稳定分配结果
  ④ ExposureLog：曝光日志（用于按 variant 统计 PV/UV）
  ⑤ ConversionLog：转化日志（用于按 variant 统计 CVR）
  ⑥ Metric：实验指标定义（北极星 / 过程指标）
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.operations.constants import ExperimentBucket, ExperimentStatus


class Experiment(models.Model):
    """A/B 实验。"""

    key = models.SlugField(max_length=64, unique=True, help_text="实验唯一 key（代码层引用）")
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    hypothesis = models.TextField(blank=True, default="", help_text="实验假设：A 比 B 在 X 指标上提升 Y%")
    bucket = models.CharField(
        max_length=16, choices=ExperimentBucket.choices, default=ExperimentBucket.CONFIG,
    )
    status = models.CharField(
        max_length=16, choices=ExperimentStatus.choices, default=ExperimentStatus.DRAFT,
    )
    target_filter = models.JSONField(default=dict, help_text="目标用户：vip_level / register_after / tags")
    traffic_allocation = models.PositiveIntegerField(
        default=100, help_text="实验覆盖流量比例（0-100）",
    )
    salt = models.CharField(max_length=32, default="default", help_text="分流盐：同一 key 不同盐互不影响")
    primary_metric = models.CharField(max_length=64, blank=True, default="")
    secondary_metrics = models.JSONField(default=list, help_text="次要指标列表")
    min_sample_size = models.PositiveIntegerField(default=0, help_text="最小样本量（达到后允许读出显著结论）")
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    conclusion = models.TextField(blank=True, default="", help_text="实验结论 / 复盘")
    winner_variant = models.CharField(max_length=64, blank=True, default="")
    operator = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_experiment"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["bucket", "status"]),
        ]


class Variant(models.Model):
    """实验变体。"""

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="variants")
    key = models.CharField(max_length=64, help_text="变体 key（control/treatment_a/...）")
    name = models.CharField(max_length=64)
    is_control = models.BooleanField(default=False)
    weight = models.PositiveIntegerField(default=50, help_text="权重 0-100")
    payload = models.JSONField(default=dict, help_text="变体配置：技能/参数/价格/文案 等")
    description = models.TextField(blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_experiment_variant"
        unique_together = [("experiment", "key")]
        ordering = ["sort_order", "id"]
        indexes = [models.Index(fields=["experiment", "is_control"])]


class Assignment(models.Model):
    """用户-实验-变体的稳定分配。"""

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="experiment_assignments",
        null=True, blank=True,
    )
    anonymous_id = models.CharField(
        max_length=64, blank=True, default="", help_text="未登录用户用 deviceId/cookie",
    )
    variant_key = models.CharField(max_length=64)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_experiment_assignment"
        unique_together = [("experiment", "user"), ("experiment", "anonymous_id")]
        indexes = [
            models.Index(fields=["experiment", "variant_key"]),
            models.Index(fields=["-assigned_at"]),
        ]


class ExposureLog(models.Model):
    """曝光日志。"""

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="exposures")
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="exposures")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    anonymous_id = models.CharField(max_length=64, blank=True, default="")
    surface = models.CharField(max_length=64, help_text="曝光位置：home / create / pricing / etc.")
    context = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_experiment_exposure"
        indexes = [
            models.Index(fields=["experiment", "variant", "-created_at"]),
            models.Index(fields=["-created_at"]),
        ]


class ConversionLog(models.Model):
    """转化日志。"""

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="conversions")
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="conversions")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    anonymous_id = models.CharField(max_length=64, blank=True, default="")
    metric = models.CharField(max_length=64, help_text="指标 key（与 Experiment.primary_metric 对应）")
    value = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    surface = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_experiment_conversion"
        indexes = [
            models.Index(fields=["experiment", "metric", "-created_at"]),
            models.Index(fields=["variant", "metric", "-created_at"]),
        ]


class ExperimentMetricSnapshot(models.Model):
    """实验指标快照（按日聚合，用于画曲线）。"""

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="metric_snapshots")
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="metric_snapshots")
    metric = models.CharField(max_length=64)
    snapshot_date = models.DateField()
    exposure_count = models.PositiveIntegerField(default=0)
    conversion_count = models.PositiveIntegerField(default=0)
    conversion_value_sum = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    extra = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_experiment_metric_snapshot"
        unique_together = [("experiment", "variant", "metric", "snapshot_date")]
        indexes = [
            models.Index(fields=["experiment", "metric", "snapshot_date"]),
        ]
