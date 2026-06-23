# -*- coding: utf-8 -*-
"""独立 Agent 输出契约字段级校验。"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List

from apps.creation.agent_runtime.independent_service import AgentRuntimeError

Validator = Callable[[Dict[str, Any]], None]


def _require_dict(body: Dict[str, Any], label: str) -> None:
    if not isinstance(body, dict):
        raise AgentRuntimeError(f"{label} 必须是对象")


_TRUE_TOKENS = {"true", "1", "yes", "y", "pass", "passed", "是", "通过", "合格", "ok", "t"}
_FALSE_TOKENS = {"false", "0", "no", "n", "fail", "failed", "否", "未通过", "不通过", "不合格", "f"}


def _coerce_bool(value: Any):
    """容忍真实 LLM 返回的布尔近似值（字符串/数字），无法识别返回 None。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        token = value.strip().lower()
        if token in _TRUE_TOKENS:
            return True
        if token in _FALSE_TOKENS:
            return False
    return None


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


def _derive_review_passed(body: Dict[str, Any]):
    """从 passed 或真实 LLM 常用替代字段推导审查是否通过。"""
    passed = _coerce_bool(body.get("passed"))
    if passed is not None:
        return passed
    for alt in (
        "reviewResult",
        "result",
        "overallResult",
        "overallStatus",
        "status",
        "verdict",
        "pass",
        "isPassed",
    ):
        passed = _coerce_bool(body.get(alt))
        if passed is not None:
            return passed
    for items_key in ("reviewItems", "checkItems", "items", "issues"):
        items = body.get(items_key)
        if not isinstance(items, list) or not items:
            continue
        statuses = []
        for item in items:
            if not isinstance(item, dict):
                continue
            for status_key in ("status", "result", "passed"):
                if status_key in item:
                    coerced = _coerce_bool(item.get(status_key))
                    if coerced is not None:
                        statuses.append(coerced)
                    break
        if statuses:
            return all(statuses)
    return None


def _validate_review_report(body: Dict[str, Any]) -> None:
    _require_dict(body, "review_report")
    passed = _derive_review_passed(body)
    if passed is None:
        raise AgentRuntimeError("review_report.passed 必须为布尔值")
    body["passed"] = passed
    if "pacingPassed" in body:
        pacing = _coerce_bool(body.get("pacingPassed"))
        if pacing is not None:
            body["pacingPassed"] = pacing


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


_NARRATIVE_PLAN_TOP_LEVEL_ALIASES: Dict[str, str] = {
    "narrative_core": "narrative_core_objective",
    "episode_narratives": "episode_narrative_designs",
    "opening_package_verification": "narrative_consistency_check",
}

_NARRATIVE_PLAN_EPISODE_ALIASES: Dict[str, str] = {
    "key_beat_chain": "narrative_beat_timing",
    "emotion_delivery": "audience_emotion_design",
}

_NARRATIVE_PLAN_FORBIDDEN_KEYS = frozenset(
    set(_NARRATIVE_PLAN_TOP_LEVEL_ALIASES) | set(_NARRATIVE_PLAN_EPISODE_ALIASES) | {"rhythm_control"}
)


def _rename_alias_fields(target: Dict[str, Any], aliases: Dict[str, str]) -> None:
    for old_key, new_key in aliases.items():
        if old_key not in target:
            continue
        if new_key not in target:
            target[new_key] = target.pop(old_key)
        else:
            target.pop(old_key)


def _coerce_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item or "").strip()]
    text = str(value or "").strip()
    if not text:
        return []
    if "；" in text or ";" in text:
        parts = re.split(r"[；;]+", text)
        return [part.strip() for part in parts if part.strip()]
    return [text]


def _coerce_narrative_mechanics(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: List[Dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            mechanism_type = str(item.get("mechanism_type") or "").strip()
            implementation = str(item.get("implementation_details") or "").strip()
            if mechanism_type or implementation:
                result.append(
                    {
                        "mechanism_type": mechanism_type or "叙事机制",
                        "implementation_details": implementation,
                    }
                )
            continue
        text = str(item or "").strip()
        if not text:
            continue
        if "：" in text:
            title, _, body = text.partition("：")
            result.append({"mechanism_type": title.strip(), "implementation_details": body.strip()})
        elif ":" in text:
            title, _, body = text.partition(":")
            result.append({"mechanism_type": title.strip(), "implementation_details": body.strip()})
        else:
            result.append({"mechanism_type": "叙事机制", "implementation_details": text})
    return result


def normalize_narrative_plan(body: Dict[str, Any]) -> Dict[str, Any]:
    """将 LLM 常见别名字段归一化为 narrative-plan.v1 契约字段（原地修改）。"""
    _rename_alias_fields(body, _NARRATIVE_PLAN_TOP_LEVEL_ALIASES)
    mechanics = body.get("narrative_mechanics")
    if mechanics is not None:
        body["narrative_mechanics"] = _coerce_narrative_mechanics(mechanics)
    designs = body.get("episode_narrative_designs")
    if not isinstance(designs, list):
        return body
    normalized_designs: List[Any] = []
    for item in designs:
        if not isinstance(item, dict):
            normalized_designs.append(item)
            continue
        episode = dict(item)
        _rename_alias_fields(episode, _NARRATIVE_PLAN_EPISODE_ALIASES)
        beat_timing = episode.get("narrative_beat_timing")
        if beat_timing is not None:
            episode["narrative_beat_timing"] = _coerce_string_list(beat_timing)
        rhythm = str(episode.pop("rhythm_control", "") or "").strip()
        if rhythm:
            techniques = episode.get("key_narrative_techniques")
            if not isinstance(techniques, list):
                techniques = [str(techniques)] if techniques else []
            if rhythm not in techniques:
                techniques.insert(0, rhythm)
            episode["key_narrative_techniques"] = techniques
        normalized_designs.append(episode)
    body["episode_narrative_designs"] = normalized_designs
    return body


def _validate_narrative_plan(body: Dict[str, Any]) -> None:
    _require_dict(body, "narrative_plan")
    normalize_narrative_plan(body)
    forbidden = sorted(key for key in body if key in _NARRATIVE_PLAN_FORBIDDEN_KEYS)
    if forbidden:
        raise AgentRuntimeError(
            "narrative_plan 使用了非契约字段 "
            f"{forbidden}，请改用 narrative_core_objective / episode_narrative_designs / "
            "narrative_beat_timing / audience_emotion_design 等标准字段"
        )
    if not str(body.get("narrative_core_objective") or "").strip():
        raise AgentRuntimeError("narrative_plan.narrative_core_objective 必填")
    designs = body.get("episode_narrative_designs")
    if not isinstance(designs, list) or not designs:
        raise AgentRuntimeError("narrative_plan.episode_narrative_designs 必须为非空数组")
    for index, item in enumerate(designs):
        if not isinstance(item, dict):
            raise AgentRuntimeError(f"narrative_plan.episode_narrative_designs[{index}] 必须是对象")
        if not str(item.get("episode_id") or "").strip():
            raise AgentRuntimeError(
                f"narrative_plan.episode_narrative_designs[{index}].episode_id 必填"
            )
        if not str(item.get("narrative_focus") or "").strip():
            raise AgentRuntimeError(
                f"narrative_plan.episode_narrative_designs[{index}].narrative_focus 必填"
            )


ARTIFACT_KEY_VALIDATORS: Dict[str, Validator] = {
    "episode_scripts": _validate_episode_scripts,
    "review_report": _validate_review_report,
    "script_score_report": _validate_script_score_report,
    "marketing_kit": _validate_marketing_kit,
    "insight_report": _validate_insight_report,
    "polish_log": _validate_polish_log,
    "narrative_plan": _validate_narrative_plan,
}

SCHEMA_VERSION_VALIDATORS: Dict[str, Validator] = {
    "episode-scripts.v1": _validate_episode_scripts,
    "review-report.v1": _validate_review_report,
    "script-score-report.v1": _validate_script_score_report,
    "marketing-kit.v1": _validate_marketing_kit,
    "insight-report.v1": _validate_insight_report,
    "polish-log.v1": _validate_polish_log,
    "narrative-plan.v1": _validate_narrative_plan,
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
