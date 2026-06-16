# -*- coding: utf-8 -*-
"""主链蓝图 — 聚合流程步骤、Agent 注册表与 LLM 路由。"""
from __future__ import annotations

from typing import Any, Dict, List

from apps.agent.catalog import portal_agent_catalog
from apps.agent.registry import AgentRegistryConfigService
from apps.agent.routes import AgentLlmRouteService
from apps.agent.runtime import post_script_pipeline_index_map
from apps.workflow.bootstrap.workflow_disk import DISK_INDEX_BY_NODE
from apps.workflow.step_admin import PipelineStepAdminService
from apps.workflow.services.flow_graph_service import FlowGraphPlanService
from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.console.orchestration.publish_service import OrchestrationPublishService


class MainChainBlueprintService:
    @staticmethod
    def _routes_by_key() -> Dict[str, Dict[str, Any]]:
        return {row["route_key"]: row for row in AgentLlmRouteService.list_admin_items()}

    @staticmethod
    def _agents_index(registry: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        agents: Dict[str, Dict[str, Any]] = {}
        for agent in registry.get("agents") or []:
            if not isinstance(agent, dict):
                continue
            agent_id = str(agent.get("id") or "").strip()
            if agent_id:
                agents[agent_id] = agent
        return agents

    @classmethod
    def enrich_step(cls, step: Dict[str, Any], agents: Dict[str, Dict[str, Any]], routes: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        agent_id = str(step.get("agent_id") or "").strip()
        agent = agents.get(agent_id) or {}
        route_key = str(step.get("llm_route_key") or agent_id or "").strip()
        route = routes.get(route_key) or {}
        return {
            **step,
            "agent_name": agent.get("name") or "",
            "agent_name_zh": agent.get("name_zh") or step.get("display_name") or "",
            "sub_skills": list(agent.get("sub_skills") or step.get("sub_skills") or []),
            "sub_skill_count": len(agent.get("sub_skills") or []),
            "llm_provider_id": route.get("llm_provider_id") or step.get("llm_provider_id"),
            "llm_provider_name": route.get("llm_provider_name"),
            "route_max_tokens": route.get("max_tokens"),
        }

    @staticmethod
    def _fusion_node_for_agent(agent_id: str) -> str:
        aid = (agent_id or "").strip()
        for fusion_id, index in DISK_INDEX_BY_NODE.items():
            if index > 5:
                continue
            try:
                from apps.agent.runtime import agent_for_pipeline_node_index

                if agent_for_pipeline_node_index(index) == aid:
                    return fusion_id
            except Exception:  # noqa: BLE001
                continue
        return f"agent-{aid}"

    @classmethod
    def _supplement_workspace_steps(
        cls,
        steps: List[Dict[str, Any]],
        agents: Dict[str, Dict[str, Any]],
        routes: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """DB 缺主链步骤时，从 Registry workspace agent 补画布占位（提示同步 SSOT）。"""
        present_agents = {
            str(step.get("agent_id") or "").strip()
            for step in steps
            if str(step.get("agent_id") or "").strip()
        }
        present_indices = {
            int(step.get("node_index"))
            for step in steps
            if step.get("node_index") is not None
        }
        merged = list(steps)
        for agent in sorted(
            (a for a in agents.values() if a.get("workspace_index")),
            key=lambda item: int(item.get("workspace_index") or 0),
        ):
            agent_id = str(agent.get("id") or "").strip()
            workspace_index = int(agent.get("workspace_index") or 0)
            if not agent_id or workspace_index <= 0:
                continue
            if agent_id in present_agents or workspace_index in present_indices:
                continue
            fusion_node_id = cls._fusion_node_for_agent(agent_id)
            merged.append(
                cls.enrich_step(
                    {
                        "id": f"placeholder-{agent_id}",
                        "node_id": fusion_node_id,
                        "fusion_node_id": fusion_node_id,
                        "node_index": workspace_index,
                        "chain_order": workspace_index,
                        "agent_id": agent_id,
                        "display_name": agent.get("name_zh") or agent.get("name") or agent_id,
                        "enabled": False,
                        "portal_visible": True,
                        "flow_placeholder": True,
                    },
                    agents,
                    routes,
                )
            )
        merged.sort(key=lambda item: (item.get("chain_order") or 999, item.get("node_index") or 999))
        return merged

    @classmethod
    def build_blueprint(cls) -> Dict[str, Any]:
        reg_payload = AgentRegistryConfigService.admin_payload()
        registry = reg_payload.get("registry") or {}
        meta = PipelineStepAdminService.meta_payload()
        catalog = portal_agent_catalog()
        routes = cls._routes_by_key()
        agents = cls._agents_index(registry)
        steps = [
            cls.enrich_step(step, agents, routes)
            for step in PipelineStepAdminService.list_steps()
        ]
        steps = cls._supplement_workspace_steps(steps, agents, routes)

        workspace_steps = [s for s in steps if s.get("portal_visible") is not False and (s.get("node_index") or 0) <= 5]
        pipeline_tail = [s for s in steps if s not in workspace_steps]

        active_pack = FusionPipelineDbService.get_active_pack()
        registry_meta = registry.get("_meta") or {}
        pack_flow_graph = dict(active_pack.flow_graph or {}) if active_pack else {}
        flow_graph = pack_flow_graph or registry_meta.get("flow_graph") or {}
        post_script_chain = list(
            (active_pack.post_script_chain if active_pack else None)
            or catalog.get("post_script_chain")
            or registry_meta.get("post_script_chain")
            or []
        )
        execution_plan = FlowGraphPlanService.execution_plan_payload(
            pack_id=str(active_pack.id) if active_pack else None
        )
        pipeline_tail_indices = sorted(post_script_pipeline_index_map().keys())
        publish_state = OrchestrationPublishService.get_publish_state()
        return {
            "version": publish_state.get("published_version") or catalog.get("version") or meta.get("db_version") or registry_meta.get("version"),
            "meta": meta,
            "registry_meta": {
                "source": reg_payload.get("source"),
                "updated_at": reg_payload.get("updated_at"),
                "version": registry_meta.get("version"),
                "file_version": reg_payload.get("file_version"),
            },
            "steps": steps,
            "workspace_steps": workspace_steps,
            "pipeline_tail_steps": pipeline_tail,
            "post_script_chain": post_script_chain,
            "post_script_append_agents": list(catalog.get("post_script_append_agents") or []),
            "polish_max_rounds": catalog.get("polish_max_rounds"),
            "flow_graph": flow_graph,
            "execution_plan": execution_plan,
            "publish_state": publish_state,
            "pipeline_pack": FusionPipelineDbService.serialize_pack_summary(active_pack)
            if active_pack
            else None,
            "execution_modes": {
                "step": {
                    "label": "分步掌控",
                    "pipeline_tail_indices": pipeline_tail_indices,
                    "hint": "节点 6/7 由 invoke_pipeline_step 按 fusion_review / fusion_score 逐步执行。",
                },
                "workspace": {
                    "label": "技能工作台",
                    "post_script_chain_key": "post_script_chain",
                    "hint": "剧本全量生成后由 post_script_chain 统一执行；勿单独触发 pipeline 尾部节点。",
                },
            },
            "tier1_section_catalog_detail": reg_payload.get("tier1_section_catalog_detail") or [],
            "catalog": catalog,
            "agents": {
                agent_id: {
                    **agent,
                    "llm_route": routes.get(agent_id) or {},
                }
                for agent_id, agent in agents.items()
            },
        }

    @classmethod
    def patch_step(cls, step_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        row = PipelineStepAdminService.update_step(step_id, data or {})
        if not row:
            raise ValueError("步骤不存在或未激活配置包")
        reg_payload = AgentRegistryConfigService.admin_payload()
        routes = cls._routes_by_key()
        agents = cls._agents_index(reg_payload.get("registry") or {})
        return cls.enrich_step(
            PipelineStepAdminService.serialize_row(row),
            agents,
            routes,
        )

    @classmethod
    def patch_registry_meta(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        row = AgentRegistryConfigService.get_active_row()
        if not row or not isinstance(row.registry, dict):
            AgentRegistryConfigService.ensure_defaults()
            row = AgentRegistryConfigService.get_active_row()
        if not row:
            raise ValueError("Agent Registry 未初始化")

        registry = dict(row.registry or {})
        meta = dict(registry.get("_meta") or {})
        if "post_script_chain" in data:
            meta["post_script_chain"] = [
                str(item).strip()
                for item in (data.get("post_script_chain") or [])
                if str(item).strip()
            ]
        if "post_script_append_agents" in data:
            meta["post_script_append_agents"] = [
                str(item).strip()
                for item in (data.get("post_script_append_agents") or [])
                if str(item).strip()
            ]
        if "polish_max_rounds" in data:
            meta["polish_max_rounds"] = max(0, int(data.get("polish_max_rounds") or 0))
        if "flow_graph" in data:
            raw_graph = data.get("flow_graph")
            meta["flow_graph"] = raw_graph if isinstance(raw_graph, dict) else {}
        registry["_meta"] = meta
        AgentRegistryConfigService.save_registry(
            registry,
            note="主链工作室更新编排元数据",
        )
        active_pack = FusionPipelineDbService.get_active_pack()
        if active_pack:
            pack_updates: Dict[str, Any] = {}
            if "flow_graph" in data:
                pack_updates["flow_graph"] = meta.get("flow_graph") or {}
            if "post_script_chain" in data:
                pack_updates["post_script_chain"] = meta.get("post_script_chain") or []
            if pack_updates:
                FusionPipelineDbService.update_pack_meta(active_pack.id, pack_updates)
        return {
            "post_script_chain": list(meta.get("post_script_chain") or []),
            "post_script_append_agents": list(meta.get("post_script_append_agents") or []),
            "polish_max_rounds": meta.get("polish_max_rounds"),
            "flow_graph": dict(meta.get("flow_graph") or {}),
        }
