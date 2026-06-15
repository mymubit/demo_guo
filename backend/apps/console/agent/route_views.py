# -*- coding: utf-8 -*-
"""模型中心 — 技能 LLM 路由配置。"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok


class AgentLlmRouteListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from apps.agent.routes import AgentLlmRouteService

        return api_ok({"items": AgentLlmRouteService.list_admin_items()})

    def post(self, request):
        from apps.agent.routes import AgentLlmRouteService

        data = request.data or {}
        route_key = (data.get("route_key") or "").strip()
        if not route_key:
            return api_fail("route_key 不能为空")
        try:
            row = AgentLlmRouteService.upsert(route_key, data)
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(
            {"id": str(row.id), "route_key": row.route_key},
            message="技能路由已保存",
            http_status=status.HTTP_201_CREATED,
        )


class AgentLlmRouteDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, route_id=None):
        from apps.agent.routes import AgentLlmRouteService
        from apps.agent.models import AgentLlmRouteConfig

        try:
            row = AgentLlmRouteConfig.objects.get(pk=route_id)
        except AgentLlmRouteConfig.DoesNotExist:
            return api_fail("技能路由不存在")
        try:
            AgentLlmRouteService.upsert(row.route_key, request.data or {})
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(None, message="技能路由已更新")


class AgentLlmRouteSeedView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        from apps.agent.routes import AgentLlmRouteService

        created = AgentLlmRouteService.seed_defaults()
        return api_ok({"created": created}, message=f"已同步 {created} 条技能路由占位")
