# -*- coding: utf-8 -*-
"""工作流执行 API —— 管理端 RESTful 接口
========================================================
面向管理后台 + 前端调度器使用 DRF 对外暴露：

  GET  /api/workflow/instances/                 —— 实例列表（分页/筛选）
  GET  /api/workflow/instances/<id>/            —— 实例详情 + 上下文 + 节点执行 timeline
  GET  /api/workflow/instances/<id>/progress/     —— 简化的进度条（轻量，前端轮询）
  POST /api/workflow/instances/<id>/cancel/     —— 取消
  POST /api/workflow/instances/<id>/resume/       —— 从断点恢复
  POST /api/workflow/instances/<id>/retry/         —— 从头重跑（建新实例）

  GET  /api/workflow/packs/<id>/debug-run/      —— 发布前干跑（预估耗时/金币/检测条件）
  POST /api/workflow/packs/<id>/validate/       —— 发布前校验
  POST /api/workflow/packs/<id>/publish/        —— 发布/灰度/回滚

注意：本文件仅定义 Serializers + Views，由 urls.py 路由注册。
========================================================
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.workflow.execution_models import NodeExecution, WorkflowInstance
from apps.workflow.workflow_admin_api import PackPublisher, PackValidator
from apps.workflow.workflow_debug_runner import debug_pack
from apps.workflow.workflow_engine import get_instance_progress
from apps.workflow.workflow_monitoring import pack_health_score, collect_pipeline_metrics

logger = logging.getLogger(__name__)


# =========================================================
# Serializers
# =========================================================
class NodeExecutionSerializer(serializers.ModelSerializer):
    """节点执行记录 —— 用于实例详情页 timeline。"""
    elapsed_ms = serializers.SerializerMethodField()

    class Meta:
        model = NodeExecution
        fields = [
            "id", "node_id", "node_name", "runner_type", "status",
            "attempt", "max_retries", "coin_cost", "duration_ms",
            "started_at", "finished_at", "elapsed_ms", "agent_execution_run_ids",
        ]
        read_only_fields = fields

    def get_elapsed_ms(self, obj: NodeExecution) -> int:
        if obj.duration_ms:
            return int(obj.duration_ms)
        if obj.started_at and obj.finished_at:
            return int((obj.finished_at - obj.started_at).total_seconds() * 1000)
        return 0


class WorkflowInstanceListSerializer(serializers.ModelSerializer):
    """实例列表 —— 轻量字段。"""
    pack_version = serializers.CharField(source="pack.version", read_only=True)
    pack_name = serializers.CharField(source="pack.display_name",
                                     read_only=True, default="")

    class Meta:
        model = WorkflowInstance
        fields = [
            "id", "pack", "pack_version", "pack_name", "user_id", "status",
            "started_at", "finished_at", "total_duration_ms", "coin_cost_total",
            "llm_token_in_total", "llm_token_out_total", "trigger_type",
            "current_node_id", "created_at", "updated_at",
        ]
        read_only_fields = fields


class WorkflowInstanceDetailSerializer(serializers.ModelSerializer):
    """实例详情 —— 带节点 timeline 和上下文摘要。"""
    pack_version = serializers.CharField(source="pack.version", read_only=True)
    nodes = serializers.SerializerMethodField()
    progress_pct = serializers.SerializerMethodField()
    context_summary = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowInstance
        fields = [f for f in WorkflowInstanceListSerializer.Meta.fields] + [
            "nodes", "progress_pct", "context_summary", "failure_reason",
        ]
        read_only_fields = fields

    def get_nodes(self, obj: WorkflowInstance) -> List[Dict[str, Any]]:
        qs = NodeExecution.objects.filter(instance=obj).order_by("created_at")
        return NodeExecutionSerializer(qs, many=True).data

    def get_progress_pct(self, obj: WorkflowInstance) -> int:
        data = get_instance_progress(obj)
        return int(data.get("progress_pct", 0))

    def get_context_summary(self, obj: WorkflowInstance) -> Dict[str, Any]:
        ctx = obj.context or {}
        keys = list(ctx.keys()) if isinstance(ctx, dict) else []
        return {
            "keys": keys[:50],
            "total_keys": len(keys),
        }


# =========================================================
# ViewSets
# =========================================================
class WorkflowInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """工作流实例查询 + 操作。"""
    queryset = WorkflowInstance.objects.all().select_related("pack").order_by(
        "-created_at"
    )
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "pack", "trigger_type", "user_id"]
    search_fields = ["user_id", "current_node_id"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return WorkflowInstanceDetailSerializer
        return WorkflowInstanceListSerializer

    # ——————————————————
    # 轻量进度查询（前端轮询）
    # ——————————————————
    @action(detail=True, methods=["GET"], url_path="progress")
    def progress(self, request, pk=None):
        instance = self.get_object()
        return Response(get_instance_progress(instance))

    # ——————————————————
    # 取消实例
    # ——————————————————
    @action(detail=True, methods=["POST"], url_path="cancel")
    def cancel(self, request, pk=None):
        instance = self.get_object()
        instance.transition_to(
            "cancelled", reason=request.data.get("reason") or "admin_cancel"
        )
        return Response({"status": "ok", "instance_status": "cancelled"})

    # ——————————————————
    # 从断点恢复（running）
    # ——————————————————
    @action(detail=True, methods=["POST"], url_path="resume")
    def resume(self, request, pk=None):
        from apps.workflow.tasks import run_workflow_instance
        instance = self.get_object()
        if instance.status in ("failed", "paused", "waiting_human", "running"):
            start = request.data.get("start_node_id") or instance.current_node_id
            run_workflow_instance.delay(str(instance.id), start_node_id=start)
            return Response({"status": "ok", "resumed_from": start or "head"})
        return Response(
            {"status": "error", "reason": "当前状态不支持恢复: " + instance.status},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ——————————————————
    # 重试：创建新的实例（重跑）
    # ——————————————————
    @action(detail=True, methods=["POST"], url_path="retry")
    def retry(self, request, pk=None):
        old = self.get_object()
        new_instance = WorkflowInstance.objects.create(
            pack=old.pack,
            project=old.project,
            user_id=old.user_id,
            trigger_type="retry",
            context=request.data.get("context") or {},
        )
        from apps.workflow.tasks import run_workflow_instance
        run_workflow_instance.delay(str(new_instance.id))
        return Response(
            {"new_instance_id": str(new_instance.id)},
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# WorkflowPack Admin 发布/调试
# =========================================================
class WorkflowPackAdminViewSet(viewsets.ViewSet):
    """面向管理员的 pack 发布/校验/调试接口。"""
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["GET"], url_path="debug-run")
    def debug_run(self, request, pk=None):
        """干跑估算 —— 不修改数据库，仅返回预测的执行计划。"""
        from apps.workflow.models import FusionPipelinePack
        try:
            pack = FusionPipelinePack.objects.get(id=pk)
        except FusionPipelinePack.DoesNotExist:
            return Response({"error": "pack 不存在"},
                            status=status.HTTP_404_NOT_FOUND)

        mock_context = request.query_params.dict() if request.query_params else {}
        report = debug_pack(pack, mock_context=mock_context)
        return Response(report)

    @action(detail=True, methods=["POST"], url_path="validate")
    def validate(self, request, pk=None):
        """发布前校验 —— 返回 issues 列表。"""
        from apps.workflow.models import FusionPipelinePack
        try:
            pack = FusionPipelinePack.objects.get(id=pk)
        except FusionPipelinePack.DoesNotExist:
            return Response({"error": "pack 不存在"},
                            status=status.HTTP_404_NOT_FOUND)

        issues = PackValidator(pack).validate()
        return Response({
            "total": len(issues),
            "has_errors": sum(1 for i in issues if getattr(i, "level", "") == "error"),
            "issues": [issue.to_dict() for issue in issues],
        })

    @action(detail=True, methods=["POST"], url_path="publish")
    def publish(self, request, pk=None):
        """发布/灰度。请求体: {"gray_weight": 100}"""
        from apps.workflow.models import FusionPipelinePack
        try:
            pack = FusionPipelinePack.objects.get(id=pk)
        except FusionPipelinePack.DoesNotExist:
            return Response({"error": "pack 不存在"},
                            status=status.HTTP_404_NOT_FOUND)

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
        """暂停发布（置为 draft）。"""
        from apps.workflow.models import FusionPipelinePack
        try:
            pack = FusionPipelinePack.objects.get(id=pk)
        except FusionPipelinePack.DoesNotExist:
            return Response({"error": "pack 不存在"},
                            status=status.HTTP_404_NOT_FOUND)
        PackPublisher(pack).pause(by=getattr(request.user, "username", "admin"))
        return Response({"pack_status": pack.pack_status})

    @action(detail=True, methods=["POST"], url_path="health")
    def health(self, request, pk=None):
        """查询 pack 健康度（近期 50 次执行的成功率/平均耗时）。"""
        from apps.workflow.models import FusionPipelinePack
        try:
            pack = FusionPipelinePack.objects.get(id=pk)
        except FusionPipelinePack.DoesNotExist:
            return Response({"error": "pack 不存在"},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(pack_health_score(pack, last_n=50))


# =========================================================
# 全局监控指标接口
# =========================================================
class WorkflowMetricsViewSet(viewsets.ViewSet):
    """监控指标（Prometheus / Grafana 可接入。

    GET /api/admin/workflow/metrics/             → JSON 结构化指标
    GET /api/admin/workflow/metrics/?format=prom  → Prometheus exposition 文本
    """
    permission_classes = [IsAdminUser]

    def list(self, request):
        minutes = int(request.query_params.get("last_n_minutes", 10) or 10)
        fmt = (request.query_params.get("format") or "json").lower()
        if fmt in ("prom", "prometheus", "text"):
            from apps.workflow.workflow_monitoring import export_prometheus_metrics
            from django.http import HttpResponse
            return HttpResponse(
                export_prometheus_metrics(last_n_minutes=minutes),
                content_type="text/plain; version=0.0.4; charset=utf-8",
            )
        return Response(collect_pipeline_metrics(last_n_minutes=minutes))


# =========================================================
# 启动新工作流（创作入口）
# =========================================================
class WorkflowLaunchViewSet(viewsets.ViewSet):
    """创作中心 —— 供前端「开始创作」调用。"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["POST"], url_path="start")
    def start(self, request):
        """发起一次新创作任务。

        请求体:
            {
              "project_id": "<uuid>",
              "pack_id": "<uuid>",       // 可选，默认使用 pack_status='active'
              "context": {...}              // 可选的初始上下文
            }

        返回:
            {"instance_id": "...", "status": "pending"}
        """
        pack_id = request.data.get("pack_id")
        project_id = request.data.get("project_id")

        if not project_id:
            return Response(
                {"error": "缺少 project_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.creation.models import Project
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response(
                {"error": "项目不存在或无权访问"},
                status=status.HTTP_404_NOT_FOUND,
            )

        from apps.workflow.orchestration_adapter import OrchestrationAdapter
        result = OrchestrationAdapter.run(
            project=project,
            user_id=str(getattr(request.user, "id", "anonymous")),
            pack_id=pack_id,
        )
        return Response(result)


__all__ = [
    "WorkflowInstanceViewSet",
    "WorkflowPackAdminViewSet",
    "WorkflowMetricsViewSet",
    "WorkflowLaunchViewSet",
    "NodeExecutionSerializer",
    "WorkflowInstanceListSerializer",
    "WorkflowInstanceDetailSerializer",
]
