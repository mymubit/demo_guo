# -*- coding: utf-8 -*-
"""agent_execution_log.py — Agent 执行结构化日志。

目标：在现有 AgentExecutionRun / SubSkillExecutionLog 追踪层之上，
提供标准化的跨 Agent 事件日志格式，重点覆盖：
  - 收敛判定事件（convergence_decision）
  - G-Eval 维度评估事件（dimension_eval）
  - 情绪策略生成事件（emotion_strategy）
  - 爆款基线比对事件（comparator_result）
  - LLM 调用摘要（llm_call）
  - 关键业务操作（business_action）

日志写入三个目的地：
  1. Python logger（JSON 格式，接入日志采集）
  2. SubSkillExecutionLog（DB 持久化，可通过 API 查询）
  3. 内存 buffer（同一请求内可读取完整事件链）
"""
from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger("agent.event")

# ── 事件类型常量 ──────────────────────────────────────────────────────────
EVENT_CONVERGENCE = "convergence_decision"
EVENT_DIMENSION_EVAL = "dimension_eval"
EVENT_EMOTION_STRATEGY = "emotion_strategy"
EVENT_COMPARATOR = "comparator_result"
EVENT_LLM_CALL = "llm_call"
EVENT_BUSINESS = "business_action"
EVENT_AGENT_START = "agent_start"
EVENT_AGENT_END = "agent_end"
EVENT_GATE = "gate_check"
EVENT_INSIGHT_LAYER = "insight_layer"

# 事件严重级别
LEVEL_INFO = "INFO"
LEVEL_WARN = "WARN"
LEVEL_ERROR = "ERROR"

# 当前请求的事件 buffer（ContextVar 保证请求隔离）
_event_buffer: ContextVar[Optional[List[Dict[str, Any]]]] = ContextVar(
    "agent_event_buffer", default=None
)


@dataclass
class AgentEvent:
    """标准化 Agent 事件结构。"""
    event_type: str
    agent_id: str
    project_id: str
    level: str = LEVEL_INFO
    message: str = ""
    duration_ms: Optional[int] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_log_str(self) -> str:
        """生成适合 logger.info() 的单行 JSON 日志。"""
        return json.dumps({
            "event": self.event_type,
            "agent": self.agent_id,
            "project": self.project_id,
            "level": self.level,
            "msg": self.message,
            "duration_ms": self.duration_ms,
            **self.data,
            "ts": self.timestamp,
        }, ensure_ascii=False)


def emit(event: AgentEvent) -> None:
    """
    发送结构化事件到所有目的地：logger + buffer。

    DB 持久化由调用方（若需要）通过 flush_buffer_to_db() 触发，
    避免每条事件都写库造成 IO 压力。
    """
    # 1. Python logger
    if event.level == LEVEL_ERROR:
        logger.error(event.to_log_str())
    elif event.level == LEVEL_WARN:
        logger.warning(event.to_log_str())
    else:
        logger.info(event.to_log_str())

    # 2. 内存 buffer
    buf = _event_buffer.get()
    if buf is not None:
        buf.append(event.to_dict())


def log_event(
    event_type: str,
    agent_id: str,
    project_id: str | int,
    *,
    message: str = "",
    level: str = LEVEL_INFO,
    duration_ms: Optional[int] = None,
    **data: Any,
) -> None:
    """便捷函数：直接构造并发送事件。"""
    emit(AgentEvent(
        event_type=event_type,
        agent_id=agent_id,
        project_id=str(project_id),
        level=level,
        message=message,
        duration_ms=duration_ms,
        data=data,
    ))


@contextmanager
def event_buffer_scope() -> Iterator[List[Dict[str, Any]]]:
    """
    在当前请求/任务范围内启用事件 buffer。
    退出时 buffer 自动清空。

    使用示例：
        with event_buffer_scope() as events:
            run_insight_agent(project)
            run_review_agent(project)
        # events 包含本次调用的所有结构化事件
    """
    buf: List[Dict[str, Any]] = []
    token = _event_buffer.set(buf)
    try:
        yield buf
    finally:
        _event_buffer.reset(token)


def flush_buffer_to_db(
    run_id: str,
    buf: List[Dict[str, Any]],
    *,
    max_events: int = 50,
) -> int:
    """Legacy SubSkillExecutionLog 已删除，事件仅保留在内存 buffer / 日志。"""
    _ = (run_id, buf, max_events)
    return 0


# ── 各 Agent 专用快捷日志函数 ────────────────────────────────────────────

def log_convergence(
    agent_id: str,
    project_id: str | int,
    *,
    state: str,
    can_fix: bool,
    fix_round: int,
    score: Optional[float],
    reason: str,
) -> None:
    """记录收敛判定事件。"""
    log_event(
        EVENT_CONVERGENCE,
        agent_id,
        project_id,
        message=f"收敛判定 state={state} can_fix={can_fix} round={fix_round}",
        level=LEVEL_WARN if not can_fix else LEVEL_INFO,
        state=state,
        can_fix=can_fix,
        fix_round=fix_round,
        score=score,
        reason=reason,
    )


def log_dimension_eval(
    agent_id: str,
    project_id: str | int,
    *,
    mode: str,
    failed_dimensions: List[str],
    passed_dimensions: List[str],
    focus_dimensions: Optional[List[str]] = None,
) -> None:
    """记录 G-Eval 维度评估事件。"""
    log_event(
        EVENT_DIMENSION_EVAL,
        agent_id,
        project_id,
        message=(
            f"维度评估 mode={mode} failed={failed_dimensions}"
            + (f" focus={focus_dimensions}" if focus_dimensions else "")
        ),
        level=LEVEL_WARN if failed_dimensions else LEVEL_INFO,
        mode=mode,
        failedDimensions=failed_dimensions,
        passedDimensions=passed_dimensions,
        focusDimensions=focus_dimensions,
    )


def log_emotion_strategy(
    agent_id: str,
    project_id: str | int,
    *,
    source: str,
    episode_count: int,
    dominant_emotion: str,
) -> None:
    """记录情绪策略生成事件。"""
    log_event(
        EVENT_EMOTION_STRATEGY,
        agent_id,
        project_id,
        message=f"情绪策略生成 source={source} episodes={episode_count} dominant={dominant_emotion}",
        source=source,
        episodeCount=episode_count,
        dominantEmotion=dominant_emotion,
    )


def log_comparator(
    agent_id: str,
    project_id: str | int,
    *,
    genre: str,
    current_score: Optional[float],
    avg_baseline: float,
    gap: Optional[float],
    weakest_dimension: str,
) -> None:
    """记录爆款基线比对事件。"""
    level = LEVEL_WARN if (gap or 0) > 15 else LEVEL_INFO
    log_event(
        EVENT_COMPARATOR,
        agent_id,
        project_id,
        message=(
            f"基线比对 genre={genre} score={current_score} baseline={avg_baseline:.1f} "
            f"gap={gap} weakest={weakest_dimension}"
        ),
        level=level,
        genre=genre,
        currentScore=current_score,
        avgBaseline=avg_baseline,
        gap=gap,
        weakestDimension=weakest_dimension,
    )


def log_insight_layer(
    agent_id: str,
    project_id: str | int,
    *,
    layer: int,
    llm_available: bool,
    duration_ms: Optional[int] = None,
) -> None:
    """记录 InsightAgent 三层分解执行事件。"""
    layer_names = {1: "剥离", 2: "观照", 3: "颠倒"}
    log_event(
        EVENT_INSIGHT_LAYER,
        agent_id,
        project_id,
        message=f"三层分解第{layer}层（{layer_names.get(layer, '?')}）llm={llm_available}",
        duration_ms=duration_ms,
        layer=layer,
        layerName=layer_names.get(layer, ""),
        llmAvailable=llm_available,
    )


# ── 集成到 AgentExecutionRunService ──────────────────────────────────────

def enrich_run_tracked_agent_result(
    project_id: str | int,
    agent_id: str,
    result: Any,
    buf: List[Dict[str, Any]],
) -> None:
    """
    在 run_tracked_agent() 完成后，根据 result 内容自动发送补充结构化事件。
    由 AgentExecutionRunService.run_tracked_agent() 调用。
    """
    outputs = getattr(result, "outputs", None) or {}
    if not isinstance(outputs, dict):
        return

    # review_report → 维度评估事件
    review_report = outputs.get("review_report")
    if isinstance(review_report, dict):
        geval = review_report.get("geval") or {}
        if geval:
            log_dimension_eval(
                agent_id,
                project_id,
                mode=geval.get("mode") or "full_review",
                failed_dimensions=geval.get("failedDimensions") or [],
                passed_dimensions=[
                    k for k in (geval.get("dimensionAnalysis") or {})
                    if (geval.get("dimensionAnalysis") or {}).get(k, {}).get("passed", True)
                    and k not in (geval.get("failedDimensions") or [])
                ],
                focus_dimensions=geval.get("focusDimensions"),
            )

    # emotion_strategy → 情绪策略事件
    emotion_strategy = outputs.get("emotion_strategy")
    if isinstance(emotion_strategy, dict):
        log_emotion_strategy(
            agent_id,
            project_id,
            source=emotion_strategy.get("source") or "unknown",
            episode_count=len(emotion_strategy.get("episodeEmotionNodes") or []),
            dominant_emotion=(emotion_strategy.get("seriesEmotionArc") or {}).get("dominant_emotion") or "",
        )

    # comparator_report → 基线比对事件
    comparator = outputs.get("comparator_report")
    if isinstance(comparator, dict):
        summary = comparator.get("summary") or {}
        final_score = comparator.get("finalScore") or {}
        log_comparator(
            agent_id,
            project_id,
            genre=comparator.get("genre") or "",
            current_score=final_score.get("current"),
            avg_baseline=final_score.get("avgBaseline") or 0,
            gap=final_score.get("gap"),
            weakest_dimension=summary.get("weakestDimension") or "",
        )
