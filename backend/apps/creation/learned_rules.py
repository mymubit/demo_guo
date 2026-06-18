# -*- coding: utf-8 -*-
"""Learned rule recorder using ScriptForge internal storage only."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

_BASE_DIR = Path(getattr(settings, "SCRIPT_FORGE_ASSET_ROOT", "")) / "learned-rules"
_LEARNED_RULES_PATH = _BASE_DIR / "learned-rules.md"
_PATTERN_LOG_PATH = _BASE_DIR / "learned-rules-log.json"
_PATTERN_THRESHOLD = 3


def _load_pattern_log() -> Dict[str, Any]:
    try:
        if _PATTERN_LOG_PATH.is_file():
            return json.loads(_PATTERN_LOG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("[LearnedRules] load pattern log failed: %s", exc)
    return {"patterns": {}, "last_updated": ""}


def _save_pattern_log(log: Dict[str, Any]) -> None:
    try:
        log["last_updated"] = datetime.now().isoformat()
        _PATTERN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _PATTERN_LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[LearnedRules] save pattern log failed: %s", exc)


def _create_learned_rules_skeleton() -> None:
    _LEARNED_RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    _LEARNED_RULES_PATH.write_text("# Learned Rules\n\n", encoding="utf-8")


def _append_learned_rule(rule: Dict[str, Any]) -> None:
    try:
        _LEARNED_RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not _LEARNED_RULES_PATH.exists():
            _create_learned_rules_skeleton()
        entry = [
            f"## [{rule['id']}] {rule['title']}",
            "",
            f"- trigger: {rule['trigger']}",
            f"- discovered_at: {rule['discovered_at']}",
            f"- confidence: {rule['confidence']}",
            f"- dimensions: {', '.join(rule.get('dimensions', []))}",
            "",
            str(rule.get("description") or ""),
            "",
        ]
        for action in rule.get("suggested_actions", []):
            entry.append(f"- {action}")
        entry.append("\n---\n")
        with _LEARNED_RULES_PATH.open("a", encoding="utf-8") as f:
            f.write("\n".join(entry))
    except Exception as exc:  # noqa: BLE001
        logger.warning("[LearnedRules] append learned rule failed: %s", exc)


def record_convergence_failure(
    *,
    project_id: str,
    project_title: str,
    failed_dimensions: List[str],
    convergence_state: str,
    fix_round: int,
    score_history: List[float],
    genre: str = "",
) -> Optional[str]:
    dimensions = sorted(str(x) for x in failed_dimensions if str(x).strip())
    key = "|".join([genre or "unknown", convergence_state or "unknown", ",".join(dimensions)])
    log = _load_pattern_log()
    patterns = log.setdefault("patterns", {})
    item = patterns.setdefault(
        key,
        {
            "count": 0,
            "project_ids": [],
            "dimensions": dimensions,
            "genre": genre,
            "state": convergence_state,
        },
    )
    item["count"] = int(item.get("count") or 0) + 1
    item.setdefault("project_ids", []).append(str(project_id))
    item["last_project_title"] = project_title
    item["last_fix_round"] = fix_round
    item["last_score_history"] = score_history
    _save_pattern_log(log)
    if item["count"] < _PATTERN_THRESHOLD:
        return None
    rule = _synthesize_rule(key, item)
    _append_learned_rule(rule)
    return rule["id"]


def _synthesize_rule(key: str, item: Dict[str, Any]) -> Dict[str, Any]:
    dimensions = list(item.get("dimensions") or [])
    genre = str(item.get("genre") or "")
    return {
        "id": f"learned-{abs(hash(key)) % 1_000_000}",
        "title": f"Repeated convergence failure: {genre or 'general'}",
        "trigger": f"{item.get('count')} similar failures",
        "discovered_at": datetime.now().isoformat(),
        "confidence": min(0.95, 0.5 + 0.1 * int(item.get("count") or 0)),
        "dimensions": dimensions,
        "description": f"Repeated blocked convergence in dimensions: {', '.join(dimensions) or 'unknown'}.",
        "suggested_actions": _generate_suggested_actions(dimensions, genre),
    }


def _generate_suggested_actions(dimensions: List[str], genre: str) -> List[str]:
    base = [f"Review prompt and rubric for {dim}." for dim in dimensions[:5]]
    if genre:
        base.append(f"Check genre-specific constraints for {genre}.")
    return base or ["Review failed dimensions and update explicit post-processing prompts."]
