# -*- coding: utf-8 -*-
"""主链工作室 API。"""
from rest_framework.permissions import IsAuthenticated

from apps.common.agent_term import attach_api_meta
from apps.common.permissions import IsAdminUser

from apps.console.base_views import AdminAPIView
from apps.console.responses import api_fail, api_ok
from apps.console.main_chain.blueprint_service import MainChainBlueprintService


class MainChainBlueprintView(AdminAPIView):
    """GET /api/admin/main-chain/blueprint/ — 主链蓝图聚合。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        payload = MainChainBlueprintService.build_blueprint()
        return api_ok(attach_api_meta(payload))


class MainChainStepPatchView(AdminAPIView):
    """PUT /api/admin/main-chain/steps/<uuid>/ — 更新单步（运营 + Agent 技能字段）。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, step_id=None):
        try:
            step = MainChainBlueprintService.patch_step(str(step_id), request.data or {})
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(step, message="步骤已保存")


class MainChainRegistryMetaView(AdminAPIView):
    """PUT /api/admin/main-chain/registry-meta/ — 更新后处理链等 _meta 编排。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request):
        try:
            meta = MainChainBlueprintService.patch_registry_meta(request.data or {})
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(meta, message="编排元数据已保存")
