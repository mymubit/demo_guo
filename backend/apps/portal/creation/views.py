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

        # 调试：CREATION_FORCE_SYNC_PIPELINE=true 时同步跑（阻塞 HTTP，勿用于生产）
        from django.conf import settings as django_settings

        if getattr(django_settings, "CREATION_FORCE_SYNC_PIPELINE", False):
            from apps.creation.tasks import run_creation_pipeline_sync, run_creation_step_sync

            logger.warning(
                "[Creation] CREATION_FORCE_SYNC_PIPELINE 已开启，同步执行 project=%s",
                project.id,
            )
            if project.pipeline_mode == Project.MODE_STEP:
                run_creation_step_sync(str(project.id), 1)
            else:
                run_creation_pipeline_sync(str(project.id))

        result = CreationSubmitResultSerializer(
            {"project_id": str(project.id), "estimated_minutes": estimated_minutes}
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
    """POST /api/creation/projects/<project_id>/confirm/ — 确认当前节点并继续。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str):
        try:
            project = CreationService.confirm_node(project_id, request.user)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无法确认"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "project_id": str(project.id),
                    "status": project.status,
                    "current_node": project.current_node_index,
                },
            },
            status=status.HTTP_200_OK,
        )


class CreationNodeRegenerateView(APIView):
    """POST /api/creation/projects/<project_id>/regenerate/ — 重跑指定节点。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str):
        node_index = request.data.get("node_index")
        try:
            if node_index is not None:
                node_index = int(node_index)
            project = CreationService.regenerate_node(
                project_id, request.user, node_index=node_index
            )
        except (PermissionDenied, ValueError, TypeError) as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无法重跑"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "project_id": str(project.id),
                    "status": project.status,
                    "current_node": project.current_node_index,
                },
            },
            status=status.HTTP_200_OK,
        )


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
            data = CreationService.get_workspace(project_id, request.user)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 0, "message": "success", "data": data},
            status=status.HTTP_200_OK,
        )


def _trigger_workspace_generation(request, project_id: str, node_index: int) -> dict:
    body = request.data if isinstance(request.data, dict) else {}
    return CreationService.trigger_skill_generation(
        project_id,
        request.user,
        int(node_index),
        script_from=body.get("from_episode"),
        script_to=body.get("to_episode"),
        batch_size=body.get("batch_size"),
        regenerate=bool(body.get("regenerate")),
        outline_mode=body.get("outline_mode"),
        outline_stage_key=body.get("stage_key"),
    )


def _save_workspace_content(request, project_id: str, node_index: int) -> dict:
    return CreationService.save_workspace_skill(
        project_id,
        request.user,
        int(node_index),
        request.data if isinstance(request.data, dict) else {},
    )


class CreationAgentGenerateView(APIView):
    """POST /api/creation/projects/<project_id>/agents/<node_index>/generate/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str, node_index: int):
        try:
            data = _trigger_workspace_generation(request, project_id, node_index)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无法生成"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 0, "message": "success", "data": data},
            status=status.HTTP_200_OK,
        )


class CreationAgentContentView(APIView):
    """PUT /api/creation/projects/<project_id>/agents/<node_index>/content/"""

    permission_classes = [IsAuthenticated]

    def put(self, request, project_id: str, node_index: int):
        try:
            data = _save_workspace_content(request, project_id, node_index)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无法保存"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 0, "message": "success", "data": data},
            status=status.HTTP_200_OK,
        )


