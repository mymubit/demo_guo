# -*- coding: utf-8 -*-
"""C 端用户主动反馈 + 行为埋点上报视图。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.console.responses import api_fail, api_ok

from . import services
from .models import CreationFeedback
from .serializers import (
    CreationFeedbackCreateSerializer,
    CreationFeedbackSerializer,
    UserBehaviorEventCreateSerializer,
    UserBehaviorEventSerializer,
)


class PortalFeedbackCreateView(APIView):
    """POST /api/operations/feedback/create/ — C 端用户主动提交反馈。"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreationFeedbackCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_fail("提交失败：" + str(serializer.errors), code=400)
        data = serializer.validated_data
        # 校验 project 归属
        project = data.get("project")
        if project and project.user_id != request.user.id:
            return api_fail("无权限关联该项目", code=403)
        feedback = CreationFeedback.objects.create(
            user=request.user,
            project=project,
            category=data["category"],
            severity=data.get("severity", CreationFeedback.Severity.P2),
            source=CreationFeedback.Source.WORKSPACE,
            title=data["title"],
            content=data.get("content", ""),
            contact=data.get("contact", ""),
            tags=data.get("tags", []),
        )
        return api_ok(CreationFeedbackSerializer(feedback).data)


class PortalFeedbackListView(APIView):
    """GET /api/operations/feedback/ — 用户查看自己提交的反馈。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = CreationFeedback.objects.filter(user=request.user).order_by("-created_at")[:50]
        return api_ok(CreationFeedbackSerializer(qs, many=True).data)


# ============================================================
# C 端用户行为埋点上报（M6）
# ============================================================
class PortalTrackEventView(APIView):
    """POST /api/operations/track/ — 前端事件上报（可匿名）。

    设计：
      • 失败必须返回 ok：埋点不能影响主流程。
      • 6 个核心事件 + 自定义 event_name 都被允许，但仅 6 个核心会被写入。
      • 用户可空（未登录访问 landing_view）。
    """

    permission_classes = []  # 允许匿名

    def post(self, request):
        serializer = UserBehaviorEventCreateSerializer(data=request.data)
        if not serializer.is_valid():
            # 埋点失败不能阻塞前端
            return api_ok({"recorded": False, "reason": "invalid_payload"})
        data = serializer.validated_data
        user = request.user if getattr(request.user, "is_authenticated", False) else None
        services.track_event(
            event_name=data["event_name"],
            user=user,
            session_id=data.get("session_id", ""),
            project_id=data.get("project_id", ""),
            page=data.get("page", ""),
            payload=data.get("payload", {}),
            source="frontend",
            request=request,
        )
        return api_ok({"recorded": True})
