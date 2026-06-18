# -*- coding: utf-8 -*-
"""融合元数据与 Schema 产物 API（网站适配技能 SSOT）。"""
from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.services import BillingService
from apps.workflow.services.pipeline_service import WorkflowPipelineService
from apps.common.user_messages import safe_api_message
from apps.portal.creation.legacy_gone import legacy_workspace_gone_response
from apps.workflow.fusion.ssot_catalog import get_ssot_catalog

from apps.creation.node_preview import build_node_preview
from apps.creation.services import CreationService

logger = logging.getLogger(__name__)


def _portal_response(request, data: dict, *, legacy_marker: str, canonical_path: str):
    from apps.common.agent_term import attach_deprecated_paths

    payload = {"code": 0, "message": "success", "data": data}
    if legacy_marker in (request.path or ""):
        payload = attach_deprecated_paths(payload, [canonical_path])
    return Response(payload, status=status.HTTP_200_OK)


def _portal_catalog(*, pack_id: str | None = None) -> dict:
    from apps.agent.catalog import enrich_portal_main_chain, portal_agent_catalog
    from apps.workflow.pipeline_store import FusionPipelineDbService
    from apps.workflow.services.flow_graph_service import FlowGraphPlanService

    default_pack = FusionPipelineDbService.resolve_pack_for_creation(pack_id)
    default_pack_id = str(default_pack.id) if default_pack else None

    catalog = get_ssot_catalog().public_catalog()
    catalog["mainChain"] = enrich_portal_main_chain(
        WorkflowPipelineService.portal_main_chain(pack_id=default_pack_id),
        pack_id=default_pack_id,
    )
    catalog["executionPlan"] = FlowGraphPlanService.execution_plan_payload(
        pack_id=default_pack_id
    )
    catalog["agentCatalog"] = portal_agent_catalog()
    catalog.pop("artifactKeys", None)
    catalog["currencyName"] = BillingService.currency_name()
    catalog["estimatedAutoCost"] = BillingService.estimate_auto_pipeline_cost()
    published = FusionPipelineDbService.list_portal_pipelines()
    catalog["publishedPipelines"] = published
    catalog["defaultPipelinePackId"] = default_pack_id
    if default_pack:
        catalog["activePipeline"] = FusionPipelineDbService.serialize_pack_portal(default_pack)
    return catalog


class FusionCatalogView(APIView):
    """GET /api/creation/fusion/catalog/ — 题材/平台/格式等枚举（SSOT，前端禁止硬编码）。"""

    permission_classes = [AllowAny]

    def get(self, request):
        return _portal_response(
            request,
            _portal_catalog(),
            legacy_marker="/workflow/catalog",
            canonical_path="/api/creation/fusion/catalog/",
        )


class FusionNodesView(APIView):
    """GET /api/creation/fusion/nodes/ — 主链节点（Agent 元数据 + 币价）。"""

    permission_classes = [AllowAny]

    def get(self, request):
        from apps.agent.catalog import enrich_portal_main_chain
        from apps.workflow.pipeline_store import FusionPipelineDbService

        pack_id = (request.query_params.get("pack_id") or "").strip() or None
        if pack_id:
            pack = FusionPipelineDbService.get_pack_by_id(pack_id)
            if pack is None or not pack.is_published_to_portal:
                return Response(
                    {"code": 40001, "message": "流水线不可用", "data": None},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            pack = FusionPipelineDbService.resolve_pack_for_creation(None)
        resolved_id = str(pack.id) if pack else None

        return _portal_response(
            request,
            {
                "mainChain": enrich_portal_main_chain(
                    WorkflowPipelineService.portal_main_chain(pack_id=resolved_id),
                    pack_id=resolved_id,
                ),
                "pipelinePackId": resolved_id,
                "currencyName": BillingService.currency_name(),
            },
            legacy_marker="/workflow/nodes",
            canonical_path="/api/creation/fusion/nodes/",
        )


class AgentCatalogView(APIView):
    """GET /api/creation/agents/catalog/ — Agent 体系 SSOT（registry v2）。"""

    permission_classes = [AllowAny]

    def get(self, request):
        from apps.agent.catalog import portal_agent_catalog

        return _portal_response(
            request,
            portal_agent_catalog(),
            legacy_marker="/agent/catalog",
            canonical_path="/api/creation/agents/catalog/",
        )


class AgentWorkspaceCatalogView(APIView):
    """GET /api/creation/agents/workspace-catalog/ — 独立 Agent 工作台能力目录。"""

    permission_classes = [AllowAny]

    def get(self, request):
        from apps.creation.agent_runtime.workspace import build_workspace_catalog

        return _portal_response(
            request,
            build_workspace_catalog(),
            legacy_marker="/agents/catalog",
            canonical_path="/api/creation/agents/workspace-catalog/",
        )


class FusionSnapshotView(APIView):
    """GET /api/creation/fusion/<project_id>/ — C 端脱敏快照。"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str):
        try:
            project = CreationService._get_user_project(project_id, request.user)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": safe_api_message(exc, "无权限"), "data": None},
                status=status.HTTP_200_OK,
            )
        from apps.creation.node_preview import build_portal_fusion_snapshot

        return Response(
            {
                "code": 0,
                "message": "success",
                "data": build_portal_fusion_snapshot(project),
            },
            status=status.HTTP_200_OK,
        )


class FusionArtifactView(APIView):
    """产物 JSON 不对 C 端开放。"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str, artifact_key: str):
        return Response(
            {
                "code": 403,
                "message": "请使用节点预览接口 /api/creation/projects/<id>/nodes/<index>/preview/",
                "data": None,
            },
            status=status.HTTP_200_OK,
        )


class CreationNodePreviewView(APIView):
    """GET /api/creation/projects/<project_id>/nodes/<node_index>/preview/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str, node_index: int):
        return legacy_workspace_gone_response()
