# apps/agent/services.py
# Agent 服务门面层
#
# 职责：统一聚合 registry / routes / binding / catalog / runtime 的业务入口，
# 避免外部模块（portal / console / creation）直接散引多个内部模块。
#
# 外部调用方应优先通过本模块访问 Agent 能力：
#   from apps.agent.services import AgentService

from __future__ import annotations

from typing import Any, Dict, List, Optional

from apps.agent.registry import AgentRegistryConfigService
from apps.agent.routes import AgentLlmRouteService


class AgentService:
    """Agent 中心统一服务门面。

    所有对 Agent 注册表、LLM 路由、运行时缓存的读写，
    外部模块统一通过此类访问，降低模块间耦合。
    """

    # ------------------------------------------------------------------
    # Agent 注册表
    # ------------------------------------------------------------------

    @staticmethod
    def get_registry_payload() -> Dict[str, Any]:
        """获取 Agent 注册表（含 DB + 文件元信息）。"""
        return AgentRegistryConfigService.admin_payload()

    @staticmethod
    def save_registry(registry: Dict[str, Any], *, note: str = "") -> None:
        """保存 Agent 注册表到 DB。"""
        AgentRegistryConfigService.save_registry(registry, note=note)

    @staticmethod
    def import_registry_from_file(*, overwrite: bool = True) -> None:
        """从磁盘 registry.json 导入注册表到 DB。"""
        AgentRegistryConfigService.import_from_file(overwrite=overwrite)

    @staticmethod
    def ensure_registry_defaults() -> None:
        """确保注册表已有默认数据（冷启动保障）。"""
        AgentRegistryConfigService.ensure_defaults()

    @staticmethod
    def migrate_pipeline_skill_config() -> int:
        """将 FusionPipelineNode 遗留配置迁移到 Agent 注册表（一次性运维操作）。"""
        return AgentRegistryConfigService.migrate_pipeline_skill_config()

    # ------------------------------------------------------------------
    # LLM 路由
    # ------------------------------------------------------------------

    @staticmethod
    def resolve_llm_provider_id(route_key: str) -> Optional[str]:
        """根据路由 key 查找对应的 LLM Provider ID。"""
        return AgentLlmRouteService.resolve_provider_id(route_key)

    @staticmethod
    def resolve_llm_provider_for_node(fusion_node_id: str) -> Optional[str]:
        """根据主链节点 ID 查找对应的 LLM Provider ID。"""
        return AgentLlmRouteService.resolve_provider_id_for_node(fusion_node_id)

    @staticmethod
    def resolve_max_tokens(route_key: str) -> Optional[int]:
        """根据路由 key 查找最大 Token 限制。"""
        return AgentLlmRouteService.resolve_max_tokens(route_key)

    @staticmethod
    def list_llm_routes() -> List[Dict[str, Any]]:
        """列出所有 LLM 路由配置（后台管理用）。"""
        return AgentLlmRouteService.list_admin_items()

    @staticmethod
    def upsert_llm_route(route_key: str, data: Dict[str, Any]) -> None:
        """新增或更新 LLM 路由配置。"""
        AgentLlmRouteService.upsert(route_key, data)

    @staticmethod
    def seed_llm_route_defaults() -> int:
        """种子初始化 LLM 路由默认配置，返回新建条目数。"""
        return AgentLlmRouteService.seed_defaults()

    # ------------------------------------------------------------------
    # Agent 目录（portal 只读）
    # ------------------------------------------------------------------

    @staticmethod
    def portal_catalog() -> Dict[str, Any]:
        """获取 C 端可见的 Agent 目录（registry v2 SSOT）。"""
        from apps.agent.catalog import portal_agent_catalog

        return portal_agent_catalog()

    # ------------------------------------------------------------------
    # 运行时缓存
    # ------------------------------------------------------------------

    @staticmethod
    def clear_runtime_cache() -> None:
        """清除 Agent 注册表运行时内存缓存。"""
        try:
            from apps.agent.runtime import get_agent_registry

            get_agent_registry.cache_clear()
        except Exception:  # noqa: BLE001
            pass
