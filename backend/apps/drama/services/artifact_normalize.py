# -*- coding: utf-8 -*-
"""产物合成补全层：写入 settings/matrix 职责字段，不做 LLM 别名或形状改写。

管线：parse → normalize（薄）→ schema validate → substance gate
- 字段契约：JSON Schema + schema_prompt_contract
- 落库入口：artifact_ingest.ingest_llm_artifact
本模块仅注入 schema 要求且非 LLM 职责的结构字段；禁止别名映射、形状折叠与「待补充」占位。
"""
from __future__ import annotations

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


def normalize_artifact(
    artifact_key: str,
    payload: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    """按产物类型做合成补全；未知类型原样返回。"""
    if not isinstance(payload, dict):
        return payload
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
    """narrative_plan：不做别名/缺省补齐，原样交给 schema。"""
    del settings  # 本产物无 settings 合成字段
    if not isinstance(raw, dict):
        return raw
    return dict(raw)


def normalize_story_bible(
    raw: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    """story_bible：不做别名/形状改写；仅在缺标题时注入 settings.title。"""
    if not isinstance(raw, dict):
        return raw
    out = dict(raw)
    if not _as_nonempty_str(out.get("drama_title")):
        title = _as_nonempty_str(settings.get("title"))
        if title:
            out["drama_title"] = title
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
    if title:
        out["title"] = title

    episode_count = raw.get("episode_count")
    if episode_count is None:
        episode_count = settings.get("episode_count")
    if episode_count is not None:
        try:
            out["episode_count"] = int(episode_count)
        except (TypeError, ValueError):
            pass

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
            if settings_idea:
                out["core_idea"] = settings_idea

    if raw.get("compliance_risk") in {"low", "medium", "high"}:
        out["compliance_risk"] = str(raw["compliance_risk"])

    refs = raw.get("reference_works")
    if isinstance(refs, list):
        out["reference_works"] = [str(item) for item in refs if item is not None]

    factors = raw.get("blockbuster_factors")
    if isinstance(factors, list) and all(isinstance(item, str) for item in factors):
        out["blockbuster_factors"] = [item for item in factors if item.strip()]

    competitors = raw.get("competitor_references")
    if isinstance(competitors, list):
        out["competitor_references"] = [
            item for item in competitors if isinstance(item, dict)
        ]

    return {key: value for key, value in out.items() if key in _PROJECT_BRIEF_KEYS}


def normalize_quality_report(
    raw: dict[str, Any],
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """注入 settings 职责字段与 revision_route；不改写维度别名/分数制/形状。"""
    settings = settings or {}
    if not isinstance(raw, dict):
        return raw

    out = dict(raw)
    if not _as_nonempty_str(out.get("drama_title")):
        title = _as_nonempty_str(settings.get("title"))
        if title:
            out["drama_title"] = title

    out["scored_artifact"] = "latest_script"

    scoring_preset = _resolve_scoring_preset(out, settings)
    out["scoring_preset"] = scoring_preset

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
        out["dimensions"] = patched

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
    """注入 settings 标题与 checked_artifact；不做合规字段别名改写。"""
    settings = settings or {}
    if not isinstance(raw, dict):
        return raw

    out = dict(raw)
    if not _as_nonempty_str(out.get("drama_title")):
        title = _as_nonempty_str(settings.get("title"))
        if title:
            out["drama_title"] = title

    out["checked_artifact"] = "latest_script"
    return out


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
    presets = loader.load_seed_yaml("foundation/constraints/scoring-presets.yaml")
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
