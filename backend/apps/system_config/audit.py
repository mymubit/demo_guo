# -*- coding: utf-8 -*-
"""配置中心审计工具。"""
from __future__ import annotations

from .models import SystemConfigAuditLog, SystemConfigItem


def client_ip(request) -> str | None:
    if request is None:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


def write_audit_log(
    *,
    config: SystemConfigItem | None,
    config_key: str,
    action: str,
    old_value=None,
    new_value=None,
    request=None,
    change_reason: str = "",
) -> None:
    user = getattr(request, "user", None) if request is not None else None
    if not getattr(user, "is_authenticated", False):
        user = None
    SystemConfigAuditLog.objects.create(
        config=config,
        config_key=config_key,
        action=action,
        old_value=old_value,
        new_value=new_value,
        change_reason=change_reason or "",
        operator=user,
        ip_address=client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:512] if request is not None else ""),
    )
