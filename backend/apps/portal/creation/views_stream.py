# -*- coding: utf-8 -*-
"""Agent 流式 SSE 与 Chunk / agent_notes API。"""
from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.user_messages import safe_api_message
from apps.creation.agent_runtime.chunk_service import list_chunks
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.agent_runtime.stream_service import AgentStreamService
from apps.creation.services import CreationService


class IndependentAgentStreamView(APIView):
    """POST /api/creation/projects/<id>/agents/<agent_id>/stream/ — SSE 流式生成。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str, agent_id: str):
        body = request.data if isinstance(request.data, dict) else {}
        params = body.get("params") if isinstance(body.get("params"), dict) else body.get("params") or {}
        if not isinstance(params, dict):
            params = {}
        try:
            project = CreationService._get_user_project(project_id, request.user)
            AgentStreamService.assert_can_stream(project, request.user, agent_id)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"code": 400, "message": safe_api_message(exc, "无法启动流式生成"), "data": None},
                status=status.HTTP_200_OK,
            )

        response = StreamingHttpResponse(
            streaming_content=AgentStreamService.stream_events(project, request.user, agent_id, params),
            content_type="text/event-stream; charset=utf-8",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class ProjectChunksView(APIView):
    """GET /api/creation/projects/<id>/chunks/ — 分片列表。"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str):
        kind = (request.query_params.get("kind") or "episode_scripts").strip()
        try:
            limit = max(1, min(200, int(request.query_params.get("limit") or 50)))
        except (TypeError, ValueError):
            limit = 50
        try:
            offset = max(0, int(request.query_params.get("offset") or 0))
        except (TypeError, ValueError):
            offset = 0
        try:
            project = CreationService._get_user_project(project_id, request.user)
            data = list_chunks(project, kind=kind, limit=limit, offset=offset)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response({"code": 0, "message": "success", "data": data}, status=status.HTTP_200_OK)


class ProjectChunksContinueView(APIView):
    """POST /api/creation/projects/<id>/chunks/continue/ — 断点续生（SSE）。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str):
        body = request.data if isinstance(request.data, dict) else {}
        agent_id = str(body.get("agent_id") or "script").strip()
        params = body.get("params") if isinstance(body.get("params"), dict) else {}
        to_episode = body.get("to_episode")
        if to_episode is not None:
            params = {**params, "episode_to": to_episode, "script_to": to_episode}
        try:
            project = CreationService._get_user_project(project_id, request.user)
            continue_from = AgentStreamService.resolve_continue_from(project, agent_id, params)
            if continue_from:
                params = {**params, "continue_from": continue_from}
            AgentStreamService.assert_can_stream(project, request.user, agent_id)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"code": 400, "message": safe_api_message(exc, "无法续生"), "data": None},
                status=status.HTTP_200_OK,
            )

        response = StreamingHttpResponse(
            streaming_content=AgentStreamService.stream_events(project, request.user, agent_id, params),
            content_type="text/event-stream; charset=utf-8",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class ProjectAgentNotesView(APIView):
    """PATCH /api/creation/projects/<id>/agent-notes/ — 更新项目 Agent 记忆。"""

    permission_classes = [IsAuthenticated]

    def patch(self, request, project_id: str):
        body = request.data if isinstance(request.data, dict) else {}
        notes = body.get("agent_notes")
        if not isinstance(notes, dict):
            return Response(
                {"code": 400, "message": "agent_notes 必须为对象", "data": None},
                status=status.HTTP_200_OK,
            )
        try:
            project = CreationService._get_user_project(project_id, request.user)
            IndependentAgentService.assert_project_owner(project, request.user)
            from apps.creation.agent_runtime.agent_notes_utils import merge_agent_notes_patch

            merged = merge_agent_notes_patch(
                dict(getattr(project, "agent_notes", None) or {}),
                notes,
            )
            project.agent_notes = merged
            project.save(update_fields=["agent_notes", "updated_at"])
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 0, "message": "success", "data": {"agent_notes": project.agent_notes}},
            status=status.HTTP_200_OK,
        )

    def get(self, request, project_id: str):
        try:
            project = CreationService._get_user_project(project_id, request.user)
            data = {"agent_notes": dict(getattr(project, "agent_notes", None) or {})}
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response({"code": 0, "message": "success", "data": data}, status=status.HTTP_200_OK)
