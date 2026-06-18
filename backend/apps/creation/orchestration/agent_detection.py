# -*- coding: utf-8 -*-
"""registry type=detection 的轻量 Python 实现（不复制 Node 检测全量逻辑）。"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, List

from ..display.character_display import build_character_bible_view

logger = logging.getLogger(__name__)

_AI_HIT_WARN_PER_EP = 3
_AI_HIT_FAIL_PER_EP = 8
_MIN_ADULT_AGE = 18
_AGE_FIELD_TEXT_KEYS = (
    "oneLineSummary",
    "appearance",
    "background",
    "coreMotivation",
    "shortTermGoal",
    "longTermGoal",
    "secret",
    "weakness",
    "signatureDialogueStyle",
)
_AGE_FIELD_LIST_KEYS = ("signatureLines", "speechPatterns", "iconicProps")
_UNDERAGE_HINTS = (
    "未成年",
    "未满十八",
    "不到十八",
    "不满十八",
    "十七岁",
    "16岁",
    "17岁",
    "高中生",
    "童养",
)
_MARRIAGE_HINTS = ("妻", "夫", "婚", "离婚", "前夫", "前妻", "订婚", "新婚")
_TRAUMA_EVENT_GROUPS = {
    "车祸": ("车祸", "交通事故", "撞车", "连环追尾"),
    "坠崖": ("推下悬崖", "被推下悬崖", "坠崖", "跌落悬崖", "摔下悬崖", "山崖坠落"),
    "火灾": ("火灾", "纵火", "大火", "火场"),
    "溺水": ("溺水", "落水", "坠河", "沉湖"),
    "中毒": ("中毒", "下毒", "毒杀", "药物过量"),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_int(value: Any) -> int | None:
    try:
        age = int(value)
    except (TypeError, ValueError):
        return None
    if age <= 0 or age > 120:
        return None
    return age


def _character_age_text(char: dict) -> str:
    parts: List[str] = []
    for key in _AGE_FIELD_TEXT_KEYS:
        val = char.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val.strip())
    for key in _AGE_FIELD_LIST_KEYS:
        values = char.get(key) or []
        if isinstance(values, list):
            parts.extend(str(item).strip() for item in values if str(item).strip())
    for block_key in ("characterArc", "voiceProfile", "behaviorProfile", "visualAnchor", "contrastRelation"):
        block = char.get(block_key) or {}
        if isinstance(block, dict):
            parts.extend(str(v).strip() for v in block.values() if isinstance(v, str) and v.strip())
    return "\n".join(parts)


def _explicit_ages(text: str) -> List[int]:
    ages = []
    for match in re.finditer(r"(?<!\d)(1[0-7]|[2-9]\d|1[01]\d)\s*岁", text or ""):
        age = _safe_int(match.group(1))
        if age is not None:
            ages.append(age)
    return ages


def _character_age_issues(char: dict) -> List[str]:
    name = (char.get("name") or "").strip() or "未命名角色"
    declared_age = _safe_int(char.get("age"))
    text = _character_age_text(char)
    issues: List[str] = []
    mentioned_ages = _explicit_ages(text)
    if declared_age is not None:
        for mentioned_age in mentioned_ages:
            if mentioned_age != declared_age:
                issues.append(f"角色「{name}」年龄字段为 {declared_age} 岁，但文本中出现 {mentioned_age} 岁")
                break
        if declared_age < _MIN_ADULT_AGE and any(hint in text for hint in _MARRIAGE_HINTS):
            issues.append(f"角色「{name}」未成年年龄与婚恋/婚姻设定冲突")
        if declared_age >= _MIN_ADULT_AGE and any(hint in text for hint in _UNDERAGE_HINTS):
            issues.append(f"角色「{name}」成年年龄与未成年/少年化表述冲突")
    return issues


def _character_trauma_event_issues(char: dict) -> List[str]:
    name = (char.get("name") or "").strip() or "未命名角色"
    text = _character_age_text(char)
    hits = []
    for label, keywords in _TRAUMA_EVENT_GROUPS.items():
        if any(keyword in text for keyword in keywords):
            hits.append(label)
    if len(hits) < 2:
        return []
    return [f"角色「{name}」关键经历同时出现「{' / '.join(hits[:3])}」，事故来源需统一"]


@lru_cache(maxsize=1)
def _ai_blacklist_phrases() -> tuple[str, ...]:
    fallback = ("首先", "综上所述", "日子一天天过去", "非常开心", "眼神复杂")
    try:
        from apps.skill.config.portal.reference_libs import ReferenceLibraryService

        data = ReferenceLibraryService.get_json("ai-keywords-blacklist.json")
        phrases: List[str] = []
        block = data.get("套话黑名单") or {}
        if isinstance(block, dict):
            for arr in block.values():
                if isinstance(arr, list):
                    phrases.extend(str(p).strip() for p in arr if str(p).strip())
        return tuple(dict.fromkeys(phrases or list(fallback)))
    except Exception as exc:  # noqa: BLE001
        logger.warning("[AgentDetection] ai blacklist load failed: %s", exc)
        return fallback


def run_character_gate(payload: dict) -> Dict[str, Any]:
    """character-gate：人设完整性快检（P 子集）。"""
    view = build_character_bible_view(payload if isinstance(payload, dict) else {})
    issues: List[str] = []
    chars = view.get("characters") or []
    if not chars:
        issues.append("未找到任何角色档案")
    protagonists = view.get("groups", {}).get("protagonists") or []
    if not protagonists:
        issues.append("缺少主角（protagonist）")
    for char in chars:
        name = (char.get("name") or "").strip()
        if not name:
            issues.append("存在无姓名的角色条目")
            continue
        if not (char.get("oneLineSummary") or char.get("coreMotivation") or char.get("personality")):
            issues.append(f"角色「{name}」缺少梗概/动机/性格描述")
        issues.extend(_character_age_issues(char))
        issues.extend(_character_trauma_event_issues(char))
    rel = (view.get("relationshipSummary") or "").strip()
    if len(chars) >= 2 and not rel and not (view.get("relationships") or []):
        issues.append("多角色项目缺少关系网摘要")
    return {
        "passed": len(issues) == 0,
        "checkedAt": _now_iso(),
        "characterCount": len(chars),
        "issues": issues[:12],
    }


def _episode_texts(payload: dict) -> List[tuple[int, str]]:
    from ..fusion.fusion_pipeline import scripts_result_to_markdown

    rows: List[tuple[int, str]] = []
    merged = scripts_result_to_markdown(payload)
    if merged.strip():
        rows.append((0, merged))
        return rows
    for ep in payload.get("episodes") or []:
        if not isinstance(ep, dict):
            continue
        num = int(ep.get("episodeNumber") or ep.get("episode") or 0)
        parts: List[str] = []
        for key in ("full_script_text", "scriptMarkdown"):
            val = (ep.get(key) or "").strip()
            if val:
                parts.append(val)
        if not parts:
            for sc in ep.get("scenes") or []:
                if not isinstance(sc, dict):
                    continue
                for dlg in sc.get("dialogues") or []:
                    if isinstance(dlg, dict):
                        parts.append(f"{dlg.get('speaker', '')}：{dlg.get('line', '')}")
        text = "\n".join(parts).strip()
        if text:
            rows.append((num, text))
    return rows


def run_creator_quality_guard(payload: dict) -> Dict[str, Any]:
    """creator-quality-guard：创作阶段 AI 套话/对白自然度快检。"""
    phrases = _ai_blacklist_phrases()
    episodes = _episode_texts(payload)
    if not episodes:
        return {
            "passed": True,
            "checkedAt": _now_iso(),
            "skipped": True,
            "reason": "无剧本文本",
            "issues": [],
        }
    per_ep: List[Dict[str, Any]] = []
    issues: List[str] = []
    for ep_num, text in episodes:
        hits = [p for p in phrases if p and p in text]
        hit_count = len(hits)
        if ep_num > 0 and hit_count >= _AI_HIT_WARN_PER_EP:
            sample = "、".join(hits[:3])
            issues.append(f"第{ep_num}集 AI 套话命中 {hit_count} 处（如：{sample}）")
        per_ep.append(
            {
                "episodeNumber": ep_num or None,
                "aiPhraseHits": hit_count,
                "samples": hits[:5],
            }
        )
    worst = max((row["aiPhraseHits"] for row in per_ep), default=0)
    passed = worst < _AI_HIT_FAIL_PER_EP and len(issues) <= 3
    return {
        "passed": passed,
        "checkedAt": _now_iso(),
        "phraseCatalogSize": len(phrases),
        "episodes": per_ep[:20],
        "issues": issues[:10],
    }
