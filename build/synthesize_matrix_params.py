#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 genre_matrix 合成 rule_params（与 theme-matrix.yaml param_synthesis 对齐）。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

ROOT = Path(__file__).resolve().parents[1]
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

    tags = genre_matrix.get("flavor_tags") or []
    if isinstance(tags, str):
        tags = [tags]
    tag_cfg = syn.get("flavor_tag_deltas") or {}
    max_tags = (cfg.get("flavor_tags") or {}).get("max_select", DEFAULT_MAX_TAGS)
    for tag in tags[:max_tags]:
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
    core_key = "-".join(str(genre_matrix.get(k, "any")) for k in dim_order)
    tag_part = "+".join(sorted(tags[:max_tags])) if tags else ""
    matrix_key = f"{core_key}|{tag_part}" if tag_part else core_key

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
        {"emotion": "ambition", "identity": "bound", "conflict": "disparity", "world": "modern", "flavor_tags": ["son-in-law", "god-wealth", "down-market", "anti-pua", "male-lead"]},
    ]
    for dims in examples:
        result = resolve_from_matrix(dims)
        rp = result["rule_params"]
        print(f"{result['matrix_key']} density={rp['reversal_density']} hooks={rp['hook_types'][:3]}")


if __name__ == "__main__":
    main()
