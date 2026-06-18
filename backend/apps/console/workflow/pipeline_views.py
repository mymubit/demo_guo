# -*- coding: utf-8 -*-
"""主链步骤统一 Admin API。"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.common.agent_term import attach_api_meta
from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.workflow.step_admin import PipelineStepAdminService

from apps.console.responses import api_fail, api_ok


class PipelineStepListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return api_ok(
            attach_api_meta(
                {
                    "items": PipelineStepAdminService.list_steps(),
                    "meta": PipelineStepAdminService.meta_payload(),
                    "tier1_section_catalog": PipelineStepAdminService.tier1_section_catalog(),
                    "tier1_section_catalog_detail": PipelineStepAdminService.tier1_section_catalog_detail(),
                }
            )
        )


class PipelineStepSyncView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        try:
            FusionPipelineDbService.ensure_builtin_default_pack()
        except Exception as exc:  # noqa: BLE001
            return api_fail(f"初始化 DB-only 主链失败：{exc}")
        from apps.agent.registry import AgentRegistryConfigService

        migrated = AgentRegistryConfigService.migrate_pipeline_skill_config()
        return api_ok(
            {
                **PipelineStepAdminService.meta_payload(),
                "migrated_agent_skill_configs": migrated,
            },
            message="DB-only 5 步主链已初始化",
        )
