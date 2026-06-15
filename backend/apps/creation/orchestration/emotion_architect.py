# -*- coding: utf-8 -*-
"""EmotionArchitectAgent：主动情绪策略设计。

来自 Novel-to-Script-Team emotion-architect 设计理念：
  - 不等 Script Agent 自行处理情绪，而是在大纲生成完成后「主动」规划情绪蓝图
  - 读取 InsightAgent 的三层分析结果（insight_report）
  - 结合大纲（series_outline）和角色圣经（character_bible）
  - 输出结构化的 emotion_strategy artifact，供 ScriptAgent 参考

情绪策略包含：
  1. 全剧情绪弧线（series-level）
  2. 逐集情绪节点（episode-level）：情绪类型 + 触发器 + 强度
  3. CP/情感线情绪设计（relationship arc）
  4. 付费墙情绪锚点建议
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

_EMOTION_STRATEGY_SYSTEM = """你是短剧情绪架构师（Emotion Architect）。你的任务是在剧本创作之前，主动规划全剧的情绪蓝图。

基于以下输入：
1. InsightAgent 的三层分析（剥离/观照/颠倒）
2. 系列大纲（series_outline）
3. 角色圣经（character_bible）
4. 题材（genre）

输出严格 JSON，禁止额外说明：
{
  "seriesEmotionArc": {
    "opening_tone": "开篇情绪基调（一句话）",
    "rising_tension": "矛盾升级阶段的情绪走向",
    "climax_emotion": "高潮情绪类型",
    "resolution_tone": "结局情绪基调",
    "dominant_emotion": "全剧主导情绪（爽/虐/甜/悬/治愈）"
  },
  "episodeEmotionNodes": [
    {
      "ep": 1,
      "emotionType": "爽感/虐心/甜蜜/悬念/治愈/愤怒/悲伤",
      "intensity": 1-10,
      "trigger": "情绪触发器（什么事件引发）",
      "characterFocus": "聚焦角色",
      "designNote": "给 ScriptAgent 的情绪设计备注"
    }
  ],
  "relationshipArc": [
    {
      "relationship": "关系名称（如：男女主）",
      "arcType": "相爱/对立/救赎/成长",
      "keyMoments": [{"ep": 1, "milestone": "关系里程碑", "emotionType": "情绪类型"}]
    }
  ],
  "paywallEmotionAnchors": [
    {"ep": 1, "anchor": "付费墙情绪锚点描述", "effectiveness": "高/中/低"}
  ],
  "scriptInstructions": [
    "给 ScriptAgent 的情绪创作指令1",
    "给 ScriptAgent 的情绪创作指令2"
  ]
}"""


def _build_emotion_payload(
    project: Project,
    insight_report: Dict[str, Any],
    series_outline: Dict[str, Any],
    character_bible: Dict[str, Any],
    project_brief: Dict[str, Any],
) -> Dict[str, Any]:
    """构建发送给 LLM 的情绪策略规划 payload。"""
    layer2 = insight_report.get("layer2_mirror") or {}
    layer3 = insight_report.get("layer3_invert") or {}
    layer1 = insight_report.get("layer1_peel") or {}

    episodes_summary = []
    for ep in (series_outline.get("episodes") or [])[:30]:
        episodes_summary.append({
            "ep": ep.get("episode") or ep.get("ep"),
            "title": ep.get("title") or ep.get("episode_title") or "",
            "summary": (ep.get("summary") or ep.get("synopsis") or "")[:200],
        })

    characters_summary = []
    for char in (character_bible.get("characters") or [])[:10]:
        characters_summary.append({
            "name": char.get("name") or char.get("characterName") or "",
            "role": char.get("role") or char.get("characterType") or "",
            "core_desire": char.get("coreDesire") or char.get("desire") or "",
        })

    return {
        "title": project.title,
        "episodeCount": project.episode_count,
        "genre": project_brief.get("genre") or "",
        "insightSummary": {
            "woundCore": layer2.get("woundCore") or "",
            "themeEssence": layer2.get("themeEssence") or "",
            "hiddenConflict": layer2.get("hiddenConflict") or "",
            "desireDrivers": (layer2.get("desireDrivers") or [])[:5],
            "reversalPoints": (layer3.get("reversalPoints") or [])[:5],
            "emotionReleaseNodes": (layer3.get("emotionReleaseNodes") or [])[:5],
            "paywallSuggestion": layer3.get("paywallSuggestion") or {},
            "optimizationSuggestions": layer3.get("optimizationSuggestions") or [],
        },
        "episodesSummary": episodes_summary,
        "characters": characters_summary,
    }


def _fallback_emotion_strategy(
    project: Project,
    insight_report: Dict[str, Any],
    series_outline: Dict[str, Any],
) -> Dict[str, Any]:
    """LLM 不可用时的规则推导降级策略。"""
    layer3 = insight_report.get("layer3_invert") or {}
    reversal_points = layer3.get("reversalPoints") or []
    emotion_nodes = layer3.get("emotionReleaseNodes") or []
    paywall = layer3.get("paywallSuggestion") or {}

    episode_nodes = []
    for node in emotion_nodes[:project.episode_count]:
        ep = node.get("ep") or 1
        episode_nodes.append({
            "ep": ep,
            "emotionType": node.get("type") or "悬念",
            "intensity": 7,
            "trigger": node.get("trigger") or "",
            "characterFocus": "",
            "designNote": node.get("expected_reaction") or "",
        })

    return {
        "seriesEmotionArc": {
            "opening_tone": "悬念开篇",
            "rising_tension": "矛盾逐渐升级",
            "climax_emotion": "情感高潮",
            "resolution_tone": "圆满或意外结局",
            "dominant_emotion": "爽感",
        },
        "episodeEmotionNodes": episode_nodes,
        "relationshipArc": [],
        "paywallEmotionAnchors": [
            {
                "ep": paywall.get("optimal_ep") or max(1, project.episode_count // 4),
                "anchor": paywall.get("reason") or "情绪锚点",
                "effectiveness": "中",
            }
        ] if paywall else [],
        "scriptInstructions": layer3.get("optimizationSuggestions") or [],
        "_fallback": True,
    }


def run_emotion_architect_agent(project: Project) -> AgentResult:
    """执行情绪策略设计，读取 insight_report 生成 emotion_strategy artifact。"""
    insight_report = get_artifact(project, "insight_report") or {}
    series_outline = get_artifact(project, "series_outline") or {}
    character_bible = get_artifact(project, "character_bible") or {}
    project_brief = get_artifact(project, "project_brief") or {}

    executed: List[str] = []

    if not insight_report:
        logger.warning("[EmotionArchitect] insight_report 缺失，降级至基础策略 project=%s", project.id)
        fallback = _fallback_emotion_strategy(project, {}, series_outline)
        strategy = {
            "agentId": "emotion_architect",
            "projectId": str(project.id),
            "source": "fallback_no_insight",
            **fallback,
        }
        save_artifact(project, "emotion_strategy", strategy)
        mark_executed(executed, "emotion-fallback")
        trace_meta = agent_execution_meta("emotion_architect", executed, node_index=12)
        return AgentResult(
            agent_id="emotion_architect",
            status="completed",
            outputs={"emotion_strategy": strategy},
            meta=trace_meta,
        )

    mark_executed(executed, "insight-reader")

    llm_result: Dict[str, Any] = {}
    try:
        from apps.skill.llm.chat import LlmService

        if LlmService.is_enabled():
            from apps.creation.monitoring.execution_run_service import get_active_run_id
            from apps.creation.orchestration.llm_tokens import resolve_agent_max_tokens
            from apps.agent.routes import AgentLlmRouteService
            from apps.skill.llm.usage_log import llm_usage_scope
            from apps.skill.models import LlmUsageLog

            payload = _build_emotion_payload(
                project, insight_report, series_outline, character_bible, project_brief
            )
            with llm_usage_scope(
                source_type=LlmUsageLog.SOURCE_AGENT,
                source_key="emotion_architect:strategy"[:64],
                project_id=project.id,
                user_id=project.user_id,
                execution_run_id=get_active_run_id(),
                sub_skill_id="emotion-strategy",
            ):
                llm_result = LlmService.generate_json(
                    system_prompt=_EMOTION_STRATEGY_SYSTEM,
                    user_prompt=json.dumps(payload, ensure_ascii=False),
                    provider_id=AgentLlmRouteService.resolve_provider_id("emotion_architect"),
                    max_tokens=resolve_agent_max_tokens("emotion_architect"),
                )
            mark_executed(executed, "emotion-strategy-llm")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[EmotionArchitect] LLM 调用失败，降级: %s", exc)

    if not llm_result:
        llm_result = _fallback_emotion_strategy(project, insight_report, series_outline)
        mark_executed(executed, "emotion-fallback")
    else:
        mark_executed(executed, "emotion-architect-complete")

    strategy: Dict[str, Any] = {
        "agentId": "emotion_architect",
        "projectId": str(project.id),
        "source": "llm" if not llm_result.get("_fallback") else "fallback",
        "seriesEmotionArc": llm_result.get("seriesEmotionArc") or {},
        "episodeEmotionNodes": llm_result.get("episodeEmotionNodes") or [],
        "relationshipArc": llm_result.get("relationshipArc") or [],
        "paywallEmotionAnchors": llm_result.get("paywallEmotionAnchors") or [],
        "scriptInstructions": llm_result.get("scriptInstructions") or [],
        "insightSource": {
            "woundCore": (insight_report.get("layer2_mirror") or {}).get("woundCore") or "",
            "themeEssence": (insight_report.get("layer2_mirror") or {}).get("themeEssence") or "",
        },
    }

    save_artifact(project, "emotion_strategy", strategy)
    persist_agent_execution_trace(project, "emotion_architect", executed)
    trace_meta = agent_execution_meta("emotion_architect", executed, node_index=12)
    logger.info(
        "[EmotionArchitect] project=%s source=%s episodeNodes=%d",
        project.id,
        strategy["source"],
        len(strategy["episodeEmotionNodes"]),
    )
    return AgentResult(
        agent_id="emotion_architect",
        status="completed",
        outputs={"emotion_strategy": strategy},
        meta=trace_meta,
    )
