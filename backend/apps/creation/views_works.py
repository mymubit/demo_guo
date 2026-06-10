"""
作品管理 API 视图

路由 /api/works/...

  GET /              我的作品列表（分页）
  GET /<id>/         作品详情（仅预渲染 HTML，不暴露原始剧本数据结构）
  GET /<id>/share/ 分享信息（同 creation.share 的作品详情分享接口）

注意：
- 所有内容以 HTML 片段形式返回，绝不包含原始剧本正文的 JSON 结构。
"""

import logging

from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from .serializers import ProjectListSerializer
from .services import CreationService

logger = logging.getLogger(__name__)


# ============================================================
# 1. 我的作品列表
# ============================================================
class WorksListView(APIView):
    """我的作品列表

    GET /api/works/?status=completed&page=1&page_size=10

    仅返回列表元信息（标题、题材、集数、状态、创建时间），
    绝不包含剧本正文。
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get(self, request):
        status_filter = request.GET.get("status", "").strip()
        qs = CreationService.list_user_projects(
            request.user, status_filter=status_filter or None
        )

        # 分页
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request, view=self)

        serializer = ProjectListSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


# ============================================================
# 2. 作品详情（只返回预渲染 HTML 片段）
# ============================================================
class WorksDetailView(APIView):
    """作品详情

    GET /api/works/<project_id>/

    返回：
      - 基本元信息（title/theme/episode_count/status）
      - rendered_result_html：已完成作品的预渲染 HTML 片段
      - rendered_progress_html：进度卡片 HTML 片段

    绝不返回原始剧本的 JSON 数据结构。
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str):
        try:
            detail = CreationService.get_project_detail(project_id, request.user)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": str(exc) or "无权限", "data": None},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"code": 0, "message": "success", "data": detail},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 3. 作品分享信息（列表接口中分享按钮直接复用 creation.views 的分享生成）
# 简化：在作品详情页可直接调用 /api/creation/share/<project_id>/ 生成分享，
# 这里仅保留一个便捷接口，方便前端直接拿分享链接
# ============================================================
class WorksShareView(APIView):
    """为作品生成分享链接（与 creation.share 语义一致）

    POST /api/works/<project_id>/share/
    Body: { "view_limit": 100, "valid_days": 7, "allow_download": false }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id: str):
        # 复用 creation 模块的分享生成
        from .views import CreationShareCreateView

        return CreationShareCreateView.as_view()(request, project_id=project_id)
