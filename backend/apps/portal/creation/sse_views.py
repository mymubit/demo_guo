# -*- coding: utf-8 -*-
"""SSE ??????

???GET /api/creation/projects/{project_id}/progress/stream/

????? EventSource ?????????????? HTTP ???
? 3 ??????????????/???????????????

SSE ?????
  event: progress
  data: {"status": "running", "progress_percent": 60, "drama_stage": "plot_design", ...}

  event: done
  data: {"status": "completed", ...}

  event: error
  data: {"status": "failed", "error_message": "..."}

???
  - ?? WSGI ??????????Gunicorn ?????uwsgi ????
  - Nginx ??? proxy_buffering ??? X-Accel-Buffering: no
  - ?????? 5 ???CLIENT_TIMEOUT_SECONDS???????
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
CLIENT_TIMEOUT_SECONDS = 300  # 5 ?????????????


def _build_event(event_type: str, data: dict) -> str:
    """?? SSE ????"""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"


def _serialize_project_state(project: Project) -> dict:
    """????????????"""
    from apps.drama.progress_service import DramaProgressService

    return {
        "project_id": str(project.id),
        "status": project.execution_status,
        "drama_stage": project.drama_stage if project.is_drama_workspace else "",
        "delivery_status": (project.delivery_status if project.is_drama_workspace else "") or "",
        "progress_percent": project.progress_percent,
        "error_message": project.error_message or "",
        "updated_at": project.updated_at.isoformat(),
    }


def _progress_stream(project_id: str, user) -> Generator[str, None, None]:
    """???????? SSE ??"""
    deadline = time.time() + CLIENT_TIMEOUT_SECONDS

    # ??????????????????
    yield ": heartbeat\n\n"

    while time.time() < deadline:
        try:
            project = Project.objects.get(id=project_id, user=user)
        except Project.DoesNotExist:
            yield _build_event("error", {"message": "??????????"})
            return

        state_data = _serialize_project_state(project)
        is_terminal = project.execution_status in (Project.STATUS_COMPLETED, Project.STATUS_FAILED)

        if is_terminal:
            event_type = "done" if project.execution_status == Project.STATUS_COMPLETED else "error"
            yield _build_event(event_type, state_data)
            return

        yield _build_event("progress", state_data)
        time.sleep(POLL_INTERVAL_SECONDS)

    # ????? timeout ????????????
    yield _build_event("timeout", {"message": "SSE ????????"})


class CreationProgressStreamView(APIView):
    """SSE ?????

    GET /api/creation/projects/{project_id}/progress/stream/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str = ""):
        user = request.user

        # ??????????????????
        if not Project.objects.filter(id=project_id, user=user).exists():
            from apps.console.responses import api_fail
            return api_fail("??????????", code=404)

        response = StreamingHttpResponse(
            streaming_content=_progress_stream(project_id, user),
            content_type="text/event-stream; charset=utf-8",
        )
        response["Cache-Control"]    = "no-cache"
        response["X-Accel-Buffering"] = "no"   # ?? Nginx ??
        return response
