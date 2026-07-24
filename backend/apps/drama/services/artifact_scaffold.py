# -*- coding: utf-8 -*-
"""产物 schema 必填骨架：LLM 漏字段时保证能过校验（占位，可后续修订覆盖）。"""
from __future__ import annotations

from typing import Any


def _title(settings: dict[str, Any]) -> str:
    for key in ("title", "core_idea"):
        value = settings.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "未命名短剧"


def _as_dict(raw: Any) -> dict[str, Any]:
    return dict(raw) if isinstance(raw, dict) else {}


def _missing(out: dict[str, Any], key: str) -> bool:
    return key not in out or out.get(key) is None


def scaffold_character_system(raw: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    out = _as_dict(raw)
    title = _title(settings)
    if _missing(out, "relationships") or not isinstance(out.get("relationships"), list):
        out["relationships"] = []
    chars = out.get("characters")
    if not isinstance(chars, list) or len(chars) == 0:
        out["characters"] = [_scaffold_v6_character(title)]
    else:
        out["characters"] = [
            _fill_v6_character(item, title=title, index=i) if isinstance(item, dict) else item
            for i, item in enumerate(chars)
        ]
    return out


def _scaffold_arc_point(ratio: float, label: str) -> dict[str, Any]:
    return {
        "episode_ratio": ratio,
        "trigger_event": f"{label}触发事件待细化",
        "state_after": f"{label}后状态待细化",
    }


def _scaffold_v6_character(title: str) -> dict[str, Any]:
    return {
        "id": "protagonist-1",
        "name": f"{title}主角",
        "role_type": "protagonist",
        "is_core": True,
        "surface_desire": "表面欲望待细化",
        "deep_need": "深层需要待细化",
        "ghost": "创伤背景待细化",
        "lie": "错误信念待细化",
        "flaw": "性格缺陷待细化",
        "contradiction": {"outward": "外在表现", "inner": "内在真实"},
        "arc": {
            "start": _scaffold_arc_point(0.0, "起点"),
            "turning_point_1": _scaffold_arc_point(0.3, "转折一"),
            "turning_point_2": _scaffold_arc_point(0.7, "转折二"),
            "end": _scaffold_arc_point(1.0, "结局"),
        },
        "voice_tag": {
            "vocabulary": "用词待细化",
            "sentence_style": "句式待细化",
            "avoidance": "回避点待细化",
        },
        "visual_anchor": {
            "type": "prop",
            "description": "视觉锚点待细化",
            "recognition_action": "识别动作待细化",
        },
    }


def _fill_v6_character(raw: dict[str, Any], *, title: str, index: int) -> dict[str, Any]:
    out = dict(raw)
    base = _scaffold_v6_character(title)
    if index > 0:
        base["id"] = f"character-{index + 1}"
        base["name"] = f"{title}角色{index + 1}"
        base["role_type"] = "supporting"
        base["is_core"] = False
    for key, value in base.items():
        if key == "arc":
            continue
        if _missing(out, key) or out.get(key) in ("", None):
            out[key] = value
    if _missing(out, "arc") or not isinstance(out.get("arc"), dict):
        out["arc"] = base["arc"]
    else:
        arc = dict(out["arc"])
        for point_key, point_val in base["arc"].items():
            if _missing(arc, point_key) or not isinstance(arc.get(point_key), dict):
                arc[point_key] = point_val
            else:
                pt = dict(arc[point_key])
                for pk, pv in point_val.items():
                    if _missing(pt, pk) or pt.get(pk) in ("", None):
                        pt[pk] = pv
                arc[point_key] = pt
        out["arc"] = arc
    for nested_key in ("contradiction", "voice_tag", "visual_anchor"):
        if not isinstance(out.get(nested_key), dict):
            out[nested_key] = base[nested_key]
            continue
        nested = dict(out[nested_key])
        for pk, pv in base[nested_key].items():
            if _missing(nested, pk) or nested.get(pk) in ("", None):
                nested[pk] = pv
        out[nested_key] = nested
    return out


def scaffold_world_system(raw: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    out = _as_dict(raw)
    title = _title(settings)
    if not isinstance(out.get("setting_summary"), str) or len(out["setting_summary"].strip()) < 10:
        if _missing(out, "setting_summary") or out.get("setting_summary") in ("", None):
            out["setting_summary"] = f"{title}的故事世界设定概述待细化补充"
    rule_id = "world-rule-core"
    if _missing(out, "rules") or not isinstance(out.get("rules"), list) or len(out["rules"]) == 0:
        out["rules"] = [
            {
                "id": rule_id,
                "name": "核心规则",
                "applies_to": ["主角"],
                "trigger_conditions": ["关键冲突发生时"],
                "changes": [{"dimension": "choice", "description": "可选行动发生变化"}],
                "violation_cost": "违反将付出代价",
                "visible_expression": "规则通过场景可见表达",
                "authority": "规则制定方",
                "exceptions": [],
            }
        ]
    if _missing(out, "power_structure") or not isinstance(out.get("power_structure"), dict):
        out["power_structure"] = {
            "resources": [
                {
                    "id": "resource-core",
                    "resource": "核心资源",
                    "controller": "控制方",
                    "rule_maker": "规则方",
                    "cost_bearer": "代价方",
                    "main_conflict_pressure": "主冲突压力来源待细化",
                }
            ],
            "loopholes": [
                {
                    "id": "loophole-core",
                    "rule_id": rule_id,
                    "available_to": ["主角"],
                    "condition": "特定条件满足时",
                    "cost": "使用漏洞需付代价",
                }
            ],
        }
    if _missing(out, "reveal_plan") or not isinstance(out.get("reveal_plan"), list):
        out["reveal_plan"] = []
    return out


def scaffold_emotion_system(raw: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    out = _as_dict(raw)
    node = {
        "index": 1,
        "event": "事件节点待细化",
        "emotion": "紧张",
        "value": 5,
        "character_action": "角色行动",
    }
    nodes = []
    for i in range(1, 9):
        row = dict(node)
        row["index"] = i
        row["event"] = f"第{i}情绪节点事件"
        nodes.append(row)
    if _missing(out, "series_curve") or not isinstance(out.get("series_curve"), list) or len(out["series_curve"]) == 0:
        out["series_curve"] = [
            {
                "episode": 1,
                "target_value": 5,
                "tone": "setup",
                "kind": "normal",
                "event": "开篇事件待细化",
                "character_choice": "角色选择待细化",
                "rhythm": {"plot": "medium", "emotional": "medium"},
            }
        ]
    if (
        _missing(out, "episode_profiles")
        or not isinstance(out.get("episode_profiles"), list)
        or len(out["episode_profiles"]) == 0
    ):
        out["episode_profiles"] = [
            {
                "episode": 1,
                "nodes": nodes,
                "landmarks": {"EV": 2, "ET": 5, "TP": 7},
                "qdn_evidence": {
                    "quality": "质量证据待细化",
                    "depth": "深度证据待细化",
                    "need_satisfaction": "需求满足证据待细化",
                },
                "rhythm": {"plot": "medium", "emotional": "medium"},
            }
        ]
    return out


def scaffold_originality_report(raw: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    out = _as_dict(raw)
    classes = [
        "character-name",
        "title-or-slogan",
        "key-plot-structure",
        "signature-dialogue",
        "character-image-or-voiceprint",
        "target-market-rights",
    ]
    if _missing(out, "comparison_status") or out.get("comparison_status") in ("", None):
        out["comparison_status"] = "not-completed"
    if (
        _missing(out, "protected_elements")
        or not isinstance(out.get("protected_elements"), list)
        or len(out["protected_elements"]) != 6
    ):
        out["protected_elements"] = [
            {"class": c, "status": "not-checked", "evidence": "待核验"} for c in classes
        ]
    if _missing(out, "similarity") or not isinstance(out.get("similarity"), dict):
        out["similarity"] = {
            "title_semantic": None,
            "dialogue": None,
            "episode_position_structure": None,
        }
    if _missing(out, "findings") or not isinstance(out.get("findings"), list):
        out["findings"] = []
    if "rewrite_plan" not in out:
        out["rewrite_plan"] = None
    if _missing(out, "ai_assets") or not isinstance(out.get("ai_assets"), list):
        out["ai_assets"] = []
    if _missing(out, "conclusion") or out.get("conclusion") in ("", None):
        out["conclusion"] = "not-completed"
    return out


def scaffold_episode_plan(raw: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    out = _as_dict(raw)
    title = _title(settings)
    if out.get("schema_version") != 2:
        if _missing(out, "schema_version"):
            out["schema_version"] = 2
    if not isinstance(out.get("artifact_version"), int) or out["artifact_version"] < 1:
        if _missing(out, "artifact_version"):
            out["artifact_version"] = 1
    if _missing(out, "based_on") or not isinstance(out.get("based_on"), dict):
        out["based_on"] = {"story_bible": 1}
    else:
        based = dict(out["based_on"])
        if not isinstance(based.get("story_bible"), int) or based["story_bible"] < 1:
            based["story_bible"] = 1
        out["based_on"] = based
    emotion_node = {
        "event": "情绪事件待细化补充",
        "emotion": "紧张",
        "intensity": 5,
        "character_action": "行动",
    }
    if _missing(out, "episodes") or not isinstance(out.get("episodes"), list) or len(out["episodes"]) == 0:
        out["episodes"] = [
            {
                "episode": 1,
                "title": f"{title}第1集",
                "core_event": "本集核心事件待细化补充说明",
                "goal_conflict": "目标与冲突待细化",
                "characters": [f"{title}主角"],
                "opening_hook": "开场钩子待细化",
                "ending_hook": "集末钩子待细化",
                "hook_grade": "B",
                "satisfaction_points": ["爽点待细化"],
                "reversal": "反转点待细化",
                "emotion_nodes": {
                    "EV": dict(emotion_node),
                    "ET": dict(emotion_node),
                    "TP": dict(emotion_node),
                },
                "paywall": None,
                "foreshadowing": [],
                "rhythm_tag": "medium-medium",
            }
        ]
    return out


def scaffold_memory_checkpoint(raw: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    out = _as_dict(raw)
    if not isinstance(out.get("episode"), int) or out["episode"] < 1:
        if _missing(out, "episode"):
            out["episode"] = 1
    for key in ("character_states", "active_clues", "foreshadowing", "next_episode_constraints"):
        if _missing(out, key) or not isinstance(out.get(key), list):
            out[key] = []
    if _missing(out, "rhythm_state") or not isinstance(out.get("rhythm_state"), dict):
        out["rhythm_state"] = {
            "plot_pace": "medium",
            "emotion_pace": "medium",
            "episode_ev": 5,
        }
    else:
        rhythm = dict(out["rhythm_state"])
        if rhythm.get("plot_pace") not in {"loose", "medium", "tight"}:
            if _missing(rhythm, "plot_pace") or rhythm.get("plot_pace") in ("", None):
                rhythm["plot_pace"] = "medium"
        if rhythm.get("emotion_pace") not in {"light", "medium", "heavy"}:
            if _missing(rhythm, "emotion_pace") or rhythm.get("emotion_pace") in ("", None):
                rhythm["emotion_pace"] = "medium"
        if not isinstance(rhythm.get("episode_ev"), int):
            if _missing(rhythm, "episode_ev"):
                rhythm["episode_ev"] = 5
        out["rhythm_state"] = rhythm
    return out


def scaffold_episode_scripts(raw: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    out = _as_dict(raw)
    title = _title(settings)
    if _missing(out, "episodes") or not isinstance(out.get("episodes"), list) or len(out["episodes"]) == 0:
        checkpoint = scaffold_memory_checkpoint({}, settings)
        out["episodes"] = [
            {
                "episode_number": 1,
                "title": f"{title}第1集",
                "script": "1-1 场景\n角色：对白待细化。",
                "word_count": 20,
                "dialogue_ratio": 0.5,
                "scene_count": 1,
                "memory_checkpoint": checkpoint,
                "production_notes": {
                    "tags": ["placeholder"],
                    "complexity_score": 1,
                    "complexity_band": "lean",
                    "high_cost_scenes": [],
                    "lower_cost_alternatives": [],
                },
            }
        ]
    else:
        filled = []
        for ep in out["episodes"]:
            if not isinstance(ep, dict):
                filled.append(ep)
                continue
            row = dict(ep)
            if _missing(row, "memory_checkpoint") or not isinstance(row.get("memory_checkpoint"), dict):
                row["memory_checkpoint"] = scaffold_memory_checkpoint({}, settings)
            else:
                row["memory_checkpoint"] = scaffold_memory_checkpoint(
                    row["memory_checkpoint"], settings
                )
            if _missing(row, "production_notes") or not isinstance(row.get("production_notes"), dict):
                row["production_notes"] = {
                    "tags": [],
                    "complexity_score": 1,
                    "complexity_band": "lean",
                    "high_cost_scenes": [],
                    "lower_cost_alternatives": [],
                }
            for key, default in (
                ("episode_number", 1),
                ("title", f"{title}分集"),
                ("script", "正文待细化"),
                ("word_count", 1),
                ("dialogue_ratio", 0.5),
                ("scene_count", 1),
            ):
                if _missing(row, key) or row.get(key) in ("", None):
                    row[key] = default
            filled.append(row)
        out["episodes"] = filled
    return out


def scaffold_production_package(raw: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    out = _as_dict(raw)
    title = _title(settings)
    if not isinstance(out.get("drama_title"), str) or not out["drama_title"].strip():
        out["drama_title"] = title
    out["source_artifact"] = "latest_script"
    for key in ("storyboard", "visual_assets", "marketing_assets"):
        if _missing(out, key) or not isinstance(out.get(key), list):
            out[key] = []
    if _missing(out, "production_plan") or not isinstance(out.get("production_plan"), dict):
        out["production_plan"] = {
            "complexity_score": 1,
            "complexity_band": "lean",
            "cost_drivers": [],
            "high_cost_scenes": [],
            "lower_cost_alternatives": [],
        }
    else:
        plan = dict(out["production_plan"])
        if not isinstance(plan.get("complexity_score"), int):
            if _missing(plan, "complexity_score"):
                plan["complexity_score"] = 1
        if plan.get("complexity_band") not in {"lean", "standard", "complex"}:
            if _missing(plan, "complexity_band") or plan.get("complexity_band") in ("", None):
                plan["complexity_band"] = "lean"
        for key in ("cost_drivers", "high_cost_scenes", "lower_cost_alternatives"):
            if _missing(plan, key) or not isinstance(plan.get(key), list):
                plan[key] = []
        out["production_plan"] = plan
    if _missing(out, "release_checklist") or not isinstance(out.get("release_checklist"), dict):
        out["release_checklist"] = {
            "target_platform": "generic",
            "policy_version": None,
            "verified_at": None,
            "blocking_items": [],
            "missing_materials": [],
            "can_release": False,
        }
    else:
        check = dict(out["release_checklist"])
        if check.get("target_platform") not in {
            "generic",
            "douyin",
            "kuaishou",
            "wechat_miniprogram",
        }:
            if _missing(check, "target_platform") or check.get("target_platform") in ("", None):
                check["target_platform"] = "generic"
        for key in ("blocking_items", "missing_materials"):
            if _missing(check, key) or not isinstance(check.get(key), list):
                check[key] = []
        if "policy_version" not in check:
            check["policy_version"] = None
        if "verified_at" not in check:
            check["verified_at"] = None
        if not isinstance(check.get("can_release"), bool):
            if _missing(check, "can_release"):
                check["can_release"] = False
        out["release_checklist"] = check
    return out
