# -*- coding: utf-8 -*-
"""主链节点元数据 — 运行时只读 FusionPipelinePack（DB SSOT）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .config_loader import FusionSkillConfig, get_fusion_config

FUSION_PROJECT_STATUS = {
    "draft": "draft",
    "planning": "planning",
    "writing": "writing",
    "reviewing": "reviewing",
    "scoring": "scoring",
    "ready": "ready",
    "blocked": "blocked",
    "exported": "exported",
}


from apps.common.agent_term import alias_agent_id


class FusionNodeRegistry:
    """主链节点查询 facade — 委托 FusionPipelineDbService。"""

    def __init__(self, config: Optional[FusionSkillConfig] = None, *, pack_id: Optional[str] = None):
        self.config = config or get_fusion_config()
        self.pack_id = str(pack_id).strip() if pack_id else None

    def main_chain_nodes(self) -> List[Dict[str, Any]]:
        from apps.workflow.pipeline_store import FusionPipelineDbService

        if self.pack_id:
            return FusionPipelineDbService.main_chain_nodes(pack_id=self.pack_id)
        return FusionPipelineDbService.main_chain_nodes()

    def total_main_nodes(self) -> int:
        return len(self.main_chain_nodes())

    def pipeline_nodes_legacy_shape(self) -> List[Dict[str, Any]]:
        return [
            alias_agent_id(
                {
                    "index": n["index"],
                    "name": n["name"],
                    "description": n["description"],
                    "fusion_node_id": n["fusion_node_id"],
                    "skill_id": n.get("skill_id") or n.get("agent_id") or "",
                }
            )
            for n in self.main_chain_nodes()
        ]

    def fusion_node_id_for_index(self, node_index: int) -> str | None:
        for n in self.main_chain_nodes():
            if n["index"] == node_index:
                return n["fusion_node_id"]
        return None

    def node_for_index(self, node_index: int) -> Optional[Dict[str, Any]]:
        for n in self.main_chain_nodes():
            if n["index"] == node_index:
                return n
        return None

    def runner_type_for_index(self, node_index: int) -> str:
        node = self.node_for_index(node_index) or {}
        return str(node.get("runner_type") or "").strip()

    def runner_path_for_index(self, node_index: int) -> str:
        node = self.node_for_index(node_index) or {}
        return str(node.get("runner_path") or "").strip()

    def status_for_fusion_node(self, fusion_node_id: str) -> str:
        for n in self.main_chain_nodes():
            if n["fusion_node_id"] == fusion_node_id:
                return n.get("fusion_status") or FUSION_PROJECT_STATUS["draft"]
        return FUSION_PROJECT_STATUS["draft"]

    def node_by_fusion_id(self, fusion_node_id: str) -> Optional[Dict[str, Any]]:
        """返回与 project-config node 兼容的字典（运行时只读 DB）。"""
        key = (fusion_node_id or "").strip()
        if not key:
            return None
        for n in self.main_chain_nodes():
            if n.get("fusion_node_id") == key:
                schema_file = (n.get("schema_file") or "").strip()
                if schema_file and not schema_file.startswith("schemas/"):
                    schema_file = f"schemas/{schema_file}"
                return {
                    "id": key,
                    "name": n.get("name") or "",
                    "name_zh": n.get("name") or "",
                    "description": n.get("description") or "",
                    "schemaFile": schema_file,
                }
        return None
