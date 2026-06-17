"""运营中心权限。

运营角色管理：按域（内容/增长/商业化/技能/客服/数据/超管）划分权限。
运营请求通过 X-Ops-Role 头（来自后台 SSO）或用户 staff_role 字段标识。
"""
from __future__ import annotations

from typing import Iterable

from rest_framework.permissions import BasePermission

from .constants import (
    OPS_ROLES,
    ROLE_COMMERCE_OPS,
    ROLE_CONTENT_OPS,
    ROLE_DATA_OPS,
    ROLE_GROWTH_OPS,
    ROLE_SKILL_OPS,
    ROLE_SUPER,
    ROLE_SUPPORT_OPS,
)


# 域 → 允许的角色
DOMAIN_CONTENT = "content"
DOMAIN_GROWTH = "growth"
DOMAIN_COMMERCE = "commerce"
DOMAIN_SKILL = "skill"
DOMAIN_SUPPORT = "support"
DOMAIN_DATA = "data"
DOMAIN_TICKET = "ticket"
DOMAIN_EXPERIMENT = "experiment"
DOMAIN_TEMPLATE = "template"
DOMAIN_UGC = "ugc"
DOMAIN_CREATOR = "creator"
DOMAIN_COMPLIANCE = "compliance"
DOMAIN_ALL = "*"

DOMAIN_ALLOWED_ROLES: dict[str, tuple[str, ...]] = {
    DOMAIN_CONTENT: (ROLE_CONTENT_OPS, ROLE_SUPER),
    DOMAIN_GROWTH: (ROLE_GROWTH_OPS, ROLE_SUPER),
    DOMAIN_COMMERCE: (ROLE_COMMERCE_OPS, ROLE_SUPER),
    DOMAIN_SKILL: (ROLE_SKILL_OPS, ROLE_SUPER),
    DOMAIN_SUPPORT: (ROLE_SUPPORT_OPS, ROLE_SUPER),
    DOMAIN_DATA: (ROLE_DATA_OPS, ROLE_SUPER),
    DOMAIN_TICKET: (ROLE_SUPPORT_OPS, ROLE_CONTENT_OPS, ROLE_SUPER),
    DOMAIN_EXPERIMENT: (ROLE_GROWTH_OPS, ROLE_DATA_OPS, ROLE_SUPER),
    DOMAIN_TEMPLATE: (ROLE_CONTENT_OPS, ROLE_SUPER),
    DOMAIN_UGC: (ROLE_CONTENT_OPS, ROLE_GROWTH_OPS, ROLE_SUPER),
    DOMAIN_CREATOR: (ROLE_GROWTH_OPS, ROLE_CONTENT_OPS, ROLE_SUPER),
    DOMAIN_COMPLIANCE: (ROLE_CONTENT_OPS, ROLE_SUPPORT_OPS, ROLE_SUPER),
    DOMAIN_ALL: (ROLE_SUPER,),
}


def get_ops_role(request) -> str:
    """从请求中提取运营角色。"""
    if not request or not request.user or not request.user.is_authenticated:
        return ""
    # 优先用 user 上的 staff_role
    role = getattr(request.user, "staff_role", "") or ""
    if role:
        return role
    # 备选：从 header 读取（来自后台 SSO）
    header = request.META.get("HTTP_X_OPS_ROLE", "")
    if header in OPS_ROLES:
        return header
    # 超管兜底
    if getattr(request.user, "is_staff", False) or getattr(request.user, "is_superuser", False):
        return ROLE_SUPER
    return ""


class HasOpsDomain(BasePermission):
    """按域检查运营角色权限。

    用法：view.permission_classes = [HasOpsDomain]; view.ops_domain = DOMAIN_CONTENT
    """

    message = "无运营权限"

    def has_permission(self, request, view) -> bool:
        role = get_ops_role(request)
        if not role:
            return False
        domain = getattr(view, "ops_domain", DOMAIN_ALL)
        allowed = DOMAIN_ALLOWED_ROLES.get(domain, ())
        return role in allowed


def has_domain_role(user, domain: str) -> bool:
    role = getattr(user, "staff_role", "") if user else ""
    if not role and user:
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            role = ROLE_SUPER
    return role in DOMAIN_ALLOWED_ROLES.get(domain, ())


def required_roles(domain: str) -> Iterable[str]:
    return DOMAIN_ALLOWED_ROLES.get(domain, ())
