# -*- coding: utf-8 -*-
"""Drama API 权限类。"""
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.drama.models import DramaProject


class IsProjectOwner(BasePermission):
    """项目所有者权限。"""

    def has_object_permission(self, request: Request, view: APIView, obj: DramaProject) -> bool:
        return obj.owner_id == request.user.id


class ProjectReadPermission(BasePermission):
    """project.read：读项目资源。"""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request: Request, view: APIView, obj: DramaProject) -> bool:
        return obj.owner_id == request.user.id or request.user.is_staff


class ProjectWritePermission(BasePermission):
    """project.write：写项目设置。"""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj: DramaProject) -> bool:
        return obj.owner_id == request.user.id


class ProjectExecutePermission(BasePermission):
    """project.execute：执行工作流命令与生成。"""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj: DramaProject) -> bool:
        return obj.owner_id == request.user.id


class ProjectApprovePermission(BasePermission):
    """project.approve：故事蓝图审批。"""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj: DramaProject) -> bool:
        return obj.owner_id == request.user.id


class DramaConfigReadPermission(BasePermission):
    """drama_config.read。"""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )


class DramaConfigWritePermission(BasePermission):
    """drama_config.write。"""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and request.user.is_staff


class DramaConfigRollbackPermission(BasePermission):
    """drama_config.rollback。"""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and request.user.is_superuser
