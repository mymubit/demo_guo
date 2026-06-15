# -*- coding: utf-8 -*-
"""人设开发产物：Fusion character-bible schema ↔ C 端展示。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

ROLE_LABELS = {
    "protagonist-female": "女主",
    "protagonist-male": "男主",
    "protagonist": "主角",
    "antagonist-female": "女反派",
    "antagonist-male": "男反派",
    "antagonist": "反派",
    "supporting": "配角",
    "cameo": "客串",
}

RELATION_LABELS = {
    "parent-child": "亲子",
    "spouse": "夫妻",
    "sibling": "兄弟姐妹",
    "romantic-lover": "恋人",
    "enemy": "敌对",
    "friend-confidant": "挚友",
    "mentor-protege": "师徒",
    "colleague": "同事",
    "ex-lover": "前任",
    "business-partner": "商业伙伴",
    "secret-identity": "隐藏身份",
    "other": "其他",
}

GENDER_LABELS = {"female": "女", "male": "男", "other": "其他"}

_PLACEHOLDER_ENDPOINTS = frozenset({"a-unknown", "b-unknown", "unknown", ""})


def _contains_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in (text or ""))


def _is_ascii_slug(text: str) -> bool:
    s = (text or "").strip()
    if not s or _contains_chinese(s):
        return False
    return all(ch.isascii() and (ch.isalnum() or ch in "-_/") for ch in s)


def _relation_type_label(rtype: str) -> str:
    r = (rtype or "").strip()
    if not r:
        return "关联"
    if r in RELATION_LABELS:
        return RELATION_LABELS[r]
    if _contains_chinese(r):
        return r
    return "其他"


def _code_display_label(code: str, mapping: Dict[str, str]) -> str:
    c = (code or "").strip()
    if not c:
        return ""
    if c in mapping:
        return mapping[c]
    if _contains_chinese(c):
        return c
    return ""


def _is_placeholder_endpoint(value: str) -> bool:
    v = (value or "").strip().lower()
    if not v or v in _PLACEHOLDER_ENDPOINTS:
        return True
    return v.endswith("-unknown")


def _names_mentioned_in_text(text: str, names: List[str]) -> List[str]:
    """按在描述中出现的位置排序，返回命中的角色名。"""
    if not text:
        return []
    hits: List[tuple[int, str]] = []
    seen: set[str] = set()
    for name in names:
        n = (name or "").strip()
        if not n or n in seen:
            continue
        pos = text.find(n)
        if pos >= 0:
            hits.append((pos, n))
            seen.add(n)
    hits.sort(key=lambda item: item[0])
    return [name for _, name in hits]


def _role_gender(role_type: str) -> str:
    rt = str(role_type or "").lower()
    if "female" in rt:
        return "female"
    if "male" in rt:
        return "male"
    return ""


def _pick_protagonist(characters: List[dict], gender: Optional[str] = None) -> Optional[dict]:
    prots = [c for c in characters if str(c.get("roleType") or "").startswith("protagonist")]
    if gender == "female":
        for c in prots:
            if _role_gender(str(c.get("roleType") or "")) == "female":
                return c
        return prots[0] if prots else None
    if gender == "male":
        for c in prots:
            if _role_gender(str(c.get("roleType") or "")) == "male":
                return c
        return prots[1] if len(prots) > 1 else (prots[0] if prots else None)
    return prots[0] if prots else None


def _pick_antagonist(characters: List[dict]) -> Optional[dict]:
    for c in characters:
        if str(c.get("roleType") or "").startswith("antagonist"):
            return c
    return None


def _infer_missing_endpoints(
    a_name: str,
    b_name: str,
    item: dict,
    characters: List[dict],
    desc: str,
) -> tuple[str, str]:
    rtype = (item.get("relationType") or item.get("type") or "").strip()
    label = _relation_type_label(rtype)
    ctx = f"{rtype} {label} {desc}"

    lover_hints = ("恋人", "情侣", "宠物", "主人", "romantic", "lover", "陌生人")
    friend_hints = ("闺蜜", "挚友", "朋友", "friend", "confidant")
    enemy_hints = ("仇敌", "敌对", "enemy", "势不两立")

    if not a_name and not b_name:
        if any(h in ctx for h in lover_hints):
            pf = _pick_protagonist(characters, "female")
            pm = _pick_protagonist(characters, "male")
            if pf and pm:
                return (pf.get("name") or "").strip(), (pm.get("name") or "").strip()
        if any(h in ctx for h in enemy_hints):
            ant = _pick_antagonist(characters)
            prot = _pick_protagonist(characters)
            if ant and prot:
                return (ant.get("name") or "").strip(), (prot.get("name") or "").strip()

    if a_name and not b_name:
        if any(h in ctx for h in friend_hints) or "女主" in ctx:
            pf = _pick_protagonist(characters, "female")
            if pf and (pf.get("name") or "").strip() != a_name:
                b_name = (pf.get("name") or "").strip()
        if not b_name and any(h in ctx for h in lover_hints):
            pm = _pick_protagonist(characters, "male")
            if pm and (pm.get("name") or "").strip() != a_name:
                b_name = (pm.get("name") or "").strip()
        if not b_name and any(h in ctx for h in enemy_hints):
            ant = _pick_antagonist(characters)
            if ant and (ant.get("name") or "").strip() != a_name:
                b_name = (ant.get("name") or "").strip()
            else:
                prot = _pick_protagonist(characters)
                if prot and (prot.get("name") or "").strip() != a_name:
                    b_name = (prot.get("name") or "").strip()

    if not a_name and b_name:
        if any(h in ctx for h in friend_hints) or "女主" in ctx:
            pf = _pick_protagonist(characters, "female")
            if pf and (pf.get("name") or "").strip() != b_name:
                a_name = (pf.get("name") or "").strip()
        if not a_name and any(h in ctx for h in lover_hints):
            pf = _pick_protagonist(characters, "female")
            if pf and (pf.get("name") or "").strip() != b_name:
                a_name = (pf.get("name") or "").strip()

    return a_name, b_name


def _extract_endpoint_name(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return (value.get("name") or value.get("characterName") or "").strip()
    return ""


def _match_character_id(name: str, characters: List[dict]) -> str:
    n = (name or "").strip()
    if not n:
        return ""
    for c in characters:
        if (c.get("name") or "").strip() == n and c.get("id"):
            return str(c["id"])
    if len(n) < 2:
        return ""
    fuzzy: List[dict] = []
    for c in characters:
        full = (c.get("name") or "").strip()
        if not full or not c.get("id") or len(full) < 2:
            continue
        if n in full or full in n or full.startswith(n) or n.startswith(full):
            fuzzy.append(c)
    if len(fuzzy) == 1:
        return str(fuzzy[0]["id"])
    return ""


def resolve_relationship_endpoints(
    item: dict,
    characters: List[dict],
) -> dict:
    """补全关系两端 ID/姓名（LLM 常只写 description）。"""
    if not isinstance(item, dict):
        return {}

    names = [(c.get("name") or "").strip() for c in characters if (c.get("name") or "").strip()]
    names_sorted = sorted(names, key=len, reverse=True)
    id_to_name = {c["id"]: c.get("name") or "" for c in characters if c.get("id")}
    name_to_id = {c.get("name") or "": c["id"] for c in characters if c.get("name") and c.get("id")}

    desc = (item.get("description") or item.get("summary") or "").strip()
    a_id = (item.get("characterAId") or item.get("fromId") or item.get("from") or "").strip()
    b_id = (item.get("characterBId") or item.get("toId") or item.get("to") or "").strip()
    a_name = (
        item.get("characterAName")
        or item.get("fromName")
        or _extract_endpoint_name(item.get("characterA"))
        or _extract_endpoint_name(item.get("aCharacter"))
        or ""
    ).strip()
    b_name = (
        item.get("characterBName")
        or item.get("toName")
        or _extract_endpoint_name(item.get("characterB"))
        or _extract_endpoint_name(item.get("bCharacter"))
        or ""
    ).strip()

    if _is_placeholder_endpoint(a_name):
        a_name = ""
    if _is_placeholder_endpoint(b_name):
        b_name = ""
    if _is_placeholder_endpoint(a_id):
        a_id = ""
    if _is_placeholder_endpoint(b_id):
        b_id = ""

    if a_id and not a_name:
        a_name = (id_to_name.get(a_id) or "").strip()
    if b_id and not b_name:
        b_name = (id_to_name.get(b_id) or "").strip()

    if a_name and not a_id:
        a_id = name_to_id.get(a_name) or _match_character_id(a_name, characters)
    if b_name and not b_id:
        b_id = name_to_id.get(b_name) or _match_character_id(b_name, characters)

    mentioned = _names_mentioned_in_text(desc, names_sorted)
    if mentioned:
        if not a_name:
            a_name = mentioned[0]
        if not b_name:
            b_name = next((n for n in mentioned if n != a_name), "")

    a_name, b_name = _infer_missing_endpoints(a_name, b_name, item, characters, desc)

    if a_name and not a_id:
        a_id = name_to_id.get(a_name) or _match_character_id(a_name, characters)
    if b_name and not b_id:
        b_id = name_to_id.get(b_name) or _match_character_id(b_name, characters)

    rtype = (item.get("relationType") or item.get("type") or "other").strip()
    rtype_label = _relation_type_label(rtype)

    return {
        "characterAId": a_id,
        "characterBId": b_id,
        "characterAName": a_name,
        "characterBName": b_name,
        "relationType": rtype,
        "relationTypeLabel": rtype_label,
        "description": desc,
        "evolutionPath": (item.get("evolutionPath") or "").strip(),
        "perspectiveA": (
            item.get("perspectiveA") or item.get("characterAPerspective") or item.get("aPerspective") or ""
        ).strip(),
        "perspectiveB": (
            item.get("perspectiveB") or item.get("characterBPerspective") or item.get("bPerspective") or ""
        ).strip(),
        "coreConflict": (item.get("coreConflict") or "").strip(),
        "hiddenTension": (item.get("hiddenTension") or "").strip(),
    }


def _normalize_creative_dna(payload: dict) -> dict:
    raw = payload.get("creativeDna") or payload.get("creativeDNA") or {}
    if not isinstance(raw, dict):
        return {}

    anti: List[dict] = []
    for item in raw.get("antiClicheElements") or raw.get("antiCliche") or []:
        if isinstance(item, dict):
            label = (item.get("label") or item.get("element") or "").strip()
            if label:
                anti.append(
                    {
                        "code": (item.get("code") or "").strip(),
                        "label": label,
                        "effect": (item.get("effect") or "").strip(),
                    }
                )
        elif isinstance(item, str) and item.strip():
            anti.append({"code": "", "label": item.strip(), "effect": ""})

    unique: List[dict] = []
    for item in raw.get("uniqueSettings") or []:
        if isinstance(item, dict):
            label = (item.get("label") or item.get("setting") or "").strip()
            if label:
                unique.append(
                    {
                        "code": (item.get("code") or "").strip(),
                        "label": label,
                        "example": (item.get("example") or "").strip(),
                    }
                )
        elif isinstance(item, str) and item.strip():
            unique.append({"code": "", "label": item.strip(), "example": ""})

    notes = [
        str(n).strip()
        for n in (raw.get("aiAuthenticityNotes") or raw.get("authenticityNotes") or [])
        if str(n).strip()
    ]
    if not anti and not unique and not notes:
        return {}
    return {
        "antiClicheElements": anti,
        "uniqueSettings": unique,
        "aiAuthenticityNotes": notes,
    }


def relationship_dedup_key(row: dict) -> tuple:
    """关系去重键：无序人物对 + 类型 + 描述摘要。"""
    a = (row.get("characterAName") or row.get("characterAId") or "").strip()
    b = (row.get("characterBName") or row.get("characterBId") or "").strip()
    pair = tuple(sorted([x for x in (a, b) if x]))
    rtype = (row.get("relationType") or row.get("relationTypeLabel") or "").strip()
    desc = (row.get("description") or "").strip()[:120]
    return (pair, rtype, desc)


def dedupe_relationships(rows: List[dict]) -> List[dict]:
    out: List[dict] = []
    seen: set[tuple] = set()
    for item in rows or []:
        if not isinstance(item, dict):
            continue
        key = relationship_dedup_key(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _char_one_liner(char: dict) -> str:
    for key in ("oneLineSummary", "summary", "coreMotivation"):
        val = (char.get(key) or "").strip()
        if val:
            return val[:200]
    surface = (char.get("surfacePersonality") or "").strip()
    if surface:
        return surface[:200]
    return ""


def _char_personality(char: dict) -> str:
    surface = (char.get("surfacePersonality") or "").strip()
    real = (char.get("realPersonality") or "").strip()
    legacy = (char.get("personality") or char.get("traits") or "").strip()
    if legacy:
        return legacy
    if surface and real:
        return f"表面：{surface}\n真实：{real}"
    return surface or real


def _as_string_list(val: Any) -> List[str]:
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, str) and val.strip():
        return [val.strip()]
    return []


def _as_joined_text(val: Any, sep: str = " · ") -> str:
    if isinstance(val, list):
        parts = [str(x).strip() for x in val if str(x).strip()]
        return sep.join(parts)
    if isinstance(val, str):
        return val.strip()
    return ""


def _normalize_voice_profile(char: dict) -> dict:
    vp = char.get("voiceProfile")
    if isinstance(vp, str) and vp.strip():
        return {"label": vp.strip(), "pitch": "", "pace": "", "summary": vp.strip()}
    if isinstance(vp, dict):
        label = (vp.get("label") or vp.get("voiceLabel") or "").strip()
        pitch = (vp.get("pitch") or vp.get("voicePitch") or "").strip()
        pace = (vp.get("pace") or vp.get("voicePace") or "").strip()
        summary = (vp.get("summary") or "").strip()
        if not summary and label:
            summary = f"{label}（音高{pitch or '中'} · 语速{pace or '中'} · AI配音参考）"
        return {"label": label, "pitch": pitch, "pace": pace, "summary": summary}
    label = (char.get("voiceLabel") or "").strip()
    pitch = (char.get("voicePitch") or "").strip()
    pace = (char.get("voicePace") or "").strip()
    if not label and not pitch and not pace:
        return {}
    summary = ""
    if isinstance(char.get("voiceProfile"), str):
        summary = char["voiceProfile"].strip()
    if not summary and label:
        summary = f"{label}（音高{pitch or '中'} · 语速{pace or '中'} · AI配音参考）"
    return {"label": label, "pitch": pitch, "pace": pace, "summary": summary}


def _normalize_behavior_profile(char: dict) -> dict:
    raw = char.get("behaviorProfile") if isinstance(char.get("behaviorProfile"), dict) else {}
    language = _as_string_list(raw.get("languageStyle") or char.get("languageStyle"))
    if not language:
        language = _as_string_list(char.get("speechPatterns"))
    return {
        "catchphrase": (raw.get("catchphrase") or char.get("catchphrase") or "").strip(),
        "habit": (raw.get("habit") or char.get("habit") or "").strip(),
        "languageStyle": language,
        "decisionLogic": _as_string_list(raw.get("decisionLogic") or char.get("decisionLogic")),
        "behaviorFeatures": _as_string_list(
            raw.get("behaviorFeatures") or char.get("behaviorFeatures") or char.get("behaviorFeature")
        ),
        "likes": _as_string_list(raw.get("likes") or char.get("likes")),
        "dislikes": _as_string_list(raw.get("dislikes") or char.get("dislikes")),
    }


def _normalize_visual_anchor(char: dict) -> dict:
    va = char.get("visualAnchor") if isinstance(char.get("visualAnchor"), dict) else {}
    behavior = char.get("behaviorProfile") if isinstance(char.get("behaviorProfile"), dict) else {}
    habit = (va.get("habitGestures") or behavior.get("habit") or char.get("habit") or "").strip()
    if isinstance(habit, str):
        habit = habit.strip()
    else:
        habit = ""
    return {
        "distinctiveFeatures": (va.get("distinctiveFeatures") or char.get("appearance") or "").strip(),
        "clothingStyle": (va.get("clothingStyle") or "").strip(),
        "habitGestures": habit,
        "consistencyRules": _as_string_list(va.get("consistencyRules")),
    }


def _role_type_label(role: str, gender: str = "") -> str:
    r = (role or "").strip()
    if r == "antagonist":
        if gender == "male":
            return "男反派"
        if gender == "female":
            return "女反派"
    if r == "protagonist":
        if gender == "female":
            return "女主"
        if gender == "male":
            return "男主"
    direct = ROLE_LABELS.get(r)
    if direct:
        return direct
    if r.startswith("antagonist"):
        return "反派"
    if r.startswith("protagonist"):
        return "主角"
    return r


def _merged_archetype_index(payload: dict) -> Dict[str, str]:
    index: Dict[str, str] = {}
    try:
        from ..character_enrichment import load_archetype_index

        index.update(load_archetype_index())
    except Exception:  # noqa: BLE001
        pass
    raw = payload.get("archetypeIndex") if isinstance(payload, dict) else {}
    if isinstance(raw, dict):
        for key, val in raw.items():
            if key and val:
                index[str(key)] = str(val).strip()
    return index


def _archetype_label(code: str, archetype_index: Optional[dict] = None) -> str:
    c = (code or "").strip()
    if not c:
        return ""
    if isinstance(archetype_index, dict):
        hit = (archetype_index.get(c) or "").strip()
        if hit:
            return hit
    return ""


def _normalize_contrast_relation(char: dict) -> dict:
    cr = char.get("contrastRelation") if isinstance(char.get("contrastRelation"), dict) else {}
    contrast_type = (cr.get("contrastType") or char.get("contrastType") or "").strip()
    contrast_desc = (cr.get("contrastDescription") or char.get("contrastDescription") or "").strip()
    if not contrast_type and not contrast_desc:
        return {}
    return {"contrastType": contrast_type, "contrastDescription": contrast_desc}


def _normalize_character(char: dict, archetype_index: Optional[dict] = None) -> dict:
    if not isinstance(char, dict):
        return {}
    role = char.get("roleType") or char.get("role") or ""
    arc = char.get("characterArc") if isinstance(char.get("characterArc"), dict) else {}
    archetype_code = char.get("archetypeCode") or ""
    archetype_label = _archetype_label(archetype_code, archetype_index)

    return {
        "id": char.get("id") or char.get("characterId") or char.get("name") or "",
        "name": char.get("name") or "",
        "roleType": role,
        "roleTypeLabel": _role_type_label(role, str(char.get("gender") or "")),
        "age": char.get("age"),
        "gender": char.get("gender") or "",
        "genderLabel": GENDER_LABELS.get(char.get("gender") or "", char.get("gender") or ""),
        "appearance": (char.get("appearance") or "").strip(),
        "oneLineSummary": _char_one_liner(char),
        "personality": _char_personality(char),
        "surfacePersonality": (char.get("surfacePersonality") or "").strip(),
        "realPersonality": (char.get("realPersonality") or "").strip(),
        "background": (char.get("background") or char.get("backstory") or "").strip(),
        "coreMotivation": (char.get("coreMotivation") or "").strip(),
        "shortTermGoal": (char.get("shortTermGoal") or "").strip(),
        "longTermGoal": (char.get("longTermGoal") or "").strip(),
        "secret": (char.get("secret") or "").strip(),
        "weakness": (char.get("weakness") or "").strip(),
        "characterArc": {
            "startingState": (arc.get("startingState") or "").strip(),
            "keyTurningPoints": [
                str(p).strip() for p in (arc.get("keyTurningPoints") or []) if str(p).strip()
            ],
            "finalState": (arc.get("finalState") or "").strip(),
        },
        "signatureLines": [
            str(l).strip() for l in (char.get("signatureLines") or []) if str(l).strip()
        ],
        "signatureDialogueStyle": _as_joined_text(char.get("signatureDialogueStyle")),
        "speechPatterns": [
            str(p).strip() for p in (char.get("speechPatterns") or []) if str(p).strip()
        ],
        "iconicProps": [str(p).strip() for p in (char.get("iconicProps") or []) if str(p).strip()],
        "archetypeCode": archetype_code,
        "archetypeLabel": archetype_label,
        "voiceProfile": _normalize_voice_profile(char),
        "behaviorProfile": _normalize_behavior_profile(char),
        "visualAnchor": _normalize_visual_anchor(char),
        "contrastRelation": _normalize_contrast_relation(char),
    }


def _collect_characters(payload: dict) -> List[dict]:
    archetype_index = _merged_archetype_index(payload)
    rows: List[dict] = []

    flat = payload.get("characters") or []
    if isinstance(flat, list) and flat:
        for c in flat:
            row = _normalize_character(c, archetype_index)
            if row.get("name"):
                rows.append(row)
        return rows

    for key in ("protagonists", "antagonists", "supportingRoles"):
        for c in payload.get(key) or []:
            row = _normalize_character(c, archetype_index)
            if row.get("name"):
                rows.append(row)
    return rows


def _relationship_summary(payload: dict) -> str:
    rel = (payload.get("relationshipSummary") or "").strip()
    if rel:
        return rel
    characters = _collect_characters(payload)
    parts: List[str] = []
    for item in payload.get("relationshipMap") or []:
        if not isinstance(item, dict):
            continue
        row = resolve_relationship_endpoints(item, characters)
        a = (row.get("characterAName") or "").strip()
        b = (row.get("characterBName") or "").strip()
        desc = (row.get("description") or "").strip()
        rtype = row.get("relationTypeLabel") or row.get("relationType") or ""
        if a and b and desc:
            parts.append(f"{a} ↔ {b}（{rtype}）：{desc}")
        elif desc:
            parts.append(desc)
    return "\n".join(parts)


def build_character_bible_view(payload: dict) -> dict:
    """C 端人设开发完整展示视图。"""
    if not isinstance(payload, dict):
        payload = {}

    archetype_codes = payload.get("archetypeCodes") or []
    if not isinstance(archetype_codes, list):
        archetype_codes = []

    archetype_index = _merged_archetype_index(payload)

    relationships = []
    characters = _collect_characters(payload)
    for item in payload.get("relationshipMap") or []:
        if not isinstance(item, dict):
            continue
        rel = resolve_relationship_endpoints(item, characters)
        if not rel.get("description") and not (
            rel.get("characterAName") and rel.get("characterBName")
        ):
            continue
        relationships.append(rel)
    relationships = dedupe_relationships(relationships)

    groups = {
        "protagonists": [c for c in characters if str(c.get("roleType", "")).startswith("protagonist")],
        "antagonists": [c for c in characters if str(c.get("roleType", "")).startswith("antagonist")],
        "supporting": [
            c
            for c in characters
            if c.get("roleType") in ("supporting", "cameo")
            or (
                not str(c.get("roleType", "")).startswith("protagonist")
                and not str(c.get("roleType", "")).startswith("antagonist")
            )
        ],
    }

    return {
        "summary": (payload.get("summary") or "").strip(),
        "relationshipSummary": _relationship_summary(payload),
        "archetypeCodes": archetype_codes,
        "archetypeIndex": archetype_index,
        "creativeDna": _normalize_creative_dna(payload),
        "characterCount": payload.get("characterCount") or len(characters),
        "characters": characters,
        "groups": groups,
        "relationships": relationships,
    }
