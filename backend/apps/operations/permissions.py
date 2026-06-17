"""运营中心权限。

个人站只面向 superuser：直接复用 Django 自带的 `is_superuser` 判断即可。
这里只暴露一个 `IsOpsAdmin`，方便 view 中复用。
"""
from rest_framework.permissions import BasePermission


class IsOpsAdmin(BasePermission):
    """运营后台通用权限：仅 is_superuser 通过。"""

    message = "仅超级管理员可访问运营后台。"

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)
