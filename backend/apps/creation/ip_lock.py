# -*- coding: utf-8 -*-
"""IP 续作锁定：ip-character-lock / ip-script-lock（规则层）。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def is_ip_sequel(brief: Optional[dict]) -> bool:
    brief = brief if isinstance(brief, dict) else {}
    entry = (brief.get("creationEntry") or "").strip()
    return entry == "ip-sequel"


def build_ip_roster(character_bible: dict) -> List[Dict[str, str]]:
    roster: List[Dict[str, str]] = []
    seen: Set[str] = set()
    for key in ("protagonists", "antagonists", "supportingRoles", "characters"):
        for c in character_bible.get(key) or []:
            if not isinstance(c, dict):
                continue
            name = (c.get("name") or "").strip()
            cid = (c.get("id") or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            roster.append(
                {
                    "id": cid,
                    "name": name,
                    "roleType": (c.get("roleType") or key.rstrip("s"))[:40],
                }
            )
    return roster


def _episode_text(ep: dict) -> str:
    parts: List[str] = []
    for key in ("scriptMarkdown", "full_script_text", "title"):
        val = (ep.get(key) or "").strip()
        if val:
            parts.append(val)
    for sc in ep.get("scenes") or []:
        if not isinstance(sc, dict):
            continue
        for dlg in sc.get("dialogues") or []:
            if isinstance(dlg, dict):
                parts.append(str(dlg.get("line") or ""))
                parts.append(str(dlg.get("character") or dlg.get("speaker") or ""))
    return "\n".join(parts)


def run_character_ip_lock(
    character_bible: dict,
    brief: Optional[dict] = None,
    *,
    prior_roster: Optional[List[dict]] = None,
) -> Dict[str, Any]:
    brief = brief if isinstance(brief, dict) else {}
    if not is_ip_sequel(brief):
        return {"skipped": True, "passed": True, "source": "ip-character-lock"}

    roster = build_ip_roster(character_bible)
    issues: List[str] = []
    locked_names = [r["name"] for r in roster if r.get("name")]

    if prior_roster:
        prior_names = {(r.get("name") or "").strip() for r in prior_roster if isinstance(r, dict)}
        prior_names.discard("")
        missing = sorted(prior_names - set(locked_names))
        if missing:
            issues.append(f"IP 续作角色 roster 缺失：{'、'.join(missing[:5])}")

    keep_rules = brief.get("ipKeepRules") or brief.get("ipSequelRules") or ""
    if isinstance(keep_rules, str) and keep_rules.strip():
        name_blob = locked_names
        for line in keep_rules.splitlines():
            token = line.strip()
            if len(token) < 2:
                continue
            if not any(token in name or name == token for name in name_blob):
                issues.append(f"须保留角色/设定未出现：{token[:24]}")

    protagonists = [
        (c.get("name") or "").strip()
        for c in (character_bible.get("protagonists") or [])
        if isinstance(c, dict) and (c.get("name") or "").strip()
    ]
    if not protagonists:
        issues.append("IP 续作须至少锁定 1 名主角")

    return {
        "skipped": False,
        "passed": len(issues) == 0,
        "checkedAt": _now_iso(),
        "source": "ip-character-lock",
        "roster": roster[:24],
        "lockedCount": len(roster),
        "forbidOoc": bool((brief.get("ipLock") or {}).get("forbidOoc")),
        "issues": issues[:10],
    }


def run_script_ip_lock(
    payload: dict,
    *,
    brief: Optional[dict] = None,
    character_bible: Optional[dict] = None,
) -> Dict[str, Any]:
    brief = brief if isinstance(brief, dict) else {}
    if not is_ip_sequel(brief):
        return {"skipped": True, "passed": True, "source": "ip-script-lock"}

    bible = character_bible if isinstance(character_bible, dict) else {}
    roster = (bible.get("ipLockRoster") or build_ip_roster(bible))[:16]
    if not roster:
        return {
            "skipped": False,
            "passed": False,
            "source": "ip-script-lock",
            "issues": ["无 IP 锁定角色 roster"],
        }

    char_map = payload.get("characterIdToNameMap") or {}
    issues: List[str] = []
    for item in roster:
        name = item.get("name") or ""
        cid = item.get("id") or ""
        if cid and char_map.get(cid) and char_map.get(cid) != name:
            issues.append(f"角色映射变更：{cid} {char_map[cid]}≠{name}")

    core_names = [
        r["name"]
        for r in roster
        if r.get("name") and str(r.get("roleType") or "").startswith(("protagonist", "antagonist"))
    ][:6]
    if not core_names:
        core_names = [r["name"] for r in roster[:2] if r.get("name")]

    episodes = payload.get("episodes") or []
    for ep in episodes:
        if not isinstance(ep, dict):
            continue
        text = _episode_text(ep)
        ep_num = ep.get("episodeNumber") or ep.get("episode")
        for name in core_names:
            if name and name not in text:
                issues.append(f"第{ep_num}集未出现锁定角色「{name}」")

    signature_lines: List[str] = []
    for key in ("protagonists", "characters"):
        for c in bible.get(key) or []:
            if not isinstance(c, dict):
                continue
            for line in c.get("signatureLines") or []:
                if isinstance(line, str) and line.strip():
                    signature_lines.append(line.strip()[:40])
    merged = "\n".join(_episode_text(ep) for ep in episodes if isinstance(ep, dict))
    if signature_lines and merged:
        hit = sum(1 for s in signature_lines if s in merged)
        if hit == 0 and len(episodes) >= 2:
            issues.append("剧本未引用角色 signatureLines，存在 OOC 风险")

    return {
        "skipped": False,
        "passed": len(issues) <= 2,
        "checkedAt": _now_iso(),
        "source": "ip-script-lock",
        "rosterSize": len(roster),
        "issues": issues[:12],
    }


def merge_character_ip_lock(character_bible: dict, brief: dict, *, prior_roster: Optional[list] = None) -> dict:
    out = dict(character_bible or {})
    report = run_character_ip_lock(out, brief, prior_roster=prior_roster)
    if not report.get("skipped"):
        out["ipLockRoster"] = report.get("roster") or build_ip_roster(out)
        out["ipCharacterLockLog"] = report
    return out
