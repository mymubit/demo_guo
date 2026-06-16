# -*- coding: utf-8 -*-
"""编排蓝图发布：草稿校验与 C 端生效快照。"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from apps.agent.registry import AgentRegistryConfigService
from apps.workflow.step_admin import PipelineStepAdminService


class OrchestrationPublishService:
    @staticmethod
    def _canonical_payload(steps: List[Dict[str, Any]], flow_graph: Dict[str, Any]) -> Dict[str, Any]:
        ordered = sorted(steps, key=lambda row: (row.get("chain_order") or 0, row.get("node_index") or 0))
        return {
            "step_order": [
                {
                    "id": str(row.get("id") or ""),
                    "node_id": str(row.get("node_id") or ""),
                    "chain_order": int(row.get("chain_order") or 0),
                    "enabled": bool(row.get("enabled", True)),
                }
                for row in ordered
            ],
            "flow_graph": flow_graph if isinstance(flow_graph, dict) else {},
        }

    @classmethod
    def compute_checksum(cls, steps: List[Dict[str, Any]], flow_graph: Dict[str, Any]) -> str:
        raw = json.dumps(cls._canonical_payload(steps, flow_graph), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def _current_snapshot(cls) -> Dict[str, Any]:
        reg_payload = AgentRegistryConfigService.admin_payload()
        registry = reg_payload.get("registry") or {}
        meta = registry.get("_meta") or {}
        flow_graph = meta.get("flow_graph") if isinstance(meta.get("flow_graph"), dict) else {}
        steps = PipelineStepAdminService.list_steps()
        checksum = cls.compute_checksum(steps, flow_graph)
        return {
            "checksum": checksum,
            "flow_graph": dict(flow_graph),
            "step_count": len(steps),
        }

    @classmethod
    def get_publish_state(cls) -> Dict[str, Any]:
        reg_payload = AgentRegistryConfigService.admin_payload()
        registry = reg_payload.get("registry") or {}
        meta = registry.get("_meta") or {}
        publish = meta.get("orchestration_publish") if isinstance(meta.get("orchestration_publish"), dict) else {}
        current = cls._current_snapshot()
        published_checksum = str(publish.get("checksum") or "")
        return {
            "is_dirty": bool(published_checksum) and published_checksum != current["checksum"],
            "has_published": bool(published_checksum),
            "published_at": publish.get("published_at") or "",
            "published_version": publish.get("version") or "",
            "published_checksum": published_checksum,
            "current_checksum": current["checksum"],
            "step_count": current["step_count"],
        }

    @classmethod
    def publish(cls, *, note: str = "") -> Dict[str, Any]:
        row = AgentRegistryConfigService.get_active_row()
        if not row or not isinstance(row.registry, dict):
            AgentRegistryConfigService.ensure_defaults()
            row = AgentRegistryConfigService.get_active_row()
        if not row:
            raise ValueError("Agent Registry 未初始化")

        registry = dict(row.registry or {})
        meta = dict(registry.get("_meta") or {})
        current = cls._current_snapshot()
        prev = meta.get("orchestration_publish") if isinstance(meta.get("orchestration_publish"), dict) else {}
        prev_version = str(prev.get("version") or meta.get("version") or "1.0.0")
        try:
            major, minor, patch = [int(part) for part in prev_version.split(".")[:3]]
            next_version = f"{major}.{minor}.{patch + 1}"
        except (TypeError, ValueError):
            next_version = "1.0.1"

        published_at = datetime.now(timezone.utc).isoformat()
        meta["orchestration_publish"] = {
            "version": next_version,
            "checksum": current["checksum"],
            "published_at": published_at,
            "flow_graph": dict(current["flow_graph"]),
            "step_count": current["step_count"],
            "note": str(note or "").strip()[:200],
        }
        meta["version"] = next_version
        registry["_meta"] = meta
        AgentRegistryConfigService.save_registry(
            registry,
            note=note or "编排蓝图发布到 C 端",
        )
        return {
            "published_at": published_at,
            "version": next_version,
            "checksum": current["checksum"],
            "step_count": current["step_count"],
            "is_dirty": False,
        }

    @classmethod
    def published_flow_graph(cls) -> Dict[str, Any]:
        from apps.agent.runtime import get_agent_registry

        meta = get_agent_registry().get("_meta") or {}
        publish = meta.get("orchestration_publish") if isinstance(meta.get("orchestration_publish"), dict) else {}
        graph = publish.get("flow_graph")
        if isinstance(graph, dict) and graph:
            return dict(graph)
        raw = meta.get("flow_graph")
        return dict(raw) if isinstance(raw, dict) else {}
