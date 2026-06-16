# -*- coding: utf-8 -*-
"""后台：创作任务管理 API

路由前缀：/api/admin/creation/tasks/
  GET      /            — 任务列表（按项目/状态/模式过滤，分页）
  GET      /<task_id>/  — 任务详情
  POST     /<task_id>/retry/   — 人工重试
  POST     /<task_id>/cancel/  — 人工取消
"""
from __future__ import annotations

import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.creation.models import CreationTask
from apps.creation.dispatch.service import TaskDispatchService
from apps.console.responses import api_fail, api_ok

logger = logging.getLogger(__name__)

_PAGE_SIZE = 20


def _serialize_task(task: CreationTask) -> dict:
    return {
        "id": str(task.id),
        "project_id": str(task.project_id),
        "workflow_id": str(task.workflow_id) if task.workflow_id else None,
        "trigger_mode": task.trigger_mode,
        "trigger_mode_label": task.get_trigger_mode_display(),
        "state": task.state,
        "state_label": task.get_state_display(),
        "current_node_index": task.current_node_index,
        "progress_percent": task.progress_percent,
        "celery_task_id": task.celery_task_id,
        "error_code": task.error_code,
        "error_message": task.error_message,
        "retry_count": task.retry_count,
        "extra": task.extra,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


class CreationTaskListView(APIView):
    """任务列表（分页 + 多维过滤）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = CreationTask.objects.select_related("project", "workflow").all()

        project_id  = request.query_params.get("project_id")
        state       = request.query_params.get("state")
        trigger_mode = request.query_params.get("trigger_mode")

        if project_id:
            qs = qs.filter(project_id=project_id)
        if state:
            qs = qs.filter(state=state)
        if trigger_mode:
            qs = qs.filter(trigger_mode=trigger_mode)

        qs = qs.order_by("-created_at")
        total = qs.count()

        page = max(1, int(request.query_params.get("page", 1)))
        offset = (page - 1) * _PAGE_SIZE
        items = [_serialize_task(t) for t in qs[offset: offset + _PAGE_SIZE]]

        return api_ok({
            "items": items,
            "total": total,
            "page": page,
            "page_size": _PAGE_SIZE,
        })


class CreationTaskDetailView(APIView):
    """任务详情"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get(self, task_id: str):
        try:
            return CreationTask.objects.select_related("project", "workflow").get(id=task_id)
        except (CreationTask.DoesNotExist, ValueError):
            return None

    def get(self, request, task_id: str = ""):
        task = self._get(task_id)
        if not task:
            return api_fail("任务不存在", code=404)
        return api_ok(_serialize_task(task))


class CreationTaskRetryView(APIView):
    """人工重试失败任务"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, task_id: str = ""):
        try:
            task = CreationTask.objects.get(id=task_id)
        except (CreationTask.DoesNotExist, ValueError):
            return api_fail("任务不存在", code=404)

        if task.state not in (CreationTask.STATE_FAILED, CreationTask.STATE_CANCELLED):
            return api_fail(f"仅 failed/cancelled 任务可重试，当前状态：{task.state}")

        new_task = TaskDispatchService.retry(task)
        return api_ok(_serialize_task(new_task), message="重试任务已创建")


class CreationTaskCancelView(APIView):
    """人工取消任务"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, task_id: str = ""):
        try:
            task = CreationTask.objects.get(id=task_id)
        except (CreationTask.DoesNotExist, ValueError):
            return api_fail("任务不存在", code=404)

        try:
            TaskDispatchService.cancel(task)
        except ValueError as exc:
            return api_fail(str(exc))

        return api_ok(_serialize_task(task), message="任务已取消")
