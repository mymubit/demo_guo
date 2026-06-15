# -*- coding: utf-8 -*-
"""后台：Agent Registry 配置读写。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.agent.registry import AgentRegistryConfigService

from apps.console.responses import api_fail, api_ok


class AgentRegistryConfigView(APIView):
    """GET/PUT /api/admin/agent/registry/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return api_ok(AgentRegistryConfigService.admin_payload())

    def put(self, request):
        data = request.data or {}
        registry = data.get("registry")
        if registry is None:
            return api_fail("缺少 registry 字段")
        try:
            row = AgentRegistryConfigService.save_registry(
                registry,
                note=str(data.get("note") or "后台保存")[:255],
                activate=data.get("activate", True) is not False,
            )
        except ValueError as exc:
            return api_fail(str(exc))
        payload = AgentRegistryConfigService.admin_payload()
        payload["saved_id"] = str(row.id)
        return api_ok(payload, message="技能注册表已保存并生效")


class AgentRegistryMigrateView(APIView):
    """POST /api/admin/agent/registry/migrate/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        from apps.agent.routes import AgentLlmRouteService

        AgentRegistryConfigService.ensure_defaults()
        seeded = AgentLlmRouteService.seed_defaults()
        migrated = AgentRegistryConfigService.migrate_pipeline_skill_config()
        payload = AgentRegistryConfigService.admin_payload()
        payload["migrated_count"] = migrated
        payload["seeded_routes"] = seeded
        return api_ok(payload, message=f"已迁移 {migrated} 个技能配置")


class AgentRegistryImportView(APIView):
    """POST /api/admin/agent/registry/import/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        overwrite = (request.data or {}).get("overwrite", True) is not False
        try:
            AgentRegistryConfigService.import_from_file(overwrite=overwrite)
        except ValueError as exc:
            return api_fail(str(exc))
        except FileNotFoundError as exc:
            return api_fail(str(exc))
        return api_ok(AgentRegistryConfigService.admin_payload(), message="已从磁盘 registry.json 导入")
