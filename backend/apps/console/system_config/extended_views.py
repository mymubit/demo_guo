# -*- coding: utf-8 -*-
"""
系统配置中心扩展 API

补充 system/configs/ 之外的：
- 全局开关批量管理
- 阈值配置快速调整
- 配额规则
- 敏感词规则
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok
from apps.system_config.audit import write_audit_log
from apps.system_config.cache import invalidate_config
from apps.system_config.models import (
    SensitiveWord,
    SystemConfigAuditLog,
    SystemConfigItem,
)
from apps.system_config.services import SystemConfigService

logger = logging.getLogger(__name__)


# ============================================================
# 1) 全局开关批量管理
# ============================================================

GLOBAL_SWITCH_KEYS = [
    "creation.enabled",          # 创作功能总开关
    "creation.theme_enabled",    # 题材模板启用
    "creation.pipeline_enabled", # 流水线启用
    "llm.provider.openai",       # Provider 启停示例 key（按 vendor）
    "llm.provider.volcano",
    "llm.provider.deepseek",
]


class GlobalSwitchView(APIView):
    """GET /api/admin/system/global-switch/ — 全局开关

    GET：返回所有 GLOBAL_SWITCH_KEYS 的当前值（含不存在项的默认值 false）
    PUT：批量更新多个开关
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            items = (
                SystemConfigItem.objects.select_related("category")
                .filter(config_key__in=GLOBAL_SWITCH_KEYS, deleted_at__isnull=True)
            )
            value_map = {item.config_key: bool(item.effective_value) for item in items}

            data = []
            for key in GLOBAL_SWITCH_KEYS:
                data.append(
                    {
                        "config_key": key,
                        "enabled": value_map.get(key, False),
                    }
                )
            return api_ok({"items": data})
        except Exception as exc:  # noqa: BLE001
            logger.warning("GlobalSwitchView.get 失败: %s", exc)
            return api_ok({"items": []})

    def put(self, request):
        try:
            updates = request.data.get("items") or request.data.get("updates") or []
            if not isinstance(updates, list):
                return api_fail("items 必须是数组")

            valid_keys = set(GLOBAL_SWITCH_KEYS)
            results: List[Dict[str, Any]] = []
            now = timezone.now()
            change_reason = (request.data.get("change_reason") or "").strip()

            with transaction.atomic():
                for entry in updates:
                    if not isinstance(entry, dict):
                        continue
                    key = str(entry.get("config_key") or "").strip()
                    if key not in valid_keys:
                        results.append(
                            {"config_key": key, "success": False, "message": "非法的配置键"}
                        )
                        continue
                    enabled = bool(entry.get("enabled", False))

                    item = SystemConfigService.get_item(key)
                    if not item:
                        results.append(
                            {"config_key": key, "success": False, "message": "配置项不存在"}
                        )
                        continue
                    old_value = item.effective_value
                    item.value = enabled
                    item.version += 1
                    if getattr(request.user, "is_authenticated", False):
                        item.updated_by = request.user
                    item.save(update_fields=["value", "version", "updated_by", "updated_at"])
                    invalidate_config(item.config_key, item.category.code)
                    write_audit_log(
                        config=item,
                        config_key=item.config_key,
                        action=SystemConfigAuditLog.Action.UPDATE,
                        old_value=old_value,
                        new_value=enabled,
                        request=request,
                        change_reason=change_reason or "后台全局开关调整",
                    )
                    results.append(
                        {"config_key": key, "success": True, "enabled": enabled}
                    )

            success_count = sum(1 for r in results if r.get("success"))
            return api_ok(
                {
                    "updated": success_count,
                    "items": results,
                },
                message=f"已更新 {success_count} 个开关",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("GlobalSwitchView.put 失败: %s", exc)
            return api_fail(f"更新失败: {exc}", code=500)


# ============================================================
# 2) 阈值配置（评分线/失败率告警/超时）
# ============================================================

THRESHOLD_KEYS = [
    {
        "config_key": "creation.quality.pass_threshold",
        "name": "质量评分通过线",
        "unit": "分",
        "default": 70,
        "min": 0,
        "max": 100,
        "value_type": "int",
    },
    {
        "config_key": "monitoring.failure_alert_threshold",
        "name": "失败率告警阈值",
        "unit": "%",
        "default": 5.0,
        "min": 0,
        "max": 100,
        "value_type": "float",
    },
    {
        "config_key": "creation.node_timeout_default",
        "name": "节点超时阈值",
        "unit": "秒",
        "default": 600,
        "min": 1,
        "max": 7200,
        "value_type": "int",
    },
    {
        "config_key": "creation.retry_max_attempts_default",
        "name": "节点默认重试次数",
        "unit": "次",
        "default": 2,
        "min": 0,
        "max": 10,
        "value_type": "int",
    },
]


def _collect_threshold_payload(items: Iterable[SystemConfigItem]) -> Dict[str, Any]:
    """把配置项收敛为 {key: {label, value, unit, default, min, max, value_type}}。"""
    by_key = {item.config_key: item for item in items}
    payload: Dict[str, Any] = {}
    for spec in THRESHOLD_KEYS:
        item = by_key.get(spec["config_key"])
        value = item.effective_value if item else None
        if value is None:
            value = spec["default"]
        # 类型兜底
        if spec["value_type"] == "int":
            try:
                value = int(value)
            except (TypeError, ValueError):
                value = spec["default"]
        elif spec["value_type"] == "float":
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = spec["default"]
        payload[spec["config_key"]] = {
            "name": spec["name"],
            "value": value,
            "unit": spec["unit"],
            "default": spec["default"],
            "min": spec.get("min"),
            "max": spec.get("max"),
            "value_type": spec["value_type"],
            "exists": item is not None,
        }
    return payload


class ThresholdConfigView(APIView):
    """GET /api/admin/system/thresholds/ — 阈值配置

    涉及的 key:
      - creation.quality.pass_threshold (默认 70)
      - monitoring.failure_alert_threshold (默认 5.0)
      - creation.node_timeout_default (默认 600)
      - creation.retry_max_attempts_default (默认 2)
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            items = SystemConfigItem.objects.filter(
                config_key__in=[s["config_key"] for s in THRESHOLD_KEYS],
                deleted_at__isnull=True,
            )
            return api_ok(_collect_threshold_payload(items))
        except Exception as exc:  # noqa: BLE001
            logger.warning("ThresholdConfigView.get 失败: %s", exc)
            return api_ok({})

    def put(self, request):
        try:
            updates = request.data.get("items") or {}
            if not isinstance(updates, dict):
                return api_fail("items 必须是对象（key -> value）")
            change_reason = (request.data.get("change_reason") or "").strip()

            spec_by_key = {s["config_key"]: s for s in THRESHOLD_KEYS}
            results: List[Dict[str, Any]] = []

            with transaction.atomic():
                for key, raw_value in updates.items():
                    if key not in spec_by_key:
                        results.append({"config_key": key, "success": False, "message": "非法的配置键"})
                        continue
                    spec = spec_by_key[key]
                    # 类型校验 + 范围校验
                    try:
                        if spec["value_type"] == "int":
                            value = int(raw_value)
                        elif spec["value_type"] == "float":
                            value = float(raw_value)
                        else:
                            value = raw_value
                    except (TypeError, ValueError):
                        results.append({"config_key": key, "success": False, "message": "值类型不匹配"})
                        continue
                    if spec.get("min") is not None and value < spec["min"]:
                        results.append({"config_key": key, "success": False, "message": f"值不能小于 {spec['min']}"})
                        continue
                    if spec.get("max") is not None and value > spec["max"]:
                        results.append({"config_key": key, "success": False, "message": f"值不能大于 {spec['max']}"})
                        continue

                    item = SystemConfigService.get_item(key)
                    if not item:
                        results.append({"config_key": key, "success": False, "message": "配置项不存在"})
                        continue
                    old_value = item.effective_value
                    item.value = value
                    item.version += 1
                    if getattr(request.user, "is_authenticated", False):
                        item.updated_by = request.user
                    item.save(update_fields=["value", "version", "updated_by", "updated_at"])
                    invalidate_config(item.config_key, item.category.code)
                    write_audit_log(
                        config=item,
                        config_key=item.config_key,
                        action=SystemConfigAuditLog.Action.UPDATE,
                        old_value=old_value,
                        new_value=value,
                        request=request,
                        change_reason=change_reason or "后台阈值调整",
                    )
                    results.append({"config_key": key, "success": True, "value": value})

            success_count = sum(1 for r in results if r.get("success"))
            return api_ok(
                {
                    "updated": success_count,
                    "items": results,
                },
                message=f"已更新 {success_count} 项阈值",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("ThresholdConfigView.put 失败: %s", exc)
            return api_fail(f"更新失败: {exc}", code=500)


# ============================================================
# 3) 配额规则
# ============================================================

QUOTA_KEYS = [
    {
        "config_key": "billing.default_node_coin_cost",
        "name": "默认节点币价",
        "unit": "币/次",
        "default": 10,
        "min": 0,
        "max": 100000,
        "value_type": "int",
    },
    {
        "config_key": "membership.free_quota_monthly",
        "name": "会员免费额度（月）",
        "unit": "次",
        "default": 5,
        "min": 0,
        "max": 10000,
        "value_type": "int",
    },
    {
        "config_key": "membership.vip_extra_quota",
        "name": "VIP 额外配额",
        "unit": "次",
        "default": 20,
        "min": 0,
        "max": 100000,
        "value_type": "int",
    },
]


def _collect_quota_payload(items: Iterable[SystemConfigItem]) -> Dict[str, Any]:
    by_key = {item.config_key: item for item in items}
    payload: Dict[str, Any] = {}
    for spec in QUOTA_KEYS:
        item = by_key.get(spec["config_key"])
        value = item.effective_value if item else None
        if value is None:
            value = spec["default"]
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = spec["default"]
        payload[spec["config_key"]] = {
            "name": spec["name"],
            "value": value,
            "unit": spec["unit"],
            "default": spec["default"],
            "min": spec.get("min"),
            "max": spec.get("max"),
            "value_type": spec["value_type"],
            "exists": item is not None,
        }
    return payload


class QuotaRulesView(APIView):
    """GET /api/admin/system/quota-rules/ — 配额规则

    涉及的 key:
      - billing.default_node_coin_cost
      - membership.free_quota_monthly
      - membership.vip_extra_quota
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            items = SystemConfigItem.objects.filter(
                config_key__in=[s["config_key"] for s in QUOTA_KEYS],
                deleted_at__isnull=True,
            )
            return api_ok(_collect_quota_payload(items))
        except Exception as exc:  # noqa: BLE001
            logger.warning("QuotaRulesView.get 失败: %s", exc)
            return api_ok({})

    def put(self, request):
        try:
            updates = request.data.get("items") or {}
            if not isinstance(updates, dict):
                return api_fail("items 必须是对象（key -> value）")
            change_reason = (request.data.get("change_reason") or "").strip()

            spec_by_key = {s["config_key"]: s for s in QUOTA_KEYS}
            results: List[Dict[str, Any]] = []

            with transaction.atomic():
                for key, raw_value in updates.items():
                    if key not in spec_by_key:
                        results.append({"config_key": key, "success": False, "message": "非法的配置键"})
                        continue
                    spec = spec_by_key[key]
                    try:
                        value = int(raw_value)
                    except (TypeError, ValueError):
                        results.append({"config_key": key, "success": False, "message": "值必须为整数"})
                        continue
                    if spec.get("min") is not None and value < spec["min"]:
                        results.append({"config_key": key, "success": False, "message": f"值不能小于 {spec['min']}"})
                        continue
                    if spec.get("max") is not None and value > spec["max"]:
                        results.append({"config_key": key, "success": False, "message": f"值不能大于 {spec['max']}"})
                        continue

                    item = SystemConfigService.get_item(key)
                    if not item:
                        results.append({"config_key": key, "success": False, "message": "配置项不存在"})
                        continue
                    old_value = item.effective_value
                    item.value = value
                    item.version += 1
                    if getattr(request.user, "is_authenticated", False):
                        item.updated_by = request.user
                    item.save(update_fields=["value", "version", "updated_by", "updated_at"])
                    invalidate_config(item.config_key, item.category.code)
                    write_audit_log(
                        config=item,
                        config_key=item.config_key,
                        action=SystemConfigAuditLog.Action.UPDATE,
                        old_value=old_value,
                        new_value=value,
                        request=request,
                        change_reason=change_reason or "后台配额调整",
                    )
                    results.append({"config_key": key, "success": True, "value": value})

            success_count = sum(1 for r in results if r.get("success"))
            return api_ok(
                {
                    "updated": success_count,
                    "items": results,
                },
                message=f"已更新 {success_count} 项配额",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("QuotaRulesView.put 失败: %s", exc)
            return api_fail(f"更新失败: {exc}", code=500)


# ============================================================
# 4) 敏感词管理
# ============================================================

def _normalize_word(raw: str) -> str:
    return str(raw or "").strip()


class SensitiveWordsView(APIView):
    """GET/POST /api/admin/system/sensitive-words/ — 敏感词管理

    GET  query: keyword, severity, category, page, page_size
    POST body  : { words: ["abc", ...], severity, category, note }
                 append-only 批量导入；去重（已存在的 word 会被跳过）。
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            keyword = (request.query_params.get("keyword") or "").strip()
            severity = (request.query_params.get("severity") or "").strip()
            category = (request.query_params.get("category") or "").strip()

            qs = SensitiveWord.objects.all()
            if keyword:
                qs = qs.filter(Q(word__icontains=keyword) | Q(note__icontains=keyword))
            if severity:
                qs = qs.filter(severity=severity)
            if category:
                qs = qs.filter(category=category)

            qs = qs.order_by("-created_at")

            paginator = StandardPagination()
            page = paginator.paginate_queryset(qs, request)
            items = [
                {
                    "id": str(row.id),
                    "word": row.word,
                    "category": row.category,
                    "severity": row.severity,
                    "severity_display": row.get_severity_display(),
                    "note": row.note,
                    "created_by": getattr(row.created_by, "nickname", "") if row.created_by else "",
                    "created_at": row.created_at,
                }
                for row in page
            ]
            return paginator.get_paginated_response(items)
        except Exception as exc:  # noqa: BLE001
            logger.exception("SensitiveWordsView.get 失败: %s", exc)
            return api_fail(f"加载失败: {exc}", code=500)

    def post(self, request):
        try:
            words = request.data.get("words") or request.data.get("items") or []
            if isinstance(words, str):
                # 兼容多行文本
                words = [line for line in words.splitlines() if line.strip()]
            if not isinstance(words, list):
                return api_fail("words 必须是数组或字符串")
            severity = str(request.data.get("severity") or SensitiveWord.SEVERITY_MEDIUM)
            category = str(request.data.get("category") or "").strip()
            note = str(request.data.get("note") or "").strip()

            if severity not in dict(SensitiveWord.SEVERITY_CHOICES):
                return api_fail(f"非法 severity: {severity}")

            normalized: List[str] = []
            seen = set()
            for raw in words:
                word = _normalize_word(raw)
                if not word or word in seen:
                    continue
                if len(word) > 128:
                    return api_fail(f"敏感词长度超过 128 字符: {word[:32]}…")
                seen.add(word)
                normalized.append(word)

            if not normalized:
                return api_ok(
                    {"created": 0, "skipped": 0, "items": []},
                    message="没有新增敏感词（可能全部为空或重复）",
                )

            # 查重：已存在的 word 跳过
            existed = set(
                SensitiveWord.objects.filter(word__in=normalized).values_list("word", flat=True)
            )
            to_create = [w for w in normalized if w not in existed]

            created_count = 0
            created_items: List[Dict[str, Any]] = []
            with transaction.atomic():
                for word in to_create:
                    obj = SensitiveWord.objects.create(
                        word=word,
                        category=category,
                        severity=severity,
                        note=note,
                        created_by=request.user if getattr(request.user, "is_authenticated", False) else None,
                    )
                    created_count += 1
                    created_items.append(
                        {
                            "id": str(obj.id),
                            "word": obj.word,
                            "severity": obj.severity,
                        }
                    )

            skipped_count = len(normalized) - created_count
            return api_ok(
                {
                    "created": created_count,
                    "skipped": skipped_count,
                    "items": created_items,
                },
                message=f"新增 {created_count} 条，跳过 {skipped_count} 条已存在",
                http_status=status.HTTP_201_CREATED,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("SensitiveWordsView.post 失败: %s", exc)
            return api_fail(f"导入失败: {exc}", code=500)
