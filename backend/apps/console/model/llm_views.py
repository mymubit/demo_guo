# -*- coding: utf-8 -*-
"""Admin 多模型 LLM 配置。"""
from __future__ import annotations

from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.common.permissions import IsAdminUser
from apps.console.responses import CACHE_KEY_DASHBOARD, CACHE_KEY_STATS, api_fail, api_ok
from apps.skill.llm.model_catalog import LlmCatalogError, LlmCatalogService
from apps.skill.llm.providers import LlmProviderError, LlmProviderService
from apps.skill.llm.chat import LlmService, LlmServiceError
from apps.skill.llm.usage_log import LlmUsageService
from apps.skill.llm.vendor_keys import LlmVendorCredentialService


def _clear_skill_cache() -> None:
    try:
        cache.delete_pattern("skill:config:*")
    except Exception:
        pass
    cache.delete(CACHE_KEY_DASHBOARD)
    cache.delete(CACHE_KEY_STATS)


def _payload() -> dict:
    providers = [
        LlmProviderService.serialize(row, include_api_key=False)
        for row in LlmProviderService.list_providers()
    ]
    return {
        "global_enabled": LlmProviderService.global_enabled(),
        "providers": providers,
        "presets": LlmProviderService.list_presets(),
        "vendor_credentials": LlmVendorCredentialService.list_for_admin(include_api_key=False),
        "catalog": [
            LlmCatalogService.serialize(row)
            for row in LlmCatalogService.list_catalog()
        ],
        "vendors": LlmCatalogService.list_vendors_grouped(),
        "status": LlmProviderService.status_payload(),
    }


class LlmConfigAdminView(APIView):
    """GET /api/admin/model/llm/ — 多模型列表与状态"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return api_ok(_payload())


class LlmGlobalSettingsView(APIView):
    """PUT /api/admin/model/llm/settings/ — 全局 LLM 开关"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request):
        data = request.data or {}
        if "enabled" not in data:
            return api_fail("缺少 enabled 字段")
        LlmProviderService.set_global_enabled(bool(data["enabled"]))
        _clear_skill_cache()
        return api_ok(_payload(), message="全局 LLM 开关已更新")


class LlmProviderListCreateView(APIView):
    """GET/POST /api/admin/model/llm/providers/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        try:
            LlmProviderService.create_provider(request.data or {})
        except LlmProviderError as exc:
            return api_fail(str(exc))
        _clear_skill_cache()
        return api_ok(_payload(), message="大模型已添加", http_status=status.HTTP_201_CREATED)


class LlmProviderDetailView(APIView):
    """PUT/DELETE /api/admin/model/llm/providers/<id>/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, provider_id=None):
        try:
            LlmProviderService.update_provider(provider_id, request.data or {})
        except LlmProviderError as exc:
            return api_fail(str(exc))
        _clear_skill_cache()
        return api_ok(_payload(), message="大模型已更新")

    def delete(self, request, provider_id=None):
        try:
            LlmProviderService.delete_provider(provider_id)
        except LlmProviderError as exc:
            return api_fail(str(exc))
        _clear_skill_cache()
        return api_ok(_payload(), message="大模型已删除")


class LlmProviderActivateView(APIView):
    """POST /api/admin/model/llm/providers/<id>/activate/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, provider_id=None):
        try:
            LlmProviderService.set_active(provider_id)
        except LlmProviderError as exc:
            return api_fail(str(exc))
        _clear_skill_cache()
        return api_ok(_payload(), message="已切换为当前使用的大模型")


class LlmPresetsSyncView(APIView):
    """POST /api/admin/model/llm/presets/sync/ — 同步目录种子并补全接入项"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        catalog_new = LlmCatalogService.ensure_seed_catalog()
        provider_new = LlmProviderService.ensure_builtin_presets()
        _clear_skill_cache()
        parts = []
        if catalog_new:
            parts.append(f"目录 {catalog_new} 条")
        if provider_new:
            parts.append(f"接入 {provider_new} 条")
        msg = "已同步：" + "、".join(parts) if parts else "目录与接入均已是最新"
        return api_ok(_payload(), message=msg)


class LlmCatalogListCreateView(APIView):
    """GET/POST /api/admin/model/llm/catalog/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return api_ok({"items": [LlmCatalogService.serialize(r) for r in LlmCatalogService.list_catalog()]})

    def post(self, request):
        try:
            LlmCatalogService.create_catalog(request.data or {})
        except LlmCatalogError as exc:
            return api_fail(str(exc))
        _clear_skill_cache()
        return api_ok(_payload(), message="目录项已添加", http_status=status.HTTP_201_CREATED)


class LlmCatalogDetailView(APIView):
    """PUT/DELETE /api/admin/model/llm/catalog/<id>/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, catalog_id=None):
        data = request.data or {}
        try:
            LlmCatalogService.update_catalog(catalog_id, data)
        except LlmCatalogError as exc:
            return api_fail(str(exc))
        recalculated = 0
        if "input_price_per_million" in data or "output_price_per_million" in data:
            recalculated = LlmUsageService.recalculate_estimated_costs(all_logs=True)
        _clear_skill_cache()
        msg = "目录项已更新"
        if recalculated:
            msg = f"目录项已更新，已重算 {recalculated} 条历史用量费用"
        return api_ok(_payload(), message=msg)

    def delete(self, request, catalog_id=None):
        try:
            LlmCatalogService.delete_catalog(catalog_id)
        except LlmCatalogError as exc:
            return api_fail(str(exc))
        _clear_skill_cache()
        return api_ok(_payload(), message="目录项已删除")


class LlmConfigTestView(APIView):
    """POST /api/admin/model/llm/test/ body: { provider_id? }"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        provider_id = (request.data or {}).get("provider_id")
        if provider_id:
            target = LlmProviderService.get_by_id(provider_id)
            if target is None:
                return api_fail("指定的大模型配置不存在")
            if not LlmProviderService.provider_has_api_key(target) or not target.base_url:
                return api_fail("请先在该厂商下保存共用 API Key，并补全模型 Base URL")
        try:
            result = LlmService.test_connectivity(provider_id=provider_id, auto_save=True)
            _clear_skill_cache()
            payload = {**_payload(), **{k: v for k, v in result.items() if k not in {"ok"}}}
            return api_ok(payload, message=result.get("message") or "连通测试成功")
        except LlmServiceError as exc:
            return api_fail(str(exc))


class LlmVendorCredentialView(APIView):
    """PUT /api/admin/model/llm/vendors/<vendor>/credential/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, vendor=None):
        data = request.data or {}
        try:
            LlmVendorCredentialService.set_vendor_credential(
                vendor,
                api_key=data.get("api_key") if "api_key" in data else None,
                volcano_key_type=data.get("volcano_key_type")
                if "volcano_key_type" in data
                else None,
            )
        except ValueError as exc:
            return api_fail(str(exc))
        _clear_skill_cache()
        return api_ok(_payload(), message=f"「{vendor}」厂商 Key 已保存并同步到该厂商下已接入模型")


class LlmRoutingPlanView(APIView):
    """GET /api/admin/model/llm/routing-plan/ — Agent 分模型绑定状态"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from apps.skill.llm.setup_provisioning import AgentLlmRoutingService

        return api_ok(AgentLlmRoutingService.routing_plan())


class LlmEnvSetupView(APIView):
    """POST /api/admin/model/llm/env-setup/ — 从环境变量创建 Provider 并绑定 Agent"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        from apps.skill.llm.setup_provisioning import AgentLlmRoutingService

        data = request.data or {}
        skip_bind = bool(data.get("skip_bind"))
        provider_map = AgentLlmRoutingService.provision_all_providers()
        if not provider_map:
            return api_fail(
                "未创建任何 Provider。请在后端 .env 配置 "
                "VOLCANO_ARK_API_KEY、VOLCANO_EP_*、ZHIPU_API_KEY 后重试。"
            )
        LlmProviderService.set_global_enabled(True)
        bound_nodes = 0
        bound_agents = 0
        if not skip_bind:
            bound_nodes = AgentLlmRoutingService.bind_fusion_node_providers(provider_map)
            bound_agents = AgentLlmRoutingService.bind_agent_route_providers(provider_map)
        AgentLlmRoutingService.activate_default_provider(provider_map)
        _clear_skill_cache()
        plan = AgentLlmRoutingService.routing_plan()
        return api_ok(
            {
                **_payload(),
                "provider_count": len(provider_map),
                "bound_nodes": bound_nodes,
                "bound_agents": bound_agents,
                "routing_plan": plan,
            },
            message=f"已接入 {len(provider_map)} 个模型，绑定 {bound_nodes} 个主链节点、{bound_agents} 个辅助 Agent",
        )


class LlmUsageRecalculateView(APIView):
    """POST /api/admin/model/llm/usage/recalculate/ — 按当前单价重算全部历史 LLM 用量费用"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        recalculated = LlmUsageService.recalculate_estimated_costs(all_logs=True)
        _clear_skill_cache()
        msg = f"已重算 {recalculated} 条历史用量费用" if recalculated else "历史用量已与当前单价一致，无需更新"
        return api_ok({"recalculated": recalculated}, message=msg)
