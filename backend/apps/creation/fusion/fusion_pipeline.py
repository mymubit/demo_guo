# -*- coding: utf-8 -*-
"""
网站侧融合后处理：LLM 流水线产出 → 写临时剧本 → 调 demo4book sub-gate/sub-score/sub-compliance。

技能为 SSOT；本模块不复制检测规则。
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.utils import timezone

from apps.workflow.fusion import FusionCliRunner, evaluate_project_readiness, get_fusion_config

from ..orchestration.sub_skill_runner import (
    cli_compliance_check,
    cli_gate_full,
    cli_score_deep,
    mark_executed,
)
from ..artifact_service import save_artifact, save_artifacts_batch
from ..models import CreationNode, Project
from ..schema_mappers import map_pipeline_result_to_artifacts
from ..services import refresh_project_progress

logger = logging.getLogger(__name__)


def _fusion_disabled_response() -> Dict[str, Any]:
    return {
        "skipped": False,
        "ok": False,
        "reason": "FUSION_SKILL_ENABLED=false",
        "fusion_status": Project.FUSION_BLOCKED,
        "error": "融合质检未启用，项目无法放行",
    }


def _episode_gates_from_project(project: Project, pipeline_result: dict) -> dict:
    from ..artifact_service import get_artifact
    from .episode_gate import summarize_episode_gates

    scripts_art = get_artifact(project, "episode_scripts") or pipeline_result.get("artifacts", {}).get(
        "episode_scripts"
    )
    if scripts_art:
        return summarize_episode_gates(scripts_art)
    scripts = pipeline_result.get("scripts") or {}
    if scripts.get("episodes"):
        return summarize_episode_gates({"episodes": scripts.get("episodes")})
    return {"total": 0, "passed": 0, "failed": 0, "passRate": 0, "failedEpisodes": []}


def scripts_result_to_markdown(scripts_data: dict) -> str:
    """将 node5 scripts 结果转为 gate/score 可读的合并剧本文本。"""
    parts = []
    for ep in scripts_data.get("episodes") or []:
        text = str(ep.get("full_script_text") or "")
        if not text.strip():
            continue
        text = re.sub(r"^##\s*第", "# 第", text, flags=re.MULTILINE)
        if not re.match(r"^#\s*第\d+集", text):
            num = ep.get("episode", len(parts) + 1)
            text = f"# 第{num}集\n\n{text}"
        parts.append(text.strip())
    return "\n\n".join(parts)


def _mark_node(
    project: Project,
    fusion_node_id: str,
    *,
    summary: str,
    status: str = CreationNode.STATUS_COMPLETED,
    error: str = "",
) -> None:
    from apps.workflow.fusion import FusionNodeRegistry

    registry = FusionNodeRegistry()
    target_index = None
    for n in registry.main_chain_nodes():
        if n["fusion_node_id"] == fusion_node_id:
            target_index = n["index"]
            break
    if target_index is None:
        return
    CreationNode.objects.filter(project=project, node_index=target_index).update(
        status=status,
        summary_text=summary[:500],
        completed_at=timezone.now() if status == CreationNode.STATUS_COMPLETED else None,
        error_message=error[:500],
    )


def _prepare_script_markdown(
    project: Project, pipeline_result: dict
) -> Tuple[Path, Path, str]:
    """写入临时剧本文本，返回 (script_path, score_out, markdown)。"""
    scripts = pipeline_result.get("scripts") or {}
    markdown = scripts_result_to_markdown(scripts)
    if not markdown.strip():
        raise ValueError("无剧本文本可供融合检测")

    work_dir = Path(getattr(settings, "CREATION_FUSION_WORK_DIR", "/tmp/scriptforge_fusion"))
    work_dir.mkdir(parents=True, exist_ok=True)
    script_path = work_dir / f"{project.id.hex}_script.md"
    score_out = work_dir / f"{project.id.hex}_score.json"
    script_path.write_text(markdown, encoding="utf-8")

    if not pipeline_result.get("artifacts"):
        schema_artifacts = map_pipeline_result_to_artifacts(pipeline_result, project)
        save_artifacts_batch(project, schema_artifacts)

    return script_path, score_out, markdown


def run_fusion_review_for_project(
    project: Project, pipeline_result: dict
) -> Dict[str, Any]:
    """节点6：gate + compliance（分步模式可单独执行）。"""
    if not getattr(settings, "FUSION_SKILL_ENABLED", True):
        return _fusion_disabled_response()

    cfg = get_fusion_config()
    runner = FusionCliRunner(cfg)
    script_path, _, markdown = _prepare_script_markdown(project, pipeline_result)

    from .compliance_fuse import merge_fuse_with_cli, run_compliance_fuse_scan

    fuse_rule = run_compliance_fuse_scan(markdown)

    from .compliance_content import run_compliance_content_scan

    content_scan = run_compliance_content_scan(markdown)

    project.fusion_status = Project.FUSION_REVIEWING
    project.skill_version = cfg.version
    project.save(update_fields=["fusion_status", "skill_version", "updated_at"])
    _mark_node(
        project, "node-6-review", summary="融合质检进行中…", status=CreationNode.STATUS_RUNNING
    )
    project.current_node_index = 6
    refresh_project_progress(project, progress_percent=72)

    compliance_tier = getattr(project, "compliance_tier", None) or "domestic"
    executed: list = []
    mark_executed(executed, "gate-full")
    gate = cli_gate_full(
        runner,
        script_path,
        episodes=project.episode_count,
        compliance_tier=compliance_tier,
        strict=False,
    )
    mark_executed(executed, "compliance-check")
    compliance = cli_compliance_check(runner, script_path, strict=False)
    mark_executed(executed, "compliance-fuse")
    save_artifact(
        project, "gate_full", gate.get("json") or {"stdout": gate.get("stdout"), "ok": gate.get("ok")}
    )
    save_artifact(
        project,
        "compliance",
        compliance.get("json") or {"stdout": compliance.get("stdout")},
    )

    gate_json = gate.get("json") or {}
    gate_passed = gate_json.get("passed", gate.get("ok"))
    compliance_json = compliance.get("json") or {}
    fuse_merged = merge_fuse_with_cli(fuse_rule, compliance_json)
    fuse = bool(fuse_merged.get("fuseTriggered")) or bool(content_scan.get("fuseTriggered"))
    save_artifact(project, "compliance_fuse_report", fuse_merged)
    save_artifact(project, "compliance_content_report", content_scan)
    mark_executed(executed, "compliance-content")

    quality_verdict = "pass" if gate_passed and not fuse else "fail"
    save_artifact(
        project,
        "quality_report",
        {
            "finalVerdict": quality_verdict,
            "complianceReport": {
                "passed": compliance_json.get("passed") and not fuse,
                "fuseTriggered": fuse,
                "level": compliance_json.get("level"),
                "fuseCategories": (fuse_merged.get("ruleScan") or {}).get("categories") or [],
            },
            "cliGateSummary": {
                "gate_full": "pass" if gate_passed else "fail",
                "compliance": "pass" if compliance_json.get("passed") else "fail",
            },
        },
    )

    _mark_node(
        project,
        "node-6-review",
        summary=(
            f"gate={'通过' if gate_passed else '未过'} · "
            f"合规={'通过' if compliance_json.get('passed') else '未过'}"
        ),
        status=CreationNode.STATUS_COMPLETED if gate_passed and not fuse else CreationNode.STATUS_FAILED,
        error="" if gate_passed and not fuse else "质检未通过",
    )
    project.refresh_from_db()
    refresh_project_progress(project, progress_percent=75)

    if project.pipeline_mode == Project.MODE_AUTO:
        from apps.billing.services import BillingService

        BillingService.charge_node(project.user, 6, reference_id=f"{project.id}:n6")

    return {
        "ok": gate_passed and not fuse,
        "gate_passed": gate_passed,
        "compliance_fuse": fuse,
        "fusion_status": project.fusion_status,
        "executed_sub_skills": executed,
    }


def run_fusion_score_for_project(
    project: Project, pipeline_result: dict
) -> Dict[str, Any]:
    """节点8（网站 index=7）：8 维评分 + 放行判定。"""
    if not getattr(settings, "FUSION_SKILL_ENABLED", True):
        return _fusion_disabled_response()

    cfg = get_fusion_config()
    runner = FusionCliRunner(cfg)
    script_path, score_out, _ = _prepare_script_markdown(project, pipeline_result)
    review_legacy = pipeline_result.get("review") or {}

    project.fusion_status = Project.FUSION_SCORING
    project.save(update_fields=["fusion_status", "updated_at"])
    _mark_node(
        project, "node-8-score", summary="8 维评分进行中…", status=CreationNode.STATUS_RUNNING
    )
    project.current_node_index = 7
    refresh_project_progress(project, progress_percent=85)

    executed: list = []
    mark_executed(executed, "score-deep")
    score = cli_score_deep(
        runner,
        script_path,
        bridge=True,
        output_path=score_out,
        strict=False,
    )
    mark_executed(executed, "s-grade-benchmark")
    score_json = score.get("json")
    eight_dim = None
    bridge_path = score_out.parent / f"{score_out.stem}.eight-dim.json"
    if bridge_path.is_file():
        eight_dim = json.loads(bridge_path.read_text(encoding="utf-8"))
        save_artifact(project, "script_score_report", eight_dim)
    elif score_json:
        save_artifact(project, "script_score_report", score_json)

    overall = None
    grade = ""
    if eight_dim:
        overall = eight_dim.get("overallScore")
        grade = eight_dim.get("grade") or ""
    elif score_json:
        overall = score_json.get("finalScore")
        grade = score_json.get("grade") or ""

    from ..artifact_service import get_artifact

    quality = get_artifact(project, "quality_report") or {}
    gate_art = get_artifact(project, "gate_full") or {}
    gate_passed = bool(gate_art.get("passed")) if gate_art else False
    compliance = get_artifact(project, "compliance") or {}
    fuse = bool((quality.get("complianceReport") or {}).get("fuseTriggered"))
    if not fuse and compliance:
        fuse = bool(compliance.get("fuseTriggered"))
    quality_verdict = quality.get("finalVerdict") or ("pass" if gate_passed and not fuse else "fail")

    if quality:
        quality["legacy_review_score"] = review_legacy.get("overall_score")
        save_artifact(project, "quality_report", quality)

    ep_gate = _episode_gates_from_project(project, pipeline_result)
    all_ep_passed = (
        ep_gate.get("total", 0) > 0 and ep_gate.get("passed", 0) == ep_gate.get("total", 0)
    )

    readiness = evaluate_project_readiness(
        project_brief_confirmed=True,
        has_structure=bool(pipeline_result.get("structure")),
        has_characters=bool(pipeline_result.get("characters")),
        has_outline=bool(pipeline_result.get("outlines")),
        all_episodes_gate_passed=all_ep_passed,
        quality_final_verdict=quality_verdict,
        score_report=eight_dim or score_json,
        compliance_fuse=fuse,
    )

    project.overall_score = overall
    project.grade = grade or ""
    project.fusion_status = readiness["status"]
    if readiness["ready"]:
        project.ready_at = timezone.now()

    update_fields = ["overall_score", "grade", "fusion_status", "updated_at"]
    if readiness["ready"]:
        update_fields.append("ready_at")
    project.save(update_fields=update_fields)

    _mark_node(
        project,
        "node-8-score",
        summary=f"综合 {overall or '—'} 分 · {grade or '—'} · 放行线 {readiness['release_pass_score']}",
        status=CreationNode.STATUS_COMPLETED if readiness["ready"] else CreationNode.STATUS_FAILED,
        error="" if readiness["ready"] else "未达放行线或维度不足",
    )

    if project.pipeline_mode == Project.MODE_AUTO:
        from apps.billing.services import BillingService

        BillingService.charge_node(project.user, 7, reference_id=f"{project.id}:n7")

    return {
        "ok": readiness["ready"],
        "fusion_status": project.fusion_status,
        "overall_score": overall,
        "grade": grade,
        "readiness": readiness,
        "gate_passed": gate_passed,
        "compliance_fuse": fuse,
        "executed_sub_skills": executed,
    }


def run_fusion_for_project(project: Project, pipeline_result: dict) -> Dict[str, Any]:
    """一键模式：节点6 + 节点8 连续执行（C 端主链未启用时跳过）。"""
    from apps.workflow.services.pipeline_service import WorkflowPipelineService

    chain_ids = {n["fusion_node_id"] for n in WorkflowPipelineService.portal_main_chain()}
    if "node-6-review" not in chain_ids:
        logger.info("[Creation] C 端主链未含质检节点，跳过融合后处理 project=%s", project.id)
        return {"ok": True, "skipped": True, "fusion_status": project.fusion_status or Project.FUSION_DRAFT}
    review = run_fusion_review_for_project(project, pipeline_result)
    if not review.get("ok"):
        project.fusion_status = Project.FUSION_BLOCKED
        project.save(update_fields=["fusion_status", "updated_at"])
        return review
    return run_fusion_score_for_project(project, pipeline_result)
