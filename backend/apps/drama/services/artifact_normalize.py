# -*- coding: utf-8 -*-
"""将 LLM 松散输出对齐到产物 schema（结构字段由 settings/合成器补全）。"""
from __future__ import annotations

from typing import Any

from apps.drama.services.matrix_synthesis import synthesize_rule_params

_PROJECT_BRIEF_KEYS = frozenset(
    {
        "title",
        "genre_matrix",
        "theme_code",
        "matrix_key",
        "rule_params",
        "preset_theme_code",
        "episode_count",
        "episode_duration",
        "core_idea",
        "target_audience",
        "core_conflict",
        "hook_concept",
        "commercial_hook",
        "reference_works",
        "compliance_risk",
        "market_opportunity",
        "blockbuster_factors",
        "competitor_references",
        "differentiation_strategy",
        "first_episode_hook",
        "paywall_direction",
    }
)

_RISK_RANK = {"low": 0, "medium": 1, "high": 2}


def normalize_artifact(
    artifact_key: str,
    payload: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    """按产物类型做契约对齐；未知类型原样返回。"""
    if artifact_key == "project_brief":
        return normalize_project_brief(payload, settings)
    if artifact_key == "story_bible":
        return normalize_story_bible(payload, settings)
    if artifact_key == "narrative_plan":
        return normalize_narrative_plan(payload, settings)
    if artifact_key == "quality_report":
        return normalize_quality_report(payload, settings)
    if artifact_key == "compliance_report":
        return normalize_compliance_report(payload, settings)
    return payload


def normalize_narrative_plan(
    raw: dict[str, Any],
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """对齐 narrative_plan：补全分集必填字段与别名，裁掉 schema 外键。"""
    settings = settings or {}
    designs_raw = raw.get("episode_narrative_designs")
    if not isinstance(designs_raw, list):
        # 兼容模型直接返回数组
        designs_raw = raw.get("episodes") if isinstance(raw.get("episodes"), list) else []

    designs: list[dict[str, Any]] = []
    for idx, item in enumerate(designs_raw):
        if not isinstance(item, dict):
            continue
        designs.append(_normalize_episode_design(item, idx=idx, settings=settings))

    if not designs:
        designs.append(
            _normalize_episode_design(
                {
                    "episode": 1,
                    "title": "第1集",
                    "core_event": "待补充本集核心事件",
                },
                idx=0,
                settings=settings,
            )
        )

    return {"episode_narrative_designs": designs}


def _normalize_episode_design(
    item: dict[str, Any],
    *,
    idx: int,
    settings: dict[str, Any],
) -> dict[str, Any]:
    episode_no = item.get("episode")
    if not isinstance(episode_no, int) or episode_no < 1:
        try:
            episode_no = int(episode_no)
        except (TypeError, ValueError):
            episode_no = idx + 1
        if episode_no < 1:
            episode_no = idx + 1

    core_event = (
        _as_nonempty_str(item.get("core_event"))
        or _as_nonempty_str(item.get("event"))
        or _as_nonempty_str(item.get("summary"))
        or "待补充本集核心事件"
    )
    title = (
        _as_nonempty_str(item.get("title"))
        or _as_nonempty_str(item.get("episode_title"))
        or f"第{episode_no}集"
    )
    opening_hook = (
        _as_nonempty_str(item.get("opening_hook"))
        or _as_nonempty_str(item.get("open_hook"))
        or _as_nonempty_str(item.get("opening"))
        or _as_nonempty_str(item.get("cold_open"))
        or _as_nonempty_str(item.get("start_hook"))
        or _as_nonempty_str(item.get("hook_open"))
        or f"开场切入：{core_event}"
    )
    ending_hook = (
        _as_nonempty_str(item.get("ending_hook"))
        or _as_nonempty_str(item.get("end_hook"))
        or _as_nonempty_str(item.get("ending"))
        or _as_nonempty_str(item.get("cliffhanger"))
        or _as_nonempty_str(item.get("hook_end"))
        or _as_nonempty_str(item.get("closing_hook"))
        or _pick_string_hook(item.get("hook"))
        or f"集末悬念：{core_event}"
    )

    intensity = item.get("emotion_intensity")
    try:
        intensity_int = int(intensity)
    except (TypeError, ValueError):
        intensity_int = 6
    intensity_int = max(1, min(10, intensity_int))

    hook_grade = str(item.get("hook_grade") or "B").strip().upper()
    if hook_grade not in {"S", "A", "B", "C"}:
        hook_grade = "B"

    foreshadowing = _normalize_foreshadowing(item.get("foreshadowing"))
    emotion_nodes = _normalize_emotion_nodes(item.get("emotion_nodes"), core_event)

    return {
        "episode": episode_no,
        "title": title,
        "core_event": core_event,
        "goal_conflict": (
            _as_nonempty_str(item.get("goal_conflict"))
            or _as_nonempty_str(item.get("conflict"))
            or "待补充目标与冲突"
        ),
        "emotion_intensity": intensity_int,
        "opening_hook": opening_hook,
        "ending_hook": ending_hook,
        "satisfaction_points": _as_str_list(
            item.get("satisfaction_points"),
            fallback=["待补充爽点"],
        ),
        "reversal": (
            _as_nonempty_str(item.get("reversal"))
            or _as_nonempty_str(item.get("twist"))
            or "待补充反转"
        ),
        "paywall_hook": (
            _as_nonempty_str(item.get("paywall_hook"))
            or _as_nonempty_str(item.get("paywall"))
            or ending_hook
        ),
        "rhythm_tag": (
            _as_nonempty_str(item.get("rhythm_tag"))
            or _as_nonempty_str(item.get("rhythm"))
            or "standard"
        ),
        "foreshadowing": foreshadowing,
        "hook_grade": hook_grade,
        "characters": _as_str_list(
            item.get("characters"),
            fallback=[_as_nonempty_str(settings.get("title")) or "主角"],
        ),
        "emotion_nodes": emotion_nodes,
    }


def _pick_string_hook(value: Any) -> str | None:
    if isinstance(value, str):
        return _as_nonempty_str(value)
    if isinstance(value, dict):
        return (
            _as_nonempty_str(value.get("ending"))
            or _as_nonempty_str(value.get("end"))
            or _as_nonempty_str(value.get("text"))
            or _as_nonempty_str(value.get("content"))
        )
    return None


def _normalize_foreshadowing(value: Any) -> dict[str, list[str]]:
    if isinstance(value, dict):
        setup = _as_str_list(value.get("setup"), fallback=[])
        payoff = _as_str_list(value.get("payoff"), fallback=[])
        return {"setup": setup, "payoff": payoff}
    if isinstance(value, list):
        return {"setup": _as_str_list(value, fallback=[]), "payoff": []}
    text = _as_nonempty_str(value)
    if text:
        return {"setup": [text], "payoff": []}
    return {"setup": [], "payoff": []}


def _normalize_emotion_nodes(value: Any, core_event: str) -> dict[str, Any]:
    src = value if isinstance(value, dict) else {}
    ev = src.get("EV") if isinstance(src.get("EV"), dict) else {"value": 5}
    et = src.get("ET") if isinstance(src.get("ET"), dict) else {"value": 5}
    tp = src.get("TP") if isinstance(src.get("TP"), dict) else {"content": core_event}
    if not tp:
        tp = {"content": core_event}
    return {"EV": ev, "ET": et, "TP": tp}


def normalize_story_bible(
    raw: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    """对齐 story_bible：补全 synopsis.short/full，裁掉 schema 外字段。"""
    title = (
        _as_nonempty_str(raw.get("drama_title"))
        or _as_nonempty_str(raw.get("title"))
        or _as_nonempty_str(settings.get("title"))
        or "未命名短剧"
    )
    logline = (
        _as_nonempty_str(raw.get("logline"))
        or _as_nonempty_str(settings.get("core_idea"))
        or "待补充一句话故事"
    )

    out: dict[str, Any] = {
        "drama_title": title,
        "logline": logline,
        "synopsis": _normalize_synopsis(raw, logline),
        "adapt_source": _normalize_adapt_source(raw, settings),
        "world_rules": _normalize_world_rules(raw.get("world_rules")),
        "characters": _normalize_characters(raw.get("characters")),
        "relationship_map": _as_object_list(raw.get("relationship_map")),
        "series_structure": _normalize_series_structure(raw.get("series_structure")),
    }
    return out


def _normalize_synopsis(raw: dict[str, Any], logline: str) -> dict[str, str]:
    syn = raw.get("synopsis")
    if isinstance(syn, str):
        text = syn.strip() or logline
        return {"short": _clip_text(text, 300), "full": text}
    if isinstance(syn, dict):
        short = (
            _as_nonempty_str(syn.get("short"))
            or _as_nonempty_str(syn.get("summary"))
            or _as_nonempty_str(syn.get("brief"))
            or _as_nonempty_str(syn.get("one_liner"))
        )
        full = (
            _as_nonempty_str(syn.get("full"))
            or _as_nonempty_str(syn.get("long"))
            or _as_nonempty_str(syn.get("complete"))
            or _as_nonempty_str(syn.get("text"))
        )
        if not short and full:
            short = _clip_text(full, 300)
        if not full and short:
            full = short
        if not short:
            short = logline
        if not full:
            full = logline
        return {"short": short, "full": full}
    return {"short": logline, "full": logline}


def _normalize_adapt_source(
    raw: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    src = raw.get("adapt_source") if isinstance(raw.get("adapt_source"), dict) else {}
    entry = str(settings.get("entry_type") or "original_track")
    default_mode = "adapt" if entry == "story_adapt" else "original"
    mode = src.get("mode") if src.get("mode") in ("original", "adapt") else default_mode
    out: dict[str, Any] = {"mode": mode}
    for key in ("retained", "enhanced", "rewritten"):
        value = src.get(key)
        if isinstance(value, list):
            out[key] = [str(item) for item in value if item is not None]
    check = _as_nonempty_str(src.get("originality_check"))
    if check:
        out["originality_check"] = check
    return out


def _normalize_world_rules(value: Any) -> dict[str, Any]:
    src = value if isinstance(value, dict) else {}
    root_rules = _normalize_root_rules(src.get("root_rules"))
    return {
        "setting_summary": (
            _as_nonempty_str(src.get("setting_summary")) or "待补充时空背景"
        ),
        "root_rules": root_rules or ["待补充世界根规则"],
        "power_structure": _normalize_power_structure(src.get("power_structure")),
    }


def _normalize_root_rules(value: Any) -> list[str]:
    """root_rules schema 为 string[]；兼容 LLM 输出的规则对象。"""
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            text = _format_root_rule_item(item)
            if text:
                result.append(text)
        return result
    text = _as_nonempty_str(value)
    return [text] if text else []


def _format_root_rule_item(item: Any) -> str | None:
    if isinstance(item, dict):
        rule = _as_nonempty_str(item.get("rule")) or _as_nonempty_str(item.get("name"))
        if not rule:
            return None
        parts = [rule]
        trigger = _as_nonempty_str(item.get("trigger"))
        cost = _as_nonempty_str(item.get("violation_cost"))
        applicable = _as_nonempty_str(item.get("applicable_to"))
        visible = _as_nonempty_str(item.get("visible_manifestation"))
        if trigger:
            parts.append(f"触发：{trigger}")
        if applicable:
            parts.append(f"适用：{applicable}")
        if cost:
            parts.append(f"代价：{cost}")
        if visible:
            parts.append(f"外显：{visible}")
        return "｜".join(parts)
    return _as_nonempty_str(item)


def _normalize_power_structure(value: Any) -> str:
    """power_structure schema 为 string；兼容 description + key_actors 对象。"""
    if isinstance(value, dict):
        chunks: list[str] = []
        desc = _as_nonempty_str(value.get("description")) or _as_nonempty_str(
            value.get("summary")
        )
        if desc:
            chunks.append(desc)
        actors = value.get("key_actors")
        if isinstance(actors, list) and actors:
            actor_lines: list[str] = []
            for actor in actors:
                if not isinstance(actor, dict):
                    text = _as_nonempty_str(actor)
                    if text:
                        actor_lines.append(text)
                    continue
                name = _as_nonempty_str(actor.get("name")) or "未命名"
                position = _as_nonempty_str(actor.get("position"))
                resources = _as_nonempty_str(actor.get("resources"))
                motivation = _as_nonempty_str(actor.get("motivation"))
                detail = name
                extras = [
                    part
                    for part in (position, resources and f"资源：{resources}", motivation and f"动机：{motivation}")
                    if part
                ]
                if extras:
                    detail = f"{name}（{'；'.join(extras)}）"
                actor_lines.append(detail)
            if actor_lines:
                chunks.append("关键人物：" + "；".join(actor_lines))
        if chunks:
            return "\n".join(chunks)
        return "待补充权力结构"
    return _as_nonempty_str(value) or "待补充权力结构"


_ROLE_TYPE_ALIASES = {
    "protagonist": "protagonist",
    "hero": "protagonist",
    "main": "protagonist",
    "lead": "protagonist",
    "主角": "protagonist",
    "antagonist": "antagonist",
    "villain": "antagonist",
    "反派": "antagonist",
    "supporting": "supporting",
    "support": "supporting",
    "配角": "supporting",
}


def _normalize_characters(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        return [
            {
                "name": "主角",
                "role_type": "protagonist",
                "surface_desire": "待补充",
                "deep_need": "待补充",
                "ghost": "待补充",
                "lie": "待补充",
                "flaw": "待补充",
                "arc": {
                    "start": "待补充",
                    "turning_point_1": "待补充",
                    "turning_point_2": "待补充",
                    "end": "待补充",
                },
                "voice_tag": "待补充",
                "visual_anchor": "待补充",
            }
        ]
    result: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        role_raw = str(item.get("role_type") or "supporting").strip().lower()
        role_type = _ROLE_TYPE_ALIASES.get(role_raw, "supporting")
        arc_src = item.get("arc") if isinstance(item.get("arc"), dict) else {}
        char: dict[str, Any] = {
            "name": _as_nonempty_str(item.get("name")) or "未命名角色",
            "role_type": role_type,
            "surface_desire": (
                _as_nonempty_str(item.get("surface_desire"))
                or _as_nonempty_str(item.get("want"))
                or _as_nonempty_str(item.get("desire"))
                or "待补充"
            ),
            "deep_need": (
                _as_nonempty_str(item.get("deep_need"))
                or _as_nonempty_str(item.get("need"))
                or "待补充"
            ),
            "ghost": (
                _as_nonempty_str(item.get("ghost"))
                or _as_nonempty_str(item.get("wound"))
                or "待补充"
            ),
            "lie": _as_nonempty_str(item.get("lie")) or "待补充",
            "flaw": _as_nonempty_str(item.get("flaw")) or "待补充",
            "arc": {
                "start": (
                    _as_nonempty_str(arc_src.get("start"))
                    or _as_nonempty_str(arc_src.get("initial"))
                    or _as_nonempty_str(arc_src.get("beginning"))
                    or "待补充"
                ),
                "turning_point_1": (
                    _as_nonempty_str(arc_src.get("turning_point_1"))
                    or _as_nonempty_str(arc_src.get("midpoint"))
                    or _as_nonempty_str(arc_src.get("mid1"))
                    or "待补充"
                ),
                "turning_point_2": (
                    _as_nonempty_str(arc_src.get("turning_point_2"))
                    or _as_nonempty_str(arc_src.get("low_point"))
                    or _as_nonempty_str(arc_src.get("mid2"))
                    or "待补充"
                ),
                "end": (
                    _as_nonempty_str(arc_src.get("end"))
                    or _as_nonempty_str(arc_src.get("final"))
                    or _as_nonempty_str(arc_src.get("ending"))
                    or "待补充"
                ),
            },
            "voice_tag": _as_nonempty_str(item.get("voice_tag")) or "待补充",
            "visual_anchor": (
                _as_nonempty_str(item.get("visual_anchor")) or "待补充"
            ),
        }
        ident = (
            _as_nonempty_str(item.get("audience_identification"))
            or _as_nonempty_str(item.get("background"))
        )
        if ident:
            char["audience_identification"] = ident
        result.append(char)
    return result or _normalize_characters([])


def _normalize_series_structure(value: Any) -> dict[str, Any]:
    src = value if isinstance(value, dict) else {}
    stages = src.get("six_stage_structure")
    if not isinstance(stages, list):
        stages = []
    # 不足 6 段时用占位补齐，避免 schema minItems 失败
    while len(stages) < 6:
        idx = len(stages) + 1
        stages.append({"stage": idx, "name": f"阶段{idx}", "summary": "待补充"})
    stages = stages[:6]
    normalized_stages: list[dict[str, Any]] = []
    for item in stages:
        if isinstance(item, dict):
            normalized_stages.append(item)
        else:
            normalized_stages.append({"summary": str(item)})

    return {
        "main_storyline": (
            _as_nonempty_str(src.get("main_storyline")) or "待补充主线"
        ),
        "six_stage_structure": normalized_stages,
        "conflict_escalation_chain": _normalize_conflict_chain(
            src.get("conflict_escalation_chain")
        ),
        "major_reversal_positions": _as_object_list(
            src.get("major_reversal_positions")
        ),
        "paywall_distribution": _as_object_list(src.get("paywall_distribution")),
        "foreshadowing_table": _as_object_list(src.get("foreshadowing_table")),
        "series_emotion_curve": _normalize_emotion_curve(
            src.get("series_emotion_curve")
        ),
    }


def _normalize_conflict_chain(value: Any) -> list[str]:
    """conflict_escalation_chain schema 为 string[]；兼容阶段对象与已字符串化的 dict。"""
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            text = _format_conflict_item(item)
            if text:
                result.append(text)
        if result:
            return result
    if isinstance(value, dict):
        text = _format_conflict_item(value)
        return [text] if text else ["待补充冲突升级链"]
    return _as_str_list(value, fallback=["待补充冲突升级链"])


def _format_conflict_item(item: Any) -> str | None:
    parsed = item
    if isinstance(item, str):
        text = item.strip()
        if not text:
            return None
        # 兼容历史落库：str(dict) / JSON 字符串
        coerced = _coerce_mapping(text)
        if coerced is None:
            return text
        parsed = coerced
    if not isinstance(parsed, dict):
        return _as_nonempty_str(parsed)

    stage = parsed.get("stage")
    conflict_type = _as_nonempty_str(parsed.get("conflict_type")) or _as_nonempty_str(
        parsed.get("type")
    )
    description = _as_nonempty_str(parsed.get("description")) or _as_nonempty_str(
        parsed.get("summary")
    )
    head = f"第{stage}幕" if stage is not None and str(stage).strip() else None
    label = " · ".join(part for part in (head, conflict_type) if part)
    if label and description:
        return f"{label}：{description}"
    if description:
        return description
    if label:
        return label
    return None


def _coerce_mapping(text: str) -> dict[str, Any] | None:
    """把 JSON / Python dict 字符串尽量还原为 dict。"""
    import ast
    import json

    cleaned = text.strip()
    if not (cleaned.startswith("{") and cleaned.endswith("}")):
        return None
    try:
        loaded = json.loads(cleaned)
        return loaded if isinstance(loaded, dict) else None
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    try:
        loaded = ast.literal_eval(cleaned)
        return loaded if isinstance(loaded, dict) else None
    except (SyntaxError, ValueError):
        return None


def _normalize_emotion_curve(value: Any) -> list[dict[str, Any]]:
    """series_emotion_curve schema 为 object[]；兼容 {description,key_points}。"""
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        points = value.get("key_points")
        if isinstance(points, list):
            result = [item for item in points if isinstance(item, dict)]
            if result:
                desc = _as_nonempty_str(value.get("description"))
                if desc and not any(
                    _as_nonempty_str(item.get("description")) == desc for item in result
                ):
                    # 保留曲线总述，挂到首点，避免信息丢失
                    first = dict(result[0])
                    if not _as_nonempty_str(first.get("curve_summary")):
                        first["curve_summary"] = desc
                    result[0] = first
                return result
        # 整段对象当作单点保留可读字段
        if any(
            key in value
            for key in ("episode", "emotion", "event", "description", "summary")
        ):
            return [value]
    return []


def _as_str_list(value: Any, fallback: list[str] | None = None) -> list[str]:
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = (
                    _format_conflict_item(item)
                    or _as_nonempty_str(item.get("description"))
                    or _as_nonempty_str(item.get("summary"))
                    or _as_nonempty_str(item.get("name"))
                )
                if text:
                    items.append(text)
                continue
            if isinstance(item, str):
                coerced = _coerce_mapping(item)
                if coerced is not None:
                    text = _format_conflict_item(coerced)
                    if text:
                        items.append(text)
                        continue
            text = _as_nonempty_str(item)
            if text:
                items.append(text)
        if items:
            return items
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return list(fallback or [])


def _as_object_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _clip_text(text: str, max_len: int) -> str:
    cleaned = text.strip()
    if len(cleaned) <= max_len:
        return cleaned
    return f"{cleaned[: max_len - 1]}…"


def normalize_project_brief(
    raw: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    """补全矩阵结构字段，并裁掉 schema 不允许的额外键。"""
    settings_matrix = dict(settings.get("genre_matrix") or {})
    raw_matrix = raw.get("genre_matrix") if isinstance(raw.get("genre_matrix"), dict) else {}

    genre_matrix: dict[str, Any] = {
        "emotion": raw_matrix.get("emotion") or settings_matrix.get("emotion"),
        "identity": raw_matrix.get("identity") or settings_matrix.get("identity"),
        "conflict": raw_matrix.get("conflict") or settings_matrix.get("conflict"),
        "world": raw_matrix.get("world") or settings_matrix.get("world"),
        "audience_channel": (
            raw_matrix.get("audience_channel")
            or raw.get("audience_channel")
            or settings.get("audience_channel")
            or "general"
        ),
    }
    structure = (
        raw_matrix.get("protagonist_structure")
        or raw.get("protagonist_structure")
        or settings.get("protagonist_structure")
    )
    if structure:
        genre_matrix["protagonist_structure"] = structure
    tags: list[Any]
    if "flavor_tags" in raw_matrix:
        tags = list(raw_matrix.get("flavor_tags") or [])
    elif "flavor_tags" in raw:
        tags = list(raw.get("flavor_tags") or [])
    else:
        tags = list(settings.get("flavor_tags") or [])
    if isinstance(tags, str):
        tags = [tags]
    if tags:
        genre_matrix["flavor_tags"] = list(tags)[:5]
    elif "flavor_tags" in raw_matrix or "flavor_tags" in raw:
        genre_matrix["flavor_tags"] = []

    synthesized = synthesize_rule_params(genre_matrix)
    # rule_params 由题材矩阵合成；模型常输出 high/对象结构等非法值，一律不采信
    rule_params = {
        "reversal_density": synthesized["reversal_density"],
        "emotion_curve": synthesized["emotion_curve"],
        "act_ratio": synthesized["act_ratio"],
        "hook_types": synthesized["hook_types"],
    }

    derived = settings.get("derived") if isinstance(settings.get("derived"), dict) else {}
    matrix_key = (
        raw.get("matrix_key")
        or derived.get("matrix_key")
        or synthesized.get("matrix_key")
    )

    core_idea = (
        _as_nonempty_str(raw.get("core_idea"))
        or _as_nonempty_str(settings.get("core_idea"))
        or _as_nonempty_str(raw.get("synopsis"))
        or _as_nonempty_str(raw.get("one_line_theme"))
        or "待补充核心创意"
    )

    out: dict[str, Any] = {
        "title": (
            _as_nonempty_str(raw.get("title"))
            or _as_nonempty_str(settings.get("title"))
            or "未命名短剧"
        ),
        "genre_matrix": genre_matrix,
        "theme_code": "matrix",
        "matrix_key": matrix_key,
        "rule_params": rule_params,
        "preset_theme_code": settings.get("preset_theme_code"),
        "episode_count": int(
            raw.get("episode_count") or settings.get("episode_count") or 1
        ),
        "episode_duration": raw.get("episode_duration"),
        "core_idea": core_idea,
        "target_audience": (
            _as_nonempty_str(raw.get("target_audience")) or "待补充目标受众"
        ),
        "core_conflict": (
            _as_nonempty_str(raw.get("core_conflict")) or "待补充核心冲突"
        ),
        "hook_concept": (
            _as_nonempty_str(raw.get("hook_concept"))
            or _as_nonempty_str(raw.get("one_line_theme"))
            or "待补充钩子概念"
        ),
        "compliance_risk": _resolve_compliance_risk(raw),
    }

    commercial = _as_nonempty_str(raw.get("commercial_hook")) or _as_nonempty_str(
        raw.get("one_line_theme")
    )
    if commercial:
        out["commercial_hook"] = commercial

    refs = raw.get("reference_works")
    if isinstance(refs, list):
        out["reference_works"] = [str(item) for item in refs if item is not None]

    market = _as_nonempty_str(raw.get("market_opportunity"))
    if market:
        out["market_opportunity"] = market

    factors = _normalize_blockbuster_factors(raw.get("blockbuster_factors"))
    if factors is not None:
        out["blockbuster_factors"] = factors

    competitors = raw.get("competitor_references")
    if isinstance(competitors, list):
        out["competitor_references"] = [
            item for item in competitors if isinstance(item, dict)
        ]

    for key in (
        "differentiation_strategy",
        "first_episode_hook",
        "paywall_direction",
    ):
        value = _as_nonempty_str(raw.get(key))
        if value:
            out[key] = value

    return {key: value for key, value in out.items() if key in _PROJECT_BRIEF_KEYS}


def _as_nonempty_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_blockbuster_factors(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
        elif isinstance(item, dict):
            label = (
                _as_nonempty_str(item.get("factor"))
                or _as_nonempty_str(item.get("description"))
                or _as_nonempty_str(item.get("name"))
            )
            if label:
                result.append(label)
    return result


def _resolve_compliance_risk(raw: dict[str, Any]) -> str:
    direct = raw.get("compliance_risk")
    if direct in _RISK_RANK:
        return str(direct)
    best = "low"
    for item in raw.get("sensitivity_pre_check") or []:
        if not isinstance(item, dict):
            continue
        level = item.get("level")
        if level in _RISK_RANK and _RISK_RANK[level] > _RISK_RANK[best]:
            best = str(level)
    return best


_QUALITY_DIMENSION_KEYS = (
    "format",
    "narrative",
    "conflict",
    "character",
    "emotion",
    "logic",
    "satisfaction",
    "hooks",
    "paywall",
    "genre_fit",
)

_QUALITY_DIMENSION_WEIGHTS: dict[str, float] = {
    "format": 0.10,
    "narrative": 0.15,
    "conflict": 0.15,
    "character": 0.10,
    "emotion": 0.10,
    "logic": 0.10,
    "satisfaction": 0.10,
    "hooks": 0.10,
    "paywall": 0.05,
    "genre_fit": 0.05,
}

_QUALITY_DIMENSION_NAME_ALIASES: dict[str, str] = {
    "格式规范": "format",
    "格式": "format",
    "format": "format",
    "叙事效率": "narrative",
    "叙事": "narrative",
    "narrative": "narrative",
    "冲突处理": "conflict",
    "冲突": "conflict",
    "conflict": "conflict",
    "角色一致性": "character",
    "角色": "character",
    "character": "character",
    "情感深度": "emotion",
    "情感": "emotion",
    "emotion": "emotion",
    "逻辑一致性": "logic",
    "逻辑": "logic",
    "logic": "logic",
    "爽点密度": "satisfaction",
    "爽点": "satisfaction",
    "satisfaction": "satisfaction",
    "钩子强度": "hooks",
    "钩子": "hooks",
    "hooks": "hooks",
    "付费点优化": "paywall",
    "付费点": "paywall",
    "paywall": "paywall",
    "赛道匹配": "genre_fit",
    "赛道": "genre_fit",
    "genre_fit": "genre_fit",
}


def normalize_quality_report(
    raw: dict[str, Any],
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """对齐 quality_report：dimensions 数组→对象，字段别名与缺省补齐。"""
    settings = settings or {}
    title = (
        _as_nonempty_str(raw.get("drama_title"))
        or _as_nonempty_str(raw.get("title"))
        or _as_nonempty_str(settings.get("title"))
        or "未命名短剧"
    )
    overall = _as_number(raw.get("overall_score"), default=0.0)
    dimensions = _normalize_quality_dimensions(raw.get("dimensions"), overall)
    overall = _rescale_overall_if_ten_point(overall, dimensions)
    needs_revision = raw.get("needs_revision")
    if not isinstance(needs_revision, bool):
        needs_revision = overall < 75
    can_continue = raw.get("can_continue_next_batch")
    if not isinstance(can_continue, bool):
        can_continue = not needs_revision
    verdict = _normalize_quality_verdict(raw.get("verdict"), overall, needs_revision)
    verdict, needs_revision, can_continue = _reconcile_quality_verdict(
        verdict, overall, needs_revision, can_continue
    )
    grade = _as_nonempty_str(raw.get("grade"))
    if grade not in {"S", "A", "B", "C", "D"}:
        grade = _grade_from_score(overall)

    scoring_preset = _as_nonempty_str(raw.get("scoring_preset")) or "standard"
    if scoring_preset not in {"standard", "strict", "relaxed", "rhythm_first"}:
        scoring_preset = "standard"

    resolved = _as_nonempty_str(raw.get("resolved_script_key")) or "external_script"
    if resolved not in {"polished_script", "episode_scripts", "external_script"}:
        resolved = "external_script"

    continuity = raw.get("continuity_summary")
    if not isinstance(continuity, dict):
        continuity = {"result": "pass", "issues": []}
    else:
        result = _as_nonempty_str(continuity.get("result")) or "pass"
        if result not in {"pass", "warning", "fail"}:
            lower = result.lower()
            if lower in {"pass", "passed", "ok"}:
                result = "pass"
            elif lower in {"warn", "warning"}:
                result = "warning"
            else:
                result = "fail"
        continuity = {
            "result": result,
            "issues": continuity.get("issues")
            if isinstance(continuity.get("issues"), list)
            else [],
        }

    out: dict[str, Any] = {
        "drama_title": title,
        "scored_artifact": "latest_script",
        "resolved_script_key": resolved,
        "scoring_preset": scoring_preset,
        "pass_threshold": _as_number(raw.get("pass_threshold"), default=75.0),
        "overall_score": overall,
        "grade": grade,
        "can_continue_next_batch": can_continue,
        "needs_revision": needs_revision,
        "dimensions": dimensions,
        "defects": raw.get("defects") if isinstance(raw.get("defects"), list) else [],
        "continuity_summary": continuity,
        "revision_priorities": (
            raw.get("revision_priorities")
            if isinstance(raw.get("revision_priorities"), list)
            else []
        ),
        "verdict": verdict,
    }
    if raw.get("config_revision") is not None:
        out["config_revision"] = str(raw.get("config_revision"))
    if "evolution_proposal" in raw:
        out["evolution_proposal"] = raw.get("evolution_proposal")
    return out


def _normalize_quality_verdict(value: Any, overall: float, needs_revision: bool) -> str:
    allowed = {"通过", "条件通过", "需要修改", "重大返工"}
    text = _as_nonempty_str(value)
    if text in allowed:
        return text
    aliases = {
        "pass": "通过",
        "passed": "通过",
        "ok": "通过",
        "条件通过": "条件通过",
        "需要修改": "需要修改",
        "建议修订": "需要修改",
        "修订": "需要修改",
        "重大返工": "重大返工",
        "fail": "重大返工",
        "failed": "重大返工",
    }
    if text:
        mapped = aliases.get(text) or aliases.get(text.lower())
        if mapped in allowed:
            return mapped
    if overall < 40:
        return "重大返工"
    if needs_revision or overall < 75:
        return "需要修改"
    if overall < 80:
        return "条件通过"
    return "通过"


def normalize_compliance_report(
    raw: dict[str, Any],
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """对齐 compliance_report：枚举与缺省字段补齐。"""
    settings = settings or {}
    title = (
        _as_nonempty_str(raw.get("drama_title"))
        or _as_nonempty_str(raw.get("title"))
        or _as_nonempty_str(settings.get("title"))
        or "未命名短剧"
    )
    check_mode = _as_nonempty_str(raw.get("check_mode")) or "standard"
    if check_mode not in {"standard", "values-risk", "full"}:
        check_mode = "standard"
    platform = _as_nonempty_str(raw.get("target_platform")) or "generic"
    if platform not in {"generic", "douyin", "kuaishou", "wechat_miniprogram"}:
        platform = "generic"
    resolved = _as_nonempty_str(raw.get("resolved_script_key")) or "external_script"
    if resolved not in {"polished_script", "episode_scripts", "external_script"}:
        resolved = "external_script"

    overall = _as_nonempty_str(raw.get("overall_result"))
    if overall not in {"通过", "风险", "不通过"}:
        # 兼容英文/同义词
        lower = (overall or "").lower()
        if lower in {"pass", "passed", "ok", "safe"}:
            overall = "通过"
        elif lower in {"risk", "warning", "warn"}:
            overall = "风险"
        elif lower in {"fail", "failed", "block", "blocked"}:
            overall = "不通过"
        else:
            blocking = raw.get("blocking_issues")
            overall = "不通过" if isinstance(blocking, list) and blocking else "通过"

    risk_items = _normalize_compliance_risk_items(raw.get("risk_items"))
    blocking = _normalize_blocking_issues(raw.get("blocking_issues"))

    return {
        "drama_title": title,
        "check_mode": check_mode,
        "target_platform": platform,
        "platform_policy_version": raw.get("platform_policy_version"),
        "platform_policy_verified_at": raw.get("platform_policy_verified_at"),
        "checked_artifact": "latest_script",
        "resolved_script_key": resolved,
        "overall_result": overall,
        "blocking_issues": blocking,
        "risk_items": risk_items,
    }


def _normalize_quality_dimensions(value: Any, overall: float) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            dim_key = _QUALITY_DIMENSION_NAME_ALIASES.get(str(key).strip(), str(key).strip())
            if dim_key in _QUALITY_DIMENSION_KEYS:
                mapped[dim_key] = _normalize_score_dimension(item, dim_key, overall)
    elif isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            name = (
                _as_nonempty_str(item.get("key"))
                or _as_nonempty_str(item.get("name"))
                or _as_nonempty_str(item.get("dimension"))
                or ""
            )
            dim_key = _QUALITY_DIMENSION_NAME_ALIASES.get(name, name)
            if dim_key in _QUALITY_DIMENSION_KEYS:
                mapped[dim_key] = _normalize_score_dimension(item, dim_key, overall)

    for key in _QUALITY_DIMENSION_KEYS:
        if key not in mapped:
            mapped[key] = {
                "score": overall,
                "weight": _QUALITY_DIMENSION_WEIGHTS[key],
                "evidence": [],
                "deductions": [],
            }
    return mapped


def _normalize_score_dimension(
    value: Any,
    key: str,
    overall: float,
) -> dict[str, Any]:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return {
            "score": float(value),
            "weight": _QUALITY_DIMENSION_WEIGHTS[key],
            "evidence": [],
            "deductions": [],
        }
    if not isinstance(value, dict):
        return {
            "score": overall,
            "weight": _QUALITY_DIMENSION_WEIGHTS[key],
            "evidence": [],
            "deductions": [],
        }

    evidence = _coerce_text_list(value.get("evidence"))
    for alt_key in ("comment", "analysis", "summary", "reason", "notes"):
        if evidence:
            break
        evidence = _coerce_text_list(value.get(alt_key))

    deductions = _coerce_text_list(value.get("deductions"))
    if not deductions:
        deductions = _coerce_text_list(
            value.get("deduction_reasons") or value.get("reasons")
        )

    weight = _as_number(value.get("weight"), default=_QUALITY_DIMENSION_WEIGHTS[key])
    if weight < 0 or weight > 1:
        weight = _QUALITY_DIMENSION_WEIGHTS[key]

    return {
        "score": _as_number(value.get("score"), default=overall),
        "weight": weight,
        "evidence": evidence,
        "deductions": deductions,
    }


def _coerce_text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if item is None:
            continue
        if isinstance(item, str):
            text = item.strip()
            if text:
                result.append(text)
            continue
        if isinstance(item, dict):
            text = (
                _as_nonempty_str(item.get("text"))
                or _as_nonempty_str(item.get("quote"))
                or _as_nonempty_str(item.get("description"))
                or _as_nonempty_str(item.get("content"))
                or ""
            )
            if text:
                result.append(text)
            continue
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def _rescale_overall_if_ten_point(
    overall: float,
    dimensions: dict[str, Any],
) -> float:
    """纠正模型误用 1-10 分制：总分或各维偏小则放大到百分制。"""
    scores = [
        float(dim.get("score"))
        for dim in dimensions.values()
        if isinstance(dim, dict) and isinstance(dim.get("score"), (int, float))
    ]
    if not scores:
        return overall

    def _scale_dims() -> None:
        for dim in dimensions.values():
            if isinstance(dim, dict) and isinstance(dim.get("score"), (int, float)):
                raw = float(dim["score"])
                if raw <= 10:
                    dim["score"] = round(raw * 10, 1)

    # 总分与各维都是十分制
    if overall <= 10 and max(scores) <= 10:
        _scale_dims()
        return round(overall * 10, 1)
    # 总分已是百分制，但各维仍像十分制（如 overall=78、维分=8/7/9）
    if overall > 10 and max(scores) <= 10 and len(scores) >= 5:
        _scale_dims()
        return overall
    return overall


def _reconcile_quality_verdict(
    verdict: str,
    overall: float,
    needs_revision: bool,
    can_continue: bool,
) -> tuple[str, bool, bool]:
    """避免「高分 + 重大返工 + 可放行」这类互相矛盾的展示。"""
    if verdict in {"重大返工", "需要修改"}:
        if overall >= 80 and not needs_revision:
            return ("通过", False, True)
        return (verdict, True, False)
    if needs_revision:
        if verdict == "通过":
            verdict = "需要修改"
        return (verdict, True, False)
    if overall >= 80:
        return ("通过", False, True)
    if overall >= 75:
        return (verdict if verdict in {"通过", "条件通过"} else "条件通过", False, True)
    return (verdict, needs_revision, can_continue)


def quality_report_evidence_too_sparse(payload: dict[str, Any]) -> bool:
    """任一维度缺少有效 evidence → 视为空壳评分（禁止只吐分数）。"""
    dims = payload.get("dimensions")
    if not isinstance(dims, dict) or not dims:
        return True
    for dim in dims.values():
        if not isinstance(dim, dict):
            return True
        evidence = dim.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            return True
        if not any(isinstance(x, str) and len(x.strip()) >= 8 for x in evidence):
            return True
    return False


def compliance_report_too_thin(payload: dict[str, Any]) -> bool:
    result = str(payload.get("overall_result") or "")
    blocking = payload.get("blocking_issues")
    risks = payload.get("risk_items")
    if not isinstance(blocking, list):
        blocking = []
    if not isinstance(risks, list):
        risks = []
    if result == "不通过" and not blocking:
        return True
    for item in blocking:
        if not isinstance(item, dict):
            return True
        title = str(item.get("title") or "").strip()
        detail = str(item.get("description") or item.get("detail") or "").strip()
        if len(title) < 2 or len(detail) < 8:
            return True
    for item in risks:
        if not isinstance(item, dict):
            return True
        if len(str(item.get("description") or "").strip()) < 8:
            return True
        if len(str(item.get("suggestion") or "").strip()) < 8:
            return True
    return False


def _normalize_blocking_issues(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, str):
            text = item.strip()
            if text:
                result.append({"title": text[:40], "description": text})
            continue
        if not isinstance(item, dict):
            continue
        row = dict(item)
        title = (
            _as_nonempty_str(row.get("title"))
            or _as_nonempty_str(row.get("name"))
            or _as_nonempty_str(row.get("issue"))
            or _as_nonempty_str(row.get("rule_key"))
            or _as_nonempty_str(row.get("category"))
            or ""
        )
        detail = (
            _as_nonempty_str(row.get("description"))
            or _as_nonempty_str(row.get("detail"))
            or _as_nonempty_str(row.get("summary"))
            or ""
        )
        if not title:
            title = (detail[:32] + "…") if len(detail) > 32 else (detail or "合规问题")
        row["title"] = title
        if detail and not _as_nonempty_str(row.get("description")):
            row["description"] = detail
        result.append(row)
    return result


def _normalize_compliance_risk_items(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        risk_type = str(item.get("type") or "p2").lower()
        if risk_type not in {"p0", "p1", "p2"}:
            risk_type = "p2"
        description = (
            _as_nonempty_str(item.get("description"))
            or _as_nonempty_str(item.get("issue"))
            or _as_nonempty_str(item.get("title"))
            or "未说明风险"
        )
        suggestion = (
            _as_nonempty_str(item.get("suggestion"))
            or _as_nonempty_str(item.get("fix"))
            or "建议人工复核后修改"
        )
        result.append(
            {
                "type": risk_type,
                "description": description,
                "suggestion": suggestion,
            }
        )
    return result


def _as_number(value: Any, *, default: float) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _grade_from_score(score: float) -> str:
    if score >= 90:
        return "S"
    if score >= 80:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    return "D"
