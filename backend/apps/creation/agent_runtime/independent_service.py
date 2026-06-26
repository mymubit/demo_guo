# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List, Tuple

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.runtime import workspace_index_for_agent
from apps.agent.models import AgentDefinition, AgentKnowledgeBinding
from apps.creation.artifact_service import get_artifact, save_artifact
from apps.creation.models import AgentExecutionRun, Project, ProjectFusionArtifact
from apps.creation.monitoring.execution_run_service import AgentExecutionRunService
from apps.creation.agent_runtime.episode_merge import (
    merge_episode_designs_by_number,
    merge_episode_outlines_by_number,
    merge_episodes_by_number,
    merge_series_outline_artifact,
)
from apps.skill.llm.chat import LlmService
from apps.skill.llm.usage_log import llm_usage_scope
from apps.skill.models import LlmUsageLog

TEMPLATE_PATH_VAR_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")
EPISODE_ARTIFACT_KEYS = frozenset({"episode_scripts", "series_outline", "polished_script"})
NARRATIVE_PLAN_ARTIFACT_KEY = "narrative_plan"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EnqueueRunResult:
    run: AgentExecutionRun
    created_new_run: bool
    should_enqueue: bool


class AgentRuntimeError(Exception):
    pass


def estimate_tokens(text: str) -> int:
    return max(1, len(text or "") // 4)


def extract_json_object(text: str) -> Dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise AgentRuntimeError("???????")
    candidates = [raw]
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.S)
    if fenced:
        candidates.insert(0, fenced.group(1))
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        candidates.append(raw[start : end + 1])
    last_error = ""
    for candidate in candidates:
        # ?????????? strict=False ??????? LLM ???
        # ?????????????????/?????
        for strict in (True, False):
            try:
                parsed = json.loads(candidate, strict=strict)
            except json.JSONDecodeError as exc:
                last_error = str(exc)
                continue
            if not isinstance(parsed, dict):
                raise AgentRuntimeError("???? JSON ???????")
            return parsed
    raise AgentRuntimeError(f"???????? JSON?{last_error}")


class IndependentAgentService:
    @staticmethod
    def assert_project_owner(project: Project, user) -> None:
        if project.user_id != getattr(user, "id", None) and not getattr(user, "is_staff", False):
            raise PermissionDenied("???????")

    @staticmethod
    def running_run(project: Project) -> AgentExecutionRun | None:
        timeout_at = timezone.now() - timedelta(minutes=30)
        AgentExecutionRun.objects.filter(
            project=project,
            status=AgentExecutionRun.STATUS_RUNNING,
            started_at__lt=timeout_at,
        ).update(
            status=AgentExecutionRun.STATUS_FAILED,
            finished_at=timezone.now(),
            error_message="????????????",
        )
        return (
            AgentExecutionRun.objects.filter(project=project, status=AgentExecutionRun.STATUS_RUNNING)
            .order_by("-started_at")
            .first()
        )

    @staticmethod
    def build_agent_input(project: Project, agent: AgentDefinition, params: Dict[str, Any]) -> Dict[str, Any]:
        contract = agent.input_contract or {}
        project_fields = contract.get("project_fields") or []
        project_payload = {
            field: getattr(project, field, None)
            for field in project_fields
            if hasattr(project, field)
        }
        required_artifacts = [str(k) for k in contract.get("required_artifacts") or []]
        optional_artifacts = [str(k) for k in contract.get("optional_artifacts") or []]
        artifacts: Dict[str, Any] = {}
        missing = []
        for key in required_artifacts:
            payload = get_artifact(project, key)
            if payload in (None, {}, []):
                missing.append(key)
            else:
                artifacts[key] = payload
        for key in optional_artifacts:
            payload = get_artifact(project, key)
            if payload not in (None, {}, []):
                artifacts[key] = payload
        if missing:
            raise AgentRuntimeError(f"??????: {', '.join(missing)}")
        params = dict(params or {})
        output_artifact_key = str(getattr(agent, "default_output_artifact_key", "") or "")
        if output_artifact_key == "series_outline":
            from apps.drama.episode_outline_store import (
                OUTLINE_MODE_EPISODES_ONLY,
                OUTLINE_MODE_STRUCTURE_ONLY,
                aggregate_series_outline,
                resolve_outline_mode,
            )
            from apps.creation.artifact_service import get_fusion_meta_payload

            ep_from, ep_to = IndependentAgentService._resolve_episode_bounds(params)
            existing_meta = get_fusion_meta_payload(project, "series_outline")
            outline_mode = resolve_outline_mode(
                params,
                episode_from=ep_from,
                existing_meta=existing_meta,
            )
            params.setdefault("outline_mode", outline_mode)

            if outline_mode == OUTLINE_MODE_STRUCTURE_ONLY:
                params.setdefault(
                    "batch_instruction",
                    (
                        "仅生成全剧结构：输出 six_stage_structure（六阶段）、"
                        "foreshadowing_list（伏笔清单）、rhythm_dual_track_validation 等；"
                        "不要输出 episode_outlines / episodes 分集数组。"
                    ),
                )
            elif outline_mode == OUTLINE_MODE_EPISODES_ONLY:
                prior = aggregate_series_outline(project)
                prior_outlines = prior.get("episode_outlines") or []
                if prior_outlines:
                    artifacts["series_outline"] = {
                        key: value
                        for key, value in prior.items()
                        if key != "_meta"
                    }
                ep_to_text = str(ep_to) if ep_to is not None else "?"
                ep_from_text = str(ep_from) if ep_from is not None else "1"
                params.setdefault(
                    "batch_instruction",
                    (
                        f"续写分集大纲：仅输出第{ep_from_text}-{ep_to_text}集 episode_outlines，"
                        f"每条必须含 episode_num、goal_conflict、ending_hook、ev_et_tp；"
                        f"不要重复输出已有集数；"
                        f"不要输出 six_stage_structure、foreshadowing_list、six_stage_narrative 等全剧结构字段。"
                    ),
                )
            elif ep_from is not None and int(ep_from) > 1:
                prior = aggregate_series_outline(project)
                prior_outlines = prior.get("episode_outlines") or []
                if prior_outlines:
                    artifacts["series_outline"] = {
                        key: value
                        for key, value in prior.items()
                        if key != "_meta"
                    }
                    ep_to_text = str(ep_to) if ep_to is not None else "?"
                    params.setdefault(
                        "batch_instruction",
                        (
                            f"续写分集大纲：仅输出第{ep_from}-{ep_to_text}集 episode_outlines，"
                            f"每条必须含 episode_num、goal_conflict、ending_hook、ev_et_tp；"
                            f"不要重复输出第1-{int(ep_from) - 1}集。"
                        ),
                    )
        blob_cfg_key = output_artifact_key
        if blob_cfg_key:
            from apps.drama.artifact_mode import ARTIFACT_MODE_EPISODES_ONLY, ARTIFACT_MODE_STRUCTURE_ONLY
            from apps.drama.episode_artifact_store import (
                EPISODE_BLOB_CONFIGS,
                aggregate_episode_blob,
                config_supports_structure_mode,
                resolve_blob_mode,
            )
            from apps.creation.artifact_service import get_fusion_meta_payload

            blob_cfg = EPISODE_BLOB_CONFIGS[blob_cfg_key]
            ep_from, ep_to = IndependentAgentService._resolve_episode_bounds(params)
            existing_meta = get_fusion_meta_payload(project, blob_cfg.fusion_key)
            blob_mode = resolve_blob_mode(
                params,
                episode_from=ep_from,
                existing_meta=existing_meta,
                config=blob_cfg,
            )
            params.setdefault("blob_mode", blob_mode)

            if blob_mode == ARTIFACT_MODE_STRUCTURE_ONLY and config_supports_structure_mode(blob_cfg):
                params.setdefault(
                    "batch_instruction",
                    (
                        "仅生成全剧叙事框架：输出 narrative_core_objective、narrative_mechanics、"
                        "narrative_consistency_check、opening_package_verification 等；"
                        "不要输出 episode_narrative_designs 分集数组。"
                    ),
                )
            elif blob_mode == ARTIFACT_MODE_EPISODES_ONLY:
                prior = aggregate_episode_blob(project, blob_cfg)
                prior_items = prior.get(blob_cfg.output_list_key) or []
                if prior_items:
                    artifacts[blob_cfg.fusion_key] = {
                        key: value for key, value in prior.items() if key != "_meta"
                    }
                ep_to_text = str(ep_to) if ep_to is not None else "?"
                ep_from_text = str(ep_from) if ep_from is not None else "1"
                if blob_cfg.fusion_key == "narrative_plan":
                    params.setdefault(
                        "batch_instruction",
                        (
                            f"续写叙事分集设计：仅输出第{ep_from_text}-{ep_to_text}集 episode_narrative_designs，"
                            f"每条必须含 episode_id、narrative_focus；不要重复已有集数；"
                            f"不要输出 narrative_core_objective、narrative_mechanics 等全剧框架字段。"
                        ),
                    )
                else:
                    params.setdefault(
                        "batch_instruction",
                        (
                            f"续写{'润色剧本' if blob_cfg.fusion_key == 'polished_script' else '剧本'}："
                            f"仅输出第{ep_from_text}-{ep_to_text}集 {blob_cfg.output_list_key}，"
                            f"每条必须含 {blob_cfg.number_field} 与正文；不要重复已有集数。"
                        ),
                    )
        payload = {
            "project": project_payload,
            "artifacts": artifacts,
            "params": params,
            "required_artifacts": required_artifacts,
            "optional_artifacts": optional_artifacts,
            "agent_notes": dict(getattr(project, "agent_notes", None) or {}),
        }
        IndependentAgentService._attach_reference_materials(project, payload)
        return payload

    @staticmethod
    def _attach_reference_materials(project: Project, input_payload: Dict[str, Any]) -> None:
        """??????????????????? Agent ???"""
        try:
            from apps.creation.library.models import ReferenceMaterial, ReferenceMaterialInjection
            from apps.creation.library.services import MaterialInjectionService

            fragments: List[Dict[str, Any]] = []
            injections = (
                ReferenceMaterialInjection.objects.filter(project=project)
                .select_related("material")
                .order_by("-injected_at")[:5]
            )
            for inj in injections:
                material = inj.material
                if material.parse_status != ReferenceMaterial.STATUS_READY:
                    continue
                parsed = material.parsed_content or {}
                fragment: Dict[str, Any] = {
                    "material_id": str(material.id),
                    "material_name": material.name,
                }
                for field in inj.injected_fields or []:
                    if field in parsed:
                        fragment[field] = parsed[field]
                if len(fragment) > 2:
                    fragments.append(fragment)

            run_params = input_payload.get("params") or {}
            material_id = run_params.get("material_id")
            if material_id:
                material_fields = run_params.get("material_fields") or [
                    "world",
                    "characters",
                    "plot_structure",
                    "themes",
                ]
                inj_result = MaterialInjectionService().inject_to_context(
                    project,
                    uuid.UUID(str(material_id)),
                    list(material_fields),
                )
                if inj_result.get("context_fragment") and not inj_result.get("error"):
                    fragments.append({
                        "material_id": inj_result.get("material_id"),
                        "material_name": inj_result.get("material_name"),
                        **inj_result.get("context_fragment", {}),
                    })

            if fragments:
                input_payload["reference_materials"] = fragments
        except Exception as exc:
            logger.warning("[IndependentAgent] ??????: %s", exc)

    # ???????????????????
    DEFAULT_KNOWLEDGE_CHARS_PER_BINDING = 4000

    # ????????????/Schema ??????????? prompt?
    # ????/??????????????????????/??????????????
    DEFAULT_INJECTION_POLICY: Dict[str, Any] = {
        "excluded_categories": ["validator", "schema"],
        "category_caps": {"reference_script": 2, "example": 3, "knowledge": 8},
    }

    @classmethod
    def _injection_policy(cls, agent: AgentDefinition) -> Dict[str, Any]:
        """????????? Agent ???????????????"""
        policy: Dict[str, Any] = {
            "excluded_categories": list(cls.DEFAULT_INJECTION_POLICY["excluded_categories"]),
            "category_caps": dict(cls.DEFAULT_INJECTION_POLICY["category_caps"]),
        }
        override = getattr(agent, "knowledge_injection_policy", None) or {}
        if isinstance(override.get("excluded_categories"), list):
            policy["excluded_categories"] = [str(c) for c in override["excluded_categories"]]
        if isinstance(override.get("category_caps"), dict):
            policy["category_caps"].update(override["category_caps"])
        if override.get("max_total_chars"):
            policy["max_total_chars"] = int(override["max_total_chars"])
        return policy

    @staticmethod
    def _knowledge_matches_project(knowledge: AgentKnowledgeItem, project: Project | None) -> bool:
        """?????????????=???????????????"""
        if project is None:
            return True

        def _hit(whitelist, value) -> bool:
            if not whitelist:
                return True
            normalized = str(value or "").strip().lower()
            return any(str(item).strip().lower() == normalized for item in whitelist)

        theme = getattr(project, "theme", "")
        platform = getattr(project, "target_platform", "")
        return (
            _hit(getattr(knowledge, "match_themes", None), theme)
            and _hit(getattr(knowledge, "match_platforms", None), platform)
            and _hit(getattr(knowledge, "match_genres", None), theme)
        )

    @classmethod
    def load_knowledge(
        cls, agent: AgentDefinition, project: Project | None = None
    ) -> List[Dict[str, Any]]:
        policy = cls._injection_policy(agent)
        excluded = {str(c).lower() for c in policy.get("excluded_categories") or []}
        caps = policy.get("category_caps") or {}
        runtime = agent.runtime_policy or {}
        max_prompt_tokens = int(runtime.get("max_prompt_tokens") or 40000)
        budget_chars = int(
            policy.get("max_total_chars") or max(4000, int(max_prompt_tokens * 4 * 0.35))
        )

        # 1. ????????? prompt ???????????????
        candidates = []
        for binding in AgentDefinitionService.enabled_bindings(agent):
            if binding.binding_type in (
                AgentKnowledgeBinding.BindingType.VALIDATOR,
                AgentKnowledgeBinding.BindingType.OUTPUT_SCHEMA,
            ):
                continue
            if binding.inject_position == AgentKnowledgeBinding.InjectPosition.VALIDATOR:
                continue
            knowledge = binding.knowledge
            if not getattr(knowledge, "is_prompt_injectable", True):
                continue
            if str(knowledge.category).lower() in excluded:
                continue
            if not cls._knowledge_matches_project(knowledge, project):
                continue
            candidates.append(binding)

        # 2. ???????????????????????
        seen_signatures = set()
        per_category_count: Dict[str, int] = {}
        selected = []
        for binding in candidates:
            knowledge = binding.knowledge
            signature = (str(knowledge.category).lower(), str(knowledge.title).strip().lower())
            if signature in seen_signatures:
                continue
            # 3. ??? Top-N?candidates ?? order_index/priority ???????????
            category = str(knowledge.category)
            cap = caps.get(category)
            if cap is not None and per_category_count.get(category, 0) >= int(cap):
                continue
            seen_signatures.add(signature)
            per_category_count[category] = per_category_count.get(category, 0) + 1
            selected.append(binding)

        # 4. ???????????
        rows = []
        used_chars = 0
        for binding in selected:
            if used_chars >= budget_chars:
                break
            knowledge = binding.knowledge
            per_cap = int(binding.max_chars) if binding.max_chars else cls.DEFAULT_KNOWLEDGE_CHARS_PER_BINDING
            text = (knowledge.content_text or "")[:per_cap]
            content_json = knowledge.content_json or {}
            json_len = len(json.dumps(content_json, ensure_ascii=False)) if content_json else 0
            if json_len > per_cap:
                content_json = {}
                json_len = 0
            remaining = budget_chars - used_chars
            if len(text) + json_len > remaining:
                text = text[: max(0, remaining - json_len)]
            used_chars += len(text) + json_len
            rows.append(
                {
                    "knowledge_id": knowledge.knowledge_id,
                    "title": knowledge.title,
                    "category": knowledge.category,
                    "inject_position": binding.inject_position,
                    "content_text": text,
                    "content_json": content_json,
                }
            )
        return rows

    @staticmethod
    def _template_roots(context: Dict[str, Any]) -> Dict[str, Any]:
        agent = context["agent"]
        return {
            "agent": {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "name_zh": agent.name_zh or agent.name,
            },
            "project": context["input"]["project"],
            "artifacts": context["input"]["artifacts"],
            "knowledge": context["knowledge"],
            "params": context["input"]["params"],
        }

    @classmethod
    def _resolve_template_path(cls, roots: Dict[str, Any], path: str) -> Any:
        segments = [seg for seg in path.split(".") if seg]
        if not segments:
            return None
        current: Any = roots.get(segments[0])
        for segment in segments[1:]:
            if isinstance(current, dict):
                current = current.get(segment)
            elif isinstance(current, list) and segment.isdigit():
                index = int(segment)
                current = current[index] if 0 <= index < len(current) else None
            else:
                return None
        return current

    @classmethod
    def _format_template_value(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    @classmethod
    def _render_template(cls, template: str, context: Dict[str, Any]) -> str:
        roots = cls._template_roots(context)
        # ?????????????????????????????????
        # ????????????? {{ }} ??????????
        template_skeleton = TEMPLATE_PATH_VAR_RE.sub("", template)
        if "{{" in template_skeleton or "}}" in template_skeleton:
            raise AgentRuntimeError("Prompt ????????")

        def _replace_path_var(match: re.Match[str]) -> str:
            path = match.group(1).strip()
            if path in roots:
                return cls._format_template_value(roots[path])
            return cls._format_template_value(cls._resolve_template_path(roots, path))

        return TEMPLATE_PATH_VAR_RE.sub(_replace_path_var, template)

    @classmethod
    def _prepare_prompt(
        cls,
        project: Project,
        agent: AgentDefinition,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        input_payload = cls.build_agent_input(project, agent, params)
        knowledge = cls.load_knowledge(agent, project)
        system_prompt, user_prompt, prompt_version = cls.render_agent_prompt(agent, input_payload, knowledge)
        estimated = estimate_tokens(system_prompt + "\n" + user_prompt)
        route = AgentDefinitionService.active_route(agent)
        max_prompt = route.max_prompt_tokens or (agent.runtime_policy or {}).get("max_prompt_tokens")
        max_prompt_int = int(max_prompt) if max_prompt else None
        input_char_summary = {}
        for key, payload in (input_payload.get("artifacts") or {}).items():
            if isinstance(payload, (dict, list)):
                text = json.dumps(payload, ensure_ascii=False)
            else:
                text = str(payload or "")
            input_char_summary[str(key)] = len(text)
        return {
            "input_payload": input_payload,
            "knowledge": knowledge,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "prompt_version": prompt_version,
            "estimated_prompt_tokens": estimated,
            "max_prompt_tokens": max_prompt_int,
            "within_limit": not max_prompt_int or estimated <= max_prompt_int,
            "input_artifact_keys": list(input_payload.get("artifacts", {}).keys()),
            "input_char_summary": input_char_summary,
        }

    @classmethod
    def preview_run(cls, project: Project, agent_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        agent = AgentDefinitionService.get_runnable(agent_id)
        prepared = cls._prepare_prompt(project, agent, dict(params or {}))
        from apps.creation.agent_runtime.agent_billing import billing_preview

        billing = billing_preview(agent_id, params)
        return {
            "agent_id": agent.agent_id,
            "estimated_prompt_tokens": prepared["estimated_prompt_tokens"],
            "max_prompt_tokens": prepared["max_prompt_tokens"],
            "within_limit": prepared["within_limit"],
            "input_artifact_keys": prepared["input_artifact_keys"],
            "input_char_summary": prepared["input_char_summary"],
            "prompt_version": prepared["prompt_version"],
            "coin_cost": billing["coin_cost"],
            "action_key": billing["action_key"],
            "currency_name": billing["currency_name"],
        }

    @classmethod
    def _append_agent_notes_block(cls, user_prompt: str, input_payload: Dict[str, Any]) -> str:
        notes = input_payload.get("agent_notes") or {}
        if not isinstance(notes, dict) or not notes:
            return user_prompt
        lines = []
        rejects = notes.get("rejects") or []
        if rejects:
            lines.append("???????????????" + "?".join(str(x) for x in rejects[:20]))
        prefs = notes.get("style_preferences") or []
        if prefs:
            lines.append("?????" + "?".join(str(x) for x in prefs[:20]))
        guidance = notes.get("character_guidance") or ""
        if guidance:
            lines.append(f"?????{guidance}")
        if not lines:
            return user_prompt
        block = "\n".join(lines)
        return f"{user_prompt}\n\n??????\n{block}"

    @classmethod
    def _build_skill_rules_snippet(cls, agent: AgentDefinition, input_payload: Dict[str, Any]) -> str:
        try:
            from apps.skill.skills.agent_scope import genre_from_project_payload
            from apps.skill.skills.loader import get_skill_rule_loader

            genre = genre_from_project_payload(input_payload.get("project") or {})
            return get_skill_rule_loader().build_agent_rules_snippet(agent.agent_id, genre=genre)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[Agent] skill rules snippet skipped agent=%s err=%s", agent.agent_id, exc)
            return ""

    @classmethod
    def render_agent_prompt(
        cls,
        agent: AgentDefinition,
        input_payload: Dict[str, Any],
        knowledge: List[Dict[str, Any]],
    ) -> Tuple[str, str, str]:
        prompt = AgentDefinitionService.active_prompt(agent)
        ctx = {"agent": agent, "input": input_payload, "knowledge": knowledge}
        user_prompt = cls._render_template(prompt.user_prompt_template, ctx)
        sections = [
            prompt.output_format_prompt,
            cls._artifact_key_hint(agent),
            prompt.constraints_prompt,
        ]
        suffix = "\n\n".join(s for s in sections if s)
        if suffix:
            user_prompt = f"{user_prompt}\n\n{suffix}"
        user_prompt = cls._append_agent_notes_block(user_prompt, input_payload)
        system_prompt = prompt.system_prompt or ""
        rules_snippet = cls._build_skill_rules_snippet(agent, input_payload)
        if rules_snippet:
            system_prompt = f"{system_prompt}\n\n{rules_snippet}".strip() if system_prompt else rules_snippet
        return system_prompt, user_prompt, prompt.version

    # ??? schema ???????????? LLM ?????????????
    SCHEMA_FIELD_HINTS: Dict[str, str] = {
        "episode-scripts.v1": (
            "payload ???? episodes ???????? episodeNumber????????????"
        ),
        "review-report.v1": (
            "payload ???????? passed?true=???false=?????"
            "?? issues ????? pacingPassed???? reviewResult/overallStatus ???????"
        ),
        "script-score-report.v1": (
            "payload ???? overallScore????? grade????????"
        ),
        "marketing-kit.v1": (
            "payload ? titles/clipHooks/posterSlogans ?????????"
        ),
        "insight-report.v1": (
            "payload ???? layer1_peel / layer2_mirror / layer3_invert ???????"
        ),
        "polish-log.v1": "payload ? suggestions ?????????",
        "narrative-plan.v1": (
            "payload ?????????narrative_core_objective?target_episode_range?? E001-E005??"
            "episode_narrative_designs?????narrative_mechanics???????narrative_consistency_check?"
            "?? narrative_core?episode_narratives?opening_package_verification?"
            "episode_narrative_designs ???? episode_id?narrative_focus?audience_emotion_design?"
            "narrative_beat_timing??????????????????"
        ),
        "series-outline.v1": (
            "payload 必须含 episode_outlines 数组；分批任务时仅输出本批集数，"
            "每条含 episode_num、goal_conflict、ending_hook、ev_et_tp；"
            "禁止只返回六阶段结构而无分集数组。"
        ),
    }

    @classmethod
    def _artifact_key_hint(cls, agent: AgentDefinition) -> str:
        """??????? artifact_key ???????????? LLM ?????"""
        contract = agent.output_contract or {}
        allowed = [str(k) for k in contract.get("artifacts") or []]
        if not allowed:
            return ""
        default_key = getattr(agent, "default_output_artifact_key", "") or allowed[0]
        parts = [
            "artifact_key ?????????????????????????"
            + " / ".join(allowed)
            + f"??????????artifact_key ???? {default_key}?"
        ]
        schema_hint = cls.SCHEMA_FIELD_HINTS.get(str(contract.get("schema_version") or ""))
        if schema_hint:
            parts.append(schema_hint)
        return " ".join(parts)

    @staticmethod
    def validate_output(
        agent: AgentDefinition,
        output: Dict[str, Any],
        *,
        run_params: dict | None = None,
    ) -> Dict[str, Any]:
        contract = agent.output_contract or {}
        allowed = [str(k) for k in contract.get("artifacts") or []]
        if not allowed:
            raise AgentRuntimeError("Agent ??????")
        validation_params = dict(run_params or {})
        if "payload" in output and isinstance(output.get("payload"), dict):
            default_key = getattr(agent, "default_output_artifact_key", "") or allowed[0]
            artifact_key = str(output.get("artifact_key") or default_key).strip()
            if artifact_key not in allowed:
                # ?? LLM ???? key?????? slug????????? key?
                # ?????????? schema ??????????????????
                logger.warning(
                    "[Agent] %s ?? artifact_key ?????: %s -> %s",
                    agent.agent_id,
                    artifact_key,
                    default_key,
                )
                artifact_key = default_key
            matched = {artifact_key: output["payload"]}
            from .output_schema_validation import validate_matched_outputs

            validate_matched_outputs(
                matched,
                schema_version=str(contract.get("schema_version") or ""),
                run_params=validation_params,
            )
            return matched
        matched = {key: output[key] for key in allowed if key in output and isinstance(output[key], dict)}
        if matched:
            from .output_schema_validation import validate_matched_outputs

            validate_matched_outputs(
                matched,
                schema_version=str(contract.get("schema_version") or ""),
                run_params=validation_params,
            )
            return matched
        normalized = {allowed[0]: output}
        from .output_schema_validation import validate_matched_outputs

        validate_matched_outputs(
            normalized,
            schema_version=str(contract.get("schema_version") or ""),
            run_params=validation_params,
        )
        return normalized

    @staticmethod
    def _resolve_episode_bounds(
        params: Dict[str, Any],
        run: AgentExecutionRun | None = None,
    ) -> Tuple[int | None, int | None]:
        if run is not None:
            if run.batch_from is not None and run.batch_to is not None:
                return int(run.batch_from), int(run.batch_to)
            params = dict(run.run_params or {})
        ep_from = params.get("episode_from") or params.get("episode_start") or params.get("script_from")
        ep_to = params.get("episode_to") or params.get("episode_end") or params.get("script_to")
        try:
            from_ep = int(ep_from) if ep_from is not None else None
        except (TypeError, ValueError):
            from_ep = None
        try:
            to_ep = int(ep_to) if ep_to is not None else None
        except (TypeError, ValueError):
            to_ep = None
        if from_ep is None and to_ep is None:
            ep_range = params.get("episode_range")
            if ep_range and "-" in str(ep_range):
                try:
                    parts = str(ep_range).split("-", 1)
                    from_ep = int(parts[0].strip())
                    to_ep = int(parts[1].strip())
                except (TypeError, ValueError, IndexError):
                    from_ep = None
                    to_ep = None
        return from_ep, to_ep

    @staticmethod
    def _episode_range_from_run(run: AgentExecutionRun) -> Tuple[int | None, int | None]:
        return IndependentAgentService._resolve_episode_bounds({}, run=run)

    @classmethod
    def _merge_artifact_body(
        cls,
        *,
        artifact_key: str,
        incoming: Dict[str, Any],
        existing: Dict[str, Any] | None,
        run: AgentExecutionRun,
    ) -> Dict[str, Any]:
        body = dict(incoming or {})
        if artifact_key == "series_outline":
            merged_base = dict(existing or {})
            ep_from, ep_to = cls._episode_range_from_run(run)
            return merge_series_outline_artifact(
                merged_base,
                body,
                episode_from=ep_from,
                episode_to=ep_to,
            )
        if artifact_key in EPISODE_ARTIFACT_KEYS:
            merged_base = dict(existing or {})
            if not merged_base.get("episodes") and isinstance(body.get("episodes"), list):
                merged_base.setdefault("nodeId", body.get("nodeId", ""))
                merged_base.setdefault("projectId", str(run.project_id))
            ep_from, ep_to = cls._episode_range_from_run(run)
            use_outlines = (
                isinstance(body.get("episode_outlines"), list)
                or isinstance(merged_base.get("episode_outlines"), list)
            )
            if use_outlines:
                merged = merge_episode_outlines_by_number(
                    merged_base,
                    body.get("episode_outlines") or [],
                    episode_from=ep_from,
                    episode_to=ep_to,
                )
                skip_keys = {"episode_outlines", "_meta", "target_episode_range"}
            else:
                merged = merge_episodes_by_number(
                    merged_base,
                    body.get("episodes") or [],
                    episode_from=ep_from,
                    episode_to=ep_to,
                )
                skip_keys = {"episodes", "_meta"}
            for field, value in body.items():
                if field not in skip_keys:
                    merged[field] = value
            return merged
        if artifact_key == NARRATIVE_PLAN_ARTIFACT_KEY:
            merged_base = dict(existing or {})
            ep_from, ep_to = cls._episode_range_from_run(run)
            designs = body.get("episode_narrative_designs") or []
            merged = merge_episode_designs_by_number(
                merged_base,
                designs if isinstance(designs, list) else [],
                episode_from=ep_from,
                episode_to=ep_to,
            )
            for field, value in body.items():
                if field in {"episode_narrative_designs", "_meta", "target_episode_range"}:
                    continue
                if field == "narrative_mechanics" and isinstance(value, list):
                    existing_mech = list(merged.get("narrative_mechanics") or [])
                    seen = {
                        str(item.get("mechanism_type") or "").strip()
                        for item in existing_mech
                        if isinstance(item, dict)
                    }
                    for item in value:
                        if not isinstance(item, dict):
                            continue
                        key = str(item.get("mechanism_type") or "").strip()
                        if key and key in seen:
                            continue
                        existing_mech.append(item)
                        if key:
                            seen.add(key)
                    merged["narrative_mechanics"] = existing_mech
                else:
                    merged[field] = value
            return merged
        if artifact_key == "polish_log":
            merged = dict(existing or {})
            for field, value in body.items():
                if field == "suggestions" and isinstance(value, list):
                    merged["suggestions"] = list(merged.get("suggestions") or []) + value
                elif field != "_meta":
                    merged[field] = value
            return merged
        return body

    @classmethod
    def persist_agent_output(
        cls,
        project: Project,
        agent: AgentDefinition,
        run: AgentExecutionRun,
        outputs: Dict[str, Dict[str, Any]],
        *,
        prompt_version: str,
    ) -> List[str]:
        overwrite_mode = cls._resolve_persist_overwrite_mode(run, agent)
        saved = []
        for key, payload in outputs.items():
            body = dict(payload or {})
            if key == "series_outline":
                ep_from, ep_to = cls._episode_range_from_run(run)
                from apps.drama.episode_outline_store import persist_series_outline_output

                try:
                    persist_series_outline_output(
                        project,
                        body,
                        agent_id=agent.agent_id,
                        run_id=str(run.id),
                        episode_from=ep_from,
                        episode_to=ep_to,
                        run_params=dict(run.run_params or {}),
                    )
                except ValueError as exc:
                    raise AgentRuntimeError(str(exc)) from exc
                saved.append(key)
                continue
            from apps.drama.episode_artifact_store import EPISODE_BLOB_CONFIGS, persist_episode_blob_output

            blob_cfg = EPISODE_BLOB_CONFIGS.get(key)
            if blob_cfg:
                ep_from, ep_to = cls._episode_range_from_run(run)
                try:
                    persist_episode_blob_output(
                        project,
                        blob_cfg,
                        body,
                        agent_id=agent.agent_id,
                        run_id=str(run.id),
                        episode_from=ep_from,
                        episode_to=ep_to,
                        run_params=dict(run.run_params or {}),
                    )
                except ValueError as exc:
                    raise AgentRuntimeError(str(exc)) from exc
                saved.append(key)
                continue
            existing = get_artifact(project, key)
            should_merge = overwrite_mode == "merge"
            if should_merge and isinstance(existing, dict):
                body = cls._merge_artifact_body(
                    artifact_key=key,
                    incoming=body,
                    existing=existing,
                    run=run,
                )
            meta = dict(body.get("_meta") or {})
            meta.update(
                {
                    "agentId": agent.agent_id,
                    "runId": str(run.id),
                    "promptVersion": prompt_version,
                    "generatedAt": timezone.now().isoformat(),
                    "schemaVersion": (agent.output_contract or {}).get("schema_version", ""),
                    "overwriteMode": overwrite_mode,
                }
            )
            body["_meta"] = meta
            save_artifact(project, key, body)
            saved.append(key)
        return saved

    @staticmethod
    def _script_batch_bounds(params: Dict[str, Any]) -> Tuple[int | None, int | None]:
        return IndependentAgentService._resolve_episode_bounds(params)

    @staticmethod
    def _resolve_overwrite_mode(agent: AgentDefinition, params: Dict[str, Any]) -> str:
        raw = (params or {}).get("overwrite")
        if raw in ("replace", "merge", "append"):
            return str(raw)
        return IndependentAgentService._runtime_overwrite_mode(agent)

    @staticmethod
    def _runtime_overwrite_mode(agent: AgentDefinition) -> str:
        policy = agent.runtime_policy or {}
        mode = policy.get("overwrite_mode")
        if mode:
            return str(mode).lower()
        try:
            from apps.drama.skills_registry import load_agent_runtime_policies

            yaml_policy = load_agent_runtime_policies().get(agent.agent_id, {})
            mode = (yaml_policy or {}).get("overwrite_mode")
            if mode:
                return str(mode).lower()
        except Exception:  # noqa: BLE001
            pass
        return "replace"

    @staticmethod
    def _resolve_persist_overwrite_mode(run: AgentExecutionRun, agent: AgentDefinition) -> str:
        if run.overwrite_mode:
            return str(run.overwrite_mode).lower()
        return IndependentAgentService._runtime_overwrite_mode(agent)

    @classmethod
    @transaction.atomic
    def enqueue_run(cls, project: Project, user, agent_id: str, params: Dict[str, Any]) -> EnqueueRunResult:
        cls.assert_project_owner(project, user)
        locked_project = Project.objects.select_for_update().get(pk=project.pk)
        running = cls.running_run(locked_project)
        if running:
            return EnqueueRunResult(run=running, created_new_run=False, should_enqueue=False)
        agent = AgentDefinitionService.get_runnable(agent_id)
        run_params = dict(params or {})
        from apps.creation.agent_runtime.agent_billing import ensure_agent_chargeable

        ensure_agent_chargeable(user, agent_id, run_params)
        prepared = cls._prepare_prompt(locked_project, agent, run_params)
        if not prepared["within_limit"]:
            raise AgentRuntimeError(
                f"???? tokens ????: {prepared['estimated_prompt_tokens']}/{prepared['max_prompt_tokens']}"
            )
        input_payload = prepared["input_payload"]
        prompt_version = prepared["prompt_version"]
        estimated = prepared["estimated_prompt_tokens"]
        route = AgentDefinitionService.active_route(agent)
        output_keys = [str(k) for k in (agent.output_contract or {}).get("artifacts") or []]
        script_from, script_to = cls._script_batch_bounds(run_params)
        node_index = workspace_index_for_agent(agent.agent_id)
        run = AgentExecutionRunService.begin_run(
            locked_project,
            agent_id=agent.agent_id,
            agent_version=agent.version,
            prompt_version=prompt_version,
            node_index=node_index,
            script_from=script_from,
            script_to=script_to,
            input_artifact_keys=list(input_payload["artifacts"].keys()),
            output_artifact_keys=output_keys,
            input_snapshot=input_payload,
            rendered_prompt_preview=(
                prepared["system_prompt"] + "\n\n" + prepared["user_prompt"]
            )[:12000],
            estimated_prompt_tokens=estimated,
            model_name=route.llm_provider.model_name if route.llm_provider else "",
            provider_name=route.llm_provider.name if route.llm_provider else "",
            started_by="user",
            run_params=run_params,
            overwrite_mode=cls._resolve_overwrite_mode(agent, run_params),
        )
        locked_project.save(update_fields=["updated_at"])
        return EnqueueRunResult(run=run, created_new_run=True, should_enqueue=True)

    @classmethod
    def execute_run(cls, run: AgentExecutionRun) -> AgentExecutionRun:
        run.refresh_from_db()
        if run.status != AgentExecutionRun.STATUS_RUNNING:
            return run
        project = run.project
        agent = AgentDefinitionService.get_runnable(run.agent_id)
        route = AgentDefinitionService.active_route(agent)
        provider_id = str(route.llm_provider_id)
        from apps.creation.agent_runtime.agent_billing import charge_agent_run, refund_agent_run

        user = project.user
        charged = False
        try:
            charge_agent_run(user, agent.agent_id, run_id=str(run.id), params=run.run_params or {})
            charged = True
            input_payload = run.input_snapshot or cls.build_agent_input(project, agent, run.run_params or {})
            knowledge = cls.load_knowledge(agent, project)
            system_prompt, user_prompt, prompt_version = cls.render_agent_prompt(agent, input_payload, knowledge)
            max_completion = route.max_completion_tokens or route.max_tokens or (agent.runtime_policy or {}).get(
                "max_completion_tokens"
            )
            with llm_usage_scope(
                source_type=LlmUsageLog.SOURCE_AGENT,
                source_key=agent.agent_id,
                project_id=project.id,
                user_id=project.user_id,
                execution_run_id=run.id,
            ):
                raw = LlmService.chat_completion(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=route.temperature,
                    max_tokens=max_completion,
                    provider_id=provider_id,
                    json_mode=True,
                )
            from apps.creation.agent_runtime.json_self_heal import parse_json_with_self_heal

            parsed, heal_attempts = parse_json_with_self_heal(
                raw,
                agent=agent,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=route.temperature,
                max_tokens=max_completion,
                provider_id=provider_id,
            )
            outputs = cls.validate_output(agent, parsed, run_params=dict(run.run_params or {}))
            with transaction.atomic():
                saved_keys = cls.persist_agent_output(
                    project,
                    agent,
                    run,
                    outputs,
                    prompt_version=prompt_version,
                )
                usage = LlmUsageLog.objects.filter(execution_run_id=run.id).order_by("-created_at").first()
                AgentExecutionRunService.finish_run(
                    run,
                    AgentExecutionRun.STATUS_COMPLETED,
                    output_artifact_key=saved_keys[0] if saved_keys else "",
                    output_summary={"outputKeys": saved_keys, "jsonHealAttempts": heal_attempts},
                    prompt_tokens=usage.prompt_tokens if usage else None,
                    completion_tokens=usage.completion_tokens if usage else None,
                    total_tokens=usage.total_tokens if usage else None,
                    model_name=usage.model_name if usage else "",
                    provider_name=usage.provider_name if usage else "",
                )
            cls.update_project_status(project)
        except Exception as exc:  # noqa: BLE001
            if charged:
                refund_agent_run(user, agent.agent_id, run_id=str(run.id))
            AgentExecutionRunService.finish_run(run, AgentExecutionRun.STATUS_FAILED, error_message=str(exc)[:2000])
            cls.update_project_status(project)
        return run

    @staticmethod
    def _compute_progress_percent(project: Project) -> int:
        """? Drama ?????????????0-100??"""
        try:
            from apps.drama.progress_service import DramaProgressService

            if project.is_drama_workspace:
                return int(project.get_completion_rate())
        except Exception:  # noqa: BLE001
            pass
        if get_artifact(project, "episode_scripts"):
            return 100
        milestones = [
            "project_brief",
            "structure_plan",
            "character_bible",
            "series_outline",
        ]
        done = sum(1 for key in milestones if get_artifact(project, key))
        return min(99, int(done / len(milestones) * 100))

    @classmethod
    def update_project_status(cls, project: Project) -> None:
        from apps.creation.project_execution import derive_execution_status

        exec_status = derive_execution_status(project)
        progress_percent = cls._compute_progress_percent(project)

        fields = ["progress_percent", "updated_at"]
        project.progress_percent = progress_percent
        if exec_status == Project.STATUS_COMPLETED and not project.completed_at:
            project.completed_at = timezone.now()
            fields.append("completed_at")
        if exec_status == Project.STATUS_FAILED:
            latest_failed = (
                AgentExecutionRun.objects.filter(
                    project=project,
                    status=AgentExecutionRun.STATUS_FAILED,
                )
                .order_by("-finished_at")
                .first()
            )
            if latest_failed:
                project.error_message = (latest_failed.error_message or "")[:2000]
                fields.append("error_message")
        from apps.creation.services._rendering import render_progress_html

        project.rendered_progress_html = render_progress_html(project)
        fields.append("rendered_progress_html")
        project.save(update_fields=fields)
