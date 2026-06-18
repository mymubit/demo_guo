# -*- coding: utf-8 -*-
"""Python-native episode quality gate for ScriptForge."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .validators.episode_gate import validate_episode

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _gate_log_from_validation(result) -> dict:
    issues = list(getattr(result, "issues", None) or [])
    return {
        "passed": bool(getattr(result, "passed", False)),
        "checkedAt": _now_iso(),
        "issues": [str(i)[:300] for i in issues[:20]],
        "validator": "python-native",
    }


def summarize_episode_gates(episode_scripts: dict) -> dict:
    episodes = episode_scripts.get("episodes") or []
    failed: List[dict] = []
    for ep in episodes:
        gate_log = ep.get("gateLog") or {}
        if gate_log and not gate_log.get("passed"):
            failed.append(
                {
                    "episodeNumber": ep.get("episodeNumber"),
                    "title": ep.get("title"),
                    "issues": (gate_log.get("issues") or [])[:5],
                }
            )
    passed = sum(1 for ep in episodes if (ep.get("gateLog") or {}).get("passed"))
    return {
        "total": len(episodes),
        "passed": passed,
        "failed": len(episodes) - passed,
        "passRate": round(passed / len(episodes) * 100, 1) if episodes else 0,
        "failedEpisodes": failed[:15],
    }


def apply_episode_gates(
    episodes: List[dict],
    outline: dict,
    *,
    work_dir: Path,
    project_hex: str,
    runner=None,
    strict: bool = False,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> List[dict]:
    if not episodes:
        return episodes
    outline_episodes = outline.get("episodes") or []
    out: List[dict] = []
    total = len(episodes)
    done = 0
    for ep in episodes:
        ep_num = ep.get("episodeNumber") or ep.get("episode")
        try:
            result = validate_episode(ep, outline_episodes=outline_episodes)
            ep = {**ep, "gateLog": _gate_log_from_validation(result)}
        except Exception as exc:  # noqa: BLE001
            logger.warning("python episode gate failed ep=%s: %s", ep_num, exc)
            ep = {
                **ep,
                "gateLog": {
                    "passed": not strict,
                    "checkedAt": _now_iso(),
                    "issues": [str(exc)[:200]],
                    "validator": "python-native",
                },
            }
        out.append(ep)
        done += 1
        if on_progress and ep_num is not None:
            try:
                on_progress(done, int(ep_num))
            except Exception as exc:  # noqa: BLE001
                logger.debug("gate on_progress callback failed: %s", exc)
    return out
