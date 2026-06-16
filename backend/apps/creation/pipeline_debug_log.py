# -*- coding: utf-8 -*-
"""创作流水线调试日志：结构化摘要，不打印完整剧本/创意正文。"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("apps.creation.pipeline")

_SENSITIVE_TEXT_KEYS = frozenset(
    {
        "coreHook",
        "coreIdea",
        "scriptMarkdown",
        "full_script_text",
        "notes",
        "outline_text",
        "novel_text",
        "relationshipSummary",
        "roughOutline",
    }
)


def _json(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except TypeError:
        return str(data)


def _text_len(val: Any) -> int:
    return len(str(val or ""))


def _brief_summary(brief: dict) -> dict:
    if not isinstance(brief, dict):
        return {"present": False}
    ta = brief.get("targetAudience")
    audience_len = _text_len(ta.get("description") if isinstance(ta, dict) else ta)
    return {
        "workingTitle": brief.get("workingTitle"),
        "theme": brief.get("theme"),
        "episodeCount": brief.get("episodeCount"),
        "formatVariant": brief.get("formatVariant"),
        "coreHookLen": _text_len(brief.get("coreHook") or brief.get("coreIdea")),
        "audienceLen": audience_len,
        "hasWritingBrief": bool(brief.get("writingBrief")),
        "keys": sorted(brief.keys()),
    }


def summarize_upstream(node_id: str, upstream: Optional[dict]) -> dict:
    upstream = upstream or {}
    out: Dict[str, Any] = {"nodeId": node_id, "upstreamKeys": sorted(upstream.keys())}
    brief = upstream.get("projectBrief")
    if brief is not None:
        out["projectBrief"] = _brief_summary(brief if isinstance(brief, dict) else {})
    structure = upstream.get("structurePlan")
    if isinstance(structure, dict):
        out["structurePlan"] = {
            "totalEpisodes": structure.get("totalEpisodes"),
            "sixStagePlan": len(structure.get("sixStagePlan") or []),
            "keyReversalPoints": len(structure.get("keyReversalPoints") or []),
            "hasWorldview": bool(structure.get("worldview")),
            "keys": sorted(structure.keys()),
        }
    chars = upstream.get("characterBible")
    if isinstance(chars, dict):
        out["characterBible"] = {
            "characterCount": chars.get("characterCount") or len(chars.get("characters") or []),
            "relationshipSummaryLen": _text_len(chars.get("relationshipSummary")),
            "keys": sorted(chars.keys()),
        }
    outline = upstream.get("seriesOutline") or upstream.get("outline")
    if isinstance(outline, dict):
        out["seriesOutline"] = {
            "totalEpisodes": outline.get("totalEpisodes"),
            "episodes": len(outline.get("episodes") or []),
            "keys": sorted(outline.keys()),
        }
    return out


def summarize_artifact(artifact_key: str, payload: Optional[dict]) -> dict:
    if not isinstance(payload, dict) or not payload:
        return {"artifactKey": artifact_key, "empty": True}

    base: Dict[str, Any] = {
        "artifactKey": artifact_key,
        "topKeys": sorted(payload.keys()),
    }

    if artifact_key == "project_brief":
        base.update(_brief_summary(payload))
        return base

    if artifact_key == "structure_plan":
        wv = payload.get("worldview") or {}
        base.update(
            {
                "totalEpisodes": payload.get("totalEpisodes"),
                "sixStagePlan": len(payload.get("sixStagePlan") or []),
                "keyReversalPoints": len(payload.get("keyReversalPoints") or []),
                "rhythmCurve": len(payload.get("rhythmCurve") or []),
                "worldviewKeys": sorted(wv.keys()) if isinstance(wv, dict) else [],
                "hasCoreStoryArc": bool(payload.get("coreStoryArc")),
            }
        )
        return base

    if artifact_key == "character_bible":
        base.update(
            {
                "characterCount": payload.get("characterCount") or len(payload.get("characters") or []),
                "relationshipSummaryLen": _text_len(payload.get("relationshipSummary")),
            }
        )
        return base

    if artifact_key == "series_outline":
        base.update(
            {
                "totalEpisodes": payload.get("totalEpisodes"),
                "episodes": len(payload.get("episodes") or []),
                "roughOutlineLen": _text_len(payload.get("roughOutline")),
            }
        )
        return base

    if artifact_key == "episode_scripts":
        eps = payload.get("episodes") or []
        word_total = sum(int(e.get("wordCount") or 0) for e in eps if isinstance(e, dict))
        base.update(
            {
                "episodes": len(eps),
                "wordTotal": word_total,
                "episodeNumbers": sorted(
                    int(e.get("episodeNumber"))
                    for e in eps
                    if isinstance(e, dict) and e.get("episodeNumber") is not None
                )[:20],
            }
        )
        return base

    for key in list(payload.keys())[:12]:
        if key in _SENSITIVE_TEXT_KEYS:
            base[f"{key}Len"] = _text_len(payload.get(key))
    return base


def summarize_loaded_artifacts(artifacts: Optional[dict]) -> dict:
    artifacts = artifacts or {}
    return {
        key: summarize_artifact(key, val if isinstance(val, dict) else {})
        for key, val in artifacts.items()
    }


def log_fusion_node_begin(
    *,
    project_id: Any,
    node_id: str,
    node_index: Optional[int] = None,
    upstream: Optional[dict] = None,
    prompt_stats: Optional[dict] = None,
    extra: Optional[dict] = None,
) -> None:
    logger.info(
        "[Fusion] BEGIN project=%s node=%s idx=%s upstream=%s prompt=%s extra=%s",
        project_id,
        node_id,
        node_index,
        _json(summarize_upstream(node_id, upstream)),
        _json(prompt_stats or {}),
        _json(extra or {}),
    )


def log_fusion_node_done(
    *,
    project_id: Any,
    node_id: str,
    artifact_key: str,
    payload: Optional[dict],
    schema_warnings: Optional[list] = None,
) -> None:
    logger.info(
        "[Fusion] DONE project=%s node=%s artifact=%s output=%s schema_warn=%s",
        project_id,
        node_id,
        artifact_key,
        _json(summarize_artifact(artifact_key, payload)),
        _json((schema_warnings or [])[:8]),
    )


def log_fusion_node_fail(
    *,
    project_id: Any,
    node_id: str,
    node_index: Optional[int] = None,
    error: str,
    upstream: Optional[dict] = None,
) -> None:
    logger.error(
        "[Fusion] FAIL project=%s node=%s idx=%s error=%s upstream=%s",
        project_id,
        node_id,
        node_index,
        error[:500],
        _json(summarize_upstream(node_id, upstream)),
    )
    try:
        from apps.monitoring.services.task_error import record_fusion_node_failure

        record_fusion_node_failure(
            project_id=project_id,
            node_id=node_id,
            node_index=node_index,
            error=error,
            upstream=summarize_upstream(node_id, upstream),
        )
    except Exception:
        logger.exception("[Fusion] monitoring write failed project=%s node=%s", project_id, node_id)


def log_skill_task_begin(
    *,
    project_id: Any,
    node_index: int,
    script_from: Optional[int] = None,
    script_to: Optional[int] = None,
    upstream_keys: Optional[list] = None,
) -> None:
    logger.info(
        "[SkillTask] BEGIN project=%s node=%s script=%s..%s loaded_artifacts=%s",
        project_id,
        node_index,
        script_from,
        script_to,
        _json(upstream_keys or []),
    )


def log_skill_task_done(
    *,
    project_id: Any,
    node_index: int,
    status: str,
    artifact_key: Optional[str] = None,
    detail: Optional[dict] = None,
) -> None:
    logger.info(
        "[SkillTask] END project=%s node=%s status=%s artifact=%s detail=%s",
        project_id,
        node_index,
        status,
        artifact_key,
        _json(detail or {}),
    )
    if status in {"failed", "exception", "error"} and not (detail or {}).get("execution_run_id"):
        try:
            from apps.monitoring.services.task_error import record_background_task_failure

            record_background_task_failure(
                task_name="creation.skill_task",
                project_id=project_id,
                node_index=node_index,
                status=status,
                detail=detail,
                exception_type="SkillTaskFailed",
            )
        except Exception:
            logger.exception("[SkillTask] monitoring write failed project=%s node=%s", project_id, node_index)


def log_skill_enqueue(
    *,
    project_id: Any,
    node_index: int,
    regenerate: bool = False,
    batch: Optional[dict] = None,
) -> None:
    logger.info(
        "[Workspace] ENQUEUE project=%s node=%s regenerate=%s batch=%s",
        project_id,
        node_index,
        regenerate,
        _json(batch or {}),
    )
