# -*- coding: utf-8 -*-
"""参考创作：各阶段 verify-creation CLI 复核（world / characters / outline）。"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from django.conf import settings

from ..artifact_renderer import episode_to_gate_markdown, outline_to_gate_markdown
from ..artifact_service import get_artifact, save_artifact

if TYPE_CHECKING:
    from ..fusion.fusion_orchestrator import FusionOrchestrator

logger = logging.getLogger(__name__)

_ARTIFACT_FILE = {
    "world": "verify_world_setting.md",
    "characters": "verify_characters_setting.md",
    "outline": "verify_outline_setting.md",
    "script": "verify_script_combined.md",
}


def _work_dir(project) -> Path:
    return Path(getattr(settings, "CREATION_FUSION_WORK_DIR", "/tmp/scriptforge_fusion")) / str(project.id)


def resolve_reference_stub_path(project) -> Optional[Path]:
    entry = (project.creation_entry or "from-scratch").strip()
    if entry != "from-reference":
        return None
    adapt = get_artifact(project, "adaptation_meta") or {}
    ref = (adapt.get("referenceWork") or project.reference_work or "").strip()
    if not ref:
        return None
    ref_path = _work_dir(project) / "reference_stub.md"
    if not ref_path.is_file():
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        ref_path.write_text(f"# 参考作品\n\n{ref}\n", encoding="utf-8")
    return ref_path


def structure_plan_to_verify_markdown(payload: dict) -> str:
    parts = ["# 世界观与六阶段结构"]
    title = (payload.get("workingTitle") or payload.get("suggestedTitle") or "").strip()
    if title:
        parts.append(f"剧名：{title}")
    wv = payload.get("worldview") if isinstance(payload.get("worldview"), dict) else {}
    if wv:
        for key in ("era", "setting", "settingSummary", "coreConflict", "tone"):
            val = (wv.get(key) or "").strip()
            if val:
                parts.append(f"{key}：{val}")
        for rule in wv.get("rootRules") or []:
            if str(rule).strip():
                parts.append(f"规则：{rule}")
        for noun in wv.get("coreNouns") or []:
            if isinstance(noun, dict):
                term = (noun.get("term") or "").strip()
                desc = (noun.get("description") or "").strip()
                if term:
                    parts.append(f"核心名词 {term}：{desc or term}")
    arc = payload.get("coreStoryArc") if isinstance(payload.get("coreStoryArc"), dict) else {}
    for key in ("openingSetup", "escalation", "climax", "resolution"):
        val = (arc.get(key) or "").strip()
        if val:
            parts.append(f"{key}：{val}")
    for stage in payload.get("sixStagePlan") or []:
        if not isinstance(stage, dict):
            continue
        label = (stage.get("label") or stage.get("key") or "").strip()
        task = (stage.get("coreTask") or "").strip()
        if label or task:
            parts.append(f"阶段 {label}：{task}")
    return "\n".join(parts).strip() or "# 结构设定\n（空）"


def character_bible_to_verify_markdown(payload: dict) -> str:
    parts = ["# 人物圣经"]
    for char in payload.get("characters") or []:
        if not isinstance(char, dict):
            continue
        name = (char.get("name") or char.get("id") or "角色").strip()
        role = (char.get("roleType") or char.get("role") or "").strip()
        lines = [f"## {name}" + (f"（{role}）" if role else "")]
        for key in (
            "oneLineSummary",
            "summary",
            "background",
            "backstory",
            "coreMotivation",
            "surfacePersonality",
            "realPersonality",
            "secret",
        ):
            val = (char.get(key) or "").strip()
            if val:
                lines.append(val)
        parts.append("\n".join(lines))
    rel = (payload.get("relationshipSummary") or "").strip()
    if rel:
        parts.append(f"## 关系网\n{rel}")
    return "\n\n".join(parts).strip() or "# 人物设定\n（空）"


def episode_scripts_to_verify_markdown(payload: dict) -> str:
    from ..fusion.fusion_pipeline import scripts_result_to_markdown

    md = scripts_result_to_markdown(payload)
    if md.strip():
        return md
    parts = ["# 剧本正文"]
    for ep in payload.get("episodes") or []:
        if isinstance(ep, dict):
            parts.append(episode_to_gate_markdown(ep))
    return "\n\n".join(parts).strip() or "# 剧本正文\n（空）"


def artifact_to_verify_markdown(artifact: str, payload: dict) -> str:
    if artifact == "world":
        return structure_plan_to_verify_markdown(payload)
    if artifact == "characters":
        return character_bible_to_verify_markdown(payload)
    if artifact == "outline":
        return outline_to_gate_markdown(payload)
    if artifact == "script":
        return episode_scripts_to_verify_markdown(payload)
    raise ValueError(f"不支持的 verify artifact: {artifact}")


def _persist_verify_report(project, artifact: str, cli: Dict[str, Any]) -> Dict[str, Any]:
    parsed = cli.get("json") if isinstance(cli.get("json"), dict) else {}
    report = {
        "artifact": artifact,
        "passed": bool(parsed.get("passed", cli.get("ok"))),
        "ok": cli.get("ok"),
        "exitCode": cli.get("exit_code"),
    }
    if parsed.get("issues"):
        report["issues"] = parsed.get("issues")[:8]
    if parsed.get("similarity"):
        report["similarity"] = parsed.get("similarity")
    meta = dict(get_artifact(project, "adaptation_meta") or {})
    reports = dict(meta.get("verifyReports") or {})
    reports[artifact] = report
    meta["verifyReports"] = reports
    save_artifact(project, "adaptation_meta", meta)
    return report


def run_reference_verify_if_needed(
    orch: FusionOrchestrator,
    *,
    artifact: str,
    payload: dict,
) -> Optional[Dict[str, Any]]:
    """from-reference 项目在设定阶段写入后跑 verify-creation（非 strict）。"""
    project = orch.project
    ref_path = resolve_reference_stub_path(project)
    if not ref_path:
        return None
    from .sub_skill_runner import cli_verify_creation_setting

    work_dir = _work_dir(project)
    work_dir.mkdir(parents=True, exist_ok=True)
    input_name = _ARTIFACT_FILE.get(artifact) or f"verify_{artifact}.md"
    input_path = work_dir / input_name
    input_path.write_text(artifact_to_verify_markdown(artifact, payload), encoding="utf-8")
    entry = (project.creation_entry or "from-reference").strip()
    try:
        cli = cli_verify_creation_setting(
            orch.runner,
            input_path,
            ref_path,
            artifact=artifact,
            entry=entry,
            strict=False,
        )
        report = _persist_verify_report(project, artifact, cli)
        if not report.get("passed"):
            logger.warning(
                "[VerifyCreation] artifact=%s project=%s issues=%s",
                artifact,
                project.id,
                (cli.get("json") or {}).get("issues", [])[:3],
            )
        return report
    except Exception as exc:  # noqa: BLE001
        logger.warning("[VerifyCreation] artifact=%s skipped: %s", artifact, exc)
        report = {"artifact": artifact, "skipped": True, "error": str(exc)[:200]}
        meta = dict(get_artifact(project, "adaptation_meta") or {})
        reports = dict(meta.get("verifyReports") or {})
        reports[artifact] = report
        meta["verifyReports"] = reports
        save_artifact(project, "adaptation_meta", meta)
        return report


def run_script_originality_gate(
    orch: FusionOrchestrator,
    payload: dict,
) -> Optional[Dict[str, Any]]:
    """ScriptAgent originality-gate：from-reference 全剧剧本 verify-creation（combined）。"""
    project = orch.project
    ref_path = resolve_reference_stub_path(project)
    if not ref_path:
        return None
    from .sub_skill_runner import _cli_path, run_cli_sub_skill

    work_dir = _work_dir(project)
    work_dir.mkdir(parents=True, exist_ok=True)
    input_path = work_dir / _ARTIFACT_FILE["script"]
    input_path.write_text(episode_scripts_to_verify_markdown(payload), encoding="utf-8")
    entry = (project.creation_entry or "from-reference").strip()
    args = [
        f"--input={_cli_path(input_path)}",
        f"--reference={_cli_path(ref_path)}",
        f"--entry={entry}",
        "--artifact=combined",
        "--json",
        "--no-strict",
    ]
    try:
        cli = run_cli_sub_skill(
            orch.runner,
            "script",
            "originality-gate",
            args,
            timeout=120,
        )
        report = _persist_verify_report(project, "script", cli)
        if not report.get("passed"):
            logger.warning(
                "[OriginalityGate] project=%s issues=%s",
                project.id,
                (cli.get("json") or {}).get("issues", [])[:3],
            )
        return report
    except Exception as exc:  # noqa: BLE001
        logger.warning("[OriginalityGate] skipped project=%s: %s", project.id, exc)
        report = {"artifact": "script", "skipped": True, "error": str(exc)[:200]}
        meta = dict(get_artifact(project, "adaptation_meta") or {})
        reports = dict(meta.get("verifyReports") or {})
        reports["script"] = report
        meta["verifyReports"] = reports
        save_artifact(project, "adaptation_meta", meta)
        return report
