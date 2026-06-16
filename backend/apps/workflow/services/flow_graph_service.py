# -*- coding: utf-8 -*-
"""流程图编排计划 — 解析 Registry flow_graph，生成线性/并行/分支执行计划。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from apps.workflow.services.pipeline_service import WorkflowPipelineService


class ExecutionStage(TypedDict):
    type: str  # single | parallel
    indices: List[int]
    group_id: str
    label: str


class FlowGraphPlanService:
    EDGE_SEQUENTIAL = "sequential"
    EDGE_BRANCH = "branch"
    EDGE_DEFAULT = "default"

    @staticmethod
    def get_flow_graph(pack_id: Optional[str] = None) -> Dict[str, Any]:
        from apps.console.orchestration.publish_service import OrchestrationPublishService
        from apps.workflow.pipeline_store import FusionPipelineDbService

        pack = FusionPipelineDbService.get_pack_by_id(pack_id) if pack_id else FusionPipelineDbService.get_active_pack()
        if pack and isinstance(pack.flow_graph, dict) and pack.flow_graph:
            return dict(pack.flow_graph)
        return OrchestrationPublishService.published_flow_graph()

    @classmethod
    def _chain_nodes(cls, pack_id: Optional[str] = None) -> List[Dict[str, Any]]:
        WorkflowPipelineService.ensure_defaults()
        return WorkflowPipelineService.portal_main_chain(pack_id=pack_id)

    @classmethod
    def _fusion_index_map(cls, pack_id: Optional[str] = None) -> Dict[str, int]:
        return {n["fusion_node_id"]: int(n["index"]) for n in cls._chain_nodes(pack_id) if n.get("fusion_node_id")}

    @classmethod
    def _index_fusion_map(cls, pack_id: Optional[str] = None) -> Dict[int, str]:
        return {int(n["index"]): n["fusion_node_id"] for n in cls._chain_nodes(pack_id) if n.get("fusion_node_id")}

    @classmethod
    def _flow_edges(cls, pack_id: Optional[str] = None) -> List[Dict[str, Any]]:
        edges = cls.get_flow_graph(pack_id).get("edges") or []
        if not isinstance(edges, list):
            return []
        normalized: List[Dict[str, Any]] = []
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            source = str(edge.get("from") or edge.get("source") or "").strip()
            target = str(edge.get("to") or edge.get("target") or "").strip()
            if not source or not target:
                continue
            normalized.append(
                {
                    "from": source,
                    "to": target,
                    "type": str(edge.get("type") or cls.EDGE_SEQUENTIAL).strip() or cls.EDGE_SEQUENTIAL,
                    "condition": edge.get("condition") if isinstance(edge.get("condition"), dict) else {},
                    "label": str(edge.get("label") or "").strip(),
                }
            )
        return normalized

    @classmethod
    def _outgoing_edges(cls, fusion_node_id: str) -> List[Dict[str, Any]]:
        fid = str(fusion_node_id or "").strip()
        return [edge for edge in cls._flow_edges() if edge.get("from") == fid]

    @classmethod
    def _project_review_passed(cls, project) -> Optional[bool]:
        from apps.creation.artifact_service import get_artifact
        from apps.creation.models import CreationNode

        report = get_artifact(project, "review_report") or {}
        if "passed" in report:
            return bool(report.get("passed"))
        node = CreationNode.objects.filter(project=project, node_index=6).first()
        if not node:
            return None
        if node.status == CreationNode.STATUS_FAILED:
            return False
        if node.status == CreationNode.STATUS_COMPLETED:
            return True
        return None

    @classmethod
    def _project_score(cls, project) -> Optional[float]:
        from apps.creation.artifact_service import get_artifact

        report = get_artifact(project, "script_score_report") or get_artifact(project, "score_report") or {}
        for key in ("finalScore", "overallScore", "fiveDimensionScore"):
            val = report.get(key)
            if val is not None:
                try:
                    return float(val)
                except (TypeError, ValueError):
                    continue
        return None

    @classmethod
    def evaluate_edge_condition(cls, project, edge: Dict[str, Any]) -> bool:
        condition = edge.get("condition") or {}
        kind = str(condition.get("kind") or "always").strip() or "always"
        if kind == "always":
            return True
        if kind == "review_passed":
            passed = cls._project_review_passed(project)
            return passed is True
        if kind == "review_failed":
            passed = cls._project_review_passed(project)
            return passed is False
        if kind == "score_gte":
            score = cls._project_score(project)
            if score is None:
                return False
            try:
                threshold = float(condition.get("value") or 0)
            except (TypeError, ValueError):
                threshold = 0.0
            return score >= threshold
        if kind == "score_lt":
            score = cls._project_score(project)
            if score is None:
                return False
            try:
                threshold = float(condition.get("value") or 0)
            except (TypeError, ValueError):
                threshold = 0.0
            return score < threshold
        return True

    @classmethod
    def resolve_next_indices(cls, project, current_index: int) -> List[int]:
        pending = cls.pending_parallel_indices(project, int(current_index))
        if pending:
            return pending

        fusion_to_index = cls._fusion_index_map()
        index_to_fusion = cls._index_fusion_map()
        fusion_node_id = index_to_fusion.get(int(current_index), "")
        outgoing = cls._outgoing_edges(fusion_node_id)
        if outgoing:
            branch_targets: List[str] = []
            default_target = ""
            for edge in outgoing:
                edge_type = edge.get("type") or cls.EDGE_SEQUENTIAL
                if edge_type == cls.EDGE_BRANCH:
                    if cls.evaluate_edge_condition(project, edge):
                        branch_targets.append(str(edge.get("to") or ""))
                elif edge_type == cls.EDGE_DEFAULT:
                    default_target = str(edge.get("to") or "")
                elif edge_type == cls.EDGE_SEQUENTIAL and not branch_targets:
                    branch_targets.append(str(edge.get("to") or ""))

            chosen: List[str] = []
            if branch_targets:
                chosen = [branch_targets[0]]
            elif default_target:
                chosen = [default_target]

            indices = [fusion_to_index[fid] for fid in chosen if fid in fusion_to_index]
            if indices:
                return indices

        next_idx = cls.creation_next_node_index(int(current_index))
        return [next_idx] if next_idx is not None else []

    @classmethod
    def next_node_index_for_project(cls, project, current_index: int) -> Optional[int]:
        resolved = cls.resolve_next_indices(project, int(current_index))
        return resolved[0] if resolved else None

    @classmethod
    def build_execution_stages(cls, pack_id: Optional[str] = None) -> List[ExecutionStage]:
        chain = cls._chain_nodes(pack_id)
        if not chain:
            return []

        flow_graph = cls.get_flow_graph(pack_id)
        parallel_groups = flow_graph.get("parallel_groups") or []
        if not isinstance(parallel_groups, list):
            parallel_groups = []

        group_by_id: Dict[str, Dict[str, Any]] = {}
        node_to_group: Dict[str, str] = {}
        for group in parallel_groups:
            if not isinstance(group, dict):
                continue
            group_id = str(group.get("id") or "").strip()
            if not group_id:
                continue
            group_by_id[group_id] = group
            for node_id in group.get("node_ids") or []:
                fid = str(node_id).strip()
                if fid:
                    node_to_group[fid] = group_id

        fusion_to_index = cls._fusion_index_map()
        consumed_groups: set[str] = set()
        stages: List[ExecutionStage] = []

        for node in chain:
            fusion_node_id = str(node.get("fusion_node_id") or "")
            group_id = node_to_group.get(fusion_node_id)
            if group_id and group_id not in consumed_groups:
                consumed_groups.add(group_id)
                group = group_by_id.get(group_id) or {}
                indices = [
                    fusion_to_index[fid]
                    for fid in (group.get("node_ids") or [])
                    if str(fid).strip() in fusion_to_index
                ]
                indices = sorted(indices, key=lambda idx: next(
                    (pos for pos, row in enumerate(chain) if row.get("index") == idx),
                    idx,
                ))
                if not indices:
                    continue
                stage_type = "parallel" if len(indices) > 1 else "single"
                stages.append(
                    {
                        "type": stage_type,
                        "indices": indices,
                        "group_id": group_id,
                        "label": str(group.get("label") or group_id),
                    }
                )
                continue
            if group_id:
                continue
            stages.append(
                {
                    "type": "single",
                    "indices": [int(node["index"])],
                    "group_id": "",
                    "label": node.get("name") or fusion_node_id,
                }
            )
        return stages

    @classmethod
    def stage_for_index(cls, node_index: int) -> Optional[ExecutionStage]:
        idx = int(node_index)
        for stage in cls.build_execution_stages():
            if idx in stage["indices"]:
                return stage
        return None

    @classmethod
    def creation_next_node_index(cls, current: int) -> Optional[int]:
        current = int(current)
        stages = cls.build_execution_stages()
        for pos, stage in enumerate(stages):
            if current not in stage["indices"]:
                continue
            if pos + 1 >= len(stages):
                return None
            return stages[pos + 1]["indices"][0]

        indices = [int(n["index"]) for n in cls._chain_nodes()]
        try:
            at = indices.index(current)
        except ValueError:
            return None
        if at + 1 < len(indices):
            return indices[at + 1]
        return None

    @classmethod
    def pending_parallel_indices(cls, project, current_index: int) -> List[int]:
        stage = cls.stage_for_index(current_index)
        if not stage or stage["type"] != "parallel":
            return []
        from apps.creation.models import CreationNode

        pending: List[int] = []
        for idx in stage["indices"]:
            if int(idx) == int(current_index):
                continue
            node = CreationNode.objects.filter(project=project, node_index=int(idx)).first()
            if not node or node.status != CreationNode.STATUS_COMPLETED:
                pending.append(int(idx))
        return pending

    @classmethod
    def execution_plan_payload(cls, pack_id: Optional[str] = None) -> Dict[str, Any]:
        stages = cls.build_execution_stages(pack_id)
        edges = cls._flow_edges(pack_id)
        return {
            "flow_graph": cls.get_flow_graph(pack_id),
            "stages": stages,
            "edges": edges,
            "has_parallel": any(stage["type"] == "parallel" for stage in stages),
            "has_branches": any(edge.get("type") == cls.EDGE_BRANCH for edge in edges),
        }

    @classmethod
    def enrich_portal_chain(
        cls,
        chain: List[Dict[str, Any]],
        pack_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        stages = cls.build_execution_stages(pack_id)
        index_to_stage: Dict[int, ExecutionStage] = {}
        for stage in stages:
            for idx in stage["indices"]:
                index_to_stage[int(idx)] = stage

        branch_sources = {
            edge.get("from")
            for edge in cls._flow_edges(pack_id)
            if edge.get("type") == cls.EDGE_BRANCH
        }

        enriched: List[Dict[str, Any]] = []
        for item in chain:
            row = dict(item)
            idx = int(row.get("index") or 0)
            stage = index_to_stage.get(idx)
            fusion_node_id = str(row.get("fusion_node_id") or "")
            if stage:
                row["orchestration_stage_type"] = stage["type"]
                row["orchestration_stage_label"] = stage.get("label") or ""
                if stage["type"] == "parallel":
                    row["orchestration_parallel_peers"] = [
                        peer for peer in stage["indices"] if int(peer) != idx
                    ]
            if fusion_node_id in branch_sources:
                row["orchestration_has_branch"] = True
            enriched.append(row)
        return enriched

    @classmethod
    def parallel_group_id_for_fusion_node(cls, fusion_node_id: str) -> str:
        flow_graph = cls.get_flow_graph()
        for group in flow_graph.get("parallel_groups") or []:
            if not isinstance(group, dict):
                continue
            node_ids = [str(item).strip() for item in (group.get("node_ids") or [])]
            if str(fusion_node_id).strip() in node_ids:
                return str(group.get("id") or "")
        return ""
