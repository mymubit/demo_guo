#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 genre_matrix 合成 rule_params（与 theme-matrix.yaml param_synthesis 对齐）。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "foundation" / "theme-matrix.yaml"

CLAMP_DENSITY = (0.12, 0.65)
MAX_HOOKS = 10
DEFAULT_MAX_TAGS = 5


def _load_matrix() -> Dict[str, Any]:
    return yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8")) or {}


def _vec_add(base: List[float], delta: List[float]) -> List[float]:
    n = max(len(base), len(delta))
    return [(base[i] if i < len(base) else 0.0) + (delta[i] if i < len(delta) else 0.0) for i in range(n)]


def _clamp_curve(values: List[float]) -> List[int]:
    return [max(1, min(10, int(round(v)))) for v in values]


def _normalize_ratio(parts: List[float]) -> List[float]:
    total = sum(parts)
    if total <= 0:
        return parts
    return [round(p / total, 4) for p in parts]


def _apply_delta(
    reversal: float,
    curve: List[float],
    act: List[float],
    hooks: List[str],
    delta: Dict[str, Any],
) -> tuple[float, List[float], List[float], List[str]]:
    reversal += float(delta.get("reversal_density") or 0)
    curve = _vec_add(curve, [float(x) for x in delta.get("emotion_curve_delta") or []])
    act = _vec_add(act, [float(x) for x in delta.get("act_ratio_delta") or []])
    hooks.extend(delta.get("hook_types_add") or [])
    return reversal, curve, act, hooks


class TagConstraintError(ValueError):
    """标签组合违反 tag_constraints。"""


def _canonical_tag_order(cfg: Dict[str, Any]) -> Dict[str, int]:
    options = (cfg.get("flavor_tags") or {}).get("options") or []
    return {opt["value"]: idx for idx, opt in enumerate(options) if opt.get("value")}


def validate_tag_constraints(cfg: Dict[str, Any], genre_matrix: Dict[str, Any]) -> None:
    """校验互斥与世界观依赖；违反抛 TagConstraintError。"""
    constraints = cfg.get("tag_constraints") or {}
    tags = set(genre_matrix.get("flavor_tags") or [])
    for group in constraints.get("mutually_exclusive") or []:
        hit = tags & set(group)
        if len(hit) > 1:
            raise TagConstraintError(f"互斥标签同选: {sorted(hit)}")
    world = genre_matrix.get("world")
    for tag, allowed_worlds in (constraints.get("requires_world") or {}).items():
        if tag in tags and world and world not in allowed_worlds:
            raise TagConstraintError(
                f"标签 {tag} 要求世界观 {allowed_worlds}，当前 world={world}"
            )


def synthesize_rule_params(genre_matrix: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load_matrix()
    syn = cfg.get("param_synthesis") or {}
    emotion = genre_matrix.get("emotion")
    if not emotion:
        raise ValueError("genre_matrix.emotion is required")

    profiles = syn.get("emotion_profiles") or {}
    profile = dict(profiles.get(emotion) or {})
    if not profile:
        raise ValueError(f"unknown emotion axis: {emotion}")

    validate_tag_constraints(cfg, genre_matrix)

    base = syn.get("base") or {}
    reversal = float(profile.get("reversal_density", base.get("reversal_density", 0.28)))
    curve = [float(x) for x in profile.get("emotion_curve", base.get("emotion_curve", []))]
    act = [float(x) for x in base.get("act_ratio", [])]
    hooks: List[str] = list(profile.get("hook_types") or base.get("hook_types") or [])

    for axis_key, delta_key in (
        ("identity", "identity_deltas"),
        ("conflict", "conflict_deltas"),
        ("world", "world_deltas"),
    ):
        val = genre_matrix.get(axis_key)
        if val:
            d = (syn.get(delta_key) or {}).get(val) or {}
            reversal, curve, act, hooks = _apply_delta(reversal, curve, act, hooks, d)

    channel = genre_matrix.get("audience_channel") or "general"
    channel_delta = (syn.get("channel_profiles") or {}).get(channel)
    if channel_delta is None:
        raise ValueError(f"unknown audience_channel: {channel}")
    reversal, curve, act, hooks = _apply_delta(reversal, curve, act, hooks, channel_delta)

    structure = genre_matrix.get("protagonist_structure")
    if structure:
        structure_delta = (syn.get("structure_deltas") or {}).get(structure)
        if structure_delta is None:
            raise ValueError(f"unknown protagonist_structure: {structure}")
        reversal, curve, act, hooks = _apply_delta(reversal, curve, act, hooks, structure_delta)

    tags = genre_matrix.get("flavor_tags") or []
    if isinstance(tags, str):
        tags = [tags]
    tag_cfg = syn.get("flavor_tag_deltas") or {}
    max_tags = (cfg.get("flavor_tags") or {}).get("max_select", DEFAULT_MAX_TAGS)
    # 幂等保证：按 options 声明顺序（canonical order）叠加，与用户选择顺序无关
    order = _canonical_tag_order(cfg)
    canonical_tags = sorted(tags[:max_tags], key=lambda t: order.get(t, len(order)))
    for tag in canonical_tags:
        d = tag_cfg.get(tag)
        if not d:
            continue
        reversal, curve, act, hooks = _apply_delta(reversal, curve, act, hooks, d)

    reversal = max(CLAMP_DENSITY[0], min(CLAMP_DENSITY[1], reversal))
    curve = _clamp_curve(curve)
    act = _normalize_ratio(act)

    dedup_hooks: List[str] = []
    seen = set()
    for h in hooks:
        if h not in seen:
            seen.add(h)
            dedup_hooks.append(h)
        if len(dedup_hooks) >= MAX_HOOKS:
            break

    dim_order = cfg.get("dim_order") or ["emotion", "identity", "conflict", "world"]
    key_parts = ["-".join(str(genre_matrix.get(k, "any")) for k in dim_order)]
    if channel != "general":
        key_parts.append(f"ch:{channel}")
    if structure:
        key_parts.append(f"ps:{structure}")
    if canonical_tags:
        key_parts.append("+".join(sorted(canonical_tags)))
    matrix_key = "|".join(key_parts)

    return {
        "matrix_key": matrix_key,
        "reversal_density": round(reversal, 3),
        "emotion_curve": curve,
        "act_ratio": act,
        "hook_types": dedup_hooks,
    }


def resolve_from_matrix(genre_matrix: Dict[str, Any]) -> Dict[str, Any]:
    rule_params = synthesize_rule_params(genre_matrix)
    return {
        "theme_code": "matrix",
        "genre_matrix": genre_matrix,
        "rule_params": rule_params,
        "matrix_key": rule_params["matrix_key"],
    }


def resolve_from_preset(theme_code: str) -> Optional[Dict[str, Any]]:
    cfg = _load_matrix()
    for preset in cfg.get("preset_templates") or []:
        if preset.get("theme_code") == theme_code:
            dims = dict(preset.get("dims") or {})
            out = resolve_from_matrix(dims)
            out["preset_theme_code"] = theme_code
            out["preset_label_zh"] = preset.get("label_zh")
            return out
    return None


def main() -> None:
    examples: List[Dict[str, Any]] = [
        {"emotion": "revenge", "identity": "reborn", "conflict": "family", "world": "ancient", "flavor_tags": ["wuxia", "angst-revenge"]},
        {"emotion": "warmth", "identity": "ordinary", "conflict": "redemption", "world": "rural", "flavor_tags": ["nongtian", "food", "slow-burn"]},
        {"emotion": "suspense", "identity": "ordinary", "conflict": "survival", "world": "virtual", "flavor_tags": ["infinite-flow", "horror", "folk-horror", "crime-procedural"]},
        {"emotion": "justice", "identity": "returning-elite", "conflict": "family", "world": "modern", "audience_channel": "male", "protagonist_structure": "single-male", "flavor_tags": ["war-god", "urban-fantasy", "angst-revenge"]},
        {"emotion": "ambition", "identity": "bound", "conflict": "disparity", "world": "modern", "audience_channel": "male", "flavor_tags": ["son-in-law", "god-wealth", "down-market", "anti-pua"]},
    ]
    for dims in examples:
        result = resolve_from_matrix(dims)
        rp = result["rule_params"]
        print(f"{result['matrix_key']} density={rp['reversal_density']} hooks={rp['hook_types'][:3]}")


if __name__ == "__main__":
    main()
