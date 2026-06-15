# -*- coding: utf-8 -*-
"""节点5 逐集 sub-gate 闭环（技能 detection/episode-gate，网站只调 CLI）。"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from apps.common.user_messages import humanize_user_message
from apps.workflow.fusion import FusionCliRunner

from .artifact_renderer import episode_to_gate_markdown, outline_to_gate_markdown

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def gate_log_from_cli_result(gate_json: dict, *, cli_ok: bool) -> dict:
    delivery = gate_json.get("delivery") or {}
    issues: List[str] = []
    for step in gate_json.get("steps") or []:
        if not step.get("passed"):
            for item in step.get("issues") or []:
                issues.append(f"{step.get('name', step.get('id', ''))}: {item}")
    if gate_json.get("issues"):
        issues.extend(gate_json["issues"])
    return {
        "passed": bool(gate_json.get("passed", cli_ok)),
        "checkedAt": _now_iso(),
        "words": delivery.get("words"),
        "dialogueRatio": delivery.get("dialogueRatio"),
        "sceneCount": delivery.get("scenes"),
        "dialogueCount": delivery.get("dialogues"),
        "issues": issues[:20],
    }


def summarize_episode_gates(episode_scripts: dict) -> dict:
    """汇总逐集 gate 结果，供 progress / 前端展示。"""
    eps = episode_scripts.get("episodes") or []
    failed: List[dict] = []
    for ep in eps:
        gl = ep.get("gateLog") or {}
        if gl and not gl.get("passed"):
            failed.append(
                {
                    "episodeNumber": ep.get("episodeNumber"),
                    "title": ep.get("title"),
                    "issues": (gl.get("issues") or [])[:5],
                }
            )
    passed = sum(1 for e in eps if (e.get("gateLog") or {}).get("passed"))
    return {
        "total": len(eps),
        "passed": passed,
        "failed": len(eps) - passed,
        "passRate": round(passed / len(eps) * 100, 1) if eps else 0,
        "failedEpisodes": failed[:15],
    }


def apply_episode_gates(
    episodes: List[dict],
    outline: dict,
    *,
    work_dir: Path,
    project_hex: str,
    runner: Optional[FusionCliRunner] = None,
    strict: bool = False,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> List[dict]:
    """为每集写入 gateLog（sub-gate --episode）。"""
    if not episodes:
        return episodes

    work_dir.mkdir(parents=True, exist_ok=True)
    r = runner or FusionCliRunner()
    outline_path = work_dir / f"{project_hex}_outline_gate.md"
    outline_path.write_text(outline_to_gate_markdown(outline), encoding="utf-8")

    out: List[dict] = []
    total = len(episodes)
    done = 0
    for ep in episodes:
        ep_num = ep.get("episodeNumber")
        if ep_num is None:
            out.append(ep)
            continue
        ep_path = work_dir / f"{project_hex}_ep{ep_num}.md"
        ep_path.write_text(episode_to_gate_markdown(ep), encoding="utf-8")
        try:
            from .orchestration.sub_skill_runner import cli_episode_gate

            cli = cli_episode_gate(
                r,
                ep_path,
                episode=int(ep_num),
                outline_path=outline_path,
                strict=strict,
            )
            gate_json = cli.get("json") or {}
            ep = {**ep, "gateLog": gate_log_from_cli_result(gate_json, cli_ok=cli.get("ok", False))}
        except Exception as exc:  # noqa: BLE001
            logger.warning("逐集 gate 失败 ep=%s: %s", ep_num, exc)
            ep = {
                **ep,
                "gateLog": {
                    "passed": False,
                    "checkedAt": _now_iso(),
                    "issues": [humanize_user_message(str(exc), default="质检执行失败")[:200]],
                },
            }
        out.append(ep)
        done += 1
        if on_progress and ep_num is not None:
            try:
                on_progress(done, int(ep_num))
            except Exception as exc:  # noqa: BLE001
                logger.debug("gate on_progress 回调异常: %s", exc)
    return out
