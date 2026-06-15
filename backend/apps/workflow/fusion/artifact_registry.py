# -*- coding: utf-8 -*-
"""节点 index ↔ artifact_key 映射 — 派生自主链节点（DB 或磁盘）。"""
from __future__ import annotations

from typing import Dict, List, Optional

from .config_loader import FusionSkillConfig, get_fusion_config
from .registry import FusionNodeRegistry
from .schema_registry import GATE_ARTIFACTS

# artifact_key → pipeline_result 顶层字段（节点未配 pipeline_result_key 时的兜底）
_DEFAULT_PIPELINE_RESULT_KEY_BY_ARTIFACT = {
    "project_brief": "project_brief",
    "structure_plan": "structure",
    "character_bible": "characters",
    "series_outline": "outlines",
    "episode_scripts": "scripts",
}

# pipeline_result 键 → 是否需要 episode_scripts → legacy scripts 转换
_PIPELINE_RESULT_LEGACY_SCRIPT_KEYS = frozenset({"scripts"})


def default_pipeline_result_key(artifact_key: str) -> str:
    key = str(artifact_key or "").strip()
    if not key:
        return ""
    return _DEFAULT_PIPELINE_RESULT_KEY_BY_ARTIFACT.get(key, key)


def _primary_artifact_map(nodes: List[dict]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for node in nodes:
        fid = node.get("fusion_node_id")
        key = node.get("artifact_key")
        if fid and key:
            mapping[fid] = key
    return mapping


class FusionArtifactRegistry:
    def __init__(self, config: Optional[FusionSkillConfig] = None):
        self.config = config or get_fusion_config()
        self.node_registry = FusionNodeRegistry(self.config)
        nodes = self.node_registry.main_chain_nodes()
        self._fusion_primary = _primary_artifact_map(nodes)
        self._index_primary: Dict[int, str] = {}
        self._index_all: Dict[int, List[str]] = {}
        self._artifact_pipeline_key: Dict[str, str] = {}
        for node in nodes:
            idx = node["index"]
            fid = node["fusion_node_id"]
            primary = self._fusion_primary.get(fid)
            all_keys: List[str] = []
            if primary:
                self._index_primary[idx] = primary
                all_keys.append(primary)
                pipeline_key = str(node.get("pipeline_result_key") or "").strip()
                if not pipeline_key:
                    pipeline_key = _DEFAULT_PIPELINE_RESULT_KEY_BY_ARTIFACT.get(primary, "")
                if pipeline_key:
                    self._artifact_pipeline_key[primary] = pipeline_key
            for extra_key in node.get("extra_artifact_keys") or []:
                if extra_key and extra_key not in all_keys:
                    all_keys.append(str(extra_key))
            if all_keys:
                self._index_all[idx] = all_keys

    def total_main_nodes(self) -> int:
        return self.node_registry.total_main_nodes()

    def max_node_index(self) -> int:
        nodes = self.node_registry.main_chain_nodes()
        return max((n["index"] for n in nodes), default=7)

    def main_chain_nodes(self) -> List[dict]:
        return self.node_registry.main_chain_nodes()

    def artifact_key_for_index(self, node_index: int) -> Optional[str]:
        return self._index_primary.get(node_index)

    def artifacts_for_node(self, node_index: int) -> List[str]:
        return list(self._index_all.get(node_index, []))

    def primary_artifact_for_fusion_node(self, fusion_node_id: str) -> Optional[str]:
        return self._fusion_primary.get(fusion_node_id)

    def pipeline_result_key_for_artifact(self, artifact_key: str) -> str:
        key = str(artifact_key or "").strip()
        if not key:
            return ""
        configured = self._artifact_pipeline_key.get(key)
        if configured:
            return configured
        return _DEFAULT_PIPELINE_RESULT_KEY_BY_ARTIFACT.get(key, "")

    def pipeline_result_sources(self) -> List[Dict[str, str]]:
        """主链节点 → pipeline_result 字段映射（按 website index 排序）。"""
        sources: List[Dict[str, str]] = []
        for node in self.main_chain_nodes():
            artifact_key = self._fusion_primary.get(node.get("fusion_node_id") or "")
            if not artifact_key:
                continue
            pipeline_key = self.pipeline_result_key_for_artifact(artifact_key)
            if not pipeline_key:
                continue
            sources.append(
                {
                    "index": str(node.get("index") or ""),
                    "artifact_key": artifact_key,
                    "pipeline_result_key": pipeline_key,
                }
            )
        return sources

    def uses_legacy_script_transform(self, pipeline_result_key: str) -> bool:
        return str(pipeline_result_key or "") in _PIPELINE_RESULT_LEGACY_SCRIPT_KEYS

    def main_chain_artifact_keys_nodes_1_5(self) -> List[str]:
        keys: List[str] = []
        for node in self.node_registry.main_chain_nodes():
            if node["index"] <= 5:
                key = self._fusion_primary.get(node["fusion_node_id"])
                if key:
                    keys.append(key)
        return keys

    def fusion_node_ids_1_5(self) -> List[str]:
        return [
            n["fusion_node_id"]
            for n in self.node_registry.main_chain_nodes()
            if n["index"] <= 5
        ]

    def next_node_index(self, current: int) -> Optional[int]:
        if current < 1:
            return 1
        if current >= self.max_node_index():
            return None
        return current + 1

    def progress_percent_for_node(self, node_index: int, *, awaiting: bool = False) -> int:
        total = max(1, self.total_main_nodes())
        if awaiting:
            return min(99, int(node_index / total * 100))
        return min(100, int(node_index / total * 100))

    def progress_span_for_running(self, node_index: int) -> tuple[int, int]:
        total = max(1, self.total_main_nodes())
        base = int((node_index - 1) / total * 100)
        span = max(1, int(100 / total))
        return base, span

    def all_artifact_keys_from_index(self, from_index: int) -> List[str]:
        keys: List[str] = []
        for idx in range(from_index, self.max_node_index() + 1):
            keys.extend(self.artifacts_for_node(idx))
        return keys

    def gate_artifact_keys(self) -> List[str]:
        return list(GATE_ARTIFACTS.keys()) + ["quality_report"]


def get_artifact_registry(config: Optional[FusionSkillConfig] = None) -> FusionArtifactRegistry:
    return FusionArtifactRegistry(config)
