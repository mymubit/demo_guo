# apps/common/permissions.py
# 自定义权限类

from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """仅允许管理员访问。

    通过用户对象的 is_admin 字段判断（若用户模型未定义 is_admin，
    则回退判断 Django 内置的 is_staff）。
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # 优先使用自定义 is_admin 字段，否则回退到 Django is_staff
        if hasattr(user, 'is_admin'):
            return bool(user.is_admin)
        return bool(getattr(user, 'is_staff', False))


class IsSuperAdmin(BasePermission):
    """仅允许超级管理员访问。

    通过用户对象的 is_super_admin 字段判断（若未定义，则回退判断
    Django 内置的 is_superuser）。
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # 优先使用自定义 is_super_admin 字段，否则回退到 Django is_superuser
        if hasattr(user, 'is_super_admin'):
            return bool(user.is_super_admin)
        return bool(getattr(user, 'is_superuser', False))


class IsMemberUser(BasePermission):
    """仅允许会员用户访问。

    通过用户对象的 is_member 字段判断；默认要求用户已登录且会员标识为 True。
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # 判断用户是否为会员；若用户模型不含 is_member，则返回 False
        if hasattr(user, 'is_member'):
            return bool(user.is_member)
        return False
