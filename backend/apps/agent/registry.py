# -*- coding: utf-8 -*-
"""DB-backed Agent Registry service."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from apps.agent.models import AgentRegistryConfig

from apps.common.agent_term import (
    attach_api_meta,
    enrich_registry_for_api,
    normalize_agent_runner_path,
    normalize_registry_for_save,
)

logger = logging.getLogger(__name__)

CONFIG_KEY = "default"


class AgentRegistryConfigService:
    @staticmethod
    def builtin_registry() -> Dict[str, Any]:
        return {
            "_meta": {"version": "scriptforge-runtime-v1"},
            "orchestrator": {"runtime": "scriptforge"},
            "agents": [
                {"id": "brief", "name": "Brief Agent", "workspace_index": 1, "outputs": ["project_brief"]},
                {"id": "structure", "name": "Structure Agent", "workspace_index": 2, "outputs": ["structure_plan"]},
                {"id": "character", "name": "Character Agent", "workspace_index": 3, "outputs": ["character_bible"]},
                {"id": "outline", "name": "Outline Agent", "workspace_index": 4, "outputs": ["series_outline"]},
                {"id": "script", "name": "Script Agent", "workspace_index": 5, "outputs": ["episode_scripts"]},
                {"id": "review", "name": "Review Agent", "outputs": ["review_report"]},
                {"id": "score", "name": "Score Agent", "outputs": ["score_report"]},
                {"id": "polish", "name": "Polish Agent", "outputs": ["episode_scripts", "polish_log"]},
                {"id": "marketing", "name": "Marketing Agent", "outputs": ["marketing_kit"]},
                {"id": "insight", "name": "Insight Agent", "outputs": ["insight_report"]},
            ],
        }

    @staticmethod
    def _resolve_registry_path() -> Path:
        raise FileNotFoundError("external agent registry import has been removed")

    @classmethod
    def _load_file_registry(cls) -> Dict[str, Any]:
        path = cls._resolve_registry_path()
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        data["_registry_path"] = str(path)
        return data

    @classmethod
    def _load_file_registry_optional(cls) -> Optional[Dict[str, Any]]:
        try:
            return cls._load_file_registry()
        except FileNotFoundError:
            return None

    @staticmethod
    def _clear_runtime_cache() -> None:
        try:
            from apps.agent.runtime import get_agent_registry

            get_agent_registry.cache_clear()
        except Exception as exc:  # noqa: BLE001
            logger.debug("agent registry cache clear failed: %s", exc)

    @staticmethod
    def _registry_has_agents(registry: Any) -> bool:
        return isinstance(registry, dict) and bool(registry.get("agents"))

    @staticmethod
    def validate_registry(registry: Any) -> Tuple[bool, str]:
        if not isinstance(registry, dict):
            return False, "registry must be a JSON object"
        agents = registry.get("agents")
        if not isinstance(agents, list) or not agents:
            return False, "registry.agents cannot be empty"
        seen = set()
        for agent in agents:
            if not isinstance(agent, dict):
                return False, "agent entries must be objects"
            agent_id = str(agent.get("id") or "").strip()
            if not agent_id:
                return False, "agent id is required"
            if agent_id in seen:
                return False, f"duplicate agent id: {agent_id}"
            seen.add(agent_id)
        meta = registry.get("_meta")
        if meta is not None and not isinstance(meta, dict):
            return False, "_meta must be an object"
        return True, ""

    @classmethod
    def get_active_row(cls) -> Optional[AgentRegistryConfig]:
        return (
            AgentRegistryConfig.objects.filter(is_active=True, config_key=CONFIG_KEY)
            .order_by("-updated_at")
            .first()
        )

    @classmethod
    def ensure_defaults(cls) -> None:
        row = cls.get_active_row()
        if row and cls._registry_has_agents(row.registry):
            return
        cls.save_registry(
            cls.builtin_registry(),
            note="built-in ScriptForge runtime",
            activate=True,
        )

    @classmethod
    def admin_payload(cls) -> Dict[str, Any]:
        row = cls.get_active_row()
        file_registry = cls._load_file_registry_optional()
        active_registry = (
            dict(row.registry)
            if row and isinstance(row.registry, dict) and row.registry
            else {"agents": [], "_meta": {}}
        )
        from apps.agent.bootstrap.tier1_sections import AGENT_TIER1_SEED
        from apps.workflow.step_admin import PipelineStepAdminService

        return attach_api_meta(
            {
            "config_key": CONFIG_KEY,
            "config_id": str(row.id) if row else None,
            "source": "db" if row and cls._registry_has_agents(row.registry) else "none",
            "is_active_db": bool(row and row.is_active),
            "display_name": row.display_name if row else "榛樿鎶€鑳芥敞鍐岃〃",
            "note": row.note if row else "",
            "updated_at": row.updated_at.isoformat() if row and row.updated_at else None,
            "file_path": file_registry.get("_registry_path") if file_registry else None,
            "file_version": (file_registry.get("_meta") or {}).get("version") if file_registry else None,
            "tier1_section_catalog": PipelineStepAdminService.tier1_section_catalog(),
            "tier1_section_catalog_detail": PipelineStepAdminService.tier1_section_catalog_detail(),
            "default_tier1_sections_by_agent": AGENT_TIER1_SEED,
            "default_tier1_sections_by_skill": AGENT_TIER1_SEED,
            "registry": enrich_registry_for_api(active_registry),
            }
        )

    @classmethod
    def save_registry(
        cls,
        registry: Dict[str, Any],
        *,
        note: str = "",
        activate: bool = True,
    ) -> AgentRegistryConfig:
        ok, message = cls.validate_registry(registry)
        if not ok:
            raise ValueError(message)

        clean = normalize_registry_for_save(dict(registry))
        for transient in ("_registry_source", "_registry_path", "_registry_config_id"):
            clean.pop(transient, None)

        row, _ = AgentRegistryConfig.objects.update_or_create(
            config_key=CONFIG_KEY,
            defaults={
                "display_name": "Default Agent Registry",
                "registry": clean,
                "is_active": activate,
                "note": note or "admin save",
            },
        )
        cls._clear_runtime_cache()
        return row

    @classmethod
    def patch_agent(cls, agent_id: str, patch: Dict[str, Any]) -> None:
        """Patch one agent in the active registry."""
        aid = (agent_id or "").strip()
        if not aid:
            raise ValueError("agent_id 涓嶈兘涓虹┖")
        row = cls.get_active_row()
        if not row or not isinstance(row.registry, dict):
            cls.ensure_defaults()
            row = cls.get_active_row()
        if not row:
            raise ValueError("Agent Registry 鏈垵濮嬪寲")

        registry = dict(row.registry or {})
        agents = list(registry.get("agents") or [])
        updated = False
        for index, agent in enumerate(agents):
            if not isinstance(agent, dict) or str(agent.get("id") or "").strip() != aid:
                continue
            merged = dict(agent)
            for key, value in patch.items():
                if key == "prompt" and isinstance(value, dict):
                    prompt = dict(merged.get("prompt") or {})
                    prompt.update(value)
                    merged["prompt"] = prompt
                elif key in ("runner", "runner_path"):
                    merged[key] = normalize_agent_runner_path(value)
                else:
                    merged[key] = value
            agents[index] = merged
            updated = True
            break
        if not updated:
            raise ValueError(f"鏈壘鍒?Agent: {aid}")
        registry["agents"] = agents
        row.registry = registry
        row.save(update_fields=["registry", "updated_at"])
        cls._clear_runtime_cache()

    @classmethod
    def patch_sub_skill_hint(cls, agent_id: str, skill_id: str, system_hint: str) -> None:
        """Patch a sub-skill system hint in the active registry."""
        aid = (agent_id or "").strip()
        sid = (skill_id or "").strip()
        if not aid or not sid:
            raise ValueError("agent_id 鍜?skill_id 涓嶈兘涓虹┖")
        row = cls.get_active_row()
        if not row or not isinstance(row.registry, dict):
            cls.ensure_defaults()
            row = cls.get_active_row()
        if not row:
            raise ValueError("Agent Registry 鏈垵濮嬪寲")

        registry = dict(row.registry or {})
        agents = list(registry.get("agents") or [])
        agent_found = False
        skill_found = False
        for ai, agent in enumerate(agents):
            if not isinstance(agent, dict) or str(agent.get("id") or "").strip() != aid:
                continue
            agent_found = True
            sub_skills = list(agent.get("sub_skills") or [])
            for si, skill in enumerate(sub_skills):
                if not isinstance(skill, dict) or str(skill.get("id") or "").strip() != sid:
                    continue
                skill_found = True
                updated_skill = dict(skill)
                updated_skill["system_hint"] = (system_hint or "").strip()
                sub_skills[si] = updated_skill
            updated_agent = dict(agent)
            updated_agent["sub_skills"] = sub_skills
            agents[ai] = updated_agent
            break

        if not agent_found:
            raise ValueError(f"鏈壘鍒?Agent: {aid}")
        if not skill_found:
            raise ValueError(f"鏈壘鍒?Agent {aid} 鐨勫瓙鎶€鑳? {sid}")

        registry["agents"] = agents
        row.registry = registry
        row.save(update_fields=["registry", "updated_at"])
        cls._clear_runtime_cache()

    @classmethod
    def migrate_pipeline_skill_config(cls) -> int:
        """Migrate pipeline skill metadata into Agent Registry and LLM routes."""
        from apps.agent.bootstrap.tier1_sections import AGENT_TIER1_SEED
        from apps.agent.binding import (
            agent_id_for_fusion_node,
            get_agent_definition,
        )
        from apps.agent.routes import AgentLlmRouteService
        from apps.workflow.prompt_seed import get_default_user_template
        from apps.workflow.pipeline_store import FusionPipelineDbService
        from apps.workflow.models import FusionPipelineNode

        pack = FusionPipelineDbService.get_active_pack()
        if not pack:
            return 0
        cls.ensure_defaults()
        AgentLlmRouteService.seed_defaults()
        migrated = 0
        for row in FusionPipelineNode.objects.filter(pack=pack):
            agent_id = agent_id_for_fusion_node(row.fusion_node_id)
            if not agent_id:
                continue
            patch: Dict[str, Any] = {}
            agent = get_agent_definition(agent_id)
            existing_tier1 = agent.get("tier1_sections") if isinstance(agent.get("tier1_sections"), list) else []
            tier1_sections = getattr(row, "tier1_sections", None) or []
            if tier1_sections:
                patch["tier1_sections"] = list(tier1_sections)
            elif not existing_tier1 and AGENT_TIER1_SEED.get(agent_id):
                patch["tier1_sections"] = list(AGENT_TIER1_SEED[agent_id])
            system_prompt = getattr(row, "system_prompt", "") or ""
            user_prompt_tpl = getattr(row, "user_prompt_tpl", "") or ""
            prompt_constraints = getattr(row, "prompt_constraints", "") or ""
            if system_prompt or user_prompt_tpl or prompt_constraints:
                patch["prompt"] = {
                    "system": system_prompt,
                    "userTemplate": user_prompt_tpl or get_default_user_template(),
                    "constraints": prompt_constraints,
                }
                patch["prompt_enabled"] = bool(getattr(row, "prompt_enabled", True))
            max_tokens = getattr(row, "max_tokens", None)
            if max_tokens:
                patch["max_tokens"] = int(max_tokens)
            route_payload: Dict[str, Any] = {}
            llm_provider_id = getattr(row, "llm_provider_id", None)
            llm_provider = getattr(row, "llm_provider", None)
            if llm_provider_id and llm_provider and getattr(llm_provider, "is_enabled", False):
                route_payload["llm_provider_id"] = str(llm_provider_id)
            if max_tokens:
                route_payload["max_tokens"] = int(max_tokens)
            if route_payload:
                AgentLlmRouteService.upsert(agent_id, route_payload)
            if not patch:
                if route_payload:
                    migrated += 1
                continue
            try:
                cls.patch_agent(agent_id, patch)
                migrated += 1
            except ValueError:
                if route_payload:
                    migrated += 1
                continue
        return migrated

    @classmethod
    def _merge_file_registry_with_db_hints(
        cls,
        file_registry: Dict[str, Any],
        db_registry: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merge imported registry data with DB-managed system hints."""




        db_agents: Dict[str, Dict[str, str]] = {}
        for agent in (db_registry.get("agents") or []):
            if not isinstance(agent, dict):
                continue
            aid = str(agent.get("id") or "").strip()
            if not aid:
                continue
            skill_hints: Dict[str, str] = {}
            for skill in (agent.get("sub_skills") or []):
                if not isinstance(skill, dict):
                    continue
                sid = str(skill.get("id") or "").strip()
                hint = (skill.get("system_hint") or "").strip()
                if sid and hint:
                    skill_hints[sid] = hint
            if skill_hints:
                db_agents[aid] = skill_hints

        if not db_agents:
            return file_registry

        merged = dict(file_registry)
        merged_agents = []
        for agent in (merged.get("agents") or []):
            if not isinstance(agent, dict):
                merged_agents.append(agent)
                continue
            aid = str(agent.get("id") or "").strip()
            hints = db_agents.get(aid) or {}
            if not hints:
                merged_agents.append(agent)
                continue
            sub_skills = []
            for skill in (agent.get("sub_skills") or []):
                if not isinstance(skill, dict):
                    sub_skills.append(skill)
                    continue
                sid = str(skill.get("id") or "").strip()
                if sid in hints:
                    skill = dict(skill)
                    skill["system_hint"] = hints[sid]
                sub_skills.append(skill)
            agent = dict(agent)
            agent["sub_skills"] = sub_skills
            merged_agents.append(agent)
        merged["agents"] = merged_agents
        return merged

    @classmethod
    @classmethod
    def import_from_file(cls, *, overwrite: bool = True) -> AgentRegistryConfig:
        existing = AgentRegistryConfig.objects.filter(config_key=CONFIG_KEY).first()
        if existing and not overwrite:
            raise ValueError("default registry already exists")
        return cls.save_registry(
            cls.builtin_registry(),
            note="built-in ScriptForge runtime",
            activate=True,
        )
