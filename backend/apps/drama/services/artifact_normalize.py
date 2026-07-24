# -*- coding: utf-8 -*-
"""产物合成补全层：补齐 schema 必填骨架，收束已知别名，剥离禁止的额外顶层键。

管线：parse → normalize（薄）→ schema validate → substance gate
- 字段契约：JSON Schema + schema_prompt_contract
- 落库入口：artifact_ingest.ingest_llm_artifact
允许：settings 注入、缺省骨架、明确别名表、additionalProperties=false 时剥未知顶层键。
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from apps.drama.services.matrix_synthesis import synthesize_rule_params
from apps.drama.services.skills_loader import get_skills_loader

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

# 结构向维度：失败主导时建议重生本批正文，而非仅文本修复
_STRUCTURE_DIM_KEYS = frozenset(
    {"narrative", "conflict", "hooks", "paywall", "character", "logic"}
)

_MATRIX_AXIS_KEYS = ("emotion", "identity", "conflict", "world")


@lru_cache(maxsize=1)
def _matrix_axis_aliases() -> dict[str, dict[str, str]]:
    """theme-matrix 四轴：value / label_zh → 规范 value。"""
    try:
        raw = get_skills_loader().load_seed_yaml("foundation/theme-matrix.yaml")
    except Exception:
        return {key: {} for key in _MATRIX_AXIS_KEYS}

    axes = (raw.get("axes") or {}) if isinstance(raw, dict) else {}
    out: dict[str, dict[str, str]] = {}
    for axis in _MATRIX_AXIS_KEYS:
        mapping: dict[str, str] = {}
        options = ((axes.get(axis) or {}).get("options") or []) if isinstance(axes, dict) else []
        for opt in options:
            if not isinstance(opt, dict):
                continue
            value = str(opt.get("value") or "").strip()
            if not value:
                continue
            mapping[value.lower()] = value
            label = str(opt.get("label_zh") or "").strip()
            if label:
                mapping[label.lower()] = value
                compact = re.sub(r"[\s+\-_/、，,]+", "", label.lower())
                if compact:
                    mapping[compact] = value
        out[axis] = mapping
    return out


def _canonicalize_axis_value(axis: str, raw: Any) -> Any:
    """将中文标签或近义写法收束为 theme-matrix 英文枚举。"""
    if raw is None:
        return raw
    text = str(raw).strip()
    if not text:
        return raw
    aliases = _matrix_axis_aliases().get(axis) or {}
    if not aliases:
        return text
    lowered = text.lower()
    if lowered in aliases:
        return aliases[lowered]
    compact = re.sub(r"[\s+\-_/、，,]+", "", lowered)
    if compact in aliases:
        return aliases[compact]
    # 标签被模型改写为「复仇+爽感」等：用包含匹配（仅当唯一命中）
    hits = [
        value
        for key, value in aliases.items()
        if key and (key in compact or compact in key) and value
    ]
    uniq = list(dict.fromkeys(hits))
    if len(uniq) == 1:
        return uniq[0]
    # 字序颠倒：都市现代 ↔ 现代都市
    sorted_compact = "".join(sorted(compact))
    sorted_hits = [
        value
        for key, value in aliases.items()
        if key and "".join(sorted(key)) == sorted_compact and value
    ]
    uniq = list(dict.fromkeys(sorted_hits))
    if len(uniq) == 1:
        return uniq[0]
    # 近形中文标签：家庭伦理 ≈ 家族伦理（仅非 ASCII 键，避免误伤英文枚举）
    scored: list[tuple[float, str]] = []
    for key, value in aliases.items():
        if not key or not value or key.isascii():
            continue
        ratio = SequenceMatcher(None, compact, key).ratio()
        if ratio >= 0.72:
            scored.append((ratio, value))
    if scored:
        scored.sort(key=lambda item: item[0], reverse=True)
        best_ratio, best_value = scored[0]
        tied = [value for ratio, value in scored if abs(ratio - best_ratio) < 1e-9]
        if len(list(dict.fromkeys(tied))) == 1:
            return best_value
    return text


def normalize_artifact(
    artifact_key: str,
    payload: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    """按产物类型做合成补全；未知类型原样返回。"""
    if not isinstance(payload, dict):
        return payload
    if artifact_key == "project_brief":
        result = normalize_project_brief(payload, settings)
    elif artifact_key == "story_bible":
        result = normalize_story_bible(payload, settings)
    elif artifact_key == "quality_report":
        result = normalize_quality_report(payload, settings)
    elif artifact_key == "compliance_report":
        result = normalize_compliance_report(payload, settings)
    elif artifact_key == "character_system":
        from apps.drama.services.artifact_scaffold import scaffold_character_system

        result = scaffold_character_system(payload, settings)
    elif artifact_key == "world_system":
        from apps.drama.services.artifact_scaffold import scaffold_world_system

        result = scaffold_world_system(payload, settings)
    elif artifact_key == "emotion_system":
        from apps.drama.services.artifact_scaffold import scaffold_emotion_system

        result = scaffold_emotion_system(payload, settings)
    elif artifact_key == "originality_report":
        from apps.drama.services.artifact_scaffold import scaffold_originality_report

        result = scaffold_originality_report(payload, settings)
    elif artifact_key == "episode_plan":
        from apps.drama.services.artifact_scaffold import scaffold_episode_plan

        result = scaffold_episode_plan(payload, settings)
    elif artifact_key == "episode_scripts":
        from apps.drama.services.artifact_scaffold import scaffold_episode_scripts

        result = scaffold_episode_scripts(payload, settings)
    elif artifact_key == "memory_checkpoint":
        from apps.drama.services.artifact_scaffold import scaffold_memory_checkpoint

        result = scaffold_memory_checkpoint(payload, settings)
    elif artifact_key == "production_package":
        from apps.drama.services.artifact_scaffold import scaffold_production_package

        result = scaffold_production_package(payload, settings)
    else:
        result = payload

    if isinstance(result, dict):
        return strip_unknown_top_level_keys(artifact_key, result)
    return result


@lru_cache(maxsize=64)
def _schema_top_level_allowed_keys(artifact_key: str) -> frozenset[str] | None:
    """若 schema 顶层 additionalProperties=false，返回允许键集合；否则 None（不剥离）。"""
    try:
        from apps.drama.skills_bridge.validate import _resolve_artifact_schema_path
        from apps.core.schema_validator import SchemaValidator

        loader = get_skills_loader()
        schema_path = _resolve_artifact_schema_path(loader, artifact_key)
        validator = SchemaValidator(schema_root=loader.root)
        schema = validator.load_schema(schema_path)
    except Exception:
        return None
    if schema.get("additionalProperties") is not False:
        return None
    props = schema.get("properties")
    if not isinstance(props, dict) or not props:
        return None
    return frozenset(props.keys())


def strip_unknown_top_level_keys(artifact_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    """additionalProperties=false 时剥离未知顶层键，避免 LLM 多吐字段导致整单失败。"""
    allowed = _schema_top_level_allowed_keys(artifact_key)
    if allowed is None:
        return payload
    return {key: value for key, value in payload.items() if key in allowed}


def normalize_story_bible(
    raw: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    """
    story_bible 归一化：补齐 schema 必填骨架，避免 LLM 漏字段导致整次生成失败。

    原则：
    - 缺失的必填结构注入占位值（可后续人工/修订覆盖）
    - 已有松散/别名形态不改写（交给校验暴露），避免 silent rewrite
    """
    if not isinstance(raw, dict):
        return raw
    out = dict(raw)
    title = (
        _as_nonempty_str(out.get("drama_title"))
        or _as_nonempty_str(settings.get("title"))
        or "未命名短剧"
    )
    if not _as_nonempty_str(out.get("drama_title")):
        out["drama_title"] = title

    if not _as_nonempty_str(out.get("logline")):
        idea = _as_nonempty_str(settings.get("core_idea"))
        out["logline"] = idea or f"{title}的核心故事一句话"

    out["synopsis"] = _normalize_synopsis(out.get("synopsis"), title=title, settings=settings)
    out["adapt_source"] = _normalize_adapt_source(out.get("adapt_source"), settings)
    out["world_rules"] = _normalize_world_rules(out.get("world_rules"), settings)

    if "relationship_map" not in out or out.get("relationship_map") is None:
        out["relationship_map"] = []
    elif not isinstance(out.get("relationship_map"), list):
        # 非 list 不改写，留给校验
        pass

    out["characters"] = _normalize_characters(out.get("characters"), title=title)
    out["series_structure"] = _normalize_series_structure(
        out.get("series_structure"), title=title
    )
    return out


def _normalize_synopsis(
    raw: Any,
    *,
    title: str,
    settings: dict[str, Any],
) -> Any:
    """补齐 synopsis.short/full；字符串形态不改写。"""
    if isinstance(raw, str):
        return raw
    idea = _as_nonempty_str(settings.get("core_idea")) or f"{title}的故事梗概"
    src = dict(raw) if isinstance(raw, dict) else {}
    out = dict(src)
    if not _as_nonempty_str(out.get("short")):
        if "short" not in out or out.get("short") in ("", None):
            full = _as_nonempty_str(out.get("full"))
            out["short"] = (full[:80] if full else idea)
    if not _as_nonempty_str(out.get("full")):
        if "full" not in out or out.get("full") in ("", None):
            short = _as_nonempty_str(out.get("short"))
            out["full"] = short or idea
    return out


_CHAR_STRING_FIELDS = (
    "name",
    "surface_desire",
    "deep_need",
    "ghost",
    "lie",
    "flaw",
    "voice_tag",
    "visual_anchor",
)
_CHAR_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "surface_desire": ("want", "desire"),
    "deep_need": ("need",),
    "ghost": ("trauma", "wound"),
    "lie": ("belief_lie",),
    "flaw": ("weakness",),
    "voice_tag": ("voice",),
    "visual_anchor": ("visual", "anchor"),
}
_ARC_FIELDS = ("start", "turning_point_1", "turning_point_2", "end")
_ARC_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "start": ("initial", "beginning"),
    "turning_point_1": ("midpoint", "mid"),
    "turning_point_2": ("low_point", "low"),
    "end": ("final", "ending"),
}


def _placeholder_character(title: str) -> dict[str, Any]:
    return {
        "name": f"{title}主角",
        "role_type": "protagonist",
        "surface_desire": "待细化",
        "deep_need": "待细化",
        "ghost": "待细化",
        "lie": "待细化",
        "flaw": "待细化",
        "arc": {
            "start": "起点待细化",
            "turning_point_1": "转折一待细化",
            "turning_point_2": "转折二待细化",
            "end": "结局待细化",
        },
        "voice_tag": "待细化",
        "visual_anchor": "待细化",
    }


def _has_any_alias(src: dict[str, Any], aliases: tuple[str, ...]) -> bool:
    return any(alias in src for alias in aliases)


def _normalize_character_arc(raw: Any) -> Any:
    """补齐 arc 正式键；若已有别名键则不注入正式键（保留松散形态）。"""
    if raw is not None and not isinstance(raw, dict):
        return raw
    src = dict(raw) if isinstance(raw, dict) else {}
    out = dict(src)
    placeholders = {
        "start": "起点待细化",
        "turning_point_1": "转折一待细化",
        "turning_point_2": "转折二待细化",
        "end": "结局待细化",
    }
    for key in _ARC_FIELDS:
        if _as_nonempty_str(out.get(key)):
            continue
        if _has_any_alias(out, _ARC_FIELD_ALIASES.get(key, ())):
            continue
        if key not in out or out.get(key) in (None, ""):
            out[key] = placeholders[key]
    return out


def _normalize_character_item(raw: Any, *, title: str, index: int) -> Any:
    """补齐角色 schema 必填字段；已有别名则不注入对应正式键。"""
    if not isinstance(raw, dict):
        return raw
    out = dict(raw)
    for key in _CHAR_STRING_FIELDS:
        if _as_nonempty_str(out.get(key)):
            continue
        if _has_any_alias(out, _CHAR_FIELD_ALIASES.get(key, ())):
            continue
        if key not in out or out.get(key) in (None, ""):
            if key == "name":
                out[key] = f"{title}角色{index + 1}"
            else:
                out[key] = "待细化"
    if "role_type" not in out or out.get("role_type") in (None, ""):
        out["role_type"] = "protagonist"
    out["arc"] = _normalize_character_arc(out.get("arc"))
    return out


def _normalize_characters(raw: Any, *, title: str) -> Any:
    """缺 characters 或空列表时注入占位主角；已有条目补齐缺失必填键。"""
    if raw is None or (isinstance(raw, list) and len(raw) == 0):
        return [_placeholder_character(title)]
    if not isinstance(raw, list):
        return raw
    return [
        _normalize_character_item(item, title=title, index=idx)
        for idx, item in enumerate(raw)
    ]


def _normalize_series_structure(raw: Any, *, title: str) -> Any:
    """补齐 series_structure 必填键；已有错误形态不改写。"""
    if raw is not None and not isinstance(raw, dict):
        return raw
    src = dict(raw) if isinstance(raw, dict) else {}
    out = dict(src)
    if not _as_nonempty_str(out.get("main_storyline")):
        if "main_storyline" not in out or out.get("main_storyline") in ("", None):
            out["main_storyline"] = f"{title}主线待细化"
    if "six_stage_structure" not in out or out.get("six_stage_structure") is None:
        out["six_stage_structure"] = [{}, {}, {}, {}, {}, {}]
    elif isinstance(out.get("six_stage_structure"), list):
        stages = list(out["six_stage_structure"])
        while len(stages) < 6:
            stages.append({})
        out["six_stage_structure"] = stages[:6] if len(stages) > 6 else stages
    for key in (
        "conflict_escalation_chain",
        "major_reversal_positions",
        "paywall_distribution",
        "foreshadowing_table",
        "series_emotion_curve",
    ):
        if key not in out or out.get(key) is None:
            out[key] = []
    return out


def _normalize_adapt_source(
    raw: Any,
    settings: dict[str, Any],
) -> dict[str, Any]:
    """保证 adapt_source.mode 存在；原创缺省 original，改编缺省 adapt。"""
    src = raw if isinstance(raw, dict) else {}
    mode = _as_nonempty_str(src.get("mode"))
    if mode not in ("original", "adapt"):
        entry = str(settings.get("entry_type") or "").strip().lower()
        mode = "adapt" if entry in ("adapt", "adaptation", "adapt_track") else "original"
    out: dict[str, Any] = {"mode": mode}
    for key in ("retained", "enhanced", "rewritten"):
        if key in src:
            out[key] = src[key]
    check = _as_nonempty_str(src.get("originality_check"))
    if check:
        out["originality_check"] = check
    return out


def _normalize_world_rules(
    raw: Any,
    settings: dict[str, Any],
) -> dict[str, Any]:
    """
    保证 world_rules 具备 schema 必填三键。

    - 完全缺失或非对象：注入最小默认值
    - 已有字段保留原值（含 LLM 松散结构），不改写别名形态
    - 仅补空缺的 setting_summary / root_rules / power_structure
    """
    src = dict(raw) if isinstance(raw, dict) else {}
    title = (
        _as_nonempty_str(settings.get("title"))
        or _as_nonempty_str(settings.get("core_idea"))
        or "故事世界"
    )
    out = dict(src)

    if not _as_nonempty_str(out.get("setting_summary")):
        if "setting_summary" not in out or out.get("setting_summary") in ("", None):
            out["setting_summary"] = f"{title}的故事设定"

    if "root_rules" not in out or out.get("root_rules") is None:
        out["root_rules"] = [f"{title}世界的基本规则待细化"]
    elif isinstance(out.get("root_rules"), list) and len(out["root_rules"]) == 0:
        out["root_rules"] = [f"{title}世界的基本规则待细化"]

    if not _as_nonempty_str(out.get("power_structure")):
        if "power_structure" not in out or out.get("power_structure") in ("", None):
            out["power_structure"] = f"{title}的权力结构待细化"

    return out

def normalize_project_brief(
    raw: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    """注入矩阵合成字段（theme_code / matrix_key / rule_params），裁掉 schema 外键。"""
    if not isinstance(raw, dict):
        return raw

    settings_matrix = dict(settings.get("genre_matrix") or {})
    raw_matrix = raw.get("genre_matrix") if isinstance(raw.get("genre_matrix"), dict) else {}

    def _axis(name: str, fallback: str) -> str:
        value = _canonicalize_axis_value(
            name, raw_matrix.get(name) or settings_matrix.get(name)
        )
        return value or fallback

    genre_matrix: dict[str, Any] = {
        "emotion": _axis("emotion", "ambition"),
        "identity": _axis("identity", "ordinary"),
        "conflict": _axis("conflict", "family"),
        "world": _axis("world", "modern"),
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

    if "flavor_tags" in raw_matrix:
        tags: Any = list(raw_matrix.get("flavor_tags") or [])
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
    # rule_params 由题材矩阵合成；模型输出一律不采信
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

    out: dict[str, Any] = {
        "genre_matrix": genre_matrix,
        "theme_code": "matrix",
        "matrix_key": matrix_key,
        "rule_params": rule_params,
        "preset_theme_code": settings.get("preset_theme_code"),
    }

    title = _as_nonempty_str(raw.get("title")) or _as_nonempty_str(settings.get("title"))
    out["title"] = title or "未命名短剧"

    episode_count = raw.get("episode_count")
    if episode_count is None:
        episode_count = settings.get("episode_count")
    try:
        out["episode_count"] = int(episode_count) if episode_count is not None else 80
    except (TypeError, ValueError):
        out["episode_count"] = 80

    if "episode_duration" in raw:
        out["episode_duration"] = raw.get("episode_duration")

    for key in (
        "core_idea",
        "target_audience",
        "core_conflict",
        "hook_concept",
        "commercial_hook",
        "market_opportunity",
        "differentiation_strategy",
        "first_episode_hook",
        "paywall_direction",
    ):
        value = _as_nonempty_str(raw.get(key))
        if value:
            out[key] = value
        elif key == "core_idea":
            settings_idea = _as_nonempty_str(settings.get("core_idea"))
            out["core_idea"] = settings_idea or f"{out['title']}的核心创意待细化"

    # schema 必填卖点字段：缺失时注入占位，避免选题生成因漏字段整单失败
    for key, default in (
        ("target_audience", "通用受众"),
        ("core_conflict", "核心冲突待细化"),
        ("hook_concept", "开篇钩子待细化"),
    ):
        if not _as_nonempty_str(out.get(key)):
            out[key] = default

    if raw.get("compliance_risk") in {"low", "medium", "high"}:
        out["compliance_risk"] = str(raw["compliance_risk"])
    elif out.get("compliance_risk") not in {"low", "medium", "high"}:
        out["compliance_risk"] = "medium"

    refs = raw.get("reference_works")
    if isinstance(refs, list):
        out["reference_works"] = [str(item) for item in refs if item is not None]

    factors = raw.get("blockbuster_factors")
    if isinstance(factors, list) and all(isinstance(item, str) for item in factors):
        out["blockbuster_factors"] = [item for item in factors if item.strip()]

    competitors = raw.get("competitor_references")
    if isinstance(competitors, list):
        normalized_competitors: list[dict[str, Any]] = []
        for item in competitors:
            if not isinstance(item, dict):
                continue
            title = _as_nonempty_str(item.get("title")) or _as_nonempty_str(
                item.get("name")
            )
            if not title:
                continue
            row: dict[str, Any] = {"title": title}
            for key in ("inspiration", "avoidance", "note", "differentiation"):
                value = _as_nonempty_str(item.get(key))
                if value:
                    row[key] = value
            normalized_competitors.append(row)
        out["competitor_references"] = normalized_competitors

    return {key: value for key, value in out.items() if key in _PROJECT_BRIEF_KEYS}


def normalize_quality_report(
    raw: dict[str, Any],
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """注入 settings 职责字段与 revision_route；补齐 schema 必填骨架；不改写已有维度别名/形状。"""
    settings = settings or {}
    if not isinstance(raw, dict):
        return raw

    out = dict(raw)
    # 常见 LLM 别名：先收束再由 normalize_artifact 剥离其余额外键
    if not isinstance(out.get("overall_score"), (int, float)) and isinstance(
        out.get("total_score"), (int, float)
    ):
        out["overall_score"] = out["total_score"]
    if (
        ("revision_priorities" not in out or out.get("revision_priorities") in (None, []))
        and out.get("revision_priority") is not None
    ):
        priority = out.get("revision_priority")
        if isinstance(priority, list):
            out["revision_priorities"] = priority
        elif isinstance(priority, dict):
            out["revision_priorities"] = [priority]
        elif isinstance(priority, str) and priority.strip():
            out["revision_priorities"] = [{"title": priority.strip()}]
    if (
        ("defects" not in out or out.get("defects") in (None, []))
        and isinstance(out.get("must_fix_issues"), list)
        and out["must_fix_issues"]
    ):
        out["defects"] = list(out["must_fix_issues"])

    if not _as_nonempty_str(out.get("drama_title")):
        title = _as_nonempty_str(settings.get("title"))
        if title:
            out["drama_title"] = title
        else:
            out["drama_title"] = "未命名短剧"

    out["scored_artifact"] = "latest_script"
    out["resolved_script_key"] = _resolve_script_key(out, settings)

    scoring_preset = _resolve_scoring_preset(out, settings)
    out["scoring_preset"] = scoring_preset

    if not isinstance(out.get("pass_threshold"), (int, float)):
        out["pass_threshold"] = 75.0

    dims = out.get("dimensions")
    if isinstance(dims, dict):
        weights = _load_quality_dimension_weights(scoring_preset)
        patched: dict[str, Any] = {}
        for key, dim in dims.items():
            if (
                key in _QUALITY_DIMENSION_KEYS
                and isinstance(dim, dict)
                and not isinstance(dim.get("weight"), (int, float))
            ):
                row = dict(dim)
                row["weight"] = weights[key]
                patched[key] = row
            else:
                patched[key] = dim
        for key in _QUALITY_DIMENSION_KEYS:
            if key not in patched:
                patched[key] = _placeholder_quality_dimension(weights.get(key, 0.1))
        out["dimensions"] = patched
    elif dims is None:
        weights = _load_quality_dimension_weights(scoring_preset)
        out["dimensions"] = {
            key: _placeholder_quality_dimension(weights.get(key, 0.1))
            for key in _QUALITY_DIMENSION_KEYS
        }

    if not isinstance(out.get("overall_score"), (int, float)):
        out["overall_score"] = _estimate_overall_score(out.get("dimensions"))

    if "grade" not in out or out.get("grade") in (None, ""):
        out["grade"] = _grade_from_score(float(out["overall_score"]))

    threshold = float(out["pass_threshold"])
    score = float(out["overall_score"])
    if not isinstance(out.get("needs_revision"), bool):
        out["needs_revision"] = score < threshold
    if not isinstance(out.get("can_continue_next_batch"), bool):
        out["can_continue_next_batch"] = not bool(out["needs_revision"])

    if "defects" not in out or out.get("defects") is None:
        out["defects"] = []
    if "revision_priorities" not in out or out.get("revision_priorities") is None:
        out["revision_priorities"] = []
    if "continuity_summary" not in out or out.get("continuity_summary") is None:
        out["continuity_summary"] = {"result": "pass", "issues": []}
    elif isinstance(out.get("continuity_summary"), dict):
        cont = dict(out["continuity_summary"])
        if cont.get("result") not in {"pass", "warning", "fail"}:
            if "result" not in cont or cont.get("result") in (None, ""):
                cont["result"] = "pass"
        if "issues" not in cont or cont.get("issues") is None:
            cont["issues"] = []
        out["continuity_summary"] = cont

    if "verdict" not in out or out.get("verdict") in (None, ""):
        out["verdict"] = "通过" if not out.get("needs_revision") else "需要修改"

    needs_revision = out.get("needs_revision")
    if isinstance(needs_revision, bool) and isinstance(out.get("dimensions"), dict):
        out["revision_route"] = resolve_revision_route(
            needs_revision=needs_revision,
            dimensions=out["dimensions"],
            pass_threshold=_as_number(out.get("pass_threshold"), default=75.0),
        )
    return out


def normalize_compliance_report(
    raw: dict[str, Any],
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """注入 settings 标题与 checked_artifact；补齐 schema 必填骨架；不做合规字段别名改写。"""
    settings = settings or {}
    if not isinstance(raw, dict):
        return raw

    out = dict(raw)
    if not _as_nonempty_str(out.get("drama_title")):
        title = _as_nonempty_str(settings.get("title"))
        if title:
            out["drama_title"] = title
        else:
            out["drama_title"] = "未命名短剧"

    out["checked_artifact"] = "latest_script"
    out["resolved_script_key"] = _resolve_script_key(out, settings)

    if "check_mode" not in out or out.get("check_mode") in (None, ""):
        out["check_mode"] = "standard"

    if "target_platform" not in out or out.get("target_platform") in (None, ""):
        prefs = settings.get("creation_preferences") or {}
        platform = _as_nonempty_str(prefs.get("target_platform")) or _as_nonempty_str(
            settings.get("target_platform")
        )
        if platform not in {"generic", "douyin", "kuaishou", "wechat_miniprogram"}:
            platform = "generic"
        out["target_platform"] = platform

    if "overall_result" not in out or out.get("overall_result") in (None, ""):
        out["overall_result"] = "通过"
    if "blocking_issues" not in out or out.get("blocking_issues") is None:
        out["blocking_issues"] = []
    if "risk_items" not in out or out.get("risk_items") is None:
        out["risk_items"] = []
    return out


def _resolve_script_key(raw: dict[str, Any], settings: dict[str, Any]) -> str:
    allowed = {"polished_script", "episode_scripts", "external_script"}
    key = _as_nonempty_str(raw.get("resolved_script_key"))
    if key in allowed:
        return key
    hint = _as_nonempty_str(settings.get("resolved_script_key"))
    if hint in allowed:
        return hint
    if settings.get("external_script_review"):
        return "external_script"
    return "episode_scripts"


def _placeholder_quality_dimension(weight: float) -> dict[str, Any]:
    return {
        "score": 70.0,
        "weight": float(weight) if isinstance(weight, (int, float)) else 0.1,
        "evidence": ["系统占位：该维度证据待模型补全"],
        "deductions": [],
    }


def _estimate_overall_score(dimensions: Any) -> float:
    if not isinstance(dimensions, dict) or not dimensions:
        return 70.0
    total = 0.0
    weight_sum = 0.0
    for dim in dimensions.values():
        if not isinstance(dim, dict):
            continue
        score = dim.get("score")
        weight = dim.get("weight")
        if not isinstance(score, (int, float)):
            continue
        w = float(weight) if isinstance(weight, (int, float)) else 1.0
        total += float(score) * w
        weight_sum += w
    if weight_sum <= 0:
        return 70.0
    return round(total / weight_sum, 1)


def _grade_from_score(score: float) -> str:
    if score >= 90:
        return "S"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    return "D"


def resolve_revision_route(
    *,
    needs_revision: bool,
    dimensions: dict[str, Any],
    pass_threshold: float,
) -> str:
    """根据失败维度决定质检后路由：pass / text_polish / rewrite_batch。

    合规硬阻断由工作台合并 compliance_report.blocking_issues 后覆盖为 user_gate。
    """
    if not needs_revision:
        return "pass"
    failing: list[str] = []
    for key, dim in (dimensions or {}).items():
        if not isinstance(dim, dict):
            continue
        score = dim.get("score")
        if isinstance(score, (int, float)) and float(score) < float(pass_threshold):
            failing.append(str(key))
    if not failing:
        return "text_polish"
    structure_n = sum(1 for key in failing if key in _STRUCTURE_DIM_KEYS)
    other_n = len(failing) - structure_n
    if structure_n > other_n:
        return "rewrite_batch"
    return "text_polish"


def quality_report_evidence_too_sparse(payload: dict[str, Any]) -> bool:
    """任一维度缺少有效 evidence，或分析/总评篇幅不足 → 视为空壳评分。"""
    dims = payload.get("dimensions")
    if not isinstance(dims, dict) or not dims:
        return True

    length_cfg = _load_quality_output_length()
    dim_min = int(length_cfg.get("dimension_analysis_min_chars") or 100)
    verdict_min = int(length_cfg.get("verdict_detail_min_chars") or 200)
    continuity_min = int(length_cfg.get("continuity_summary_min_chars") or 80)

    for dim in dims.values():
        if not isinstance(dim, dict):
            return True
        evidence = dim.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            return True
        if not any(isinstance(x, str) and len(x.strip()) >= 8 for x in evidence):
            return True
        analysis_chars = _dimension_analysis_char_count(dim)
        if analysis_chars < dim_min:
            return True

    verdict_detail = str(payload.get("verdict_detail") or "").strip()
    if len(verdict_detail) < verdict_min:
        return True

    continuity = payload.get("continuity_summary")
    if isinstance(continuity, dict):
        summary = str(continuity.get("summary") or "").strip()
        if summary and len(summary) < continuity_min:
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
        detail = str(item.get("description") or "").strip()
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


_PLACEHOLDER_COMPETITOR = re.compile(r"^竞品\s*\d+$")
_SLOGAN_DIFF_MARKERS = (
    "质量更好",
    "更有深度",
    "差异化明显",
    "独特视角",
    "内容更好",
    "更打动人",
    "更有共鸣",
)
_VAGUE_HOOK_MARKERS = (
    "关键证据即将公开",
    "婚礼现场反击",
)


def project_brief_too_thin(payload: dict[str, Any]) -> bool:
    """竞品占位名、口号差异化、过短钩子 → 视为空壳选题简报。"""
    competitors = payload.get("competitor_references")
    if not isinstance(competitors, list) or len(competitors) < 2:
        return True
    for item in competitors:
        if not isinstance(item, dict):
            return True
        title = str(item.get("title") or item.get("name") or "").strip()
        if len(title) < 2 or _PLACEHOLDER_COMPETITOR.match(title):
            return True
        inspiration = str(
            item.get("inspiration") or item.get("borrow") or item.get("note") or ""
        ).strip()
        avoidance = str(
            item.get("avoidance") or item.get("avoid") or item.get("pitfall") or ""
        ).strip()
        if len(inspiration) < 8 or len(avoidance) < 8:
            return True

    market = str(payload.get("market_opportunity") or "").strip()
    if len(market) < 20:
        return True

    diff = str(payload.get("differentiation_strategy") or "").strip()
    if len(diff) < 20:
        return True
    if any(marker in diff for marker in _SLOGAN_DIFF_MARKERS) and len(diff) < 48:
        return True

    hook = str(payload.get("first_episode_hook") or "").strip()
    if len(hook) < 12:
        return True
    if hook in _VAGUE_HOOK_MARKERS:
        return True

    paywall = str(payload.get("paywall_direction") or "").strip()
    if len(paywall) < 8:
        return True
    if paywall in _VAGUE_HOOK_MARKERS:
        return True

    return False


def _resolve_scoring_preset(
    raw: dict[str, Any],
    settings: dict[str, Any],
) -> str:
    preset = _as_nonempty_str(raw.get("scoring_preset"))
    if not preset:
        prefs = settings.get("creation_preferences") or {}
        preset = _as_nonempty_str(prefs.get("scoring_preset")) or "standard"
    if preset not in {"standard", "strict", "relaxed", "rhythm_first"}:
        return "standard"
    return preset


def _load_quality_dimension_weights(scoring_preset: str) -> dict[str, float]:
    """从 quality-scoring.yaml + scoring-presets.yaml 读取十维权重 SSOT。"""
    loader = get_skills_loader()
    scoring = loader.load_seed_yaml("foundation/constraints/quality-scoring.yaml")
    presets = loader.load_seed_yaml("foundation/presets/scoring-presets.yaml")
    preset_map = presets.get("presets") if isinstance(presets.get("presets"), dict) else {}
    if scoring_preset not in preset_map:
        scoring_preset = "standard"
    preset = preset_map.get(scoring_preset) or {}
    preset_weights = preset.get("weights") if isinstance(preset.get("weights"), dict) else {}

    weights: dict[str, float] = {}
    for dim in scoring.get("dimensions") or []:
        if not isinstance(dim, dict):
            continue
        key = str(dim.get("key") or "")
        if key not in _QUALITY_DIMENSION_KEYS:
            continue
        raw_weight = preset_weights.get(key, dim.get("weight"))
        weights[key] = _as_number(raw_weight, default=0.0)

    for key in _QUALITY_DIMENSION_KEYS:
        weights.setdefault(key, 0.0)
    return weights


def _load_quality_output_length() -> dict[str, Any]:
    try:
        scoring = get_skills_loader().load_seed_yaml(
            "foundation/constraints/quality-scoring.yaml"
        )
        length = scoring.get("output_length")
        return length if isinstance(length, dict) else {}
    except Exception:
        return {}


def _dimension_analysis_char_count(dim: dict[str, Any]) -> int:
    chunks: list[str] = []
    for key in ("evidence", "deductions"):
        value = dim.get(key)
        if isinstance(value, str):
            chunks.append(value.strip())
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    chunks.append(item.strip())
    return sum(len(part) for part in chunks)


def _as_nonempty_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_number(value: Any, *, default: float) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
