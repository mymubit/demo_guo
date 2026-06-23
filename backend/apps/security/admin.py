# -*- coding: utf-8 -*-
"""
安全模块 Django Admin 配置

审计日志只允许查看，不允许编辑、删除、新增。
"""
from __future__ import annotations

import json

from django.contrib import admin
from django.db.models import JSONField
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import AuditLog


# ----------------------------------------------------------------------
# 审计日志 Admin
# ----------------------------------------------------------------------
class AuditLogAdmin(admin.ModelAdmin):
    """
    审计日志管理界面

    特性：
        - 只允许查看（禁用新增/编辑/删除）
        - 支持按操作类型、时间、用户ID、IP筛选
        - 支持按时间排序
        - JSON 扩展字段以美化方式展示
    """

    # ---- 显示列表 ----
    list_display = (
        "id_short",
        "created_at",
        "action",
        "user_id",
        "ip_address",
        "device_fingerprint",
        "request_method",
        "request_path_short",
        "response_status",
    )

    # ---- 只读字段（防止修改） ----
    readonly_fields = (
        "id",
        "created_at",
        "action",
        "user_id",
        "ip_address",
        "device_fingerprint",
        "request_path",
        "request_method",
        "request_hash",
        "response_status",
        "extra_info_pretty",
    )

    # ---- 搜索 & 过滤 ----
    search_fields = (
        "user_id",
        "ip_address",
        "device_fingerprint",
        "request_path",
        "request_hash",
    )

    list_filter = (
        "action",
        "response_status",
        "request_method",
        ("created_at", admin.DateFieldListFilter),
    )

    # ---- 排序 ----
    ordering = ("-created_at",)

    # ---- 分页 ----
    list_per_page = 50
    list_max_show_all = 200

    # ---- 详情字段分组 ----
    fieldsets = (
        (
            _("基本信息"),
            {
                "fields": (
                    "id",
                    "created_at",
                    "action",
                    "response_status",
                )
            },
        ),
        (
            _("用户与设备"),
            {
                "fields": (
                    "user_id",
                    "ip_address",
                    "device_fingerprint",
                )
            },
        ),
        (
            _("请求信息"),
            {
                "fields": (
                    "request_method",
                    "request_path",
                    "request_hash",
                )
            },
        ),
        (
            _("扩展信息"),
            {
                "fields": ("extra_info_pretty",),
                "classes": ("collapse",),
            },
        ),
    )

    # ---- 禁用操作 ----
    actions = None  # 禁止批量操作
    actions_on_top = False
    actions_on_bottom = False

    # ---- 自定义方法 ----
    @admin.display(description=_("ID"), ordering="id")
    def id_short(self, obj: AuditLog) -> str:
        """显示缩短的 UUID。"""
        uid = str(obj.id)
        return f"{uid[:8]}…{uid[-4:]}"

    @admin.display(description=_("请求路径"), ordering="request_path")
    def request_path_short(self, obj: AuditLog) -> str:
        """限制路径显示长度。"""
        path = obj.request_path or ""
        if len(path) > 60:
            return path[:57] + "…"
        return path

    @admin.display(description=_("扩展信息 (JSON)"))
    def extra_info_pretty(self, obj: AuditLog) -> str:
        """美化显示 JSON 扩展字段。"""
        data = obj.extra_info or {}
        if not data:
            return "-"
        try:
            pretty = json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            pretty = str(data)
        return format_html(
            "<pre style='white-space:pre-wrap; word-break:break-all; "
            "background:#f8f8f8; padding:8px; border:1px solid #e0e0e0; "
            "border-radius:4px; margin:0; max-width:800px;'>{}</pre>",
            pretty,
        )

    # ---- 权限控制：彻底禁止增/改/删 ----
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    # ---- 禁用操作：save_model / delete_model 留空以防万一 ----
    def save_model(self, request, obj, form, change):  # type: ignore[override]
        # 理论上不会走到这里（has_change_permission 已返回 False），做兜底
        raise RuntimeError("审计日志不允许修改")

    def delete_model(self, request, obj):  # type: ignore[override]
        raise RuntimeError("审计日志不允许删除")


# 注册模型到 Django Admin
admin.site.register(AuditLog, AuditLogAdmin)
