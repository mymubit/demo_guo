# -*- coding: utf-8 -*-
"""从 drama-skills/foundation/theme-matrix.yaml 加载题材矩阵 UI 配置。"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict, List

from apps.drama.skills_registry import _read_yaml, get_drama_skills_root

logger = logging.getLogger(__name__)

DEFAULT_DIM_ORDER = ["emotion", "identity", "conflict", "world"]
FEATURED_BADGES = (
    "经典爆款",
    "破圈潜力",
    "高爆款率",
    "新兴热点",
    "长尾优选",
    "热门组合",
    "创新杂交",
    "平台黑马",
)


@lru_cache(maxsize=1)
def load_theme_matrix_raw() -> Dict[str, Any]:
    root = get_drama_skills_root()
    path = root / "foundation" / "theme-matrix.yaml"
    data = _read_yaml(path)
    if not data:
        logger.warning("[theme_matrix] theme-matrix.yaml 未找到或为空: %s", path)
    return data


def clear_theme_matrix_cache() -> None:
    load_theme_matrix_raw.cache_clear()
    build_theme_matrix_ui_config.cache_clear()


def theme_code_from_dims(dims: Dict[str, Any], dim_order: List[str] | None = None) -> str:
    order = dim_order or DEFAULT_DIM_ORDER
    parts = [str(dims[axis]) for axis in order if dims.get(axis)]
    return "-".join(parts)


def build_matrix_theme_code(
    dims: Dict[str, Any],
    flavor_tags: List[str] | None = None,
    dim_order: List[str] | None = None,
) -> str:
    """与 theme-matrix.yaml resolve.matrix_key 对齐：四轴 + 可选风味标签。"""
    axis_code = theme_code_from_dims(dims, dim_order)
    if not axis_code:
        return ""
    tags = sorted({str(tag).strip() for tag in (flavor_tags or []) if str(tag).strip()})
    if not tags:
        return axis_code
    return f"{axis_code}|{'+'.join(tags)}"


def _group_flavor_options(
    categories: List[Dict[str, str]],
    options: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    label_map = {cat["id"]: cat["label"] for cat in categories}
    grouped: Dict[str, Dict[str, Any]] = {
        cat_id: {"id": cat_id, "label": label, "options": []}
        for cat_id, label in label_map.items()
    }
    for opt in options:
        cat_id = str(opt.get("category") or "").strip() or "uncategorized"
        if cat_id not in grouped:
            grouped[cat_id] = {
                "id": cat_id,
                "label": label_map.get(cat_id, cat_id),
                "options": [],
            }
        grouped[cat_id]["options"].append(opt)
    return [grouped[cat_id] for cat_id in label_map if grouped[cat_id]["options"]] + [
        grouped[cat_id]
        for cat_id in grouped
        if cat_id not in label_map and grouped[cat_id]["options"]
    ]


def _normalize_axis_options(options: Any) -> List[Dict[str, str]]:
    if not isinstance(options, list):
        return []
    normalized: List[Dict[str, str]] = []
    for opt in options:
        if not isinstance(opt, dict):
            continue
        value = str(opt.get("value") or "").strip()
        if not value:
            continue
        normalized.append(
            {
                "value": value,
                "label": str(opt.get("label_zh") or opt.get("label") or value),
                "desc": str(opt.get("desc") or ""),
            }
        )
    return normalized


def _normalize_dims(raw_dims: Any) -> Dict[str, Any]:
    if not isinstance(raw_dims, dict):
        return {}
    dims = dict(raw_dims)
    flavor_tags = dims.get("flavor_tags")
    if isinstance(flavor_tags, list):
        dims["flavor_tags"] = [str(tag) for tag in flavor_tags if tag]
    return dims


@lru_cache(maxsize=1)
def build_theme_matrix_ui_config() -> Dict[str, Any]:
    raw = load_theme_matrix_raw()
    if not raw:
        return {}

    dim_order = [str(axis) for axis in (raw.get("dim_order") or DEFAULT_DIM_ORDER)]
    axes_raw = raw.get("axes") if isinstance(raw.get("axes"), dict) else {}
    axes: Dict[str, Dict[str, Any]] = {}
    for axis_key in dim_order:
        axis = axes_raw.get(axis_key) if isinstance(axes_raw.get(axis_key), dict) else {}
        axes[axis_key] = {
            "label": str(axis.get("label_zh") or axis_key),
            "hint": str(axis.get("hint") or ""),
            "min_select": int(axis.get("min_select") or 1),
            "max_select": int(axis.get("max_select") or 1),
            "options": _normalize_axis_options(axis.get("options")),
        }

    preset_templates: List[Dict[str, Any]] = []
    for item in raw.get("preset_templates") or []:
        if not isinstance(item, dict):
            continue
        code = str(item.get("theme_code") or "").strip()
        if not code:
            continue
        dims = _normalize_dims(item.get("dims"))
        preset_templates.append(
            {
                "code": code,
                "label": str(item.get("label_zh") or code),
                "dims": dims,
            }
        )

    featured_combos: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw.get("featured_combos") or []):
        if not isinstance(item, dict):
            continue
        code = str(item.get("id") or "").strip()
        if not code:
            continue
        featured_combos.append(
            {
                "code": code,
                "label": str(item.get("label_zh") or code),
                "heat": FEATURED_BADGES[idx % len(FEATURED_BADGES)],
                "dims": _normalize_dims(item.get("dims")),
            }
        )

    flavor_raw = raw.get("flavor_tags") if isinstance(raw.get("flavor_tags"), dict) else {}
    flavor_options: List[Dict[str, str]] = []
    for opt in flavor_raw.get("options") or []:
        if not isinstance(opt, dict):
            continue
        value = str(opt.get("value") or "").strip()
        if not value:
            continue
        flavor_options.append(
            {
                "value": value,
                "label": str(opt.get("label_zh") or value),
                "category": str(opt.get("category") or ""),
            }
        )

    categories: List[Dict[str, str]] = []
    for cat in flavor_raw.get("categories") or []:
        if not isinstance(cat, dict):
            continue
        cat_id = str(cat.get("id") or "").strip()
        if not cat_id:
            continue
        categories.append(
            {
                "id": cat_id,
                "label": str(cat.get("label_zh") or cat_id),
            }
        )

    return {
        "version": str(raw.get("version") or ""),
        "dim_order": dim_order,
        "axes": axes,
        "preset_templates": preset_templates,
        "featured_combos": featured_combos,
        "flavor_tags": {
            "max_select": int(flavor_raw.get("max_select") or 5),
            "hint": str(flavor_raw.get("hint") or ""),
            "categories": categories,
            "options": flavor_options,
            "groups": _group_flavor_options(categories, flavor_options),
        },
    }
