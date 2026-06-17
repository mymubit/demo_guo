"""A/B 实验服务层。

核心能力：
  ① 稳定分流：基于 user_id 或 anonymous_id + experiment.salt 做哈希
  ② 变体加权随机
  ③ 流量分桶（traffic_allocation 决定是否进入实验）
  ④ 效果对比：曝光/转化/显著性
"""
from __future__ import annotations

import hashlib
import logging
import math
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.utils import timezone

from apps.operations.constants import ExperimentStatus
from apps.operations.exceptions import (
    ExperimentError,
    ExperimentNotRunning,
    ExperimentTrafficInvalid,
    OperationsError,
)

from .models import (
    Assignment,
    ConversionLog,
    Experiment,
    ExperimentMetricSnapshot,
    ExposureLog,
    Variant,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 状态机
# ──────────────────────────────────────────────
def start_experiment(experiment: Experiment, operator: str = "") -> Experiment:
    if experiment.status != ExperimentStatus.DRAFT:
        raise ExperimentError("只有草稿状态可以启动")
    if not experiment.variants.filter(is_control=True).exists():
        raise ExperimentError("实验必须包含至少一个 control 变体")
    total_weight = sum(v.weight for v in experiment.variants.all())
    if total_weight <= 0:
        raise ExperimentTrafficInvalid("变体总权重必须大于 0")
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = timezone.now()
    experiment.operator = operator
    experiment.save(update_fields=["status", "started_at", "operator", "updated_at"])
    return experiment


def pause_experiment(experiment: Experiment, operator: str = "") -> Experiment:
    if experiment.status != ExperimentStatus.RUNNING:
        raise ExperimentError("只有进行中状态可以暂停")
    experiment.status = ExperimentStatus.PAUSED
    experiment.operator = operator
    experiment.save(update_fields=["status", "operator", "updated_at"])
    return experiment


def conclude_experiment(
    experiment: Experiment,
    *,
    winner_variant_key: str = "",
    conclusion: str = "",
    operator: str = "",
) -> Experiment:
    if experiment.status not in (ExperimentStatus.RUNNING, ExperimentStatus.PAUSED):
        raise ExperimentError("只有进行中或暂停状态可以结束")
    experiment.status = ExperimentStatus.CONCLUDED
    experiment.ended_at = timezone.now()
    experiment.winner_variant = winner_variant_key
    experiment.conclusion = conclusion
    experiment.operator = operator
    experiment.save(update_fields=[
        "status", "ended_at", "winner_variant", "conclusion", "operator", "updated_at",
    ])
    return experiment


# ──────────────────────────────────────────────
# 分流算法
# ──────────────────────────────────────────────
def _stable_hash(experiment_key: str, salt: str, subject_id: str) -> int:
    """稳定哈希：相同输入永远返回相同 0-9999 的桶号。"""
    raw = f"{experiment_key}:{salt}:{subject_id}"
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 10000


def assign_variant(
    experiment: Experiment,
    *,
    user=None,
    anonymous_id: str = "",
) -> Variant | None:
    """为用户分配变体；返回 None 表示未进入实验。"""
    if experiment.status != ExperimentStatus.RUNNING:
        return None

    subject_id = ""
    if user and getattr(user, "id", None):
        subject_id = f"u{user.id}"
    elif anonymous_id:
        subject_id = f"a{anonymous_id}"
    else:
        return None  # 无身份不进入实验

    # 是否进入实验（traffic_allocation）
    bucket = _stable_hash(experiment.key, experiment.salt, f"ta:{subject_id}")
    if bucket >= experiment.traffic_allocation * 100:  # 0-10000
        return None

    # 已有分配 → 直接返回（保证稳定）
    if user and user.id:
        existing = Assignment.objects.filter(experiment=experiment, user=user).first()
        if existing:
            return experiment.variants.filter(key=existing.variant_key).first()
    if anonymous_id:
        existing = Assignment.objects.filter(
            experiment=experiment, anonymous_id=anonymous_id,
        ).first()
        if existing:
            return experiment.variants.filter(key=existing.variant_key).first()

    # 重新分配
    variant_bucket = _stable_hash(experiment.key, experiment.salt, f"var:{subject_id}") % 100
    cumulative = 0
    chosen = None
    for v in experiment.variants.all().order_by("sort_order", "id"):
        if v.weight <= 0:
            continue
        cumulative += v.weight
        if variant_bucket < cumulative:
            chosen = v
            break
    if chosen is None:
        chosen = experiment.variants.filter(is_control=True).first()
    if chosen is None:
        return None

    # 持久化分配
    Assignment.objects.create(
        experiment=experiment, user=user, anonymous_id=anonymous_id,
        variant_key=chosen.key,
    )
    return chosen


# ──────────────────────────────────────────────
# 曝光 / 转化埋点
# ──────────────────────────────────────────────
def log_exposure(
    *,
    experiment_key: str,
    variant_key: str,
    user=None,
    anonymous_id: str = "",
    surface: str = "",
    context: dict | None = None,
) -> bool:
    """记录一次曝光（按 dedup 由调用方控制）。"""
    try:
        exp = Experiment.objects.get(key=experiment_key)
    except Experiment.DoesNotExist:
        return False
    var = exp.variants.filter(key=variant_key).first()
    if var is None:
        return False
    ExposureLog.objects.create(
        experiment=exp, variant=var, user=user, anonymous_id=anonymous_id,
        surface=surface[:64], context=context or {},
    )
    return True


def log_conversion(
    *,
    experiment_key: str,
    variant_key: str,
    metric: str,
    value: float = 1.0,
    user=None,
    anonymous_id: str = "",
    surface: str = "",
) -> bool:
    try:
        exp = Experiment.objects.get(key=experiment_key)
    except Experiment.DoesNotExist:
        return False
    var = exp.variants.filter(key=variant_key).first()
    if var is None:
        return False
    ConversionLog.objects.create(
        experiment=exp, variant=var, user=user, anonymous_id=anonymous_id,
        metric=metric[:64], value=value, surface=surface[:64],
    )
    return True


# ──────────────────────────────────────────────
# 效果分析
# ──────────────────────────────────────────────
def analyze_experiment(experiment: Experiment) -> dict:
    """实验效果分析：每个变体的曝光/转化/CVR/显著性。"""
    variants = list(experiment.variants.all().order_by("sort_order", "id"))
    exposures = dict(
        ExposureLog.objects.filter(experiment=experiment)
        .values_list("variant__key").annotate(c=Count("id")).values_list("variant__key", "c")
    )
    conversions = dict(
        ConversionLog.objects.filter(experiment=experiment)
        .values_list("variant__key").annotate(c=Count("id")).values_list("variant__key", "c")
    )
    rows = []
    control = next((v for v in variants if v.is_control), variants[0] if variants else None)
    for v in variants:
        uv = exposures.get(v.key, 0)
        cv = conversions.get(v.key, 0)
        cvr = (cv / uv) if uv else 0.0
        row = {
            "variant_key": v.key,
            "variant_name": v.name,
            "is_control": v.is_control,
            "weight": v.weight,
            "exposures": uv,
            "conversions": cv,
            "cvr": round(cvr, 6),
        }
        if control and v.id != control.id and control.key in exposures and v.key in exposures:
            control_cvr = (conversions.get(control.key, 0) / exposures.get(control.key, 1)) if exposures.get(control.key) else 0
            lift = ((cvr - control_cvr) / control_cvr) if control_cvr else 0
            p_value = _two_proportion_p(
                n1=exposures.get(control.key, 0), x1=conversions.get(control.key, 0),
                n2=exposures.get(v.key, 0), x2=conversions.get(v.key, 0),
            )
            row["lift"] = round(lift, 6)
            row["p_value"] = round(p_value, 6) if p_value is not None else None
            row["significant"] = (p_value is not None and p_value < 0.05)
        else:
            row["lift"] = 0
            row["p_value"] = None
            row["significant"] = False
        rows.append(row)
    return {
        "experiment": {
            "id": experiment.id,
            "key": experiment.key,
            "name": experiment.name,
            "status": experiment.status,
            "started_at": experiment.started_at,
            "ended_at": experiment.ended_at,
        },
        "variants": rows,
    }


def _two_proportion_p(n1: int, x1: int, n2: int, x2: int) -> float | None:
    """双比例 Z 检验 p-value。"""
    if n1 <= 0 or n2 <= 0:
        return None
    p1 = x1 / n1
    p2 = x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    if p_pool in (0, 1):
        return None
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return None
    z = (p2 - p1) / se
    # 正态分布 CDF（简化版）
    from math import erf, sqrt

    cdf = 0.5 * (1 + erf(abs(z) / sqrt(2)))
    p_value = 2 * (1 - cdf)
    return max(0.0, min(1.0, p_value))


def build_daily_snapshot(experiment_id: int) -> int:
    """每日聚合（定时任务调用）。"""
    exp = Experiment.objects.get(id=experiment_id)
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    rows = 0
    for variant in exp.variants.all():
        exposures = ExposureLog.objects.filter(
            experiment=exp, variant=variant, created_at__date=yesterday,
        ).count()
        convs = ConversionLog.objects.filter(
            experiment=exp, variant=variant, created_at__date=yesterday,
        )
        conv_count = convs.count()
        conv_sum = convs.aggregate(s=Sum("value"))["s"] or 0
        # 这里按主指标聚合（每个实验一个主指标）；简化处理 = 全 metric
        for metric in {experiment_primary_metric(exp), *exp.secondary_metrics}:
            ExperimentMetricSnapshot.objects.update_or_create(
                experiment=exp, variant=variant, metric=metric, snapshot_date=yesterday,
                defaults={
                    "exposure_count": exposures,
                    "conversion_count": conv_count,
                    "conversion_value_sum": conv_sum,
                },
            )
            rows += 1
    return rows


def experiment_primary_metric(exp: Experiment) -> str:
    return exp.primary_metric or "primary"
