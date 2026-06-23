# -*- coding: utf-8 -*-
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
from apps.creation.services.works import build_user_work_list_page

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
        scope = request.GET.get("scope", "").strip()
        try:
            page = max(1, int(request.GET.get("page", "1")))
        except ValueError:
            page = 1
        try:
            page_size = min(100, max(1, int(request.GET.get("page_size", "20"))))
        except ValueError:
            page_size = 20

        payload = build_user_work_list_page(
            request.user,
            page=page,
            page_size=page_size,
            status_filter=status_filter or None,
            keyword=keyword,
            ordering=ordering,
            scope=scope,
        )

        return Response(
            {
                "code": 0,
                "message": "success",
                "data": payload["items"],
                "pagination": payload["pagination"],
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
            try:
                from apps.drama.progress_service import DramaProgressService

                from apps.creation.models import Project
                ws_project = Project.objects.filter(id=project_id, user=request.user).first()
                if ws_project and ws_project.is_drama_workspace:
                    data["drama"] = DramaProgressService.build_admin_summary(ws_project)
                    data["drama_workspace_url"] = f"/drama/workspace/{ws_project.id}"
                    data["progress_percent"] = int(ws_project.get_completion_rate())
            except Exception:  # noqa: BLE001
                pass
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
        if project.execution_status not in {Project.STATUS_COMPLETED, Project.STATUS_AWAITING}:
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
        from apps.creation.project_execution import filter_projects_by_execution_status

        qs = CreationService.list_user_projects(request.user)
        total = qs.count()
        pending = filter_projects_by_execution_status(qs, Project.STATUS_PENDING).count()
        running = filter_projects_by_execution_status(qs, Project.STATUS_RUNNING).count()
        completed = filter_projects_by_execution_status(qs, Project.STATUS_COMPLETED).count()
        failed = filter_projects_by_execution_status(qs, Project.STATUS_FAILED).count()

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
