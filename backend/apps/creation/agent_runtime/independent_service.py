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
from apps.creation.agent_runtime.episode_merge import merge_episodes_by_number
from apps.skill.llm.chat import LlmService
from apps.skill.llm.usage_log import llm_usage_scope
from apps.skill.models import LlmUsageLog

TEMPLATE_PATH_VAR_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")
EPISODE_ARTIFACT_KEYS = frozenset({"episode_scripts", "series_outline"})

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
        raise AgentRuntimeError("模型返回空内容")
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
        # 先严格解析；失败后用 strict=False 兜底，容忍真实 LLM 偶发的
        # 字符串内裸控制字符（如未转义的换行/制表符）。
        for strict in (True, False):
            try:
                parsed = json.loads(candidate, strict=strict)
            except json.JSONDecodeError as exc:
                last_error = str(exc)
                continue
            if not isinstance(parsed, dict):
                raise AgentRuntimeError("模型输出 JSON 顶层必须是对象")
            return parsed
    raise AgentRuntimeError(f"模型输出不是合法 JSON：{last_error}")


class IndependentAgentService:
    @staticmethod
    def assert_project_owner(project: Project, user) -> None:
        if project.user_id != getattr(user, "id", None) and not getattr(user, "is_staff", False):
            raise PermissionDenied("无权操作该项目")

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
            error_message="运行超时，已自动标记失败",
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
            raise AgentRuntimeError(f"缺少输入产物: {', '.join(missing)}")
        payload = {
            "project": project_payload,
            "artifacts": artifacts,
            "params": dict(params or {}),
            "required_artifacts": required_artifacts,
            "optional_artifacts": optional_artifacts,
            "agent_notes": dict(getattr(project, "agent_notes", None) or {}),
        }
        IndependentAgentService._attach_reference_materials(project, payload)
        return payload

    @staticmethod
    def _attach_reference_materials(project: Project, input_payload: Dict[str, Any]) -> None:
        """合并素材库注入内容；失败时降级，不阻断 Agent 运行。"""
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
            logger.warning("[IndependentAgent] 素材注入降级: %s", exc)

    # 单条知识未显式限长时的默认上限（字符）
    DEFAULT_KNOWLEDGE_CHARS_PER_BINDING = 4000

    # 知识注入默认策略：校验器/Schema 仅供校验层使用，不进入 prompt；
    # 参考剧本/示例属于「按相关性精选」内容，每类限量；规则/限制类不限量（由预算兜底）。
    DEFAULT_INJECTION_POLICY: Dict[str, Any] = {
        "excluded_categories": ["validator", "schema"],
        "category_caps": {"reference_script": 2, "example": 3, "knowledge": 8},
    }

    @classmethod
    def _injection_policy(cls, agent: AgentDefinition) -> Dict[str, Any]:
        """合并全局默认策略与 Agent 自定义注入策略（后台可配置）。"""
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
        """相关性匹配：维度白名单为空=通用；非空则需命中项目对应值。"""
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

        # 1. 过滤：仅保留可作为 prompt 上下文、且与当前项目相关的知识
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

        # 2. 跨源去重（同类同标题视为重复，保留排序靠前者）
        seen_signatures = set()
        per_category_count: Dict[str, int] = {}
        selected = []
        for binding in candidates:
            knowledge = binding.knowledge
            signature = (str(knowledge.category).lower(), str(knowledge.title).strip().lower())
            if signature in seen_signatures:
                continue
            # 3. 每类别 Top-N（candidates 已按 order_index/priority 排序，靠前即更高优先）
            category = str(knowledge.category)
            cap = caps.get(category)
            if cap is not None and per_category_count.get(category, 0) >= int(cap):
                continue
            seen_signatures.add(signature)
            per_category_count[category] = per_category_count.get(category, 0) + 1
            selected.append(binding)

        # 4. 组装并按总预算兜底截断
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
        # 仅校验模板自身是否残留无法解析的占位符：剥离所有合法变量后再检测，
        # 避免注入的产物内容本身含有 {{ }} 时被误判为渲染失败。
        template_skeleton = TEMPLATE_PATH_VAR_RE.sub("", template)
        if "{{" in template_skeleton or "}}" in template_skeleton:
            raise AgentRuntimeError("Prompt 模板变量渲染失败")

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
            lines.append("用户曾拒绝以下方向，请勿重复：" + "；".join(str(x) for x in rejects[:20]))
        prefs = notes.get("style_preferences") or []
        if prefs:
            lines.append("风格偏好：" + "、".join(str(x) for x in prefs[:20]))
        guidance = notes.get("character_guidance") or ""
        if guidance:
            lines.append(f"角色指导：{guidance}")
        if not lines:
            return user_prompt
        block = "\n".join(lines)
        return f"{user_prompt}\n\n【项目记忆】\n{block}"

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

    # 各产物 schema 的强制输出字段说明，防止 LLM 自由发挥字段名导致校验失败
    SCHEMA_FIELD_HINTS: Dict[str, str] = {
        "episode-scripts.v1": (
            "payload 必须包含 episodes 数组，每个元素含 episodeNumber（数字）与剧本正文字段。"
        ),
        "review-report.v1": (
            "payload 必须包含布尔字段 passed（true=通过，false=不通过），"
            "可选 issues 数组与布尔 pacingPassed；不要用 reviewResult/overallStatus 等替代字段名。"
        ),
        "script-score-report.v1": (
            "payload 必须包含 overallScore（数字）或 grade（等级字符串）。"
        ),
        "marketing-kit.v1": (
            "payload 的 titles/clipHooks/posterSlogans 若提供必须为数组。"
        ),
        "insight-report.v1": (
            "payload 至少包含 layer1_peel / layer2_mirror / layer3_invert 中的一个对象。"
        ),
        "polish-log.v1": "payload 的 suggestions 若提供必须为数组。",
    }

    @classmethod
    def _artifact_key_hint(cls, agent: AgentDefinition) -> str:
        """注入契约允许的 artifact_key 取值与产物字段规范，防止 LLM 自创结构。"""
        contract = agent.output_contract or {}
        allowed = [str(k) for k in contract.get("artifacts") or []]
        if not allowed:
            return ""
        default_key = getattr(agent, "default_output_artifact_key", "") or allowed[0]
        parts = [
            "artifact_key 字段只能取以下契约值之一，禁止自行命名或拼接主题："
            + " / ".join(allowed)
            + f"；若只输出单个产物，artifact_key 必须使用 {default_key}。"
        ]
        schema_hint = cls.SCHEMA_FIELD_HINTS.get(str(contract.get("schema_version") or ""))
        if schema_hint:
            parts.append(schema_hint)
        return " ".join(parts)

    @staticmethod
    def validate_output(agent: AgentDefinition, output: Dict[str, Any]) -> Dict[str, Any]:
        contract = agent.output_contract or {}
        allowed = [str(k) for k in contract.get("artifacts") or []]
        if not allowed:
            raise AgentRuntimeError("Agent 缺少输出契约")
        if "payload" in output and isinstance(output.get("payload"), dict):
            default_key = getattr(agent, "default_output_artifact_key", "") or allowed[0]
            artifact_key = str(output.get("artifact_key") or default_key).strip()
            if artifact_key not in allowed:
                # 真实 LLM 偶发自创 key（如用主题拼 slug），回退到契约默认 key；
                # 产物结构正确性由后续 schema 校验把关，避免整链路因命名问题失败。
                logger.warning(
                    "[Agent] %s 输出 artifact_key 非法已回退: %s -> %s",
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
            )
            return matched
        matched = {key: output[key] for key in allowed if key in output and isinstance(output[key], dict)}
        if matched:
            from .output_schema_validation import validate_matched_outputs

            validate_matched_outputs(
                matched,
                schema_version=str(contract.get("schema_version") or ""),
            )
            return matched
        normalized = {allowed[0]: output}
        from .output_schema_validation import validate_matched_outputs

        validate_matched_outputs(
            normalized,
            schema_version=str(contract.get("schema_version") or ""),
        )
        return normalized

    @staticmethod
    def _episode_range_from_run(run: AgentExecutionRun) -> Tuple[int | None, int | None]:
        params = run.run_params or {}
        ep_from = run.batch_from or params.get("episode_from") or params.get("script_from")
        ep_to = run.batch_to or params.get("episode_to") or params.get("script_to")
        try:
            from_ep = int(ep_from) if ep_from is not None else None
        except (TypeError, ValueError):
            from_ep = None
        try:
            to_ep = int(ep_to) if ep_to is not None else None
        except (TypeError, ValueError):
            to_ep = None
        return from_ep, to_ep

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
        if artifact_key in EPISODE_ARTIFACT_KEYS:
            merged_base = dict(existing or {})
            if not merged_base.get("episodes") and isinstance(body.get("episodes"), list):
                merged_base.setdefault("nodeId", body.get("nodeId", ""))
                merged_base.setdefault("projectId", str(run.project_id))
            ep_from, ep_to = cls._episode_range_from_run(run)
            merged = merge_episodes_by_number(
                merged_base,
                body.get("episodes") or [],
                episode_from=ep_from,
                episode_to=ep_to,
            )
            for field, value in body.items():
                if field not in {"episodes", "_meta"}:
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
        overwrite_mode = (run.overwrite_mode or (agent.runtime_policy or {}).get("overwrite_mode") or "replace").lower()
        saved = []
        for key, payload in outputs.items():
            body = dict(payload or {})
            if overwrite_mode == "merge":
                existing = get_artifact(project, key)
                if isinstance(existing, dict):
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
        ep_from = params.get("episode_from") or params.get("script_from")
        ep_to = params.get("episode_to") or params.get("script_to")
        try:
            from_ep = int(ep_from) if ep_from is not None else None
        except (TypeError, ValueError):
            from_ep = None
        try:
            to_ep = int(ep_to) if ep_to is not None else None
        except (TypeError, ValueError):
            to_ep = None
        return from_ep, to_ep

    @staticmethod
    def _resolve_overwrite_mode(agent: AgentDefinition, params: Dict[str, Any]) -> str:
        raw = (params or {}).get("overwrite")
        if raw in ("replace", "merge", "append"):
            return str(raw)
        return (agent.runtime_policy or {}).get("overwrite_mode", "replace")

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
                f"预计输入 tokens 超过上限: {prepared['estimated_prompt_tokens']}/{prepared['max_prompt_tokens']}"
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
        locked_project.fusion_status = Project.FUSION_WRITING
        locked_project.save(update_fields=["fusion_status", "updated_at"])
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
            outputs = cls.validate_output(agent, parsed)
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
    def _derive_fusion_status(project: Project) -> str:
        """根据产物与运行态推导 fusion_status。"""
        from apps.creation.project_execution import derive_execution_status

        status = derive_execution_status(project)
        if status == Project.STATUS_FAILED:
            return Project.FUSION_BLOCKED
        if get_artifact(project, "episode_scripts"):
            return Project.FUSION_READY
        if status == Project.STATUS_RUNNING:
            latest = (
                AgentExecutionRun.objects.filter(project=project)
                .order_by("-started_at")
                .values_list("agent_id", flat=True)
                .first()
            )
            if latest == "score":
                return Project.FUSION_SCORING
            if latest == "review":
                return Project.FUSION_REVIEWING
            if get_artifact(project, "series_outline"):
                return Project.FUSION_WRITING
            return Project.FUSION_PLANNING
        if get_artifact(project, "series_outline") or get_artifact(project, "structure_plan"):
            return Project.FUSION_PLANNING
        return Project.FUSION_DRAFT

    @staticmethod
    def _compute_progress_percent(project: Project) -> int:
        """按核心产物完成度估算进度（0-100）。"""
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
        fusion_status = cls._derive_fusion_status(project)
        progress_percent = cls._compute_progress_percent(project)
        fields = ["fusion_status", "progress_percent", "updated_at"]
        project.fusion_status = fusion_status
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
