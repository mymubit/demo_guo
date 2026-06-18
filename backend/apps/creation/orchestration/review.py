# -*- coding: utf-8 -*-
"""ReviewAgent：gate + compliance + pacing 启发式 + G-Eval 多维度评估模式。

G-Eval 改造说明（来自 StoryForge narrative-reviewer/logic-auditor 设计）：
  1. 将 review 拆分为「维度分析」（chain-of-thought）和「维度判定」两阶段
  2. 维度判定结果写入 CreationNode.last_failed_dimensions
  3. 下轮 re-review 时只复查上轮 FAIL 的维度，防止"维度漂移"（新问题无限冒出）
  4. 每个维度有独立的 PASS/FAIL 状态和具体修改建议
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..artifact_service import get_artifact, save_artifact
from ..models import CreationNode, Project
from ..step_mode import build_pipeline_result_from_project
from .pacing_heuristics import analyze_pacing
from .plot_structure_review import analyze_plot_structure
from .quality_guard import run_quality_guard
from .score_quick import run_score_quick_preview
from .sub_skill_runner import agent_execution_meta, mark_executed, persist_agent_execution_trace
from .types import AgentResult

logger = logging.getLogger(__name__)

# G-Eval 维度定义（来自 StoryForge 评估分层设计）
_DIMENSION_KEYS = {
    "pacing": "节奏与叙事效率",
    "plot_structure": "剧情结构与冲突",
    "quality_guard": "质量保护（AI痕迹/短剧基因）",
    "compliance": "合规熔断",
    "content_safety": "内容安全审核",
}


def _extract_failed_dimensions(
    pacing_passed: bool,
    plot_passed: bool,
    quality_passed: bool,
    fuse_triggered: bool,
    content_passed: bool,
) -> List[str]:
    """提取本轮未通过的维度 key 列表（G-Eval 失败维度）。"""
    failed = []
    if not pacing_passed:
        failed.append("pacing")
    if not plot_passed:
        failed.append("plot_structure")
    if not quality_passed:
        failed.append("quality_guard")
    if fuse_triggered:
        failed.append("compliance")
    if not content_passed:
        failed.append("content_safety")
    return failed


def _get_focus_dimensions(project: Project) -> Optional[List[str]]:
    """
    获取上轮 review 的失败维度列表。
    若存在（re-review 场景），只复查这些维度；
    若为空（首次 review），全量检查。
    """
    try:
        node = CreationNode.objects.filter(
            project=project,
            node_index=6,
        ).first()
        if node and node.last_failed_dimensions:
            return list(node.last_failed_dimensions)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ReviewAgent] 读取 last_failed_dimensions 失败: %s", exc)
    return None


def _save_failed_dimensions(project: Project, failed: List[str]) -> None:
    """将本轮失败维度写入 CreationNode.last_failed_dimensions。"""
    try:
        CreationNode.objects.filter(project=project, node_index=6).update(
            last_failed_dimensions=failed
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ReviewAgent] 写入 last_failed_dimensions 失败: %s", exc)


def _build_dimension_analysis(
    *,
    pacing: Dict[str, Any],
    plot_structure: Dict[str, Any],
    quality_guard: Dict[str, Any],
    fuse_triggered: bool,
    fuse_report: Dict[str, Any],
    content_report: Dict[str, Any],
    focus_dimensions: Optional[List[str]],
) -> Dict[str, Any]:
    """
    G-Eval 维度分析层：逐维度 chain-of-thought。

    focus_dimensions 非空时（re-review）只输出需关注的维度详情，
    其余维度标记为 skipped=True，不重新评估。
    """
    def _should_check(key: str) -> bool:
        if focus_dimensions is None:
            return True
        return key in focus_dimensions

    dims: Dict[str, Any] = {}

    if _should_check("pacing"):
        dims["pacing"] = {
            "passed": bool(pacing.get("passed")),
            "skipped": False,
            "score": None,
            "issues": pacing.get("assessments") or [],
            "chain_of_thought": f"节奏检测：共 {pacing.get('totalEpisodes', 0)} 集，"
                f"通过={'是' if pacing.get('passed') else '否'}，"
                f"评估={pacing.get('assessments') or []}",
        }
    else:
        dims["pacing"] = {"passed": True, "skipped": True, "reason": "上轮通过，本轮跳过"}

    if _should_check("plot_structure"):
        dims["plot_structure"] = {
            "passed": bool(plot_structure.get("passed")),
            "skipped": False,
            "issues": plot_structure.get("issues") or [],
            "chain_of_thought": f"剧情结构检测：冲突升级={'已检测' if plot_structure else '无数据'}，"
                f"通过={'是' if plot_structure.get('passed') else '否'}",
        }
    else:
        dims["plot_structure"] = {"passed": True, "skipped": True, "reason": "上轮通过，本轮跳过"}

    if _should_check("quality_guard"):
        dims["quality_guard"] = {
            "passed": bool(quality_guard.get("passed")),
            "skipped": False,
            "issues": quality_guard.get("issues") or [],
            "chain_of_thought": f"质量保护：AI痕迹/短剧基因检测，通过={'是' if quality_guard.get('passed') else '否'}",
        }
    else:
        dims["quality_guard"] = {"passed": True, "skipped": True, "reason": "上轮通过，本轮跳过"}

    if _should_check("compliance"):
        dims["compliance"] = {
            "passed": not fuse_triggered,
            "skipped": False,
            "triggered": fuse_triggered,
            "issues": fuse_report.get("issues") or [],
            "chain_of_thought": f"合规熔断：触发={'是' if fuse_triggered else '否'}，"
                f"类别={list((fuse_report.get('ruleScan') or {}).get('categories') or fuse_report.get('categories') or [])}",
        }
    else:
        dims["compliance"] = {"passed": True, "skipped": True, "reason": "上轮通过，本轮跳过"}

    if _should_check("content_safety"):
        content_passed = bool(content_report.get("passed", True)) if content_report else True
        dims["content_safety"] = {
            "passed": content_passed,
            "skipped": False,
            "issues": (content_report.get("issues") or [])[:6],
            "findingCount": content_report.get("findingCount") if content_report else 0,
            "chain_of_thought": f"内容安全：高风险={content_report.get('highRiskCount', 0)}，"
                f"通过={'是' if content_passed else '否'}",
        }
    else:
        dims["content_safety"] = {"passed": True, "skipped": True, "reason": "上轮通过，本轮跳过"}

    return dims


def run_review_agent(project: Project) -> AgentResult:
    from ..fusion.fusion_pipeline import scripts_result_to_markdown

    pipeline_result = build_pipeline_result_from_project(project)
    scripts = pipeline_result.get("scripts") or {}
    markdown = scripts_result_to_markdown(scripts)

    # 获取上轮失败维度（G-Eval 修复范围限定）
    focus_dimensions = _get_focus_dimensions(project)
    is_re_review = focus_dimensions is not None
    if is_re_review:
        logger.info(
            "[ReviewAgent] re-review 模式：只复查失败维度 %s project=%s",
            focus_dimensions,
            project.id,
        )
    else:
        logger.info("[ReviewAgent] 首次 review，全量检查 project=%s", project.id)

    executed: list = []

    # — 节奏检测 —
    if focus_dimensions is None or "pacing" in focus_dimensions:
        pacing = analyze_pacing(markdown) if markdown.strip() else {
            "passed": False,
            "assessments": ["无剧本文本，跳过节奏分析"],
            "totalEpisodes": 0,
        }
        mark_executed(executed, "pacing-keyword-heuristics")
    else:
        pacing = {"passed": True, "assessments": [], "totalEpisodes": 0, "skipped": True}

    # — 剧情结构检测 —
    if focus_dimensions is None or "plot_structure" in focus_dimensions:
        structure_plan = get_artifact(project, "structure_plan") or {}
        series_outline = get_artifact(project, "series_outline") or {}
        episode_scripts = scripts if isinstance(scripts, dict) else {}
        plot_structure = analyze_plot_structure(
            structure_plan=structure_plan,
            series_outline=series_outline,
            episode_scripts=episode_scripts,
        )
        mark_executed(executed, "plot-structure-review")
    else:
        plot_structure = {"passed": True, "issues": [], "skipped": True}

    # — 质量保护 —
    if focus_dimensions is None or "quality_guard" in focus_dimensions:
        score_report = get_artifact(project, "script_score_report") or get_artifact(project, "score_report") or {}
        quality_guard_result = run_quality_guard(episode_scripts if "episode_scripts" in dir() else scripts, score_report=score_report)
        mark_executed(executed, "quality-guard")
    else:
        quality_guard_result = {"passed": True, "issues": [], "skipped": True}

    # — 快速评分预览 —
    score_quick = run_score_quick_preview(project, pipeline_result)
    if not score_quick.get("skipped"):
        mark_executed(executed, "score-quick")
        save_artifact(project, "score_quick_report", score_quick)

    quality = get_artifact(project, "quality_report") or {}
    gate = get_artifact(project, "gate_full") or {}
    fuse_report = get_artifact(project, "compliance_fuse_report") or {}
    content_report = get_artifact(project, "compliance_content_report") or {}

    gate_passed = bool(gate.get("passed")) if gate else bool(markdown.strip())
    fuse_triggered = False
    if not fuse_triggered and fuse_report:
        fuse_triggered = bool(fuse_report.get("fuseTriggered"))
    if not fuse_triggered and content_report:
        fuse_triggered = bool(content_report.get("fuseTriggered"))

    pacing_passed = bool(pacing.get("passed"))
    plot_passed = bool(plot_structure.get("passed"))
    quality_passed = bool(quality_guard_result.get("passed"))
    content_passed = bool(content_report.get("passed", True)) if content_report else True

    # G-Eval 维度分析层（chain-of-thought）
    dimension_analysis = _build_dimension_analysis(
        pacing=pacing,
        plot_structure=plot_structure,
        quality_guard=quality_guard_result,
        fuse_triggered=fuse_triggered,
        fuse_report=fuse_report,
        content_report=content_report,
        focus_dimensions=focus_dimensions,
    )

    # 提取失败维度并持久化（供下轮 re-review 使用）
    failed_dimensions = _extract_failed_dimensions(
        pacing_passed=pacing_passed,
        plot_passed=plot_passed,
        quality_passed=quality_passed,
        fuse_triggered=fuse_triggered,
        content_passed=content_passed,
    )
    _save_failed_dimensions(project, failed_dimensions)

    overall_ok = (
        gate_passed
        and not fuse_triggered
        and pacing_passed
        and plot_passed
        and quality_passed
        and content_passed
    )

    review_report: Dict[str, Any] = {
        "agentId": "review",
        "passed": overall_ok,
        "gatePassed": gate_passed,
        # G-Eval 字段
        "geval": {
            "mode": "re_review" if is_re_review else "full_review",
            "focusDimensions": focus_dimensions,
            "failedDimensions": failed_dimensions,
            "dimensionAnalysis": dimension_analysis,
            "dimensionLabels": _DIMENSION_KEYS,
        },
        # 原有兼容字段
        "pacing": pacing,
        "plotStructure": plot_structure,
        "qualityGuard": quality_guard_result,
        "scoreQuick": score_quick,
        "complianceContent": {
            "passed": content_passed,
            "findingCount": content_report.get("findingCount"),
            "highRiskCount": content_report.get("highRiskCount"),
            "issues": (content_report.get("issues") or [])[:6],
        }
        if content_report
        else None,
        "complianceFuse": {
            "triggered": fuse_triggered,
            "categories": (fuse_report.get("ruleScan") or {}).get("categories")
            or fuse_report.get("categories")
            or [],
            "issues": fuse_report.get("issues") or [],
        }
        if fuse_report
        else {"triggered": fuse_triggered, "categories": [], "issues": []},
        "qualityVerdict": quality.get("finalVerdict"),
        "cliGateSummary": quality.get("cliGateSummary"),
        "complianceReport": quality.get("complianceReport"),
        "issues": [],
    }

    # 只收集本轮关注维度的 issues
    if not gate_passed:
        review_report["issues"].append("全剧 gate 未通过")
    if fuse_triggered and (focus_dimensions is None or "compliance" in focus_dimensions):
        review_report["issues"].append("合规熔断触发")
        review_report["issues"].extend((fuse_report.get("issues") or [])[:3])
    if not pacing_passed and (focus_dimensions is None or "pacing" in focus_dimensions):
        review_report["issues"].extend(pacing.get("assessments") or [])
    if not plot_passed and (focus_dimensions is None or "plot_structure" in focus_dimensions):
        review_report["issues"].extend(plot_structure.get("issues") or [])
    if not quality_passed and (focus_dimensions is None or "quality_guard" in focus_dimensions):
        review_report["issues"].extend(quality_guard_result.get("issues") or [])
    if not content_passed and (focus_dimensions is None or "content_safety" in focus_dimensions):
        review_report["issues"].extend((content_report.get("issues") or [])[:4])

    save_artifact(project, "review_report", review_report)
    trace_meta = agent_execution_meta("review", executed, node_index=0)
    persist_agent_execution_trace(project, "review", executed)
    logger.info(
        "[ReviewAgent] project=%s passed=%s gate=%s pacing=%s failed_dims=%s mode=%s",
        project.id,
        overall_ok,
        gate_passed,
        pacing_passed,
        failed_dimensions,
        "re_review" if is_re_review else "full",
    )
    return AgentResult(
        agent_id="review",
        status="completed",
        outputs={"review_report": review_report, "passed": overall_ok},
        errors=[] if overall_ok else review_report["issues"][:5],
        meta=trace_meta,
    )
