"""独立 Agent 输出契约字段级校验。"""
from __future__ import annotations

from typing import Any, Callable, Dict, List

from apps.creation.agent_runtime.independent_service import AgentRuntimeError

Validator = Callable[[Dict[str, Any]], None]


def _require_dict(body: Dict[str, Any], label: str) -> None:
    if not isinstance(body, dict):
        raise AgentRuntimeError(f"{label} 必须是对象")


def _validate_episode_scripts(body: Dict[str, Any]) -> None:
    _require_dict(body, "episode_scripts")
    episodes = body.get("episodes")
    if not isinstance(episodes, list) or not episodes:
        raise AgentRuntimeError("episode_scripts.episodes 必须为非空数组")
    for index, episode in enumerate(episodes):
        if not isinstance(episode, dict):
            raise AgentRuntimeError(f"episode_scripts.episodes[{index}] 必须是对象")
        if episode.get("episodeNumber") is None:
            raise AgentRuntimeError(f"episode_scripts.episodes[{index}].episodeNumber 必填")


def _validate_review_report(body: Dict[str, Any]) -> None:
    _require_dict(body, "review_report")
    if not isinstance(body.get("passed"), bool):
        raise AgentRuntimeError("review_report.passed 必须为布尔值")


def _validate_script_score_report(body: Dict[str, Any]) -> None:
    _require_dict(body, "script_score_report")
    if body.get("overallScore") is None and not body.get("grade"):
        raise AgentRuntimeError("script_score_report 需包含 overallScore 或 grade")


def _validate_marketing_kit(body: Dict[str, Any]) -> None:
    _require_dict(body, "marketing_kit")
    titles = body.get("titles")
    if titles is not None and not isinstance(titles, list):
        raise AgentRuntimeError("marketing_kit.titles 必须为数组")


def _validate_insight_report(body: Dict[str, Any]) -> None:
    _require_dict(body, "insight_report")
    layer_keys = ("layer1_peel", "layer2_mirror", "layer3_invert")
    if not any(isinstance(body.get(key), dict) for key in layer_keys):
        raise AgentRuntimeError("insight_report 需至少包含一层分析结果")


def _validate_polish_log(body: Dict[str, Any]) -> None:
    _require_dict(body, "polish_log")
    suggestions = body.get("suggestions")
    if suggestions is not None and not isinstance(suggestions, list):
        raise AgentRuntimeError("polish_log.suggestions 必须为数组")


ARTIFACT_KEY_VALIDATORS: Dict[str, Validator] = {
    "episode_scripts": _validate_episode_scripts,
    "review_report": _validate_review_report,
    "script_score_report": _validate_script_score_report,
    "marketing_kit": _validate_marketing_kit,
    "insight_report": _validate_insight_report,
    "polish_log": _validate_polish_log,
}

SCHEMA_VERSION_VALIDATORS: Dict[str, Validator] = {
    "episode-scripts.v1": _validate_episode_scripts,
    "review-report.v1": _validate_review_report,
    "script-score-report.v1": _validate_script_score_report,
    "marketing-kit.v1": _validate_marketing_kit,
    "insight-report.v1": _validate_insight_report,
    "polish-log.v1": _validate_polish_log,
}


def validate_matched_outputs(
    matched: Dict[str, Dict[str, Any]],
    *,
    schema_version: str = "",
) -> None:
    """按 artifact key 与 schema_version 做字段级校验。"""
    version_validator = SCHEMA_VERSION_VALIDATORS.get(schema_version)
    for artifact_key, body in matched.items():
        if not isinstance(body, dict):
            raise AgentRuntimeError(f"产物 {artifact_key} 必须是对象")
        key_validator = ARTIFACT_KEY_VALIDATORS.get(artifact_key)
        if key_validator:
            key_validator(body)
        elif version_validator:
            version_validator(body)
