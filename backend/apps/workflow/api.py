# -*- coding: utf-8 -*-
"""工作流 API — Pack 发布/调试与 Legacy 入口防御。"""
from __future__ import annotations

import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.workflow.workflow_admin_api import PackPublisher, PackValidator
from apps.workflow.workflow_debug_runner import debug_pack
from apps.workflow.workflow_engine import LegacyWorkflowRemovedError

logger = logging.getLogger(__name__)


class WorkflowPackAdminViewSet(viewsets.ViewSet):
    """面向管理员的 pack 发布/校验/调试接口。"""
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["GET"], url_path="debug-run")
    def debug_run(self, request, pk=None):
        from apps.workflow.models import FusionPipelinePack

        try:
            pack = FusionPipelinePack.objects.get(id=pk)
        except FusionPipelinePack.DoesNotExist:
            return Response({"error": "pack 不存在"}, status=status.HTTP_404_NOT_FOUND)

        mock_context = request.query_params.dict() if request.query_params else {}
        report = debug_pack(pack, mock_context=mock_context)
        return Response(report)

    @action(detail=True, methods=["POST"], url_path="validate")
    def validate(self, request, pk=None):
        from apps.workflow.models import FusionPipelinePack

        try:
            pack = FusionPipelinePack.objects.get(id=pk)
        except FusionPipelinePack.DoesNotExist:
            return Response({"error": "pack 不存在"}, status=status.HTTP_404_NOT_FOUND)

        issues = PackValidator(pack).validate()
        return Response({
            "total": len(issues),
            "has_errors": sum(1 for i in issues if getattr(i, "level", "") == "error"),
            "issues": [issue.to_dict() for issue in issues],
        })

    @action(detail=True, methods=["POST"], url_path="publish")
    def publish(self, request, pk=None):
        from apps.workflow.models import FusionPipelinePack

        try:
            pack = FusionPipelinePack.objects.get(id=pk)
        except FusionPipelinePack.DoesNotExist:
            return Response({"error": "pack 不存在"}, status=status.HTTP_404_NOT_FOUND)

        gray_weight = int(request.data.get("gray_weight", 100) or 100)
        ok, issues, message = PackPublisher(pack).publish(
            gray_weight=gray_weight,
            published_by=getattr(request.user, "username", "admin"),
        )
        return Response({
            "ok": ok,
            "pack_version": pack.version,
            "pack_status": pack.pack_status,
            "gray_weight": pack.gray_weight,
            "message": message,
            "issues": [getattr(i, "to_dict", lambda: {})() for i in issues],
        }, status=status.HTTP_200_OK if ok else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["POST"], url_path="pause")
    def pause(self, request, pk=None):
        from apps.workflow.models import FusionPipelinePack

        try:
            pack = FusionPipelinePack.objects.get(id=pk)
        except FusionPipelinePack.DoesNotExist:
            return Response({"error": "pack 不存在"}, status=status.HTTP_404_NOT_FOUND)
        PackPublisher(pack).pause(by=getattr(request.user, "username", "admin"))
        return Response({"pack_status": pack.pack_status})

    @action(detail=True, methods=["POST"], url_path="health")
    def health(self, request, pk=None):
        from apps.workflow.workflow_monitoring import pack_health_score
        from apps.workflow.models import FusionPipelinePack

        try:
            pack = FusionPipelinePack.objects.get(id=pk)
        except FusionPipelinePack.DoesNotExist:
            return Response({"error": "pack 不存在"}, status=status.HTTP_404_NOT_FOUND)
        return Response(pack_health_score(pack, last_n=50))


class WorkflowMetricsViewSet(viewsets.ViewSet):
    """监控指标（基于 AgentExecutionRun）。"""
    permission_classes = [IsAdminUser]

    def list(self, request):
        from apps.workflow.workflow_monitoring import collect_pipeline_metrics

        minutes = int(request.query_params.get("last_n_minutes", 10) or 10)
        fmt = (request.query_params.get("format") or "json").lower()
        if fmt in ("prom", "prometheus", "text"):
            from django.http import HttpResponse
            from apps.workflow.workflow_monitoring import export_prometheus_metrics

            return HttpResponse(
                export_prometheus_metrics(last_n_minutes=minutes),
                content_type="text/plain; version=0.0.4; charset=utf-8",
            )
        return Response(collect_pipeline_metrics(last_n_minutes=minutes))


class WorkflowLaunchViewSet(viewsets.ViewSet):
    """创作中心 —— Legacy workflow 发起入口（已下线）。"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["POST"], url_path="start")
    def start(self, request):
        raise LegacyWorkflowRemovedError("workflow 发起创作已下线，请使用独立 Agent 工作台")


__all__ = [
    "WorkflowPackAdminViewSet",
    "WorkflowMetricsViewSet",
    "WorkflowLaunchViewSet",
]
