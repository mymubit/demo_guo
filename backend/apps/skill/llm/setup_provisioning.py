# -*- coding: utf-8 -*-
"""setup 命令用：从环境变量创建 Provider 并写入 DB 绑定（运行时仅读 DB）。"""
from __future__ import annotations

import logging
import os
from typing import Dict, Optional

from django.conf import settings

from apps.skill.config.bootstrap.llm_setup_presets import (
    AGENT_PRESET_KEYS,
    DEFAULT_ACTIVE_PRESET,
    NATIVE_PRESET_CONFIG,
    NATIVE_PRESET_KEYS,
    NODE_PRESET_KEYS,
)
from apps.skill.llm.volcengine_config import (
    DEFAULT_VOLCANO_PAYG_BASE_URL,
    get_volcano_key_type_from_env,
    infer_volcano_key_type,
    resolve_volcano_base_url,
)
from apps.skill.llm.volcengine_chat import PRESET_ENDPOINT_ENV

logger = logging.getLogger(__name__)

VOLCANO_ARK_BASE_URL = DEFAULT_VOLCANO_PAYG_BASE_URL


class AgentLlmRoutingService:
    @staticmethod
    def volcano_api_key() -> str:
        return (
            getattr(settings, "VOLCANO_ARK_API_KEY", "")
            or os.getenv("VOLCANO_ARK_API_KEY", "")
            or ""
        ).strip()

    @staticmethod
    def volcano_base_url() -> str:
        key_type = get_volcano_key_type_from_env()
        if key_type:
            from apps.skill.llm.providers import LlmProviderService

            return LlmProviderService.normalize_base_url(resolve_volcano_base_url(key_type))
        raw = getattr(settings, "VOLCANO_ARK_BASE_URL", "") or os.getenv(
            "VOLCANO_ARK_BASE_URL", VOLCANO_ARK_BASE_URL
        )
        from apps.skill.llm.providers import LlmProviderService

        return LlmProviderService.normalize_base_url(raw or VOLCANO_ARK_BASE_URL)

    @classmethod
    def is_native_preset(cls, preset_key: str) -> bool:
        return preset_key in NATIVE_PRESET_KEYS

    @classmethod
    def native_api_key(cls, preset_key: str) -> str:
        cfg = NATIVE_PRESET_CONFIG.get(preset_key) or {}
        env_name = cfg.get("api_key_env", "ZHIPU_API_KEY")
        return (getattr(settings, env_name, "") or os.getenv(env_name, "") or "").strip()

    @classmethod
    def native_model_name(cls, preset_key: str) -> str:
        cfg = NATIVE_PRESET_CONFIG.get(preset_key) or {}
        env_name = cfg.get("model_env", "")
        if env_name:
            val = getattr(settings, env_name, None) or os.getenv(env_name, "")
            if val:
                return str(val).strip()
        return str(cfg.get("model_default") or preset_key)

    @classmethod
    def native_base_url(cls, preset_key: str) -> str:
        cfg = NATIVE_PRESET_CONFIG.get(preset_key) or {}
        from apps.skill.llm.providers import LlmProviderService

        return LlmProviderService.normalize_base_url(
            cfg.get("base_url") or "https://open.bigmodel.cn/api/paas/v4"
        )

    @classmethod
    def endpoint_for_preset(cls, preset_key: str) -> str:
        """推理接入点 ep-xxx（可选，未配置则走 Model ID）。"""
        env_name = PRESET_ENDPOINT_ENV.get(preset_key, "")
        if env_name:
            val = getattr(settings, env_name, None) or os.getenv(env_name, "")
            if val:
                return str(val).strip()
        return ""

    @classmethod
    def resolve_volcano_model_name(cls, preset_key: str) -> str:
        """火山 chat/completions 的 model：优先 ep-xxx 环境变量，否则目录 Model ID。"""
        ep = cls.endpoint_for_preset(preset_key)
        if ep:
            return ep
        from apps.skill.llm.model_catalog import LlmCatalogService

        catalog = LlmCatalogService.get_by_preset_key(preset_key)
        if catalog and catalog.model_name:
            name = str(catalog.model_name).strip()
            if name and name.lower() not in {"ep-xxx", "ep-xxxxxxxxx"}:
                return name
        return ""

    @classmethod
    def resolve_provider_by_preset(cls, preset_key: str) -> Optional[str]:
        if not preset_key:
            return None
        from apps.skill.models import LlmProvider

        qs = LlmProvider.objects.filter(
            is_enabled=True,
            catalog__preset_key=preset_key,
        ).exclude(api_key_encrypted="").exclude(base_url="").order_by(
            "-is_active", "sort_order", "-created_at"
        )
        row = qs.first()
        if row:
            return str(row.id)
        return None

    @classmethod
    def routing_plan(cls) -> Dict[str, object]:
        """供管理命令展示的路由表（读 DB 绑定状态）。"""
        from apps.agent.routes import AgentLlmRouteService
        from apps.workflow.step_admin import PipelineStepAdminService

        nodes = {}
        for node_id, preset in NODE_PRESET_KEYS.items():
            nodes[node_id] = {
                "preset_key": preset,
                "channel": "native" if cls.is_native_preset(preset) else "volcano",
                "endpoint_env": PRESET_ENDPOINT_ENV.get(preset, "")
                or (NATIVE_PRESET_CONFIG.get(preset, {}).get("api_key_env", "")),
                "provider_id": PipelineStepAdminService.resolve_provider_id(node_id),
            }
        agents = {}
        for agent_id, preset in AGENT_PRESET_KEYS.items():
            agents[agent_id] = {
                "preset_key": preset,
                "channel": "native" if cls.is_native_preset(preset) else "volcano",
                "endpoint_env": PRESET_ENDPOINT_ENV.get(preset, "")
                or (NATIVE_PRESET_CONFIG.get(preset, {}).get("api_key_env", "")),
                "provider_id": AgentLlmRouteService.resolve_provider_id(agent_id),
            }
        return {
            "volcano_base_url": cls.volcano_base_url(),
            "volcano_key_type": get_volcano_key_type_from_env() or "payg",
            "volcano_api_key_set": bool(cls.volcano_api_key()),
            "zhipu_api_key_set": bool(cls.native_api_key("glm-5")),
            "default_active_preset": DEFAULT_ACTIVE_PRESET,
            "nodes": nodes,
            "agents": agents,
        }

    @classmethod
    def provision_volcano_providers(cls, *, dry_run: bool = False) -> Dict[str, str]:
        """从环境变量创建/更新火山 Provider，返回 preset_key -> provider_id。"""
        from apps.skill.llm.model_catalog import LlmCatalogService
        from apps.skill.llm.providers import LlmProviderService
        from apps.skill.models import LlmProvider

        api_key = cls.volcano_api_key()
        if not api_key:
            raise ValueError("缺少 VOLCANO_ARK_API_KEY")

        LlmCatalogService.ensure_seed_catalog()
        base_url = cls.volcano_base_url()
        needed_presets = sorted(
            preset
            for preset in (set(NODE_PRESET_KEYS.values()) | set(AGENT_PRESET_KEYS.values()))
            if not cls.is_native_preset(preset)
        )
        result: Dict[str, str] = {}

        for preset_key in needed_presets:
            catalog = LlmCatalogService.get_by_preset_key(preset_key)
            if catalog is None:
                logger.warning("目录 preset 不存在: %s", preset_key)
                continue
            endpoint = cls.resolve_volcano_model_name(preset_key)
            if not endpoint:
                logger.warning(
                    "跳过 %s：目录无 Model ID，且未设置 %s",
                    preset_key,
                    PRESET_ENDPOINT_ENV.get(preset_key, "VOLCANO_EP_*"),
                )
                continue

            existing = LlmProvider.objects.filter(catalog=catalog).first()
            if not existing:
                existing = LlmProvider.objects.filter(
                    base_url=base_url,
                    model_name=endpoint[:128],
                ).first()
            if dry_run:
                result[preset_key] = str(existing.id) if existing else "(dry-run)"
                continue

            if existing:
                existing.base_url = base_url
                existing.model_name = endpoint[:128]
                existing.catalog = catalog
                existing.volcano_key_type = get_volcano_key_type_from_env() or infer_volcano_key_type(base_url)
                existing.set_api_key(api_key)
                existing.is_enabled = True
                existing.save()
                row = existing
            else:
                row = LlmProviderService.create_provider(
                    {
                        "catalog_id": str(catalog.id),
                        "api_key": api_key,
                        "base_url": base_url,
                        "model_name": endpoint,
                        "volcano_key_type": get_volcano_key_type_from_env()
                        or infer_volcano_key_type(base_url),
                        "is_enabled": True,
                        "set_active": False,
                    }
                )
            result[preset_key] = str(row.id)

        return result

    @classmethod
    def provision_native_providers(cls, *, dry_run: bool = False) -> Dict[str, str]:
        """智谱等原生 API Provider（GLM-5 不走火山 ep-xxx）。"""
        from apps.skill.llm.model_catalog import LlmCatalogService
        from apps.skill.llm.providers import LlmProviderService
        from apps.skill.models import LlmProvider

        LlmCatalogService.ensure_seed_catalog()
        needed = sorted(
            preset
            for preset in (set(NODE_PRESET_KEYS.values()) | set(AGENT_PRESET_KEYS.values()))
            if cls.is_native_preset(preset)
        )
        result: Dict[str, str] = {}

        for preset_key in needed:
            cfg = NATIVE_PRESET_CONFIG.get(preset_key)
            if not cfg:
                continue
            api_key = cls.native_api_key(preset_key)
            if not api_key:
                logger.warning(
                    "跳过 %s：未设置 %s",
                    preset_key,
                    cfg.get("api_key_env", "ZHIPU_API_KEY"),
                )
                continue

            catalog = LlmCatalogService.get_by_preset_key(preset_key)
            if catalog is None:
                logger.warning("目录 preset 不存在: %s", preset_key)
                continue

            base_url = cls.native_base_url(preset_key)
            model_name = cls.native_model_name(preset_key)[:128]

            existing = LlmProvider.objects.filter(catalog=catalog).first()
            if not existing:
                existing = LlmProvider.objects.filter(
                    base_url=base_url,
                    model_name=model_name,
                ).first()

            if dry_run:
                result[preset_key] = str(existing.id) if existing else "(dry-run)"
                continue

            if existing:
                existing.base_url = base_url
                existing.model_name = model_name
                existing.catalog = catalog
                existing.set_api_key(api_key)
                existing.is_enabled = True
                existing.save()
                row = existing
            else:
                row = LlmProviderService.create_provider(
                    {
                        "catalog_id": str(catalog.id),
                        "api_key": api_key,
                        "base_url": base_url,
                        "model_name": model_name,
                        "is_enabled": True,
                        "set_active": False,
                    }
                )
            result[preset_key] = str(row.id)

        return result

    @classmethod
    def provision_all_providers(cls, *, dry_run: bool = False) -> Dict[str, str]:
        merged: Dict[str, str] = {}
        try:
            merged.update(cls.provision_volcano_providers(dry_run=dry_run))
        except ValueError:
            if dry_run:
                pass
            else:
                logger.warning("火山 Provider 未创建：缺少 VOLCANO_ARK_API_KEY")
        merged.update(cls.provision_native_providers(dry_run=dry_run))
        return merged

    @classmethod
    def bind_fusion_node_providers(cls, provider_map: Dict[str, str]) -> int:
        """将主链 fusion 节点对应 Agent 绑定到 AgentLlmRouteConfig（不再写 FusionPipelineNode）。"""
        from apps.agent.binding import agent_id_for_fusion_node
        from apps.agent.routes import AgentLlmRouteService
        from apps.skill.models import LlmProvider

        AgentLlmRouteService.seed_defaults()
        bound = 0
        for node_id, preset_key in NODE_PRESET_KEYS.items():
            provider_id = provider_map.get(preset_key)
            if not provider_id:
                continue
            provider = LlmProvider.objects.filter(pk=provider_id, is_enabled=True).first()
            if provider is None:
                continue
            agent_id = agent_id_for_fusion_node(node_id)
            if not agent_id:
                continue
            AgentLlmRouteService.upsert(agent_id, {"llm_provider_id": str(provider.id)})
            bound += 1
        return bound

    @classmethod
    def bind_agent_route_providers(cls, provider_map: Dict[str, str]) -> int:
        """将辅助 Agent 绑定到 AgentLlmRouteConfig（DB）。"""
        from apps.agent.routes import AgentLlmRouteService
        from apps.agent.models import AgentLlmRouteConfig
        from apps.skill.models import LlmProvider

        AgentLlmRouteService.seed_defaults()
        bound = 0
        for agent_id, preset_key in AGENT_PRESET_KEYS.items():
            provider_id = provider_map.get(preset_key)
            if not provider_id:
                continue
            provider = LlmProvider.objects.filter(pk=provider_id, is_enabled=True).first()
            if provider is None:
                continue
            row, _ = AgentLlmRouteConfig.objects.update_or_create(
                route_key=agent_id,
                defaults={"is_active": True},
            )
            row.llm_provider = provider
            row.save(update_fields=["llm_provider", "updated_at"])
            bound += 1
        return bound

    @classmethod
    def activate_default_provider(cls, provider_map: Dict[str, str]) -> None:
        from apps.skill.llm.providers import LlmProviderService

        provider_id = provider_map.get(DEFAULT_ACTIVE_PRESET)
        if provider_id:
            LlmProviderService.set_active(provider_id)
