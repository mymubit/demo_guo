# -*- coding: utf-8 -*-
"""结构与世界观产物：Fusion schema ↔ C 端展示字段。"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

_CONFLICT_DENSITY_MAP = {"low": 0.6, "medium": 1.0, "high": 1.5}
_PLACEHOLDER_TITLE_RE = re.compile(r"^[\w-]+\s*·\s*\d{10,14}$")
_EP_GROUP_RE = re.compile(r"ep\s*(\d+)\s*[-–~至]\s*(\d+)", re.I)
_EP_RANGE_RE = re.compile(r"(\d+)\s*[-–~至]\s*(\d+)")
_EP_SINGLE_RE = re.compile(r"(\d+)")


def _join_dream_note_parts(parts: List[str]) -> str:
    cleaned: List[str] = []
    for part in parts:
        s = re.sub(r"[。；;、\s]+$", "", (part or "").strip())
        if s:
            cleaned.append(s)
    return "；".join(cleaned)[:800]


def _clean_dream_notes(text: str) -> str:
    s = (text or "").strip()
    if not s:
        return ""
    s = re.sub(r"。\s*；", "；", s)
    s = re.sub(r"；{2,}", "；", s)
    return _join_dream_note_parts(s.split("；"))


def _parse_episode_group_label(text: str) -> tuple[Optional[int], Optional[int], str]:
    raw = (text or "").strip()
    if not raw:
        return None, None, ""
    match = _EP_GROUP_RE.search(raw) or _EP_RANGE_RE.search(raw)
    if match:
        start, end = int(match.group(1)), int(match.group(2))
        label = str(start) if start == end else f"{start}-{end}"
        return start, end, label
    single = _EP_SINGLE_RE.search(raw)
    if single:
        num = int(single.group(1))
        return num, num, str(num)
    return None, None, raw


def normalize_rhythm_block(block: dict) -> dict:
    """兼容 episodeGroup / episodeStart+End，统一 episodeRange。"""
    if not isinstance(block, dict):
        return block
    out = dict(block)
    ep_range = (out.get("episodeRange") or "").strip()
    group = (out.get("episodeGroup") or out.get("episode_group") or "").strip()
    start = out.get("episodeStart")
    end = out.get("episodeEnd")

    if not ep_range and group:
        ps, pe, ep_range = _parse_episode_group_label(group)
        if ps is not None:
            out.setdefault("episodeStart", ps)
            out.setdefault("episodeEnd", pe)

    if not ep_range and start is not None and end is not None:
        si, ei = int(start), int(end)
        ep_range = str(si) if si == ei else f"{si}-{ei}"

    if not ep_range and start is not None:
        ep_range = str(int(start))
        out.setdefault("episodeEnd", int(start))

    if ep_range:
        out["episodeRange"] = ep_range
        if start is None or end is None:
            ps, pe, _ = _parse_episode_group_label(ep_range)
            if ps is not None:
                out.setdefault("episodeStart", ps)
                out.setdefault("episodeEnd", pe)
    return out


def normalize_rhythm_curve(payload: dict) -> None:
    curve = payload.get("rhythmCurve")
    if not isinstance(curve, list):
        return
    normalized: List[dict] = []
    seen: set[str] = set()
    for item in curve:
        if not isinstance(item, dict):
            continue
        block = normalize_rhythm_block(item)
        key = (block.get("episodeRange") or "").strip()
        if not key:
            fallback = f"__idx_{len(normalized)}"
            if fallback in seen:
                continue
            seen.add(fallback)
            normalized.append(block)
            continue
        if key in seen:
            continue
        seen.add(key)
        normalized.append(block)
    payload["rhythmCurve"] = normalized


def is_placeholder_working_title(title: str, theme: str = "") -> bool:
    """识别提交时的题材代码+时间戳代称，或空标题。"""
    t = (title or "").strip()
    if not t:
        return True
    if _PLACEHOLDER_TITLE_RE.match(t):
        return True
    theme_key = (theme or "").strip()
    if theme_key and t.startswith(f"{theme_key} ·"):
        return True
    return False


def resolve_structure_working_title(
    payload: dict,
    project=None,
    *,
    brief: Optional[dict] = None,
) -> str:
    """从结构产物解析建议剧名，忽略占位代称。"""
    if not isinstance(payload, dict):
        return ""
    theme = getattr(project, "theme", "") if project else ""
    for key in ("workingTitle", "suggestedTitle", "projectTitle"):
        candidate = (payload.get(key) or "").strip()
        if candidate and not is_placeholder_working_title(candidate, theme):
            return candidate[:200]

    wv = payload.get("worldview") if isinstance(payload.get("worldview"), dict) else {}
    for noun in wv.get("coreNouns") or []:
        if not isinstance(noun, dict):
            continue
        term = (noun.get("term") or "").strip()
        if 2 <= len(term) <= 12 and not is_placeholder_working_title(term, theme):
            return term[:200]

    arc = payload.get("coreStoryArc") if isinstance(payload.get("coreStoryArc"), dict) else {}
    opening = (arc.get("openingSetup") or "").strip()
    if opening:
        for sep in ("，", ",", "。", "；", ";", " "):
            if sep in opening:
                head = opening.split(sep, 1)[0].strip()
                if 2 <= len(head) <= 16 and not is_placeholder_working_title(head, theme):
                    return head[:200]
                break

    if brief is None and project is not None:
        from ..artifact_service import get_artifact

        brief = get_artifact(project, "project_brief") or {}
    if isinstance(brief, dict):
        brief_title = (brief.get("workingTitle") or "").strip()
        if brief_title and not is_placeholder_working_title(brief_title, theme):
            return brief_title[:200]

    project_title = (getattr(project, "title", "") or "").strip() if project else ""
    if project_title and not is_placeholder_working_title(project_title, theme):
        return project_title[:200]
    return ""


def apply_structure_working_title(payload: dict, project, *, brief: Optional[dict] = None) -> dict:
    """归一化并写入 structure_plan.workingTitle（非占位）。"""
    if not isinstance(payload, dict):
        return payload
    title = resolve_structure_working_title(payload, project, brief=brief)
    if title:
        payload["workingTitle"] = title
    elif "workingTitle" in payload and is_placeholder_working_title(
        payload.get("workingTitle", ""), getattr(project, "theme", "") if project else ""
    ):
        payload.pop("workingTitle", None)
    return payload


def sync_project_title_from_structure(project, payload: dict, *, brief: Optional[dict] = None) -> bool:
    """节点 2 完成后，用建议剧名更新 project.title 与 project_brief。"""
    title = resolve_structure_working_title(payload, project, brief=brief)
    if not title:
        return False
    theme = getattr(project, "theme", "")
    if title == (project.title or "").strip():
        return False
    project.title = title[:200]
    project.save(update_fields=["title", "updated_at"])

    from ..artifact_service import get_artifact, save_artifact

    brief_payload = dict(brief if brief is not None else get_artifact(project, "project_brief") or {})
    if brief_payload:
        brief_payload["workingTitle"] = title
        save_artifact(project, "project_brief", brief_payload)
    return True


def workspace_display_title(project) -> str:
    """工作台标题：优先结构建议剧名，占位代称回落为题材名。"""
    from ..artifact_service import get_artifact

    structure = get_artifact(project, "structure_plan") or {}
    title = resolve_structure_working_title(structure, project)
    if title:
        return title
    project_title = (getattr(project, "title", "") or "").strip()
    theme = getattr(project, "theme", "") or ""
    if project_title and not is_placeholder_working_title(project_title, theme):
        return project_title
    try:
        from apps.workflow.fusion.ssot_catalog import get_ssot_catalog

        return get_ssot_catalog().theme_display_name(theme) or theme or "创作项目"
    except Exception:  # noqa: BLE001
        return project_title or theme or "创作项目"


def structure_worldview_summary(worldview: Any, payload: Optional[dict] = None) -> str:
    if isinstance(worldview, dict):
        setting = (worldview.get("settingSummary") or worldview.get("setting") or "").strip()
        if setting:
            return setting
        rules = worldview.get("rootRules") or []
        if isinstance(rules, list) and rules:
            return "\n".join(str(r).strip() for r in rules if str(r).strip())
        sub = worldview.get("subWorld") or {}
        if isinstance(sub, dict):
            parts = [sub.get("economicLogic"), sub.get("socialStructure")]
            joined = "\n".join(str(p).strip() for p in parts if p and str(p).strip())
            if joined:
                return joined

    if isinstance(payload, dict):
        arc = payload.get("coreStoryArc") or {}
        if isinstance(arc, dict):
            parts = [
                (arc.get("openingSetup") or "").strip(),
                (arc.get("escalation") or "").strip(),
            ]
            joined = "\n\n".join(p for p in parts if p)
            if joined:
                return joined
        six = payload.get("sixStagePlan") or []
        if isinstance(six, list) and six:
            tasks = [
                str(s.get("coreTask") or "").strip()
                for s in six[:3]
                if isinstance(s, dict) and s.get("coreTask")
            ]
            if tasks:
                return "\n".join(tasks)
    return ""


def structure_reversal_text(payload: dict) -> str:
    key_rev = payload.get("keyReversalPoints") or []
    if isinstance(key_rev, list) and key_rev:
        parts: List[str] = []
        for r in key_rev:
            if not isinstance(r, dict):
                continue
            ep = r.get("episodeNumber")
            desc = (r.get("description") or r.get("reversalType") or "").strip()
            if ep and desc:
                parts.append(f"第{ep}集·{desc[:48]}")
            elif desc:
                parts.append(desc[:48])
        if parts:
            return " · ".join(parts)

    act = payload.get("actStructure") or {}
    if isinstance(act, dict):
        pts = act.get("reversalPoints") or []
        if isinstance(pts, list):
            parts = []
            for p in pts:
                if isinstance(p, dict):
                    parts.append(str(p.get("label") or p.get("name") or p.get("episode") or ""))
                else:
                    parts.append(str(p))
            return " · ".join(x for x in parts if x)
    return ""


def structure_act_count(payload: dict, fallback: int = 4) -> Optional[int]:
    six = payload.get("sixStagePlan") or []
    if isinstance(six, list) and six:
        return len(six)
    act = payload.get("actStructure") or {}
    if isinstance(act, dict) and act.get("actCount"):
        try:
            return int(act["actCount"])
        except (TypeError, ValueError):
            pass
    return fallback if payload else None


_STAGE_INTENSITY_RANGES = [
    (3, 6),
    (5, 7),
    (7, 9),
    (8, 10),
    (9, 10),
    (8, 10),
]

_REVERSAL_TYPE_TO_CODE = {
    "身份大反转": "identity-reveal",
    "立场转变": "motivation-change",
    "真相揭露": "hidden-truth",
    "情感爆发": "relationship-reversal",
    "绝地逆袭": "fortunes-reversal",
    "计划崩盘": "villain-twist",
    "契约设定": "relationship-reversal",
    "态度反转": "relationship-reversal",
    "误会铺垫": "hidden-truth",
    "冲突爆发": "other",
    "情感反转": "relationship-reversal",
    "身份暗示": "identity-reveal",
    "身份反转": "identity-reveal",
    "身份暗示反转": "identity-reveal",
    "身份暴露小反转": "identity-reveal",
    "能力暴露反转": "identity-reveal",
    "信息反转": "hidden-truth",
}

_VALID_REVERSAL_TYPES = frozenset(
    {
        "identity-reveal",
        "relationship-reversal",
        "fortunes-reversal",
        "hidden-truth",
        "villain-twist",
        "motivation-change",
        "other",
    }
)


def normalize_reversal_type(raw: str) -> str:
    """LLM 常输出中文 reversalType，归一化为 schema enum。"""
    s = (raw or "").strip()
    if s in _VALID_REVERSAL_TYPES:
        return s
    if s in _REVERSAL_TYPE_TO_CODE:
        return _REVERSAL_TYPE_TO_CODE[s]
    if "身份" in s:
        return "identity-reveal"
    if any(k in s for k in ("情感", "关系", "态度", "契约")):
        return "relationship-reversal"
    if any(k in s for k in ("真相", "秘密", "信息", "误会", "揭露")):
        return "hidden-truth"
    if any(k in s for k in ("逆袭", "命运", "翻盘")):
        return "fortunes-reversal"
    if any(k in s for k in ("反派", "计划崩盘", "阴谋")):
        return "villain-twist"
    if any(k in s for k in ("动机", "立场")):
        return "motivation-change"
    return "other"


def normalize_key_reversal_points(payload: dict) -> None:
    points = payload.get("keyReversalPoints")
    if not isinstance(points, list):
        return
    for item in points:
        if isinstance(item, dict) and item.get("reversalType") is not None:
            item["reversalType"] = normalize_reversal_type(str(item["reversalType"]))


def _act_to_six_stage(act: dict, stage_index: int) -> dict:
    lo, hi = _STAGE_INTENSITY_RANGES[min(stage_index - 1, 5)]
    purpose = (act.get("purpose") or "").strip()
    key_events = act.get("key_events") or []
    core = purpose
    if key_events:
        core = f"{purpose}；关键事件：{'、'.join(str(e) for e in key_events[:3])}"
    ep_count = act.get("episode_count") or 1
    return {
        "stageIndex": stage_index,
        "stageName": (act.get("act_name") or f"阶段{stage_index}").strip(),
        "startEpisode": act.get("episode_start"),
        "endEpisode": act.get("episode_end"),
        "episodeCount": ep_count,
        "coreTask": (core or purpose or f"阶段{stage_index}核心任务")[:500],
        "keyReversalCount": max(1, ep_count // 5),
        "emotionalIntensityRange": {"min": lo, "max": hi},
        "primaryTheme": (purpose or act.get("act_name") or "")[:120],
    }


def _emotion_curve_to_rhythm_blocks(curve: List[dict], total_eps: int) -> List[dict]:
    blocks: List[dict] = []
    chunk_size = 10
    for start in range(1, total_eps + 1, chunk_size):
        end = min(start + chunk_size - 1, total_eps)
        segment = [p for p in curve if start <= int(p.get("episode") or 0) <= end]
        if not segment:
            continue
        avg = round(sum(int(p.get("emotion_value") or 5) for p in segment) / len(segment))
        key_events = [
            str(p.get("note") or "").strip()
            for p in segment
            if p.get("is_key_point") and str(p.get("note") or "").strip()
        ][:4]
        notes = (segment[-1].get("note") or "").strip()
        blocks.append(
            {
                "episodeRange": f"{start}-{end}",
                "episodeStart": start,
                "episodeEnd": end,
                "intensityLevel": max(1, min(10, avg)),
                "keyEvents": key_events,
                "notes": notes[:300],
            }
        )
    return blocks


def _engine_reversal_to_schema(item: dict) -> dict:
    rtype = (item.get("reversal_type") or "其他").strip()
    return {
        "episodeNumber": int(item.get("episode") or 1),
        "reversalType": _REVERSAL_TYPE_TO_CODE.get(rtype, "other"),
        "description": (item.get("description") or rtype)[:300],
        "foreshadowEpisodes": [],
    }


def _min_reversal_count(episode_count: int) -> int:
    return max(8, episode_count // 10)


def enrich_structure_payload(
    payload: dict,
    *,
    theme: str = "",
    episode_count: Optional[int] = None,
) -> dict:
    """用老版规则引擎回填 LLM 未写全的六阶段、节奏曲线与反转点（保留模型已有内容）。"""
    if not isinstance(payload, dict):
        return payload

    from ..engine.node2_structure import Node2Structure

    total = int(payload.get("totalEpisodes") or episode_count or 80)
    theme_code = (theme or "mixed-theme").strip() or "mixed-theme"
    engine = Node2Structure()

    six = payload.get("sixStagePlan")
    if not isinstance(six, list) or len(six) < 6:
        acts = engine.calculate_act_distribution(total, theme_code)
        payload["sixStagePlan"] = [_act_to_six_stage(act, i + 1) for i, act in enumerate(acts)]

    rhythm = payload.get("rhythmCurve")
    expected_blocks = max(1, (total + 9) // 10)
    if not isinstance(rhythm, list) or len(rhythm) < max(3, expected_blocks // 2):
        try:
            curve = engine.calculate_emotion_curve(total, theme_code)
            payload["rhythmCurve"] = _emotion_curve_to_rhythm_blocks(curve, total)
        except (IndexError, ZeroDivisionError):
            config = Node2Structure.EMOTION_CURVE_CONFIGS.get(
                theme_code, Node2Structure.EMOTION_CURVE_CONFIGS["mixed-theme"]
            )
            base = config.get("curve") or [4, 5, 6, 7, 8, 9, 10, 10]
            fallback: List[dict] = []
            for start in range(1, total + 1, 10):
                end = min(start + 9, total)
                mid = (start + end) / 2
                ratio = (mid - 1) / max(1, total - 1)
                idx = min(int(ratio * (len(base) - 1)), len(base) - 1)
                level = max(1, min(10, int(base[idx])))
                fallback.append(
                    {
                        "episodeRange": f"{start}-{end}",
                        "episodeStart": start,
                        "episodeEnd": end,
                        "intensityLevel": level,
                        "keyEvents": [f"第{end}集情绪峰值"] if end % 10 == 0 else [],
                        "notes": (config.get("description") or "")[:300],
                    }
                )
            payload["rhythmCurve"] = fallback

    reversals = payload.get("keyReversalPoints")
    if not isinstance(reversals, list):
        reversals = []
    min_revs = _min_reversal_count(total)
    if len(reversals) < min_revs:
        existing_eps = {
            int(r.get("episodeNumber"))
            for r in reversals
            if isinstance(r, dict) and r.get("episodeNumber") is not None
        }
        for item in engine.generate_reversal_points(total, theme_code):
            ep = int(item.get("episode") or 0)
            if ep and ep not in existing_eps:
                reversals.append(_engine_reversal_to_schema(item))
                existing_eps.add(ep)
        for ep in (3, 5, max(8, total // 4), max(12, total // 3)):
            if 1 <= ep <= total and ep not in existing_eps and len(reversals) < min_revs:
                reversals.append(
                    {
                        "episodeNumber": ep,
                        "reversalType": "identity-reveal" if ep <= 5 else "hidden-truth",
                        "description": f"第{ep}集关键剧情转折，推动主线进入下一阶段",
                        "foreshadowEpisodes": [max(1, ep - 2)],
                    }
                )
                existing_eps.add(ep)
        payload["keyReversalPoints"] = sorted(
            reversals,
            key=lambda r: int(r.get("episodeNumber") or 0) if isinstance(r, dict) else 0,
        )

    from ..reference_library import backfill_reversal_codes, backfill_rhythm_hook_codes

    payload["keyReversalPoints"] = backfill_reversal_codes(payload.get("keyReversalPoints") or [])
    payload["rhythmCurve"] = backfill_rhythm_hook_codes(
        payload.get("rhythmCurve") or [],
        theme=theme_code,
    )

    arc = payload.get("coreStoryArc")
    if not isinstance(arc, dict):
        arc = {}
        payload["coreStoryArc"] = arc
    stages = payload.get("sixStagePlan") or []
    if isinstance(stages, list) and stages:
        fillers = {
            "openingSetup": (stages[0].get("coreTask") or stages[0].get("primaryTheme") or ""),
            "escalation": (stages[1].get("coreTask") or "") if len(stages) > 1 else "",
            "midpointTwist": (stages[2].get("coreTask") or "") if len(stages) > 2 else "",
            "finalConfrontation": (stages[4].get("coreTask") or "") if len(stages) > 4 else "",
            "resolution": (stages[5].get("coreTask") or "") if len(stages) > 5 else "",
        }
        for key, val in fillers.items():
            if val and not (arc.get(key) or "").strip():
                arc[key] = str(val)[:500]

    constraints = payload.get("structuralConstraints")
    if not isinstance(constraints, dict):
        payload["structuralConstraints"] = {
            "maxScenesPerEpisode": 3,
            "hookThresholdSeconds": 5,
            "minReversalsPerEpisode": 1,
            "targetConflictDensity": 1.0,
            "keyEpisodeEveryNEpisodes": 10,
            "emotionalCurveMonotonicRising": True,
        }

    from ..industry_benchmarks import apply_structure_benchmark_hints

    return apply_structure_benchmark_hints(payload)


_DREAM_LABEL_FALLBACK = {
    "absoluteSafety": "绝对安全感",
    "efficientSatisfaction": "高效满足感",
    "enhancedRealism": "强化真实感",
    "fantasyAppeal": "幻想吸引力",
    "dreamPotential": "梦境潜力",
    "emotionalDepth": "情感深度",
}


def _split_noun_entry(raw: str) -> Dict[str, str]:
    text = (raw or "").strip()
    if not text:
        return {"term": "", "definition": ""}
    for sep in ("：", ":", "—", "-", "·"):
        if sep in text:
            term, definition = text.split(sep, 1)
            term = term.strip()
            definition = definition.strip()
            if term and definition:
                return {"term": term[:80], "definition": definition[:500]}
    if len(text) <= 12:
        return {"term": text, "definition": ""}
    return {"term": text[:12], "definition": text}


_NOUN_TIER_LABELS = {
    "root": "根概念",
    "mechanism": "运行机制",
    "trace": "痕迹表现",
    "carrier": "承载处",
    "derived": "派生概念",
}


def normalize_core_nouns(raw: Any) -> List[Dict[str, str]]:
    nouns: List[Dict[str, str]] = []
    if not isinstance(raw, list):
        return nouns
    for item in raw:
        if isinstance(item, dict):
            term = (item.get("term") or item.get("name") or "").strip()
            definition = (item.get("definition") or item.get("desc") or item.get("description") or "").strip()
            if term or definition:
                row = {"term": term or definition[:12], "definition": definition or term}
                tier = (item.get("tier") or item.get("level") or "").strip().lower()
                if tier in _NOUN_TIER_LABELS:
                    row["tier"] = tier
                    row["tierLabel"] = _NOUN_TIER_LABELS[tier]
                nouns.append(row)
        elif isinstance(item, str) and item.strip():
            parsed = _split_noun_entry(item)
            if parsed["term"] or parsed["definition"]:
                nouns.append(parsed)
    return nouns


def build_world_self_check(wv: dict, nouns: List[dict]) -> List[dict]:
    """世界观自检表（对齐 world-setting-builder 8 项检查）。"""
    if not isinstance(wv, dict):
        wv = {}
    rules = [str(r).strip() for r in (wv.get("rootRules") or []) if str(r).strip()]
    setting = (wv.get("settingSummary") or "").strip()
    first_rule = rules[0] if rules else ""
    tiered = [n for n in nouns if n.get("tier")]
    checks = [
        ("rootRuleConcise", "根法则简洁性", len(first_rule) > 0 and len(first_rule) <= 80),
        ("rootRuleFundamental", "根法则根本性", len(rules) >= 2 and len(setting) >= 20),
        ("abilityExplain", "能力解释", len(setting) >= 30 or any("能力" in r or "规则" in r for r in rules)),
        ("protagonistExplain", "主角解释", len(setting) >= 30),
        ("antagonistConstraint", "反派约束", len(rules) >= 2),
        ("ironLawGuard", "铁律防护", len(first_rule) >= 8),
        ("nounCount", "名词数量 3-7", 3 <= len(nouns) <= 7),
        ("nounTier", "名词层级", len(tiered) >= 2 or len(nouns) >= 3),
    ]
    return [{"key": key, "label": label, "passed": bool(ok)} for key, label, ok in checks]


def _build_reference_library_summary() -> dict:
    from ..reference_library import build_reference_library_summary

    return build_reference_library_summary()


_SCHEMA_DREAM_KEYS = ("absoluteSafety", "efficientSatisfaction", "enhancedRealism")
_DEFAULT_DREAM_SCORES = {
    "absoluteSafety": 7,
    "efficientSatisfaction": 8,
    "enhancedRealism": 7,
}
_DREAM_SCORE_ALIASES = {
    "absoluteSafety": ("absoluteSafety", "emotionalDepth", "safety"),
    "efficientSatisfaction": ("efficientSatisfaction", "fantasyAppeal", "dreamPotential", "satisfaction"),
    "enhancedRealism": ("enhancedRealism", "enhancedReality", "realism"),
}


def _coerce_dream_score(val: Any) -> Optional[int]:
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        score = int(round(val))
        return max(1, min(10, score))
    if isinstance(val, dict):
        inner = val.get("score")
        if isinstance(inner, (int, float)):
            return _coerce_dream_score(inner)
    return None


def finalize_dream_indicators(wv: dict) -> dict:
    """归一化并补全梦境三指标，确保 sub-world 可校验。"""
    if not isinstance(wv, dict):
        return {"absoluteSafety": 7, "efficientSatisfaction": 8, "enhancedRealism": 7, "notes": ""}

    dream = normalize_dream_indicators(wv.get("dreamIndicators"))
    scores = dict(dream.get("scores") or {})
    raw = wv.get("dreamIndicators")
    if isinstance(raw, dict):
        for key in _SCHEMA_DREAM_KEYS:
            if key not in scores and raw.get(key) is not None:
                coerced = _coerce_dream_score(raw.get(key))
                if coerced is not None:
                    scores[key] = coerced

    finalized: Dict[str, Any] = {}
    for schema_key in _SCHEMA_DREAM_KEYS:
        val = None
        for candidate in _DREAM_SCORE_ALIASES.get(schema_key, (schema_key,)):
            if candidate in scores:
                val = _coerce_dream_score(scores[candidate])
                if val is not None:
                    break
        finalized[schema_key] = val if val is not None else _DEFAULT_DREAM_SCORES[schema_key]

    notes = (dream.get("notes") or "").strip()
    if not notes and isinstance(raw, dict):
        notes = (raw.get("notes") or "").strip()
    if not notes:
        notes = "基于题材与结构规划自动补全梦境三指标，可在工作台编辑后保存。"

    out = {**finalized, "notes": _clean_dream_notes(notes)[:800]}
    wv["dreamIndicators"] = out
    return out


def normalize_dream_indicators(raw: Any) -> Dict[str, Any]:
    """兼容 schema 标准字段与 LLM 自由形态 dreamIndicators。"""
    if not raw:
        return {"scores": {}, "notes": ""}
    if isinstance(raw, list):
        notes = []
        for item in raw:
            if isinstance(item, dict):
                name = (item.get("name") or "").strip()
                desc = (item.get("description") or item.get("notes") or "").strip()
                if name and desc:
                    notes.append(f"{name}：{desc}")
                elif desc:
                    notes.append(desc)
        return {
            "scores": {
                "absoluteSafety": 7,
                "efficientSatisfaction": 8,
                "enhancedRealism": 6,
            },
            "notes": _join_dream_note_parts(notes),
        }

    if not isinstance(raw, dict):
        return {"scores": {}, "notes": str(raw)[:800]}

    scores: Dict[str, Any] = {}
    note_parts: List[str] = []
    schema_keys = ("absoluteSafety", "efficientSatisfaction", "enhancedRealism")
    for key in schema_keys:
        val = raw.get(key)
        if val is not None:
            scores[key] = val

    for key, val in raw.items():
        if key in schema_keys or key == "notes":
            continue
        if isinstance(val, dict):
            score = val.get("score")
            notes = (val.get("notes") or val.get("description") or "").strip()
            label = _DREAM_LABEL_FALLBACK.get(key, key)
            if score is not None:
                scores[key] = score
            if notes:
                note_parts.append(f"{label}：{notes}")
        elif isinstance(val, (int, float)):
            scores[key] = val
        elif isinstance(val, str) and val.strip():
            note_parts.append(f"{_DREAM_LABEL_FALLBACK.get(key, key)}：{val.strip()}")

    extra_notes = _clean_dream_notes(raw.get("notes") or "")
    if extra_notes:
        note_parts.append(extra_notes)
    return {"scores": scores, "notes": _join_dream_note_parts(note_parts)}


def validate_worldview_issues(payload: dict) -> List[str]:
    """与 sub-world CLI 对齐的世界观块校验（用于展示与存量回填）。"""
    issues: List[str] = []
    wv = payload.get("worldview") if isinstance(payload.get("worldview"), dict) else None
    if not wv:
        issues.append("缺少 worldview 块")
        return issues
    setting = (wv.get("settingSummary") or wv.get("setting") or "").strip()
    if len(setting) < 5:
        issues.append("worldview.settingSummary 须 ≥5 字")
    rules = wv.get("rootRules") or []
    if not isinstance(rules, list) or len([r for r in rules if str(r).strip()]) < 2:
        issues.append("worldview.rootRules 须至少 2 条")
    di = wv.get("dreamIndicators") or {}
    if not isinstance(di, dict):
        di = {}
    for key in _SCHEMA_DREAM_KEYS:
        val = _coerce_dream_score(di.get(key))
        if val is None or val < 6:
            issues.append(f"worldview.dreamIndicators.{key} 建议 ≥6（当前 {val if val is not None else '缺失'}）")
    return issues


def build_world_validation_log(payload: dict) -> Dict[str, Any]:
    """读取或按 sub-world 规则即时生成世界观校验日志。"""
    stored = payload.get("worldValidationLog")
    if isinstance(stored, dict) and "passed" in stored:
        issues = [str(i) for i in (stored.get("issues") or []) if str(i).strip()]
        return {
            "passed": bool(stored.get("passed")),
            "issues": issues,
            "checker": (stored.get("checker") or "sub-world").strip(),
        }
    issues = validate_worldview_issues(payload)
    return {"passed": len(issues) == 0, "issues": issues, "checker": "sub-world"}


def normalize_structure_payload(payload: dict, project=None) -> dict:
    """LLM 输出归一化：修正类型并补全 C 端可读字段。"""
    if not isinstance(payload, dict):
        return payload

    sc = payload.get("structuralConstraints")
    if isinstance(sc, dict):
        tcd = sc.get("targetConflictDensity")
        if isinstance(tcd, str):
            sc["targetConflictDensity"] = _CONFLICT_DENSITY_MAP.get(tcd.lower(), 1.0)

    wv = payload.get("worldview")
    if not isinstance(wv, dict):
        wv = {}
        payload["worldview"] = wv
    if isinstance(wv, dict):
        wv["coreNouns"] = normalize_core_nouns(wv.get("coreNouns"))
        finalize_dream_indicators(wv)
        if not (wv.get("settingSummary") or "").strip():
            summary = structure_worldview_summary(wv, payload)
            if summary:
                wv["settingSummary"] = summary[:4000]

    if project is not None:
        apply_structure_working_title(payload, project)
        enrich_structure_payload(
            payload,
            theme=getattr(project, "theme", "") or "",
            episode_count=getattr(project, "episode_count", None),
        )

    normalize_key_reversal_points(payload)
    normalize_rhythm_curve(payload)
    if not (payload.get("nodeName") or "").strip():
        payload["nodeName"] = "结构与世界观节点"

    payload["worldValidationLog"] = build_world_validation_log(payload)
    return payload


_FORMAT_LABELS = {
    "variant-a": "变体 A",
    "variant-b": "变体 B",
    "variant-c": "变体 C",
    "variant-d": "变体 D",
}

_THEME_LABELS = {
    "family-revenge": "家庭伦理复仇",
    "overbearing-ceo": "豪门霸总",
    "sweet-pet": "甜宠虐恋",
    "time-travel": "穿越重生",
    "urban-rebirth": "都市逆袭",
    "ancient-costume": "古装权谋",
    "suspense-reversal": "悬疑反转",
    "male-advancement": "都市男频",
    "mixed-theme": "混合题材",
    "urban-romance": "都市情感",
}

_LOCATION_LABELS = {
    "urban": "都市",
    "rural": "乡村",
    "ancient": "古装",
    "fantasy": "幻想",
    "mixed": "混合",
}

_REVERSAL_LABELS = {
    "identity-reveal": "身份揭晓",
    "relationship-reversal": "关系反转",
    "fortunes-reversal": "命运反转",
    "hidden-truth": "隐藏真相",
    "villain-twist": "反派反转",
    "motivation-change": "动机转变",
    "other": "其他",
}


def _normalize_act_structure(payload: dict) -> dict:
    act = payload.get("actStructure") if isinstance(payload.get("actStructure"), dict) else {}
    points = []
    for item in act.get("reversalPoints") or []:
        if isinstance(item, dict):
            points.append(
                {
                    "label": (item.get("label") or item.get("name") or "").strip(),
                    "episode": item.get("episode") or item.get("episodeNumber"),
                    "description": (item.get("description") or "").strip(),
                }
            )
        elif item:
            points.append({"label": str(item).strip(), "episode": None, "description": ""})

    act_count = act.get("actCount")
    try:
        act_count = int(act_count) if act_count is not None else None
    except (TypeError, ValueError):
        act_count = None
    if not act_count:
        six = payload.get("sixStagePlan") or []
        if isinstance(six, list) and six:
            act_count = len(six)

    theme_code = (act.get("themeCode") or "").strip()

    return {
        "actCount": act_count,
        "themeCode": theme_code,
        "themeCodeLabel": _code_display_label(theme_code, _THEME_LABELS),
        "reversalPoints": points,
    }


def _contains_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in (text or ""))


def _code_display_label(code: str, mapping: dict) -> str:
    c = (code or "").strip()
    if not c:
        return ""
    if c in mapping:
        return mapping[c]
    if _contains_chinese(c):
        return c
    return ""


def build_structure_plan_view(payload: dict, project) -> dict:
    """C 端结构与世界观完整展示视图。"""
    wv = payload.get("worldview") if isinstance(payload.get("worldview"), dict) else {}

    setting = (wv.get("settingSummary") or wv.get("setting") or "").strip()
    if not setting:
        setting = structure_worldview_summary(wv, payload)

    fmt = payload.get("formatVariant") or ""
    loc = wv.get("locationType") or ""

    stages = []
    for stage in payload.get("sixStagePlan") or []:
        if not isinstance(stage, dict):
            continue
        intensity = stage.get("emotionalIntensityRange") or {}
        stages.append(
            {
                "stageIndex": stage.get("stageIndex"),
                "stageName": stage.get("stageName") or "",
                "episodeRange": f"{stage.get('startEpisode', '?')}-{stage.get('endEpisode', '?')}",
                "episodeCount": stage.get("episodeCount"),
                "coreTask": stage.get("coreTask") or "",
                "keyReversalCount": stage.get("keyReversalCount"),
                "intensityMin": intensity.get("min"),
                "intensityMax": intensity.get("max"),
                "primaryTheme": stage.get("primaryTheme") or "",
            }
        )

    reversals = []
    for rev in payload.get("keyReversalPoints") or []:
        if not isinstance(rev, dict):
            continue
        rtype = rev.get("reversalType") or "other"
        from ..reference_library import enrich_reversal_point

        reversals.append(
            enrich_reversal_point(
                {
                    "episodeNumber": rev.get("episodeNumber"),
                    "reversalType": rtype,
                    "reversalTypeLabel": _REVERSAL_LABELS.get(rtype, rtype),
                    "description": rev.get("description") or "",
                    "foreshadowEpisodes": rev.get("foreshadowEpisodes") or [],
                    "reversalCode": rev.get("reversalCode") or rev.get("patternCode"),
                }
            )
        )

    rhythm = []
    theme_key = (getattr(project, "theme", "") or "").strip()
    for block in payload.get("rhythmCurve") or []:
        if not isinstance(block, dict):
            continue
        normalized = normalize_rhythm_block(block)
        from ..reference_library import enrich_rhythm_block_view

        view_block = enrich_rhythm_block_view(
            normalized,
            reversals=reversals,
            theme=theme_key,
        )
        rhythm.append(
            {
                "episodeRange": view_block.get("episodeRange") or "",
                "episodeStart": view_block.get("episodeStart"),
                "episodeEnd": view_block.get("episodeEnd"),
                "intensityLevel": view_block.get("intensityLevel"),
                "keyEvents": view_block.get("keyEvents") or [],
                "notes": view_block.get("notes") or "",
                "suggestedHookCodes": view_block.get("suggestedHookCodes") or [],
                "suggestedHooks": view_block.get("suggestedHooks") or [],
                "linkedReversals": view_block.get("linkedReversals") or [],
            }
        )

    arc = payload.get("coreStoryArc") if isinstance(payload.get("coreStoryArc"), dict) else {}
    constraints = (
        payload.get("structuralConstraints")
        if isinstance(payload.get("structuralConstraints"), dict)
        else {}
    )

    nouns = normalize_core_nouns(wv.get("coreNouns"))

    rules = [str(r).strip() for r in (wv.get("rootRules") or []) if str(r).strip()]

    sub_world_labels = {
        "businessLogic": "商业逻辑",
        "designProfession": "专业设定",
        "socialHierarchy": "社会层级",
        "economicLogic": "经济逻辑",
        "socialStructure": "社会结构",
    }
    sub_world = []
    for src_key in ("subWorldConsistency", "subWorld"):
        block = wv.get(src_key)
        if not isinstance(block, dict):
            continue
        for key, label in sub_world_labels.items():
            val = (block.get(key) or "").strip()
            if val:
                sub_world.append({"key": key, "label": label, "text": val})

    view = {
        "workingTitle": resolve_structure_working_title(payload, project),
        "totalEpisodes": payload.get("totalEpisodes") or project.episode_count,
        "formatVariant": fmt,
        "formatVariantLabel": _code_display_label(fmt, _FORMAT_LABELS),
        "worldValidationLog": build_world_validation_log(payload),
        "worldview": {
            "settingSummary": setting,
            "timePeriod": (wv.get("timePeriod") or "").strip(),
            "locationType": loc,
            "locationTypeLabel": _code_display_label(loc, _LOCATION_LABELS),
            "rootRules": rules,
            "coreNouns": nouns,
            "subWorldConsistency": sub_world,
        },
        "sixStagePlan": stages,
        "rhythmCurve": rhythm,
        "keyReversalPoints": reversals,
        "coreStoryArc": {
            "openingSetup": (arc.get("openingSetup") or "").strip(),
            "escalation": (arc.get("escalation") or "").strip(),
            "midpointTwist": (arc.get("midpointTwist") or "").strip(),
            "finalConfrontation": (arc.get("finalConfrontation") or "").strip(),
            "resolution": (arc.get("resolution") or "").strip(),
        },
        "structuralConstraints": {
            "maxScenesPerEpisode": constraints.get("maxScenesPerEpisode"),
            "hookThresholdSeconds": constraints.get("hookThresholdSeconds"),
            "minReversalsPerEpisode": constraints.get("minReversalsPerEpisode"),
            "targetConflictDensity": constraints.get("targetConflictDensity"),
            "keyEpisodeEveryNEpisodes": constraints.get("keyEpisodeEveryNEpisodes"),
            "emotionalCurveMonotonicRising": constraints.get("emotionalCurveMonotonicRising"),
        },
        "actStructure": _normalize_act_structure(payload),
        "referenceLibrary": _build_reference_library_summary(),
    }
    from .portal_display import portal_sanitize_structure_plan_view

    return portal_sanitize_structure_plan_view(view)
