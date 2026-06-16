# -*- coding: utf-8 -*-
"""主链步骤 Admin — 流水线仅存编排元数据，技能配置读写 Agent Registry。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.db import transaction

from apps.agent.binding import (
    agent_id_for_fusion_node,
    pipeline_step_skill_view,
)
from apps.common.agent_term import alias_agent_id
from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.workflow.models import FusionPipelineNode


class PipelineStepAdminService:
    @staticmethod
    def _active_nodes_qs():
        pack = FusionPipelineDbService.get_active_pack()
        if not pack:
            return FusionPipelineNode.objects.none()
        return FusionPipelineNode.objects.filter(pack=pack).order_by("chain_order")

    @staticmethod
    def tier1_section_catalog() -> List[str]:
        from apps.workflow.tier1_sections import tier1_section_catalog_detail

        return [item["key"] for item in tier1_section_catalog_detail()]

    @staticmethod
    def tier1_section_catalog_detail() -> List[Dict[str, str]]:
        from apps.workflow.tier1_sections import tier1_section_catalog_detail

        return tier1_section_catalog_detail()

    @staticmethod
    def list_steps() -> List[Dict[str, Any]]:
        items = []
        for row in PipelineStepAdminService._active_nodes_qs():
            items.append(PipelineStepAdminService.serialize_row(row))
        return items

    @staticmethod
    def meta_payload() -> Dict[str, Any]:
        meta = FusionPipelineDbService.meta_payload()
        steps = PipelineStepAdminService.list_steps()
        enabled = [s for s in steps if s.get("enabled")]
        meta["estimated_auto_cost"] = sum(int(s.get("coin_cost") or 0) for s in enabled)
        meta["enabled_count"] = len(enabled)
        meta["node_count"] = len(steps)
        return meta

    @staticmethod
    def serialize_row(row: FusionPipelineNode) -> Dict[str, Any]:
        skill = pipeline_step_skill_view(row.fusion_node_id)
        agent_id = skill.get("agent_id") or agent_id_for_fusion_node(row.fusion_node_id) or ""
        return alias_agent_id({
            "id": str(row.id),
            "node_id": row.fusion_node_id,
            "fusion_node_id": row.fusion_node_id,
            "node_index": row.website_index,
            "chain_order": row.chain_order,
            "agent_id": agent_id,
            "display_name": row.name,
            "name": row.name,
            "description": row.description or "",
            "output_key": row.output_key or "",
            "schema_file": row.schema.filename if row.schema_id else "",
            "enabled": row.enabled,
            "requires_confirm": row.requires_confirm,
            "portal_visible": row.portal_visible,
            "coin_cost": row.coin_cost,
            "runner_type": row.runner_type or "",
            "runner_path": row.runner_path or "",
            "artifact_key": row.artifact_key or "",
            "updated_at": row.updated_at,
            # 技能配置（只读视图，实际 SSOT 在 Agent Registry / Agent LLM 路由）
            "tier1_sections": skill.get("tier1_sections") or [],
            "system_prompt": skill.get("system_prompt") or "",
            "user_prompt_tpl": skill.get("user_prompt_tpl") or "",
            "constraints": skill.get("constraints") or "",
            "prompt_enabled": skill.get("prompt_enabled", True),
            "max_tokens": skill.get("max_tokens"),
            "llm_route_key": skill.get("llm_route_key") or agent_id,
            "skill_config_source": "agent" if agent_id else "legacy",
        })

    @staticmethod
    def get_step(node_uuid: str) -> Optional[FusionPipelineNode]:
        return PipelineStepAdminService._active_nodes_qs().filter(pk=node_uuid).first()

    @staticmethod
    def _apply_skill_patch_to_agent(agent_id: str, data: Dict[str, Any]) -> None:
        if not agent_id:
            return
        from apps.agent.registry import AgentRegistryConfigService

        patch: Dict[str, Any] = {}
        if "tier1_sections" in data:
            sections = data.get("tier1_sections") or []
            patch["tier1_sections"] = [str(s).strip() for s in sections if str(s).strip()]
        prompt_keys = ("system_prompt", "user_prompt_tpl", "constraints", "prompt_enabled")
        if any(key in data for key in prompt_keys):
            prompt_patch: Dict[str, Any] = {}
            if "system_prompt" in data:
                prompt_patch["system"] = str(data.get("system_prompt") or "")
            if "user_prompt_tpl" in data:
                prompt_patch["userTemplate"] = str(data.get("user_prompt_tpl") or "")
            if "constraints" in data:
                prompt_patch["constraints"] = str(data.get("constraints") or "")
            patch["prompt"] = prompt_patch
            if "prompt_enabled" in data:
                patch["prompt_enabled"] = bool(data["prompt_enabled"])
        if "max_tokens" in data:
            val = data["max_tokens"]
            patch["max_tokens"] = max(256, int(val)) if val not in (None, "") else None
        if "sub_skills" in data:
            patch["sub_skills"] = data.get("sub_skills") or []
        if patch:
            AgentRegistryConfigService.patch_agent(agent_id, patch)

        if "llm_provider_id" in data or "max_tokens" in data:
            from apps.agent.routes import AgentLlmRouteService

            route_payload: Dict[str, Any] = {}
            if "max_tokens" in data:
                val = data["max_tokens"]
                route_payload["max_tokens"] = max(256, int(val)) if val not in (None, "") else None
            if "llm_provider_id" in data:
                route_payload["llm_provider_id"] = data.get("llm_provider_id")
            if route_payload:
                AgentLlmRouteService.upsert(agent_id, route_payload)

    @staticmethod
    def reorder_steps(ordered_ids: List[str]) -> List[Dict[str, Any]]:
        pack = FusionPipelineDbService.get_active_pack()
        if not pack:
            raise ValueError("无激活的流水线配置包")

        qs = FusionPipelineNode.objects.filter(pack=pack)
        by_id = {str(row.id): row for row in qs}
        active_ids = [str(item).strip() for item in ordered_ids if str(item).strip()]
        expected_ids = {str(row.id) for row in qs}
        if set(active_ids) != expected_ids or len(active_ids) != len(expected_ids):
            raise ValueError("步骤列表与当前配置包不一致，无法重排")

        offset = 10_000
        with transaction.atomic():
            temp_rows = []
            for idx, node_id in enumerate(active_ids, start=1):
                row = by_id[node_id]
                row.chain_order = offset + idx
                temp_rows.append(row)
            FusionPipelineNode.objects.bulk_update(temp_rows, ["chain_order"])

            final_rows = []
            for idx, node_id in enumerate(active_ids, start=1):
                row = by_id[node_id]
                row.chain_order = idx
                final_rows.append(row)
            FusionPipelineNode.objects.bulk_update(final_rows, ["chain_order"])

        FusionPipelineDbService.clear_caches()
        return PipelineStepAdminService.list_steps()

    @staticmethod
    def update_step(node_uuid: str, data: Dict[str, Any]) -> Optional[FusionPipelineNode]:
        row = PipelineStepAdminService.get_step(node_uuid)
        if not row:
            return None

        if "display_name" in data or "name" in data:
            row.name = str(data.get("display_name") or data.get("name") or row.name)[:128]
        if "description" in data:
            row.description = str(data.get("description") or "")
        if "enabled" in data:
            row.enabled = bool(data["enabled"])
        if "requires_confirm" in data:
            row.requires_confirm = bool(data["requires_confirm"])
        if "portal_visible" in data:
            row.portal_visible = bool(data["portal_visible"])
        if "coin_cost" in data:
            row.coin_cost = max(0, int(data["coin_cost"]))

        skill_keys = {
            "tier1_sections",
            "system_prompt",
            "user_prompt_tpl",
            "constraints",
            "prompt_enabled",
            "max_tokens",
            "llm_provider_id",
            "sub_skills",
        }
        if skill_keys.intersection(data.keys()):
            agent_id = agent_id_for_fusion_node(row.fusion_node_id) or ""
            PipelineStepAdminService._apply_skill_patch_to_agent(agent_id, data)

        row.save()
        FusionPipelineDbService.clear_caches()
        return row

    @staticmethod
    def resolve_prompt_for_node(fusion_node_id: str) -> Optional[Dict[str, Any]]:
        from apps.agent.binding import resolve_prompt_for_node

        return resolve_prompt_for_node(fusion_node_id)

    @staticmethod
    def resolve_provider_id(fusion_node_id: str) -> Optional[str]:
        from apps.agent.routes import AgentLlmRouteService

        return AgentLlmRouteService.resolve_provider_id_for_node(fusion_node_id)

    @staticmethod
    def _legacy_resolve_provider_id(fusion_node_id: str) -> Optional[str]:
        from apps.skill.models import LlmProvider

        active = LlmProvider.objects.filter(is_active=True, is_enabled=True).first()
        return str(active.id) if active else None

    @staticmethod
    def build_prompts_dict() -> Dict[str, Any]:
        from apps.agent.binding import build_prompts_dict_by_agent

        return build_prompts_dict_by_agent()

    @staticmethod
    def update_tier1_sections(node_id: str, sections: Any) -> bool:
        agent_id = agent_id_for_fusion_node(node_id)
        if not agent_id:
            return False
        from apps.agent.registry import AgentRegistryConfigService

        AgentRegistryConfigService.patch_agent(
            agent_id,
            {"tier1_sections": [str(s).strip() for s in (sections or []) if str(s).strip()]},
        )
        return True
