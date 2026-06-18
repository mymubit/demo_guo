from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List, Tuple

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.models import AgentDefinition, AgentKnowledgeBinding
from apps.creation.artifact_service import get_artifact, save_artifact
from apps.creation.models import AgentExecutionRun, Project
from apps.creation.monitoring.execution_run_service import AgentExecutionRunService
from apps.creation.orchestration.agent_common import merge_episodes_by_number
from apps.skill.llm.chat import LlmService
from apps.skill.llm.usage_log import llm_usage_scope
from apps.skill.models import LlmUsageLog

TEMPLATE_PATH_VAR_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")
EPISODE_ARTIFACT_KEYS = frozenset({"episode_scripts", "series_outline"})


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
        try:
            parsed = json.loads(candidate)
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
        timeout_at = timezone.now() - timedelta(hours=2)
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
        return {
            "project": project_payload,
            "artifacts": artifacts,
            "params": dict(params or {}),
            "required_artifacts": required_artifacts,
            "optional_artifacts": optional_artifacts,
        }

    @staticmethod
    def load_knowledge(agent: AgentDefinition) -> List[Dict[str, Any]]:
        rows = []
        for binding in AgentDefinitionService.enabled_bindings(agent):
            if binding.binding_type == AgentKnowledgeBinding.BindingType.VALIDATOR:
                continue
            knowledge = binding.knowledge
            text = knowledge.content_text or ""
            if binding.max_chars:
                text = text[: int(binding.max_chars)]
            rows.append(
                {
                    "knowledge_id": knowledge.knowledge_id,
                    "title": knowledge.title,
                    "category": knowledge.category,
                    "inject_position": binding.inject_position,
                    "content_text": text,
                    "content_json": knowledge.content_json or {},
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

        def _replace_path_var(match: re.Match[str]) -> str:
            path = match.group(1).strip()
            if path in roots:
                return cls._format_template_value(roots[path])
            return cls._format_template_value(cls._resolve_template_path(roots, path))

        rendered = TEMPLATE_PATH_VAR_RE.sub(_replace_path_var, template)
        if "{{" in rendered or "}}" in rendered:
            raise AgentRuntimeError("Prompt 模板变量渲染失败")
        return rendered

    @classmethod
    def _prepare_prompt(
        cls,
        project: Project,
        agent: AgentDefinition,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        input_payload = cls.build_agent_input(project, agent, params)
        knowledge = cls.load_knowledge(agent)
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
        return {
            "agent_id": agent.agent_id,
            "estimated_prompt_tokens": prepared["estimated_prompt_tokens"],
            "max_prompt_tokens": prepared["max_prompt_tokens"],
            "within_limit": prepared["within_limit"],
            "input_artifact_keys": prepared["input_artifact_keys"],
            "input_char_summary": prepared["input_char_summary"],
            "prompt_version": prepared["prompt_version"],
        }

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
            prompt.constraints_prompt,
        ]
        suffix = "\n\n".join(s for s in sections if s)
        if suffix:
            user_prompt = f"{user_prompt}\n\n{suffix}"
        return prompt.system_prompt, user_prompt, prompt.version

    @staticmethod
    def validate_output(agent: AgentDefinition, output: Dict[str, Any]) -> Dict[str, Any]:
        contract = agent.output_contract or {}
        allowed = [str(k) for k in contract.get("artifacts") or []]
        if not allowed:
            raise AgentRuntimeError("Agent 缺少输出契约")
        if "payload" in output and isinstance(output.get("payload"), dict):
            artifact_key = str(output.get("artifact_key") or allowed[0])
            if artifact_key not in allowed:
                raise AgentRuntimeError(f"输出 artifact_key 不在契约内: {artifact_key}")
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
        run = AgentExecutionRunService.begin_run(
            locked_project,
            agent_id=agent.agent_id,
            agent_version=agent.version,
            prompt_version=prompt_version,
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
            overwrite_mode=(agent.runtime_policy or {}).get("overwrite_mode", "replace"),
        )
        locked_project.status = Project.STATUS_RUNNING
        locked_project.save(update_fields=["status", "updated_at"])
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
        system_prompt = ""
        user_prompt = ""
        try:
            input_payload = run.input_snapshot or cls.build_agent_input(project, agent, run.run_params or {})
            knowledge = cls.load_knowledge(agent)
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
                raw = LlmService._chat_completion(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=route.temperature,
                    max_tokens=max_completion,
                    provider_id=provider_id,
                    json_mode=True,
                )
            parsed = extract_json_object(raw)
            outputs = cls.validate_output(agent, parsed)
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
                output_summary={"outputKeys": saved_keys},
                prompt_tokens=usage.prompt_tokens if usage else None,
                completion_tokens=usage.completion_tokens if usage else None,
                total_tokens=usage.total_tokens if usage else None,
                model_name=usage.model_name if usage else "",
                provider_name=usage.provider_name if usage else "",
            )
            cls.update_project_status(project)
        except Exception as exc:  # noqa: BLE001
            AgentExecutionRunService.finish_run(run, AgentExecutionRun.STATUS_FAILED, error_message=str(exc)[:2000])
            cls.update_project_status(project)
        return run

    @staticmethod
    def update_project_status(project: Project) -> None:
        if AgentExecutionRun.objects.filter(project=project, status=AgentExecutionRun.STATUS_RUNNING).exists():
            status = Project.STATUS_RUNNING
        elif get_artifact(project, "episode_scripts"):
            status = Project.STATUS_COMPLETED
        else:
            status = Project.STATUS_PENDING
        if project.status != status:
            project.status = status
            project.save(update_fields=["status", "updated_at"])
