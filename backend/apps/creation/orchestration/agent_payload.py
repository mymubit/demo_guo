# -*- coding: utf-8 -*-
"""Agent LLM 产物解包与结构归一化（修复嵌套 JSON / 空 episodes 等联调问题）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def unwrap_llm_payload(skill_id: str, payload: Any) -> dict:
    """将 LLM 返回的外层包装展开为可 merge 的业务 dict。"""
    if not isinstance(payload, dict):
        if isinstance(payload, list):
            return _episode_wrapper(payload, skill_id)
        return {}

    out = dict(payload)

    for wrapper in (
        "seriesOutline",
        "structurePlan",
        "characterBible",
        "episodeScripts",
        "projectBrief",
    ):
        inner = out.get(wrapper)
        if isinstance(inner, dict):
            merged = dict(inner)
            for key, val in out.items():
                if key != wrapper and val is not None:
                    merged.setdefault(key, val)
            out = merged
            break

    if skill_id == "relationship-weaver":
        rels = out.get("relationships")
        if isinstance(rels, list) and not out.get("relationshipMap"):
            out["relationshipMap"] = rels

    episodes = out.get("episodes")
    if isinstance(episodes, dict):
        out["episodes"] = [episodes]

    return out


def _episode_wrapper(episodes: List[Any], skill_id: str) -> dict:
    cleaned = [e for e in episodes if isinstance(e, dict)]
    if skill_id == "episode-script-writer":
        return {"episodes": cleaned}
    if skill_id == "episode-outline-writer":
        return {"episodes": cleaned}
    return {"episodes": cleaned}


def coerce_outline_chunk(chunk: Any) -> dict:
    """大纲 LLM 块：兼容 episodes 单对象 / 整包 seriesOutline。"""
    base = unwrap_llm_payload("episode-outline-writer", chunk)
    eps = base.get("episodes") or []
    if not eps and base.get("episodeNumber") is not None:
        base["episodes"] = [base]
    if isinstance(base.get("episodes"), dict):
        base["episodes"] = [base["episodes"]]
    return base


def coerce_script_chunk(chunk: Any) -> dict:
    """剧本 LLM 块：兼容 episodes 单对象 / 顶层单集字段。"""
    base = unwrap_llm_payload("episode-script-writer", chunk)
    eps = base.get("episodes") or []
    if not eps and base.get("episodeNumber") is not None:
        row = dict(base)
        row.pop("episodes", None)
        base = {k: v for k, v in base.items() if k not in ("episodeNumber", "scenes", "scriptMarkdown")}
        base["episodes"] = [row]
    if isinstance(base.get("episodes"), dict):
        base["episodes"] = [base["episodes"]]
    return base


def coerce_character_chunk(chunk: Any) -> dict:
    return unwrap_llm_payload("character-generator", chunk)


def fixer_patch_meaningful(patch: dict) -> bool:
    """fixer 是否返回了可合并的有效字段。"""
    if not isinstance(patch, dict) or not patch:
        return False
    ignore = frozenset(
        {
            "validationIssues",
            "nodeId",
            "nodeName",
            "projectBrief",
            "structurePlan",
            "seriesOutline",
            "characterBible",
        }
    )
    for key, val in patch.items():
        if key in ignore:
            continue
        if val is None:
            continue
        if isinstance(val, (list, dict)) and not val:
            continue
        if isinstance(val, str) and not val.strip():
            continue
        return True
    return False


def extract_fixer_patch(skill_id: str, patch: dict) -> dict:
    """plan-fixer / world-fixer 可能返回整包或仅补丁。"""
    out = unwrap_llm_payload(skill_id, patch)
    if skill_id == "plan-fixer" and isinstance(out.get("seriesOutline"), dict):
        return out["seriesOutline"]
    if skill_id == "world-fixer" and isinstance(out.get("structurePlan"), dict):
        return out["structurePlan"]
    return out
