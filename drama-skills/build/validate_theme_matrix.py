#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 theme-matrix.yaml：频道/轴/结构/标签/约束/合成 deltas 完整性与幂等性。"""
from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "foundation" / "theme-matrix.yaml"

sys.path.insert(0, str(ROOT / "build"))
from synthesize_matrix_params import synthesize_rule_params  # noqa: E402

VALID_TIERS = {"hot", "standard", "longtail"}


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
    orphan_deltas = tag_deltas - tags
    if orphan_deltas:
        errors.append(f"flavor_tag_deltas 存在孤儿标签: {sorted(orphan_deltas)}")

    cat_tags: Set[str] = set()
    for cat in (cfg.get("flavor_tags") or {}).get("categories") or []:
        cat_tags.update(cat.get("tags") or [])
    if cat_tags != tags:
        errors.append(f"categories 与 options 不一致: 缺 {sorted(tags - cat_tags)} 多 {sorted(cat_tags - tags)}")

    # 频道与主角结构：选项与 delta 必须闭合
    channel_opts = {o["value"] for o in (cfg.get("audience_channel") or {}).get("options") or []}
    channel_profiles = set((syn.get("channel_profiles") or {}).keys())
    if channel_opts != channel_profiles:
        errors.append(
            f"channel_profiles 与 audience_channel.options 不一致: "
            f"缺 {sorted(channel_opts - channel_profiles)} 多 {sorted(channel_profiles - channel_opts)}"
        )
    default_channel = (cfg.get("audience_channel") or {}).get("default")
    if default_channel not in channel_opts:
        errors.append(f"audience_channel.default={default_channel} 不在选项中")

    structure_opts = {o["value"] for o in (cfg.get("protagonist_structure") or {}).get("options") or []}
    structure_deltas = set((syn.get("structure_deltas") or {}).keys())
    if structure_opts != structure_deltas:
        errors.append(
            f"structure_deltas 与 protagonist_structure.options 不一致: "
            f"缺 {sorted(structure_opts - structure_deltas)} 多 {sorted(structure_deltas - structure_opts)}"
        )

    # tier 必须合法
    for opt in (cfg.get("flavor_tags") or {}).get("options") or []:
        if opt.get("tier") not in VALID_TIERS:
            errors.append(f"标签 {opt.get('value')} tier 非法: {opt.get('tier')}")

    # tag_constraints 引用必须真实存在
    constraints = cfg.get("tag_constraints") or {}
    worlds = _axis_values(cfg, "world")
    for group in constraints.get("mutually_exclusive") or []:
        for tag in group:
            if tag not in tags:
                errors.append(f"tag_constraints.mutually_exclusive 引用不存在标签: {tag}")
    for tag, allowed in (constraints.get("requires_world") or {}).items():
        if tag not in tags:
            errors.append(f"tag_constraints.requires_world 引用不存在标签: {tag}")
        for world in allowed or []:
            if world not in worlds:
                errors.append(f"tag_constraints.requires_world[{tag}] 引用不存在世界观: {world}")

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
        channel = dims.get("audience_channel")
        if channel and channel not in channel_opts:
            errors.append(f"featured {combo.get('id')} 无效 audience_channel: {channel}")
        structure = dims.get("protagonist_structure")
        if structure and structure not in structure_opts:
            errors.append(f"featured {combo.get('id')} 无效 protagonist_structure: {structure}")

    # 幂等性：标签乱序合成结果必须一致
    idempotency_dims = {
        "emotion": "justice",
        "identity": "returning-elite",
        "conflict": "family",
        "world": "modern",
        "audience_channel": "male",
        "protagonist_structure": "single-male",
        "flavor_tags": ["war-god", "urban-fantasy", "angst-revenge", "down-market"],
    }
    baseline = synthesize_rule_params(idempotency_dims)
    shuffled_tags = list(idempotency_dims["flavor_tags"])
    rng = random.Random(42)
    for _ in range(5):
        rng.shuffle(shuffled_tags)
        result = synthesize_rule_params({**idempotency_dims, "flavor_tags": list(shuffled_tags)})
        if result != baseline:
            errors.append(f"合成不幂等：标签顺序 {shuffled_tags} 与 baseline 结果不同")
            break

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
