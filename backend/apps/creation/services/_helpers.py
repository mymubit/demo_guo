# -*- coding: utf-8 -*-
"""创作服务辅助函数。"""

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from ..models import Project


def _get_user_project(project_id: str, user) -> Project:
    """获取并校验 project 归属（必须为当前用户创建）。"""
    try:
        project = Project.objects.get(id=project_id)
    except ObjectDoesNotExist:
        raise PermissionDenied("作品不存在或无访问权限")
    if project.user_id != user.id:
        raise PermissionDenied("无权限访问该作品")
    return project
