# -*- coding: utf-8 -*-
"""按 registry sub_skill 类型执行辅助步骤（retrieval / trace / CLI）。"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

from django.utils import timezone

from ..artifact_service import get_artifact, save_artifact
from ..models import Project
from apps.agent.runtime import get_agent

if TYPE_CHECKING:
    from apps.workflow.fusion.cli_runner import FusionCliRunner
    from apps.workflow.fusion.config_loader import FusionSkillConfig

logger = logging.getLogger(__name__)

_NAMED_SCRIPT_FILES = {
    "verify-creation": ("sub-brief", "verify-creation.js"),
}

TRACE_ARTIFACT_KEY = "agent_execution_traces"


def reference_files_for_agent(agent_id: str) -> List[str]:
    agent = get_agent(agent_id) or {}
    files: List[str] = []
    for skill in agent.get("sub_skills") or []:
        if not isinstance(skill, dict):
            continue
        for ref in skill.get("references") or []:
            if isinstance(ref, str) and ref not in files:
                files.append(ref)
    return files


def inject_knowledge_upstream(
    agent_id: str,
    upstream: Dict[str, Any],
    project: Project,
) -> Dict[str, Any]:
    """reference-injector：为 LLM upstream 注入 KnowledgeAgent 检索块。"""
    from .knowledge import retrieve_references

    out = dict(upstream)
    refs = reference_files_for_agent(agent_id)
    out["knowledgeReferences"] = retrieve_references(
        theme=(project.theme or "").strip(),
        tags=refs[:5] if refs else None,
    )
    return out


def mark_executed(executed: List[str], skill_id: str) -> None:
    if skill_id and skill_id not in executed:
        executed.append(skill_id)


def build_execution_trace(
    agent_id: str,
    executed: List[str],
    *,
    trace_entries: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, str]]:
    """将 executed_sub_skills 与 registry 定义对齐，供 API/日志展示。"""
    if trace_entries:
        return list(trace_entries)

    agent = get_agent(agent_id) or {}
    defined = {s.get("id"): s for s in (agent.get("sub_skills") or []) if isinstance(s, dict)}
    trace: List[Dict[str, str]] = []
    for skill_id in executed:
        meta = defined.get(skill_id) or {}
        trace.append(
            {
                "id": skill_id,
                "type": str(meta.get("type") or ""),
                "cli": str(meta.get("cli") or ""),
                "script": str(meta.get("script") or ""),
                "status": "executed",
                "message": "",
            }
        )
    for skill_id, meta in defined.items():
        if skill_id not in executed:
            trace.append(
                {
                    "id": skill_id,
                    "type": str(meta.get("type") or ""),
                    "cli": str(meta.get("cli") or ""),
                    "script": str(meta.get("script") or ""),
                    "status": "skipped",
                    "message": "",
                }
            )
    return trace


def agent_execution_meta(
    agent_id: str,
    executed: List[str],
    *,
    node_index: int,
    trace_entries: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Agent 运行 meta：sub_skills 定义 + 执行轨迹。"""
    agent_def = get_agent(agent_id) or {}
    trace = build_execution_trace(agent_id, executed, trace_entries=trace_entries)
    return {
        "node_index": node_index,
        "sub_skills": [
            {
                "id": str(s.get("id") or ""),
                "type": str(s.get("type") or ""),
                "cli": str(s.get("cli") or ""),
            }
            for s in (agent_def.get("sub_skills") or [])
            if isinstance(s, dict)
        ],
        "executed_sub_skills": list(executed),
        "execution_trace": trace,
        "output_artifacts": agent_def.get("outputs") or [],
    }


def _get_rule_version_snapshot() -> Dict[str, str]:
    """
    读取 skill-rules/ 各文件的 version 字段，记录生成时使用的规则版本。
    供 evolve_audit 精确定位"是哪个规则版本导致了低分"。
    """
    try:
        from apps.skill.skills.loader import get_skill_rule_loader
        loader = get_skill_rule_loader()
        snapshot = {}
        for tier_name, getter in [
            ("tier1", loader.get_tier1),
            ("tier2", loader.get_tier2),
            ("tier3", loader.get_tier3),
            ("tier4", loader.get_tier4),
        ]:
            data = getter()
            if data:
                meta = data.get("_meta") or {}
                snapshot[tier_name] = meta.get("version", "unknown")
        return snapshot
    except Exception:  # noqa: BLE001
        return {}


def _get_active_rule_config_ids(project: "Project") -> Dict[str, str]:
    """
    收集本次生成实际使用的 DB SkillRuleConfig 记录 ID（调用链追踪）。
    返回格式：{ "tier2_genre": "<uuid>", "tier3_node_<id>": "<uuid>", ... }
    """
    try:
        from apps.skill.skills.loader import get_skill_rule_loader
        from apps.creation.artifact_service import get_artifact

        loader = get_skill_rule_loader()
        brief = get_artifact(project, "project_brief") or {}
        genre = (brief.get("theme") or "").strip().lower() or None

        result: Dict[str, str] = {}
        if genre:
            _, rid = loader._db_active_content(2, "genre", genre, "genre_full")
            if rid:
                result["tier2_genre"] = rid

        # 收集所有节点的 tier3 active config
        for node_id in ["node-2-structure", "node-3-character", "node-4-outline", "node-5-script"]:
            _, rid = loader._db_active_content(3, "node", node_id, "pipeline_node_full")
            if rid:
                result[f"tier3_{node_id}"] = rid
        return result
    except Exception:  # noqa: BLE001
        return {}


def persist_execution_trace(
    project: Project,
    node_index: int,
    agent_id: str,
    executed: List[str],
    *,
    trace_entries: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """持久化节点级 sub-skill 执行轨迹（artifact: agent_execution_traces）。"""
    trace = build_execution_trace(agent_id, executed, trace_entries=trace_entries)
    store = dict(get_artifact(project, TRACE_ARTIFACT_KEY) or {})
    store[str(node_index)] = {
        "agent_id": agent_id,
        "node_index": node_index,
        "executed_sub_skills": list(executed),
        "execution_trace": trace,
        "updated_at": timezone.now().isoformat(),
        "skill_rule_versions": _get_rule_version_snapshot(),
        "active_rule_config_ids": _get_active_rule_config_ids(project),
    }
    save_artifact(project, TRACE_ARTIFACT_KEY, store)
    return store[str(node_index)]


def get_execution_trace_for_node(project: Project, node_index: int) -> List[Dict[str, str]]:
    store = get_artifact(project, TRACE_ARTIFACT_KEY) or {}
    entry = store.get(str(node_index)) or store.get(int(node_index)) or {}
    return list(entry.get("execution_trace") or [])


def sub_skill_meta(agent_id: str, skill_id: str) -> Optional[Dict[str, Any]]:
    agent = get_agent(agent_id) or {}
    for skill in agent.get("sub_skills") or []:
        if isinstance(skill, dict) and skill.get("id") == skill_id:
            return skill
    return None


def resolve_registry_script_path(config: FusionSkillConfig, meta: Dict[str, Any]) -> Path:
    """解析 registry sub_skill 的 script/runtime 字段为绝对脚本路径。"""
    runtime = str(meta.get("runtime") or "").strip().replace("\\", "/")
    script_name = str(meta.get("script") or "").strip()
    if runtime:
        rel = runtime[len("runtime/") :] if runtime.startswith("runtime/") else runtime
        path = config.runtime_dir / rel
    elif script_name in _NAMED_SCRIPT_FILES:
        folder, filename = _NAMED_SCRIPT_FILES[script_name]
        path = config.runtime_dir / folder / filename
    else:
        raise ValueError(f"sub-skill 无法解析脚本路径: script={script_name!r}")
    if not path.is_file():
        raise FileNotFoundError(f"子技能脚本不存在：{path}")
    return path


def run_cli_sub_skill(
    runner: FusionCliRunner,
    agent_id: str,
    skill_id: str,
    args: List[str],
    *,
    cwd: Optional[Any] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """按 registry 定义执行 type=cli 的 sub-skill（逐步执行器入口）。"""
    meta = sub_skill_meta(agent_id, skill_id)
    if not meta:
        raise ValueError(f"未找到 sub-skill: {agent_id}/{skill_id}")
    skill_type = str(meta.get("type") or "")
    if "cli" not in skill_type:
        raise ValueError(f"sub-skill 非 CLI 类型: {skill_id} ({skill_type})")
    cli_name = str(meta.get("cli") or "").strip()
    script_name = str(meta.get("script") or "").strip()
    runtime_rel = str(meta.get("runtime") or "").strip()
    if cli_name:
        logger.info("[SubSkill] CLI agent=%s skill=%s cli=%s", agent_id, skill_id, cli_name)
        return runner.run(cli_name, args, cwd=cwd, timeout=timeout)
    if script_name or runtime_rel:
        script_path = resolve_registry_script_path(runner.config, meta)
        logger.info(
            "[SubSkill] script agent=%s skill=%s path=%s",
            agent_id,
            skill_id,
            script_path.name,
        )
        return runner.run_file(
            script_path,
            args,
            label=skill_id,
            cwd=cwd,
            timeout=timeout,
        )
    raise ValueError(f"sub-skill 缺少 cli/script 字段: {skill_id}")


def _cli_path(path: Union[str, Path]) -> str:
    return str(Path(path).resolve())


def unwrap_fusion_cli_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """FusionCliRunner 外层 {ok, json, exit_code}；子技能业务字段在 json 内。"""
    inner = result.get("json")
    if isinstance(inner, dict):
        payload = dict(inner)
        if "passed" not in payload and "ok" in result:
            payload.setdefault("passed", bool(result["ok"]))
        return payload
    return result


def cli_verify_creation_brief(
    runner: FusionCliRunner,
    reference_path: Union[str, Path],
    *,
    entry: str = "from-reference",
    strict: bool = False,
    timeout: int = 60,
) -> Dict[str, Any]:
    args = [
        f"--reference={_cli_path(reference_path)}",
        f"--entry={entry}",
        "--brief-only",
        "--json",
    ]
    if not strict:
        args.append("--no-strict")
    return run_cli_sub_skill(runner, "adapt", "verify-creation", args, timeout=timeout)


def cli_verify_creation_setting(
    runner: FusionCliRunner,
    input_path: Union[str, Path],
    reference_path: Union[str, Path],
    *,
    artifact: str = "combined",
    entry: str = "from-reference",
    strict: bool = False,
    timeout: int = 90,
) -> Dict[str, Any]:
    args = [
        f"--input={_cli_path(input_path)}",
        f"--reference={_cli_path(reference_path)}",
        f"--entry={entry}",
        f"--artifact={artifact}",
        "--json",
    ]
    if not strict:
        args.append("--no-strict")
    return run_cli_sub_skill(runner, "adapt", "verify-creation", args, timeout=timeout)


def cli_brief_enrich(
    runner: FusionCliRunner,
    input_path: Union[str, Path],
    *,
    output_path: Optional[Union[str, Path]] = None,
    strict: bool = False,
) -> Dict[str, Any]:
    args = [f"--input={_cli_path(input_path)}", "--json"]
    if output_path:
        args.append(f"--output={_cli_path(output_path)}")
    if strict:
        args.append("--strict")
    return run_cli_sub_skill(runner, "brief", "brief-enricher", args)


def cli_world_validate(
    runner: FusionCliRunner,
    input_path: Union[str, Path],
    *,
    strict: bool = False,
) -> Dict[str, Any]:
    args = [f"--input={_cli_path(input_path)}", "--json"]
    if not strict:
        args.append("--no-strict")
    return run_cli_sub_skill(runner, "world", "world-validator", args)


def cli_plan_validate(
    runner: FusionCliRunner,
    input_path: Union[str, Path],
    *,
    episodes: Optional[int] = None,
    strict: bool = False,
) -> Dict[str, Any]:
    args = [f"--input={_cli_path(input_path)}", "--json"]
    if episodes:
        args.append(f"--episodes={episodes}")
    if not strict:
        args.append("--no-strict")
    return run_cli_sub_skill(runner, "outline", "plan-validator", args)


def cli_episode_gate(
    runner: FusionCliRunner,
    script_path: Union[str, Path],
    *,
    episode: int,
    outline_path: Optional[Union[str, Path]] = None,
    strict: bool = False,
    timeout: int = 120,
) -> Dict[str, Any]:
    args = [
        f"--input={_cli_path(script_path)}",
        f"--episode={episode}",
        "--json",
    ]
    if outline_path and Path(outline_path).is_file():
        args.append(f"--outline={_cli_path(outline_path)}")
    if not strict:
        args.append("--no-strict")
    return run_cli_sub_skill(
        runner,
        "script",
        "episode-gate",
        args,
        timeout=timeout,
    )


def cli_gate_full(
    runner: FusionCliRunner,
    script_path: Union[str, Path],
    *,
    episodes: Optional[int] = None,
    compliance_tier: str = "domestic",
    strict: bool = False,
    timeout: int = 180,
) -> Dict[str, Any]:
    args = [f"--input={_cli_path(script_path)}", "--full", "--json"]
    if episodes:
        args.append(f"--episodes={episodes}")
    if compliance_tier and compliance_tier != "domestic":
        args.append(f"--compliance-tier={compliance_tier}")
    if not strict:
        args.append("--no-strict")
    return run_cli_sub_skill(runner, "review", "gate-full", args, timeout=timeout)


def cli_compliance_check(
    runner: FusionCliRunner,
    script_path: Union[str, Path],
    *,
    strict: bool = False,
    timeout: int = 120,
) -> Dict[str, Any]:
    args = [f"--input={_cli_path(script_path)}", "--json"]
    if not strict:
        args.append("--no-strict")
    return run_cli_sub_skill(runner, "review", "compliance-check", args, timeout=timeout)


def cli_score_deep(
    runner: FusionCliRunner,
    script_path: Union[str, Path],
    *,
    bridge: bool = True,
    output_path: Optional[Union[str, Path]] = None,
    strict: bool = False,
    timeout: int = 180,
) -> Dict[str, Any]:
    args = [
        f"--input={_cli_path(script_path)}",
        "--mode=deep",
        "--format=json",
    ]
    if bridge:
        args.append("--bridge")
    if output_path:
        args.append(f"--output={_cli_path(output_path)}")
    if not strict:
        args.append("--no-strict")
    return run_cli_sub_skill(runner, "score", "score-deep", args, timeout=timeout)


def cli_score_quick(
    runner: FusionCliRunner,
    script_path: Union[str, Path],
    *,
    bridge: bool = True,
    output_path: Optional[Union[str, Path]] = None,
    brief_path: Optional[Union[str, Path]] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    args = [
        f"--input={_cli_path(script_path)}",
        "--mode=quick",
        "--format=json",
        "--no-strict",
    ]
    if bridge:
        args.append("--bridge")
    if output_path:
        args.append(f"--output={_cli_path(output_path)}")
    if brief_path:
        args.append(f"--brief={_cli_path(brief_path)}")
    return run_cli_sub_skill(runner, "review", "score-quick", args, timeout=timeout)


def cli_marketing_kit(
    runner: FusionCliRunner,
    *,
    title: str,
    logline: str,
    theme: str,
    episodes: int,
    timeout: int = 60,
) -> Dict[str, Any]:
    args = [
        f"--title={title}",
        f"--logline={logline}",
        f"--theme={theme}",
        f"--episodes={episodes}",
        "--json",
    ]
    return run_cli_sub_skill(runner, "marketing", "marketing-kit", args, timeout=timeout)


def cli_pipeline_writeback(
    runner: FusionCliRunner,
    analysis_path: Union[str, Path],
    *,
    dry_run: bool = True,
    timeout: int = 90,
) -> Dict[str, Any]:
    args = [f"--analysis={_cli_path(analysis_path)}", "--json"]
    if not dry_run:
        args.append("--apply")
    return run_cli_sub_skill(runner, "knowledge", "pipeline-writeback", args, timeout=timeout)


def persist_agent_execution_trace(
    project: Project,
    agent_id: str,
    executed: List[str],
) -> Dict[str, Any]:
    """后处理 Agent 轨迹（按 agent_id 存储）。"""
    trace = build_execution_trace(agent_id, executed)
    store = dict(get_artifact(project, TRACE_ARTIFACT_KEY) or {})
    store[agent_id] = {
        "agent_id": agent_id,
        "executed_sub_skills": list(executed),
        "execution_trace": trace,
        "updated_at": timezone.now().isoformat(),
    }
    save_artifact(project, TRACE_ARTIFACT_KEY, store)
    return store[agent_id]
