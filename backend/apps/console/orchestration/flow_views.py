# -*- coding: utf-8 -*-
"""调度中心 · 流程编排 API（统一读写蓝图、重排、后处理链）。"""
from rest_framework.permissions import IsAuthenticated

from apps.common.agent_term import attach_api_meta
from apps.common.permissions import IsAdminUser

from apps.console.base_views import AdminAPIView
from apps.console.responses import api_fail, api_ok
from apps.console.main_chain.blueprint_service import MainChainBlueprintService
from apps.console.orchestration.publish_service import OrchestrationPublishService
from apps.workflow.step_admin import PipelineStepAdminService


class OrchestrationFlowBlueprintView(AdminAPIView):
    """GET /api/admin/orchestration/flow/blueprint/ — 流程编排蓝图。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        payload = MainChainBlueprintService.build_blueprint()
        return api_ok(attach_api_meta(payload))


class OrchestrationFlowStepPatchView(AdminAPIView):
    """PUT /api/admin/orchestration/flow/steps/<uuid>/ — 更新单步。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, step_id=None):
        try:
            step = MainChainBlueprintService.patch_step(str(step_id), request.data or {})
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(step, message="步骤已保存")


class OrchestrationFlowStepsReorderView(AdminAPIView):
    """PUT /api/admin/orchestration/flow/steps/reorder/ — 拖拽重排 chain_order。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request):
        ordered_ids = request.data.get("ordered_ids") or request.data.get("order") or []
        if not isinstance(ordered_ids, list) or not ordered_ids:
            return api_fail("ordered_ids 不能为空")
        try:
            steps = PipelineStepAdminService.reorder_steps(ordered_ids)
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok({"steps": steps}, message="流程顺序已更新")


class OrchestrationFlowRegistryMetaView(AdminAPIView):
    """PUT /api/admin/orchestration/flow/registry-meta/ — 后处理链与画布元数据。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request):
        try:
            meta = MainChainBlueprintService.patch_registry_meta(request.data or {})
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(meta, message="编排元数据已保存")


class OrchestrationFlowPublishView(AdminAPIView):
    """POST /api/admin/orchestration/flow/publish/ — 发布编排蓝图到 C 端。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        note = str((request.data or {}).get("note") or "").strip()
        try:
            payload = OrchestrationPublishService.publish(note=note)
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(payload, message="编排蓝图已发布")
