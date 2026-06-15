# -*- coding: utf-8 -*-
"""compliance-content：内容合规细检（规则层，补充 compliance-check CLI）。"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _config_dir() -> Path:
    try:
        from apps.workflow.fusion import get_fusion_config

        return get_fusion_config().root / "config"
    except Exception:  # noqa: BLE001
        root = getattr(settings, "FUSION_SKILL_ROOT", "") or ""
        if root:
            return Path(root) / "config"
        return Path(__file__).resolve().parents[4] / "demo4book" / "short-drama-script-creator" / "config"


@lru_cache(maxsize=4)
def _load_compliance_config(filename: str) -> dict:
    path = _config_dir() / filename
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


_VILLAIN_WHITEWASH = (
    (r"反派.*(?:其实|原来).*(?:好人|苦衷|被迫)", "施害者洗白倾向"),
    (r"(?:小三|婆婆|恶婆婆).*(?:情有可原|值得同情)", "反派合理化"),
)


def _scan_keywords(
    text: str,
    keywords: List[str],
    *,
    label: str,
    level: str,
) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    lower = text.lower()
    for kw in keywords or []:
        token = str(kw).strip()
        if not token:
            continue
        count = text.count(token) + lower.count(token.lower())
        if count:
            hits.append(
                {
                    "code": label,
                    "keyword": token,
                    "count": count,
                    "level": level,
                }
            )
    return hits


def _scan_patterns(text: str, patterns: Tuple[Tuple[str, str], ...], *, level: str = "MEDIUM") -> List[Dict[str, Any]]:
    import re

    hits: List[Dict[str, Any]] = []
    for pattern, label in patterns:
        found = re.findall(pattern, text, flags=re.IGNORECASE)
        if found:
            hits.append({"code": label, "level": level, "count": len(found)})
    return hits


def _scan_fuse_combos(text: str, combos: List[list], *, label: str) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for combo in combos or []:
        if not isinstance(combo, list) or len(combo) < 2:
            continue
        if all(str(token) in text for token in combo):
            hits.append(
                {
                    "code": label,
                    "level": "HIGH",
                    "combo": combo,
                    "detail": "+".join(str(t) for t in combo),
                }
            )
    return hits


def run_compliance_content_scan(text: str) -> Dict[str, Any]:
    body = (text or "").strip()
    if not body:
        return {
            "passed": True,
            "skipped": True,
            "reason": "无剧本文本",
            "checkedAt": _now_iso(),
            "source": "compliance-content-rule",
            "issues": [],
            "findings": [],
        }

    findings: List[Dict[str, Any]] = []

    false_ad = _load_compliance_config("合规检测-虚假宣传关键词.json")
    findings.extend(
        _scan_keywords(
            body,
            false_ad.get("虚假宣传风险关键词") or [],
            label="false-advertising",
            level=str(false_ad.get("风险等级") or "warning").upper(),
        )
    )

    hot = _load_compliance_config("合规检测-社会热点敏感.json")
    hot_level = str(hot.get("风险等级") or "warning").upper()
    findings.extend(
        _scan_keywords(
            body,
            hot.get("社会事件敏感关键词") or [],
            label="hot-sensitive",
            level="FUSE" if hot_level == "FUSE" else hot_level,
        )
    )

    copyright_cfg = _load_compliance_config("合规检测-版权风险.json")
    findings.extend(
        _scan_keywords(
            body,
            copyright_cfg.get("版权风险关键词") or [],
            label="copyright-ip",
            level=str(copyright_cfg.get("风险等级") or "warning").upper(),
        )
    )
    findings.extend(
        _scan_keywords(
            body,
            copyright_cfg.get("知名IP片段") or [],
            label="copyright-quote",
            level="HIGH",
        )
    )
    findings.extend(
        _scan_fuse_combos(
            body,
            copyright_cfg.get("改编融梗熔断组合") or [],
            label="adaptation-fuse-combo",
        )
    )
    findings.extend(_scan_patterns(body, _VILLAIN_WHITEWASH))

    issues: List[str] = []
    high_count = 0
    fuse_triggered = False
    for item in findings:
        lvl = str(item.get("level") or "").upper()
        if lvl in ("HIGH", "FUSE", "WARNING"):
            high_count += 1
        if lvl == "FUSE" or item.get("code") == "adaptation-fuse-combo":
            fuse_triggered = True
        code = item.get("code") or "risk"
        kw = item.get("keyword") or item.get("detail") or item.get("combo")
        issues.append(f"{code}: {kw}")

    passed = not fuse_triggered and high_count <= 2 and len(findings) <= 8

    return {
        "passed": passed,
        "fuseTriggered": fuse_triggered,
        "skipped": False,
        "checkedAt": _now_iso(),
        "source": "compliance-content-rule",
        "findingCount": len(findings),
        "highRiskCount": high_count,
        "findings": findings[:20],
        "issues": issues[:16],
    }
