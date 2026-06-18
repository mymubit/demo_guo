"""
创作 API 视图

路由 /api/creation/...

接口：
  POST /submit/              提交创作任务
  GET  /progress/<project_id>/   查询创作进度
  GET  /download/<project_id>/   下载剧本（返回二进制文件流）
  GET  /dl/<token>/               以一次性 token 下载（匿名场景）
  POST /share/<project_id>/       为作品生成分享链接
  GET  /share/view/<token>/       匿名查看分享内容（返回 HTML 片段）

安全设计：
- 所有需要身份认证的接口使用 IsAuthenticated
- 绝不将原始剧本数据结构返回给前端
- 下载接口直接返回 FileResponse（二进制流），不包装 JSON
"""

import io
import logging

from django.core.exceptions import PermissionDenied
from django.http import FileResponse, HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.user_messages import safe_api_message
from apps.creation.serializers import (
    CreationSubmitSerializer,
    CreationSubmitResultSerializer,
    ProjectProgressSerializer,
    ShareCreateSerializer,
    ShareCreateResultSerializer,
    ShareViewSerializer,
)
from apps.creation.models import Project
from apps.creation.services import CreationService
from apps.portal.creation.legacy_gone import legacy_gone_response, legacy_workspace_gone_response

logger = logging.getLogger(__name__)


# ============================================================
# 1. 提交创作
# ============================================================
class CreationSubmitView(APIView):
    """提交创作任务

    POST /api/creation/submit/
    Body:
      {
        "theme": "family-revenge",
        "core_idea": "一句话创意描述",
        "episode_count": 30,
        "format_variant": "B",
        "audience": "",
        "reference_work": ""
      }
    Response:
      {
        "code": 0,
        "message": "success",
        "data": { "project_id": "...", "estimated_minutes": 12 }
      }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreationSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project, estimated_minutes = CreationService.submit(
                user=request.user,
                data=serializer.validated_data,
            )
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )

        result = CreationSubmitResultSerializer(
            {
                "project_id": str(project.id),
                "estimated_minutes": estimated_minutes,
                "status": project.status,
                "workspace_url": f"/creation?project={project.id}",
            }
        )
        return Response(
            {"code": 0, "message": "success", "data": result.data},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 2. 查询进度
# ============================================================
class CreationProgressView(APIView):
    """查询创作进度

    GET /api/creation/progress/<project_id>/

    Response.data 仅包含 status / progress / 预渲染 HTML，
    绝不包含任何原始剧本数据结构。
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str):
        try:
            data = CreationService.get_progress(project_id, request.user)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )

        serializer = ProjectProgressSerializer(data)
        return Response(
            {"code": 0, "message": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 3. 下载剧本（登录用户，直接按 project_id 下载）
# ============================================================
class CreationDownloadView(APIView):
    """下载剧本

    GET /api/creation/download/<project_id>/?format=md

    返回：二进制文件流（FileResponse），不包装任何 JSON。
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str):
        file_format = request.GET.get("format", "md").lower()
        if file_format not in {"md", "html", "zip", "pdf"}:
            file_format = "md"

        try:
            file_bytes, file_name, content_type = CreationService.download_script(
                project_id=project_id,
                user=request.user,
                file_format=file_format,
            )
        except PermissionDenied as exc:
            # 下载失败也以 HTTP 403 响应，不包装 JSON
            return HttpResponse(
                content=safe_api_message(exc, "无权限下载"),
                status=status.HTTP_403_FORBIDDEN,
                content_type="text/plain; charset=utf-8",
            )

        # 以二进制流返回，设置 filename 与 Content-Type
        response = FileResponse(
            io.BytesIO(file_bytes),
            content_type=content_type,
            as_attachment=True,
            filename=file_name,
        )
        # 安全：禁止浏览器嗅探内容类型
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Length"] = str(len(file_bytes))
        return response


# ============================================================
# 4. 使用一次性下载 token 下载（分享下载 / 短时匿名下载）
# ============================================================
class CreationDownloadByTokenView(APIView):
    """以一次性 token 下载

    GET /api/creation/dl/<token>/?format=md

    返回：二进制文件流，无 JSON 包装。
    """

    permission_classes = [AllowAny]

    def get(self, request, token: str):
        file_format = request.GET.get("format", "md").lower()
        if file_format not in {"md", "html", "zip", "pdf"}:
            file_format = "md"

        try:
            file_bytes, file_name, content_type = CreationService.download_by_token(
                token=token,
                file_format=file_format,
            )
        except PermissionDenied as exc:
            return HttpResponse(
                content=safe_api_message(exc, "下载链接无效或已过期"),
                status=status.HTTP_403_FORBIDDEN,
                content_type="text/plain; charset=utf-8",
            )

        response = FileResponse(
            io.BytesIO(file_bytes),
            content_type=content_type,
            as_attachment=True,
            filename=file_name,
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Length"] = str(len(file_bytes))
        return response


# ============================================================
# 5. 生成分享链接
# ============================================================
class CreationShareCreateView(APIView):
    """生成作品分享链接

    POST /api/creation/share/<project_id>/
    Body（可选）:
      {
        "view_limit": 100,
        "valid_days": 7,
        "allow_download": false,
        "custom_title": ""
      }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str):
        serializer = ShareCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        try:
            result = CreationService.generate_share_link(
                project_id=project_id,
                user=request.user,
                view_limit=params.get("view_limit", 100),
                valid_days=params.get("valid_days", 7),
                allow_download=params.get("allow_download", False),
                custom_title=params.get("custom_title", ""),
            )
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )

        serializer = ShareCreateResultSerializer(result)
        return Response(
            {"code": 0, "message": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 6. 查看分享页（公开访问）
# ============================================================
class ShareView(APIView):
    """查看分享页内容（公开）

    GET /api/creation/share/view/<token>/

    Response: 仅返回预渲染 HTML 片段 + 少量元信息，
    绝不暴露原始剧本数据结构。
    """

    permission_classes = [AllowAny]

    def get(self, request, token: str):
        try:
            data = CreationService.get_share_view(token)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "链接无效"), "data": None},
                status=status.HTTP_200_OK,
            )

        serializer = ShareViewSerializer(data)
        return Response(
            {"code": 0, "message": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 分步模式：确认 / 重跑节点
# ============================================================
class CreationNodeConfirmView(APIView):
    """POST /api/creation/projects/<project_id>/confirm/ — 已废弃。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str):
        return legacy_gone_response("分步确认节点接口已废弃，请使用独立 Agent 运行接口。")


class CreationNodeRegenerateView(APIView):
    """POST /api/creation/projects/<project_id>/regenerate/ — 已废弃。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str):
        return legacy_gone_response("节点重跑接口已废弃，请使用独立 Agent 运行接口。")


class AiFieldGenerateView(APIView):
    """POST /api/creation/ai/generate/ — 表单字段 AI 生成（扣币，仅返回文本）"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        action_key = (request.data.get("action_key") or "").strip()
        if not action_key:
            return Response(
                {"code": 4001, "message": "缺少 action_key", "data": None},
                status=status.HTTP_200_OK,
            )
        context = request.data.get("context") or {}
        if not isinstance(context, dict):
            context = {}
        try:
            from apps.creation.ai_field_service import generate_field_content

            data = generate_field_content(request.user, action_key, context)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无法生成"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 0, "message": "success", "data": data},
            status=status.HTTP_200_OK,
        )


class CreationWorkspaceView(APIView):
    """GET /api/creation/projects/<project_id>/workspace/ — 技能工作台。"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str):
        try:
            project = CreationService._get_user_project(project_id, request.user)
            from apps.creation.agent_runtime.workspace import build_independent_workspace

            data = build_independent_workspace(project)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 0, "message": "success", "data": data},
            status=status.HTTP_200_OK,
        )


class IndependentAgentRunView(APIView):
    """POST /api/creation/projects/<project_id>/agents/<agent_id>/run/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str, agent_id: str):
        body = request.data if isinstance(request.data, dict) else {}
        params = body.get("params") if isinstance(body.get("params"), dict) else {}
        try:
            project = CreationService._get_user_project(project_id, request.user)
            from apps.creation.agent_runtime.independent_service import IndependentAgentService
            from apps.creation.tasks import run_independent_agent
            from dj_queue.api import enqueue_on_commit

            result = IndependentAgentService.enqueue_run(project, request.user, agent_id, params)
            run = result.run
            if result.should_enqueue:
                enqueue_on_commit(run_independent_agent, str(project.id), agent_id, params, str(run.id))
            data = {
                "run_id": str(run.id),
                "agent_id": run.agent_id,
                "status": "queued" if result.created_new_run else run.status,
                "project_id": str(project.id),
                "created_new_run": result.created_new_run,
                "already_running": not result.created_new_run,
            }
        except (PermissionDenied, ValueError) as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无法运行 Agent"), "data": None},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"code": 400, "message": safe_api_message(exc, "无法运行 Agent"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response({"code": 0, "message": "success", "data": data}, status=status.HTTP_200_OK)


class IndependentAgentEstimateView(APIView):
    """POST /api/creation/projects/<project_id>/agents/<agent_id>/estimate/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str, agent_id: str):
        body = request.data if isinstance(request.data, dict) else {}
        params = body.get("params") if isinstance(body.get("params"), dict) else {}
        try:
            project = CreationService._get_user_project(project_id, request.user)
            from apps.creation.agent_runtime.independent_service import IndependentAgentService

            data = IndependentAgentService.preview_run(project, agent_id, params)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"code": 400, "message": safe_api_message(exc, "无法预估 tokens"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response({"code": 0, "message": "success", "data": data}, status=status.HTTP_200_OK)


class IndependentAgentRunListView(APIView):
    """GET /api/creation/projects/<project_id>/agents/<agent_id>/runs/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str, agent_id: str):
        try:
            project = CreationService._get_user_project(project_id, request.user)
            from apps.creation.monitoring.execution_run_service import AgentExecutionRunService

            data = AgentExecutionRunService.list_runs_for_project(project, agent_id=agent_id)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response({"code": 0, "message": "success", "data": data}, status=status.HTTP_200_OK)


class IndependentAgentRunDetailView(APIView):
    """GET /api/creation/projects/<project_id>/runs/<run_id>/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str, run_id: str):
        try:
            project = CreationService._get_user_project(project_id, request.user)
            from apps.creation.monitoring.execution_run_service import AgentExecutionRunService

            data = AgentExecutionRunService.get_run_detail(run_id, include_sensitive=False)
            if not data or data.get("project_id") != str(project.id):
                raise PermissionDenied("运行记录不存在")
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response({"code": 0, "message": "success", "data": data}, status=status.HTTP_200_OK)


class ProjectArtifactView(APIView):
    """GET /api/creation/projects/<project_id>/artifacts/<artifact_key>/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str, artifact_key: str):
        try:
            project = CreationService._get_user_project(project_id, request.user)
            from apps.creation.artifact_service import get_artifact
            from apps.creation.workspace.workspace_editor import build_artifact_editor_view

            payload = get_artifact(project, artifact_key)
            if payload is None:
                return Response(
                    {"code": 404, "message": "artifact not found", "data": None},
                    status=status.HTTP_200_OK,
                )
            editor_view = build_artifact_editor_view(project, artifact_key)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "artifact_key": artifact_key,
                    "payload": payload,
                    "editor_view": editor_view,
                },
            },
            status=status.HTTP_200_OK,
        )


class CreationAgentGenerateView(APIView):
    """POST /api/creation/projects/<project_id>/agents/<node_index>/generate/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str, node_index: int):
        return legacy_workspace_gone_response()


class CreationAgentContentView(APIView):
    """PUT /api/creation/projects/<project_id>/agents/<node_index>/content/"""

    permission_classes = [IsAuthenticated]

    def put(self, request, project_id: str, node_index: int):
        return legacy_workspace_gone_response()


class CreationAgentQualityAlertAckView(APIView):
    """POST /api/creation/projects/<project_id>/agents/<node_index>/quality-alert/ack/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str, node_index: int):
        return legacy_workspace_gone_response()


