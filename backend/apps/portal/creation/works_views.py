"""
我的作品 API 视图

路由 /api/works/...

接口：
  GET  /api/works/                我的作品列表（支持 status 过滤 + 分页）
  GET  /api/works/<project_id>/   作品详情（返回 rendered_result_html + 元信息）
  POST /api/works/<project_id>/share/  生成分享链接（复用 CreationShareCreateView 逻辑）

安全设计：
- 所有需要身份认证的接口使用 IsAuthenticated
- 绝不将原始剧本数据结构返回给前端
- 作品详情仅以预渲染 HTML 形式提供剧本内容
"""

import logging

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.creation.models import Project
from apps.creation.serializers import (
    ProjectListSerializer,
    ShareCreateSerializer,
    ShareCreateResultSerializer,
)
from apps.creation.script_export import export_work
from apps.common.user_messages import safe_api_message
from apps.creation.services import CreationService

logger = logging.getLogger(__name__)


# ============================================================
# 1. 我的作品列表
# ============================================================
class WorkListView(APIView):
    """我的作品列表

    GET /api/works/?status=pending&page=1&page_size=20

    Query 参数：
      - status: 可选, pending / running / completed / failed
      - page: 页码, 默认 1
      - page_size: 每页数量, 默认 20, 最大 100

    Response:
      {
        "code": 0,
        "message": "success",
        "data": [
          { "project_id": "...", "title": "...", "theme": "...",
            "episode_count": 30, "format_variant": "B", "status": "completed",
            "status_text": "已完成", "progress_percent": 100,
            "created_at": "...", "updated_at": "..." }
        ],
        "pagination": {
          "total": 100,
          "page": 1,
          "page_size": 20,
          "total_pages": 5
        }
      }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 解析查询参数
        status_filter = request.GET.get("status", "").strip()
        keyword = request.GET.get("q", "").strip()
        ordering = request.GET.get("ordering", "newest").strip()
        try:
            page = max(1, int(request.GET.get("page", "1")))
        except ValueError:
            page = 1
        try:
            page_size = min(100, max(1, int(request.GET.get("page_size", "20"))))
        except ValueError:
            page_size = 20

        # 获取当前用户的作品列表
        qs = CreationService.list_user_projects(
            request.user,
            status_filter or None,
            keyword=keyword,
            ordering=ordering,
        )
        total = qs.count()

        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        items_qs = list(qs[start:end])

        for project in items_qs:
            if (
                project.pipeline_mode == Project.MODE_WORKSPACE
                and project.status == Project.STATUS_RUNNING
            ):
                CreationService._reconcile_project_running_state(project)

        # 传入 model 实例给 Serializer（SerializerMethodField 会读取 obj.get_status_display）
        items = ProjectListSerializer(instance=items_qs, many=True)

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return Response(
            {
                "code": 0,
                "message": "success",
                "data": items.data,
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                },
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# 2. 作品详情
# ============================================================
class WorkDetailView(APIView):
    """作品详情

    GET /api/works/<project_id>/

    返回元信息 + 预渲染 HTML 片段（含数字水印）。
    绝不暴露原始剧本数据结构。

    Response:
      {
        "code": 0,
        "message": "success",
        "data": {
          "project_id": "...",
          "title": "...",
          "theme": "...",
          "episode_count": 30,
          "format_variant": "B",
          "audience": "",
          "reference_work": "",
          "status": "completed",
          "status_text": "已完成",
          "progress_percent": 100,
          "total_duration_minutes": 3,
          "created_at": "...",
          "updated_at": "...",
          "completed_at": "...",
          "rendered_result_html": "<div>...</div>",
          "rendered_progress_html": "<div>...</div>"
        }
      }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str):
        try:
            data = CreationService.get_project_detail(project_id, request.user)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"code": 0, "message": "success", "data": data},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, project_id: str):
        """DELETE /api/works/<project_id>/ — 永久删除作品及关联数据。"""
        try:
            data = CreationService.delete_user_project(project_id, request.user)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无法删除"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 0, "message": "作品已删除", "data": data},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 3. 生成分享链接（与 CreationShareCreateView 相同逻辑）
# ============================================================
class WorkShareCreateView(APIView):
    """为作品生成分享链接

    POST /api/works/<project_id>/share/
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

        result_serializer = ShareCreateResultSerializer(result)
        return Response(
            {"code": 0, "message": "success", "data": result_serializer.data},
            status=status.HTTP_200_OK,
        )


class WorkExportView(APIView):
    """GET /api/works/<project_id>/export/?format=md"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str):
        fmt = request.GET.get("format", "md")
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response(
                {"code": 404, "message": "作品不存在", "data": None},
                status=status.HTTP_200_OK,
            )
        if project.status not in {Project.STATUS_COMPLETED, Project.STATUS_AWAITING}:
            return Response(
                {"code": 4001, "message": "作品尚未完成，暂不可导出", "data": None},
                status=status.HTTP_200_OK,
            )
        try:
            payload = export_work(project, fmt)
        except ValueError as exc:
            return Response(
                {"code": 4001, "message": safe_api_message(exc, "请求无效"), "data": None},
                status=status.HTTP_200_OK,
            )
        if request.GET.get("download") == "1":
            response = HttpResponse(payload["content"], content_type=payload["content_type"])
            response["Content-Disposition"] = f'attachment; filename="{payload["filename"]}"'
            return response
        return Response(
            {"code": 0, "message": "success", "data": payload},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 4. 作品统计（可选：给前端 /works 页面顶部展示摘要）
# ============================================================
class WorkPolishApplyView(APIView):
    """POST /api/works/<project_id>/agents/polish/apply/ — 用户确认后写回润色建议。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str):
        body = request.data if isinstance(request.data, dict) else {}
        try:
            data = CreationService.apply_work_polish(
                project_id,
                request.user,
                indices=body.get("indices"),
                apply_all=bool(body.get("apply_all")),
                patch_script_fields=bool(body.get("patch_script_fields")),
            )
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 0, "message": "success", "data": data},
            status=status.HTTP_200_OK,
        )


class WorkAgentRunView(APIView):
    """POST /api/works/<project_id>/agents/<agent_id>/run/ — 触发 Agent。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str, agent_id: str):
        try:
            data = CreationService.run_work_agent(project_id, request.user, agent_id)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 0, "message": "success", "data": data},
            status=status.HTTP_200_OK,
        )


class WorkStatsView(APIView):
    """我的作品统计摘要

    GET /api/works/stats/

    Response:
      {
        "code": 0,
        "message": "success",
        "data": {
          "total": 42,
          "pending": 2,
          "running": 1,
          "completed": 38,
          "failed": 1
        }
      }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = CreationService.list_user_projects(request.user)
        total = qs.count()
        pending = qs.filter(status=Project.STATUS_PENDING).count()
        running = qs.filter(status=Project.STATUS_RUNNING).count()
        completed = qs.filter(status=Project.STATUS_COMPLETED).count()
        failed = qs.filter(status=Project.STATUS_FAILED).count()

        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "total": total,
                    "pending": pending,
                    "running": running,
                    "completed": completed,
                    "failed": failed,
                },
            },
            status=status.HTTP_200_OK,
        )
