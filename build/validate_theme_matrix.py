#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 theme-matrix.yaml：轴/标签/合成/deltas 完整性。"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "foundation" / "theme-matrix.yaml"

sys.path.insert(0, str(ROOT / "build"))
from synthesize_matrix_params import synthesize_rule_params  # noqa: E402


def _load() -> Dict[str, Any]:
    return yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8")) or {}


def _axis_values(cfg: Dict[str, Any], axis: str) -> Set[str]:
    opts = (cfg.get("axes") or {}).get(axis, {}).get("options") or []
    return {o["value"] for o in opts if o.get("value")}


def _tag_values(cfg: Dict[str, Any]) -> Set[str]:
    opts = (cfg.get("flavor_tags") or {}).get("options") or []
    return {o["value"] for o in opts if o.get("value")}


def validate() -> int:
    cfg = _load()
    syn = cfg.get("param_synthesis") or {}
    errors: List[str] = []

    emotions = _axis_values(cfg, "emotion")
    profiles = set((syn.get("emotion_profiles") or {}).keys())
    missing_emotion = emotions - profiles
    if missing_emotion:
        errors.append(f"emotion_profiles 缺失: {sorted(missing_emotion)}")

    for axis, delta_key in (
        ("identity", "identity_deltas"),
        ("conflict", "conflict_deltas"),
        ("world", "world_deltas"),
    ):
        vals = _axis_values(cfg, axis)
        deltas = set((syn.get(delta_key) or {}).keys())
        missing = vals - deltas
        if missing:
            errors.append(f"{delta_key} 缺失: {sorted(missing)}")

    tags = _tag_values(cfg)
    tag_deltas = set((syn.get("flavor_tag_deltas") or {}).keys())
    missing_tags = tags - tag_deltas
    if missing_tags:
        errors.append(f"flavor_tag_deltas 缺失: {sorted(missing_tags)}")

    cat_tags: Set[str] = set()
    for cat in (cfg.get("flavor_tags") or {}).get("categories") or []:
        cat_tags.update(cat.get("tags") or [])
    if cat_tags != tags:
        errors.append(f"categories 与 options 不一致: 缺 {sorted(tags - cat_tags)} 多 {sorted(cat_tags - tags)}")

    for preset in cfg.get("preset_templates") or []:
        dims = preset.get("dims") or {}
        try:
            synthesize_rule_params(dims)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"preset {preset.get('theme_code')} 合成失败: {exc}")

    for combo in cfg.get("featured_combos") or []:
        dims = combo.get("dims") or {}
        try:
            synthesize_rule_params(dims)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"featured {combo.get('id')} 合成失败: {exc}")
        em = dims.get("emotion")
        if em and em not in emotions:
            errors.append(f"featured {combo.get('id')} 无效 emotion: {em}")
        for tag in dims.get("flavor_tags") or []:
            if tag not in tags:
                errors.append(f"featured {combo.get('id')} 无效 tag: {tag}")

    if errors:
        print("VALIDATE FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    cov = cfg.get("coverage_model") or {}
    tag_count = len(tags)
    combo_count = len(cfg.get("featured_combos") or [])
    if cov.get("flavor_tag_count") and cov["flavor_tag_count"] != tag_count:
        errors.append(f"coverage_model.flavor_tag_count={cov['flavor_tag_count']} 实际={tag_count}")
    if cov.get("featured_combo_count") and cov["featured_combo_count"] != combo_count:
        errors.append(f"coverage_model.featured_combo_count={cov['featured_combo_count']} 实际={combo_count}")

    if errors:
        print("VALIDATE FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK theme-matrix v{cfg.get('version')} tags={tag_count} featured={combo_count}")
    print(f"  emotions={len(emotions)} identity={len(_axis_values(cfg, 'identity'))} "
          f"conflict={len(_axis_values(cfg, 'conflict'))} world={len(_axis_values(cfg, 'world'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
