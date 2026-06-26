# -*- coding: utf-8 -*-
"""创作元数据 API — drama.* 新体系。

旧的 FusionPipelineDbService、FusionNodesView 等已移除。
现在直接使用 get_creation_catalog() 和 portal_agent_catalog()。
"""
from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.services import BillingService
from apps.skill.config.portal.creation_catalog import get_creation_catalog
from apps.creation.services import CreationService

logger = logging.getLogger(__name__)


def _portal_catalog() -> dict:
    from apps.agent.catalog import portal_agent_catalog

    catalog = get_creation_catalog().public_catalog()
    catalog["mainChain"] = []
    catalog["executionPlan"] = {"mode": "drama_skills", "hint": "使用 Drama Skills 工作台"}
    catalog["agentCatalog"] = portal_agent_catalog()
    catalog.pop("artifactKeys", None)
    catalog["currencyName"] = BillingService.currency_name()
    catalog["estimatedAutoCost"] = BillingService.estimate_auto_pipeline_cost()
    catalog["publishedPipelines"] = []
    catalog["defaultPipelinePackId"] = None
    return catalog


class FusionCatalogView(APIView):
    """GET /api/creation/fusion/catalog/ — 题材/平台/格式等枚举（SSOT）。"""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {"code": 0, "message": "success", "data": _portal_catalog()},
            status=status.HTTP_200_OK,
        )


class AgentCatalogView(APIView):
    """GET /api/creation/agents/catalog/ — Agent 体系（drama.* 12 角色）。"""

    permission_classes = [AllowAny]

    def get(self, request):
        from apps.agent.catalog import portal_agent_catalog
        track_mode = request.query_params.get("track_mode", "fast")
        agents = portal_agent_catalog(track_mode=track_mode)
        return Response(
            {"code": 0, "message": "success", "data": {"agents": agents, "total": len(agents)}},
            status=status.HTTP_200_OK,
        )


class AgentWorkspaceCatalogView(APIView):
    """GET /api/creation/agents/workspace-catalog/ — 工作台 Agent 目录（含完成状态）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.agent.catalog import get_workspace_catalog
        project_id = request.query_params.get("project_id", "")
        data = get_workspace_catalog(project_id=project_id, user_id=request.user.id)
        return Response(
            {"code": 0, "message": "success", "data": data},
            status=status.HTTP_200_OK,
        )


class FusionNodesView(APIView):
    """GET /api/creation/fusion/nodes/ — 已移除（旧7节点主链不再存在）。"""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {"code": 410, "message": "旧节点系统已移除，请使用 /api/drama/ 接口"},
            status=status.HTTP_410_GONE,
        )
