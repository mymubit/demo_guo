# -*- coding: utf-8 -*-
"""operations 视图层。

路由：
  /api/admin/operations/dashboard/      聚合 Dashboard
  /api/admin/operations/content-quality/ 内容质量
  /api/admin/operations/feedback/       反馈列表 / 详情 / 录入 / 处理
  /api/admin/operations/config-hit/      配置命中率
  /api/admin/operations/samples/        抽样候选

  /api/portal/operations/feedback/      C 端用户主动反馈
"""
from __future__ import annotations

import logging

from django.db.models import Count, Q
from rest_framework import status as drf_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.common.pagination import StandardPagination
from apps.console.responses import api_fail, api_ok

from . import services
from .models import CreationFeedback
from .serializers import (
    CreationFeedbackCreateSerializer,
    CreationFeedbackHandleSerializer,
    CreationFeedbackSerializer,
)

logger = logging.getLogger(__name__)


# ============================================================
# Dashboard
# ============================================================
class OperationsDashboardView(APIView):
    """GET /api/admin/operations/dashboard/ — 运营 Dashboard 聚合。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            days = int(request.query_params.get("days", "30"))
        except (TypeError, ValueError):
            days = 30
        days = max(1, min(90, days))
        data = services.full_dashboard(days=days)
        return api_ok(data)


# ============================================================
# Content Quality
# ============================================================
class ContentQualityView(APIView):
    """GET /api/admin/operations/content-quality/ — 内容质量看板。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            days = int(request.query_params.get("days", "30"))
        except (TypeError, ValueError):
            days = 30
        days = max(1, min(90, days))
        return api_ok(services.content_quality_dashboard(days=days))


# ============================================================
# Config Hit
# ============================================================
class ConfigHitView(APIView):
    """GET /api/admin/operations/config-hit/ — 配置命中率。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", "30"))
        except (TypeError, ValueError):
            limit = 30
        limit = max(5, min(100, limit))
        return api_ok(services.config_hit_dashboard(limit=limit))


# ============================================================
# Feedback list / detail
# ============================================================
class FeedbackListView(APIView):
    """GET /api/admin/operations/feedback/ — 反馈列表（分页 + 过滤）。"""

    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardPagination

    def get(self, request):
        status_filter = (request.query_params.get("status") or "").strip()
        category = (request.query_params.get("category") or "").strip()
        severity = (request.query_params.get("severity") or "").strip()
        source = (request.query_params.get("source") or "").strip()
        keyword = (request.query_params.get("keyword") or "").strip()
        p0_only = (request.query_params.get("p0_only") or "").strip().lower() in (
            "1", "true", "yes",
        )

        qs = CreationFeedback.objects.select_related("user", "project", "handler").order_by("-created_at")
        if status_filter:
            qs = qs.filter(status=status_filter)
        if category:
            qs = qs.filter(category=category)
        if severity:
            qs = qs.filter(severity=severity)
        if source:
            qs = qs.filter(source=source)
        if p0_only:
            qs = qs.filter(severity="P0", status__in=["open", "in_progress"])
        if keyword:
            qs = qs.filter(
                Q(title__icontains=keyword) | Q(content__icontains=keyword)
            )

        # facets
        if (request.query_params.get("facets") or "").strip().lower() in ("1", "true", "yes"):
            base = CreationFeedback.objects.all()
            facets = {
                "all": base.count(),
                "open": base.filter(status="open").count(),
                "in_progress": base.filter(status="in_progress").count(),
                "resolved": base.filter(status="resolved").count(),
                "p0_open": base.filter(
                    severity="P0", status__in=["open", "in_progress"]
                ).count(),
                "by_category": dict(
                    base.values_list("category").annotate(c=Count("id")).values_list("category", "c")
                ),
                "by_severity": dict(
                    base.values_list("severity").annotate(c=Count("id")).values_list("severity", "c")
                ),
                "by_source": dict(
                    base.values_list("source").annotate(c=Count("id")).values_list("source", "c")
                ),
            }
        else:
            facets = None

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = CreationFeedbackSerializer(page, many=True)
        response = paginator.get_paginated_response(serializer.data)
        if facets is not None:
            response.data["facets"] = facets
        # 解包为统一格式
        pagination_meta = response.data.get("pagination") or {}
        total = pagination_meta.get("total", 0)
        return api_ok({
            "items": serializer.data,
            "pagination": {
                "total": total,
                "page": int(request.query_params.get("page", "1")),
                "page_size": paginator.page_size,
                "total_pages": pagination_meta.get(
                    "total_pages",
                    ((total + paginator.page_size - 1) // paginator.page_size)
                    if paginator.page_size
                    else 0,
                ),
            },
            "facets": facets,
        })


class FeedbackDetailView(APIView):
    """GET/PATCH/DELETE /api/admin/operations/feedback/<id>/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_object(self, feedback_id):
        try:
            return CreationFeedback.objects.get(pk=feedback_id)
        except CreationFeedback.DoesNotExist:
            return None

    def get(self, request, feedback_id):
        obj = self.get_object(feedback_id)
        if not obj:
            return api_fail("反馈不存在", code=404, http_status=drf_status.HTTP_404_NOT_FOUND)
        return api_ok(CreationFeedbackSerializer(obj).data)

    def patch(self, request, feedback_id):
        obj = self.get_object(feedback_id)
        if not obj:
            return api_fail("反馈不存在", code=404, http_status=drf_status.HTTP_404_NOT_FOUND)
        serializer = CreationFeedbackHandleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from django.utils import timezone
        if "status" in data:
            obj.status = data["status"]
        if "handler_note" in data:
            obj.handler_note = data["handler_note"]
        if "tags" in data:
            obj.tags = data["tags"]
        if "handler" in data:
            if data["handler"]:
                obj.handler_id = data["handler"]
            else:
                obj.handler = None

        # 状态变 resolved/wont_fix 时自动记录 handled_at
        if obj.status in ["resolved", "wont_fix"] and not obj.handled_at:
            obj.handled_at = timezone.now()
        if "handler" in data and data["handler"] and not obj.handled_at:
            obj.handled_at = timezone.now()

        obj.save()
        return api_ok(CreationFeedbackSerializer(obj).data)

    def delete(self, request, feedback_id):
        obj = self.get_object(feedback_id)
        if not obj:
            return api_fail("反馈不存在", code=404, http_status=drf_status.HTTP_404_NOT_FOUND)
        obj.delete()
        return api_ok({"id": str(feedback_id), "deleted": True})


class FeedbackSummaryView(APIView):
    """GET /api/admin/operations/feedback/summary/ — 反馈汇总。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            days = int(request.query_params.get("days", "30"))
        except (TypeError, ValueError):
            days = 30
        days = max(1, min(90, days))
        return api_ok(services.feedback_summary(days=days))


# ============================================================
# Sample Projects（运营抽样回访）
# ============================================================
class SampleListView(APIView):
    """GET /api/admin/operations/samples/ — 抽样候选。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            days = int(request.query_params.get("days", "7"))
            limit = int(request.query_params.get("limit", "20"))
        except (TypeError, ValueError):
            days, limit = 7, 20
        days = max(1, min(30, days))
        limit = max(5, min(50, limit))
        return api_ok({
            "items": services.sample_projects_for_feedback(days=days, limit=limit),
        })


class SampleMarkView(APIView):
    """POST /api/admin/operations/samples/mark/ — 标记已抽样。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        ids = request.data.get("project_ids") or []
        if not isinstance(ids, list):
            return api_fail("project_ids 必须是列表", code=400)
        n = services.mark_projects_sampled([str(x) for x in ids])
        return api_ok({"updated": n})


# ============================================================
# 用户行为埋点（M6 后台查询）
# ============================================================
class BehaviorEventListView(APIView):
    """GET /api/admin/operations/behavior/ — 行为事件列表（带 funnel 概览）。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from .models import UserBehaviorEvent

        try:
            days = int(request.query_params.get("days", "7"))
        except (TypeError, ValueError):
            days = 7
        days = max(1, min(30, days))

        event_name = (request.query_params.get("event_name") or "").strip()
        try:
            limit = min(500, max(10, int(request.query_params.get("limit", "100"))))
        except (TypeError, ValueError):
            limit = 100

        qs = UserBehaviorEvent.objects.select_related("user").order_by("-created_at")
        if event_name:
            qs = qs.filter(event_name=event_name)
        from datetime import timedelta
        from django.utils import timezone as dj_tz
        threshold_dt = dj_tz.now() - timedelta(days=days)
        qs = qs.filter(created_at__gte=threshold_dt)

        items = list(qs[:limit])
        data = {
            "funnel": services.behavior_funnel(days=days),
            "items": [
                {
                    "id": str(e.id),
                    "event_name": e.event_name,
                    "source": e.source,
                    "user_id": str(e.user_id) if e.user_id else "",
                    "session_id": e.session_id,
                    "project_id": e.project_id,
                    "page": e.page,
                    "payload": e.payload,
                    "created_at": e.created_at.isoformat() if e.created_at else "",
                }
                for e in items
            ],
        }
        return api_ok(data)
