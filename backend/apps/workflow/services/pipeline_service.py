# -*- coding: utf-8 -*-
"""主链工作流配置服务。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from apps.common.agent_term import alias_agent_id
from apps.workflow.fusion.registry import FusionNodeRegistry


def _billing_service():
    from apps.billing.services import BillingService

    return BillingService


class WorkflowPipelineService:
    """主链编排 — FusionPipelineNode（Pack）为 SSOT。"""

    @classmethod
    def _registry(cls, pack_id: Optional[str] = None) -> FusionNodeRegistry:
        return FusionNodeRegistry(pack_id=pack_id)

    @classmethod
    def ensure_defaults(cls) -> None:
        from apps.workflow.pipeline_store import FusionPipelineDbService

        if FusionPipelineDbService.has_active_nodes():
            return
        FusionPipelineDbService.ensure_builtin_default_pack()

    @classmethod
    def portal_hidden_fusion_node_ids(cls, pack_id: Optional[str] = None) -> frozenset:
        cls.ensure_defaults()
        hidden = {
            n["fusion_node_id"]
            for n in cls._registry(pack_id).main_chain_nodes()
            if not n.get("portal_visible", True)
        }
        return frozenset(hidden)

    @classmethod
    def _exclude_portal_nodes(cls, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        hidden = cls.portal_hidden_fusion_node_ids()
        return [n for n in nodes if n.get("fusion_node_id") not in hidden]

    @classmethod
    def creation_max_node_index(cls, pack_id: Optional[str] = None) -> int:
        chain = cls.portal_main_chain(pack_id=pack_id)
        return max((n["index"] for n in chain), default=5)

    @classmethod
    def creation_next_node_index(cls, current: int) -> Optional[int]:
        from apps.workflow.services.flow_graph_service import FlowGraphPlanService

        return FlowGraphPlanService.creation_next_node_index(current)

    @classmethod
    def enabled_nodes(cls, pack_id: Optional[str] = None) -> List[Dict[str, Any]]:
        cls.ensure_defaults()
        return [
            {
                "index": n["index"],
                "fusion_node_id": n["fusion_node_id"],
                "name": n.get("name") or "",
                "requires_confirm": n.get("requires_confirm", True),
                "coin_cost": n.get("coin_cost") or _billing_service().get_node_coin_cost(n["index"]),
            }
            for n in cls._registry(pack_id).main_chain_nodes()
            if n.get("enabled", True)
        ]

    @classmethod
    def public_nodes(cls) -> List[Dict[str, Any]]:
        return [
            {
                "index": n["index"],
                "name": n["name"],
                "coin_cost": n.get("coin_cost") or _billing_service().get_node_coin_cost(n["index"]),
            }
            for n in cls.portal_main_chain()
        ]

    @classmethod
    def portal_main_chain(cls, pack_id: Optional[str] = None) -> List[Dict[str, Any]]:
        cls.ensure_defaults()
        out: List[Dict[str, Any]] = []
        for n in cls._registry(pack_id).main_chain_nodes():
            if not n.get("enabled", True):
                continue
            if not n.get("portal_visible", True):
                continue
            out.append(
                alias_agent_id(
                    {
                        "index": n["index"],
                        "fusion_node_id": n["fusion_node_id"],
                        "name": n.get("name") or n["fusion_node_id"],
                        "description": n.get("description") or "",
                        "output_key": n.get("output_key") or "",
                        "agent_id": n.get("agent_id") or n.get("skill_id") or "",
                        "coin_cost": n.get("coin_cost") or _billing_service().get_node_coin_cost(n["index"]),
                        "requires_confirm": n.get("requires_confirm", True),
                        "portal_visible": n.get("portal_visible", True),
                    }
                )
            )
        return out

    @classmethod
    def admin_pipeline_meta(cls) -> Dict[str, Any]:
        from apps.workflow.step_admin import PipelineStepAdminService

        return PipelineStepAdminService.meta_payload()

    @classmethod
    def node_meta_by_index(cls, pack_id: Optional[str] = None) -> Dict[int, Dict[str, Any]]:
        return {n["index"]: n for n in cls.portal_main_chain(pack_id=pack_id)}

    @classmethod
    def display_name_for_index(cls, node_index: int) -> str:
        for n in FusionNodeRegistry().main_chain_nodes():
            if n["index"] == node_index:
                return n.get("name") or f"步骤 {node_index}"
        return f"步骤 {node_index}"

    @classmethod
    def is_node_enabled(cls, node_index: int) -> bool:
        for n in FusionNodeRegistry().main_chain_nodes():
            if n["index"] == node_index:
                return bool(n.get("enabled", True))
        return True

    @classmethod
    def pipeline_nodes_for_creation(cls, pack_id: Optional[str] = None) -> List[Dict[str, Any]]:
        cls.ensure_defaults()
        out = []
        hidden = cls.portal_hidden_fusion_node_ids(pack_id=pack_id)
        for n in cls._registry(pack_id).main_chain_nodes():
            fid = n["fusion_node_id"]
            if fid in hidden or not n.get("enabled", True):
                continue
            out.append(
                alias_agent_id(
                    {
                        "index": n["index"],
                        "name": n.get("name") or "",
                        "fusion_node_id": fid,
                        "description": n.get("description") or "",
                        "output_key": n.get("output_key") or "",
                        "agent_id": n.get("agent_id") or n.get("skill_id") or "",
                    }
                )
            )
        return out
