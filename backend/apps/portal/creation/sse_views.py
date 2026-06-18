# -*- coding: utf-8 -*-
"""SSE 实时进度推送

接口：GET /api/creation/projects/{project_id}/progress/stream/

客户端通过 EventSource 订阅项目创作进度，替代自适应 HTTP 轮询。
每 3 秒推送一次最新状态，项目完成/失败后发送终止事件后关闭连接。

SSE 事件格式：
  event: progress
  data: {"status": "running", "progress_percent": 60, "current_node_index": 4, ...}

  event: done
  data: {"status": "completed", ...}

  event: error
  data: {"status": "failed", "error_message": "..."}

注意：
  - 依赖 WSGI 服务器支持流式响应（Gunicorn 默认支持，uwsgi 需配置）
  - Nginx 需关闭 proxy_buffering 或设置 X-Accel-Buffering: no
  - 最大持续时间 5 分钟（CLIENT_TIMEOUT_SECONDS），超时后重连
"""
from __future__ import annotations

import json
import logging
import time
from typing import Generator

from django.http import StreamingHttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.creation.models import Project

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 3
CLIENT_TIMEOUT_SECONDS = 300  # 5 分钟后关闭，客户端自动重连


def _build_event(event_type: str, data: dict) -> str:
    """构造 SSE 事件文本"""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"


def _serialize_project_state(project: Project) -> dict:
    """提取客户端需要的进度字段"""
    return {
        "project_id":         str(project.id),
        "status":             project.execution_status,
        "fusion_status":      project.fusion_status,
        "progress_percent":   project.progress_percent,
        "current_node_index": project.current_node_index,
        "total_nodes":        project.total_nodes,
        "error_message":      project.error_message or "",
        "updated_at":         project.updated_at.isoformat(),
    }


def _progress_stream(project_id: str, user) -> Generator[str, None, None]:
    """生成器：持续产生 SSE 事件"""
    deadline = time.time() + CLIENT_TIMEOUT_SECONDS

    # 首次发送心跳，让客户端知道连接已建立
    yield ": heartbeat\n\n"

    while time.time() < deadline:
        try:
            project = Project.objects.get(id=project_id, user=user)
        except Project.DoesNotExist:
            yield _build_event("error", {"message": "项目不存在或无权访问"})
            return

        state_data = _serialize_project_state(project)
        is_terminal = project.execution_status in (Project.STATUS_COMPLETED, Project.STATUS_FAILED)

        if is_terminal:
            event_type = "done" if project.execution_status == Project.STATUS_COMPLETED else "error"
            yield _build_event(event_type, state_data)
            return

        yield _build_event("progress", state_data)
        time.sleep(POLL_INTERVAL_SECONDS)

    # 超时：发送 timeout 事件让客户端决定是否重连
    yield _build_event("timeout", {"message": "SSE 连接超时，请重连"})


class CreationProgressStreamView(APIView):
    """SSE 进度流接口

    GET /api/creation/projects/{project_id}/progress/stream/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str = ""):
        user = request.user

        # 权限预检：项目必须存在且属于当前用户
        if not Project.objects.filter(id=project_id, user=user).exists():
            from apps.console.responses import api_fail
            return api_fail("项目不存在或无权访问", code=404)

        response = StreamingHttpResponse(
            streaming_content=_progress_stream(project_id, user),
            content_type="text/event-stream; charset=utf-8",
        )
        response["Cache-Control"]    = "no-cache"
        response["X-Accel-Buffering"] = "no"   # 关闭 Nginx 缓冲
        return response
