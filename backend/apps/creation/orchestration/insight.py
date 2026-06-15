# -*- coding: utf-8 -*-
"""InsightAgent：深度拉片与剧本三层分解分析。

来自 Novel-to-Script-Team insight-architect 的「开天眼」三层方法论：
  - 第一层：剥离（Peel）   —— 表层叙事  → 时间轴 + 人物弧 + 戏剧结构
  - 第二层：观照（Mirror） —— 隐藏真相  → 权力结构/欲望驱动/伤痛内核
  - 第三层：颠倒（Invert） —— 情感爆点  → 逆转设计/情绪释放节点/钩子设计

输出写入 insight_report artifact，供 EmotionArchitectAgent 读取生成情绪策略。
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from ..artifact_service import get_artifact, save_artifact
from ..models import Project
from ..step_mode import build_pipeline_result_from_project
from .sub_skill_runner import (
    agent_execution_meta,
    mark_executed,
    persist_agent_execution_trace,
)
from .types import AgentResult

logger = logging.getLogger(__name__)

# 三层分解的 LLM 提示词
_LAYER1_PEEL_SYSTEM = """你是短剧叙事结构分析师。执行【第一层：剥离】——剥去表象，还原客观叙事骨架。

输出严格 JSON，禁止额外说明：
{
  "timeline": [{"ep": 1, "event": "事件描述", "turning_point": false}],
  "character_arcs": [{"name": "角色名", "start_state": "初始状态", "end_state": "结局状态", "arc_type": "成长/堕落/轮回"}],
  "dramatic_structure": {"hook": "第X集", "rising_action": "第X-X集", "climax": "第X集", "resolution": "第X集"},
  "episode_count": 0,
  "pacing_rhythm": "快/中/慢"
}"""

_LAYER2_MIRROR_SYSTEM = """你是深层叙事心理分析师。执行【第二层：观照】——透过表层叙事，看见隐藏的权力/欲望/伤痛结构。

输入为第一层分析结果 + 原始剧本摘录。
输出严格 JSON，禁止额外说明：
{
  "power_structure": "谁控制谁，如何控制（核心权力关系）",
  "desire_drivers": [{"character": "角色", "core_desire": "核心欲望", "fear": "核心恐惧"}],
  "wound_core": "整部剧的底层情感伤痛（一句话）",
  "hidden_conflict": "台词下面的真实冲突（非表面矛盾）",
  "theme_essence": "去掉情节，这个故事真正在说什么"
}"""

_LAYER3_INVERT_SYSTEM = """你是短剧爆点设计师。执行【第三层：颠倒】——找到情感释放的最大化节点，设计反转与钩子。

输入为前两层分析结果。
输出严格 JSON，禁止额外说明：
{
  "reversal_points": [{"ep": 1, "description": "反转描述", "emotional_impact": "高/中/低", "type": "身份/关系/价值观/真相"}],
  "emotion_release_nodes": [{"ep": 1, "type": "爽感/虐心/治愈/悬念", "trigger": "触发器", "expected_reaction": "观众预期反应"}],
  "hook_design": [{"ep": 1, "hook_type": "悬念钩/情感钩/爽点钩", "hook_content": "钩子内容"}],
  "paywall_suggestion": {"optimal_ep": 1, "reason": "为什么这集适合付费墙"},
  "optimization_suggestions": ["建议1", "建议2"]
}"""


def _call_llm_layer(
    project: Project,
    system: str,
    user_payload: Dict[str, Any],
    sub_skill_id: str,
) -> Dict[str, Any]:
    """调用 LLM 执行单层分析，失败时返回空字典（降级处理）。"""
    try:
        from apps.skill.llm.chat import LlmService

        if not LlmService.is_enabled():
            return {}

        from apps.creation.monitoring.execution_run_service import get_active_run_id
        from apps.creation.orchestration.llm_tokens import resolve_agent_max_tokens
        from apps.agent.routes import AgentLlmRouteService
        from apps.skill.llm.usage_log import llm_usage_scope
        from apps.skill.models import LlmUsageLog

        with llm_usage_scope(
            source_type=LlmUsageLog.SOURCE_AGENT,
            source_key=f"insight:{sub_skill_id}"[:64],
            project_id=project.id,
            user_id=project.user_id,
            execution_run_id=get_active_run_id(),
            sub_skill_id=sub_skill_id,
        ):
            return LlmService.generate_json(
                system_prompt=system,
                user_prompt=json.dumps(user_payload, ensure_ascii=False),
                provider_id=AgentLlmRouteService.resolve_provider_id("insight"),
                max_tokens=resolve_agent_max_tokens("insight"),
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[InsightAgent] LLM 层 %s 失败（降级）: %s", sub_skill_id, exc)
        return {}


def _extract_basic_structure(text: str) -> Dict[str, Any]:
    """快速提取基础结构信息（无需 LLM，作为降级兜底）。"""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    episode_headings = [ln for ln in lines if ln.startswith("# 第")][:20]
    return {
        "lineCount": len(lines),
        "charCount": len(text),
        "episodeHeadings": episode_headings,
        "estimatedEpisodeCount": len(episode_headings),
        "hasDialogue": "：" in text or ":" in text,
    }


def _layer1_peel(project: Project, markdown: str, artifacts: Dict[str, Any]) -> Dict[str, Any]:
    """第一层：剥离 — 客观叙事骨架提取。"""
    basic = _extract_basic_structure(markdown)
    user_payload = {
        "title": project.title,
        "episodeCount": project.episode_count,
        "genre": artifacts.get("project_brief", {}).get("genre", ""),
        "scriptExcerpt": markdown[:10000],
    }
    llm_result = _call_llm_layer(project, _LAYER1_PEEL_SYSTEM, user_payload, "layer1-peel")
    return {
        "basicStructure": basic,
        "timeline": llm_result.get("timeline") or [],
        "characterArcs": llm_result.get("character_arcs") or [],
        "dramaticStructure": llm_result.get("dramatic_structure") or {},
        "pacingRhythm": llm_result.get("pacing_rhythm") or "未知",
        "llmAvailable": bool(llm_result),
    }


def _layer2_mirror(
    project: Project,
    markdown: str,
    artifacts: Dict[str, Any],
    layer1: Dict[str, Any],
) -> Dict[str, Any]:
    """第二层：观照 — 权力/欲望/伤痛结构挖掘。"""
    user_payload = {
        "title": project.title,
        "genre": artifacts.get("project_brief", {}).get("genre", ""),
        "layer1Analysis": layer1,
        "scriptExcerpt": markdown[5000:15000] if len(markdown) > 5000 else markdown[:10000],
    }
    llm_result = _call_llm_layer(project, _LAYER2_MIRROR_SYSTEM, user_payload, "layer2-mirror")
    return {
        "powerStructure": llm_result.get("power_structure") or "",
        "desireDrivers": llm_result.get("desire_drivers") or [],
        "woundCore": llm_result.get("wound_core") or "",
        "hiddenConflict": llm_result.get("hidden_conflict") or "",
        "themeEssence": llm_result.get("theme_essence") or "",
        "llmAvailable": bool(llm_result),
    }


def _layer3_invert(
    project: Project,
    layer1: Dict[str, Any],
    layer2: Dict[str, Any],
    artifacts: Dict[str, Any],
) -> Dict[str, Any]:
    """第三层：颠倒 — 情感爆点 & 钩子设计。"""
    user_payload = {
        "title": project.title,
        "episodeCount": project.episode_count,
        "genre": artifacts.get("project_brief", {}).get("genre", ""),
        "layer1Summary": {
            "dramaticStructure": layer1.get("dramaticStructure"),
            "characterArcs": layer1.get("characterArcs"),
            "pacingRhythm": layer1.get("pacingRhythm"),
        },
        "layer2Summary": {
            "woundCore": layer2.get("woundCore"),
            "hiddenConflict": layer2.get("hiddenConflict"),
            "themeEssence": layer2.get("themeEssence"),
            "desireDrivers": layer2.get("desireDrivers"),
        },
    }
    llm_result = _call_llm_layer(project, _LAYER3_INVERT_SYSTEM, user_payload, "layer3-invert")
    return {
        "reversalPoints": llm_result.get("reversal_points") or [],
        "emotionReleaseNodes": llm_result.get("emotion_release_nodes") or [],
        "hookDesign": llm_result.get("hook_design") or [],
        "paywallSuggestion": llm_result.get("paywall_suggestion") or {},
        "optimizationSuggestions": llm_result.get("optimization_suggestions") or [],
        "llmAvailable": bool(llm_result),
    }


def _compare_with_project_outline(
    project: Project,
    layer1: Dict[str, Any],
    artifacts: Dict[str, Any],
) -> Dict[str, Any]:
    """将拉片结果与项目大纲做对齐比较。"""
    outline_eps = len((artifacts.get("series_outline") or {}).get("episodes") or [])
    script_eps = len(layer1.get("basicStructure", {}).get("episodeHeadings") or [])
    return {
        "outlineEpisodeCount": outline_eps,
        "scriptEpisodeCount": script_eps,
        "aligned": outline_eps <= 0 or script_eps >= min(outline_eps, 1),
        "characterArcCount": len(layer1.get("characterArcs") or []),
    }


def run_insight_agent(
    project: Project,
    *,
    source_text: Optional[str] = None,
    compare_project: bool = True,
) -> AgentResult:
    if source_text:
        markdown = source_text
    else:
        from ..fusion.fusion_pipeline import scripts_result_to_markdown

        pipeline = build_pipeline_result_from_project(project)
        markdown = scripts_result_to_markdown(pipeline.get("scripts") or {})

    if not markdown.strip():
        return AgentResult(agent_id="insight", status="error", errors=["无可分析剧本文本"])

    artifacts = {
        "project_brief": get_artifact(project, "project_brief") or {},
        "series_outline": get_artifact(project, "series_outline") or {},
        "character_bible": get_artifact(project, "character_bible") or {},
    }
    executed: List[str] = []

    # ── 第一层：剥离 ───────────────────────────────────────────────────
    layer1 = _layer1_peel(project, markdown, artifacts)
    mark_executed(executed, "layer1-peel")
    if layer1.get("llmAvailable"):
        mark_executed(executed, "film-analyzer-layer1")

    # ── 第二层：观照 ───────────────────────────────────────────────────
    layer2 = _layer2_mirror(project, markdown, artifacts, layer1)
    mark_executed(executed, "layer2-mirror")
    if layer2.get("llmAvailable"):
        mark_executed(executed, "film-analyzer-layer2")

    # ── 第三层：颠倒 ───────────────────────────────────────────────────
    layer3 = _layer3_invert(project, layer1, layer2, artifacts)
    mark_executed(executed, "layer3-invert")
    if layer3.get("llmAvailable"):
        mark_executed(executed, "film-analyzer-layer3")

    # ── 与项目大纲对齐比较 ────────────────────────────────────────────
    compare_result = None
    if compare_project:
        compare_result = _compare_with_project_outline(project, layer1, artifacts)
        mark_executed(executed, "compare-with-project")

    report: Dict[str, Any] = {
        "agentId": "insight",
        "projectId": str(project.id),
        "methodology": "三层分解法（剥离→观照→颠倒）",
        "layer1_peel": layer1,
        "layer2_mirror": layer2,
        "layer3_invert": layer3,
        "compareWithProject": compare_result,
        # 向后兼容旧字段
        "structure": layer1.get("basicStructure") or {},
        "analysis": {
            "characters": [arc.get("name") for arc in (layer1.get("characterArcs") or [])],
            "rhythmNotes": layer1.get("pacingRhythm") or "",
            "cpLines": [],
            "paywallHints": [layer3.get("paywallSuggestion") or {}],
            "hookPoints": [h.get("hook_content") for h in (layer3.get("hookDesign") or [])],
        },
    }

    save_artifact(project, "insight_report", report)
    trace_meta = agent_execution_meta("insight", executed, node_index=0)
    persist_agent_execution_trace(project, "insight", executed)
    logger.info(
        "[InsightAgent] project=%s layers=3 reversals=%d hooks=%d llm=%s",
        project.id,
        len(layer3.get("reversalPoints") or []),
        len(layer3.get("hookDesign") or []),
        all([layer1.get("llmAvailable"), layer2.get("llmAvailable"), layer3.get("llmAvailable")]),
    )
    return AgentResult(
        agent_id="insight",
        status="completed",
        outputs={"insight_report": report},
        meta=trace_meta,
    )
