# -*- coding: utf-8 -*-
"""人物圣经产物：LLM 稀疏输出 → schema 对齐 + 原型索引补全。"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

from .display.character_display import dedupe_relationships, resolve_relationship_endpoints

NODE_ID = "node-3-character"
NODE_NAME = "人设开发节点"

_ROLE_BUCKETS = (
    ("protagonists", ("protagonist-female", "protagonist-male", "protagonist")),
    ("antagonists", ("antagonist-female", "antagonist-male", "antagonist")),
    ("supportingRoles", ("supporting", "cameo")),
)


def _slug_id(name: str, prefix: str = "char") -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", (name or "").strip()).strip("-").lower()
    return f"{prefix}-{slug or 'unknown'}"


def _ensure_char_id(char: dict, seen: set[str]) -> dict:
    row = dict(char)
    cid = (row.get("id") or row.get("characterId") or "").strip()
    name = (row.get("name") or "").strip()
    if not cid:
        cid = _slug_id(name)
    base = cid
    n = 2
    while cid in seen:
        cid = f"{base}-{n}"
        n += 1
    seen.add(cid)
    row["id"] = cid
    row.setdefault("name", name or cid)
    return row


def _bucket_role(role: str) -> str:
    r = (role or "").strip().lower()
    if r.startswith("protagonist"):
        return "protagonists"
    if r.startswith("antagonist"):
        return "antagonists"
    return "supportingRoles"


@lru_cache(maxsize=1)
def load_archetype_index() -> Dict[str, str]:
    try:
        from apps.skill.config.portal.reference_libs import ReferenceLibraryService

        data = ReferenceLibraryService.get_json("character-archetypes.json")
        index: Dict[str, str] = {}
        for label, meta in (data.get("archetypes") or {}).items():
            if not isinstance(meta, dict):
                continue
            code = (meta.get("code") or "").strip()
            if code:
                index[code] = str(label)
        return index
    except Exception:  # noqa: BLE001
        return {}


def _normalize_relationship(item: dict, id_to_name: Dict[str, str], characters: List[dict]) -> Optional[dict]:
    if not isinstance(item, dict):
        return None
    row = resolve_relationship_endpoints(item, characters)
    if not row.get("description") and not (row.get("characterAName") and row.get("characterBName")):
        return None
    return {
        "characterAId": row.get("characterAId") or "",
        "characterBId": row.get("characterBId") or "",
        "characterAName": row.get("characterAName") or "",
        "characterBName": row.get("characterBName") or "",
        "relationType": row.get("relationType") or "other",
        "description": row.get("description") or "",
        "evolutionPath": row.get("evolutionPath") or "",
        "perspectiveA": row.get("perspectiveA") or "",
        "perspectiveB": row.get("perspectiveB") or "",
        "coreConflict": row.get("coreConflict") or "",
        "hiddenTension": row.get("hiddenTension") or "",
    }


def normalize_character_bible_payload(
    payload: dict,
    *,
    theme: str = "",
    archetype_refs: Optional[dict] = None,
) -> dict:
    """生成后归一化：分桶角色、关系图、原型索引。"""
    if not isinstance(payload, dict):
        return {}

    out = dict(payload)
    out.setdefault("nodeId", NODE_ID)
    out.setdefault("nodeName", NODE_NAME)

    seen_ids: set[str] = set()
    buckets: Dict[str, List[dict]] = {
        "protagonists": [],
        "antagonists": [],
        "supportingRoles": [],
    }

    has_buckets = any(isinstance(out.get(k), list) and out.get(k) for k in buckets)
    flat = out.get("characters") or []

    if has_buckets:
        for key in buckets:
            rows = []
            for c in out.get(key) or []:
                if isinstance(c, dict):
                    rows.append(_ensure_char_id(c, seen_ids))
            buckets[key] = rows
    elif isinstance(flat, list) and flat:
        for c in flat:
            if not isinstance(c, dict):
                continue
            row = _ensure_char_id(c, seen_ids)
            buckets[_bucket_role(row.get("roleType") or row.get("role") or "")].append(row)
    else:
        for key in buckets:
            for c in out.get(key) or []:
                if isinstance(c, dict):
                    buckets[key].append(_ensure_char_id(c, seen_ids))

    if not buckets["protagonists"] and buckets["supportingRoles"]:
        buckets["protagonists"].append(buckets["supportingRoles"].pop(0))
    if not buckets["antagonists"] and len(buckets["supportingRoles"]) > 1:
        buckets["antagonists"].append(buckets["supportingRoles"].pop(0))

    out["protagonists"] = buckets["protagonists"]
    out["antagonists"] = buckets["antagonists"]
    out["supportingRoles"] = buckets["supportingRoles"]

    id_to_name = {
        c["id"]: c.get("name") or ""
        for group in buckets.values()
        for c in group
        if c.get("id")
    }
    all_chars = [c for group in buckets.values() for c in group]

    rel_map: List[dict] = []
    seen_keys: set[tuple] = set()
    for src_key in ("relationshipMap", "relationships"):
        for item in out.get(src_key) or []:
            row = _normalize_relationship(item, id_to_name, all_chars)
            if not row:
                continue
            key = (
                tuple(sorted([
                    (row.get("characterAName") or "").strip(),
                    (row.get("characterBName") or "").strip(),
                ])),
                (row.get("relationType") or "").strip(),
                (row.get("description") or "").strip()[:120],
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            rel_map.append(row)
    out["relationshipMap"] = dedupe_relationships(rel_map)

    if not (out.get("relationshipSummary") or "").strip() and rel_map:
        parts = [
            f"{r.get('characterAName')} ↔ {r.get('characterBName')}：{r.get('description', '')[:80]}"
            for r in rel_map[:6]
            if r.get("description")
        ]
        out["relationshipSummary"] = "\n".join(parts)

    codes: List[str] = []
    for group in buckets.values():
        for c in group:
            code = (c.get("archetypeCode") or "").strip()
            if code and code not in codes:
                codes.append(code)
    out["archetypeCodes"] = codes or out.get("archetypeCodes") or ["other"]

    index = dict(load_archetype_index())
    if isinstance(out.get("archetypeIndex"), dict):
        index.update({k: v for k, v in out["archetypeIndex"].items() if k and v})
    if isinstance(archetype_refs, dict):
        for block in archetype_refs.get("blocks") or []:
            if block.get("file") == "character-archetypes.json":
                excerpt = block.get("excerpt")
                if isinstance(excerpt, dict):
                    for label, meta in excerpt.items():
                        if isinstance(meta, dict) and meta.get("code"):
                            index[meta["code"]] = str(label)
    out["archetypeIndex"] = index

    total = sum(len(buckets[k]) for k in buckets)
    out["characterCount"] = total or out.get("characterCount") or 0
    return out
