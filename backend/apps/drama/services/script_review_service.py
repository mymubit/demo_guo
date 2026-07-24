# -*- coding: utf-8 -*-
"""独立剧本评审：CRUD、脚本包装、触发执行、对比投影。"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from rest_framework import status

from apps.core.exceptions import BusinessException, NOT_FOUND, VALIDATION_ERROR
from apps.drama.models import ScriptReview, ScriptReviewRun, V3CommandRun, V3Project

_MAX_SCRIPT_BYTES = 2 * 1024 * 1024
_ALLOWED_UPLOAD_SUFFIXES = {".txt", ".md"}
_KIND_TO_COMMAND = {
    ScriptReviewRun.Kind.QUALITY: "score_external_script",
    ScriptReviewRun.Kind.COMPLIANCE: "check_external_compliance",
}


def wrap_script_as_episode_scripts(*, title: str, script_text: str) -> dict[str, Any]:
    """将外界全文包装为 episode_scripts 形态，供 scorer/compliance 复用。"""
    text = (script_text or "").strip()
    display = (title or "").strip() or "外界剧本"
    return {
        "episodes": [
            {
                "episode_number": 1,
                "title": display,
                "script": text,
                "word_count": len(text),
                "dialogue_ratio": 0.5,
                "scene_count": max(1, text.count("\n\n") or text.count("\n") or 1),
            }
        ]
    }


def stub_project_brief(*, title: str) -> dict[str, Any]:
    display = (title or "").strip() or "外界剧本"
    return {
        "title": display,
        "genre_matrix": {
            "emotion": "ambition",
            "identity": "ordinary",
            "conflict": "family",
            "world": "modern",
        },
        "episode_count": 1,
        "core_idea": "外界剧本独立评审",
        "target_audience": "通用",
        "core_conflict": "待评分剧本内冲突",
        "hook_concept": "外界输入",
        "compliance_risk": "standard",
    }


def stub_episode_plan(*, title: str) -> dict[str, Any]:
    display = (title or "").strip() or "外界剧本"
    return {
        "episodes": [
            {
                "episode": 1,
                "title": display,
                "summary": "外界剧本全文（单集包装）",
                "hook": "开篇",
                "payoff": "收束",
            }
        ]
    }


def default_title_from_text(script_text: str) -> str:
    for line in (script_text or "").splitlines():
        cleaned = line.strip().lstrip("#").strip()
        if cleaned:
            return cleaned[:200]
    return "未命名剧本"


def decode_upload_bytes(raw: bytes, *, filename: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in _ALLOWED_UPLOAD_SUFFIXES:
        raise BusinessException(
            VALIDATION_ERROR,
            "仅支持 .txt / .md 文件",
            http_status=status.HTTP_400_BAD_REQUEST,
        )
    if len(raw) > _MAX_SCRIPT_BYTES:
        raise BusinessException(
            VALIDATION_ERROR,
            f"文件过大，上限 {_MAX_SCRIPT_BYTES // (1024 * 1024)}MB",
            http_status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BusinessException(
            VALIDATION_ERROR,
            "文件编码须为 UTF-8",
            http_status=status.HTTP_400_BAD_REQUEST,
        ) from exc


def _resolve_owned_project(*, owner, project_id: UUID | str | None) -> V3Project | None:
    if project_id is None or project_id == "":
        return None
    try:
        return V3Project.objects.get(id=project_id, owner=owner)
    except V3Project.DoesNotExist as exc:
        raise BusinessException(
            NOT_FOUND,
            "关联项目不存在或无权访问",
            http_status=status.HTTP_404_NOT_FOUND,
        ) from exc


def create_review(
    *,
    owner,
    script_text: str,
    title: str = "",
    project_id: UUID | str | None = None,
    source_type: str = ScriptReview.SourceType.PASTE,
    source_filename: str = "",
) -> ScriptReview:
    text = (script_text or "").strip()
    if not text:
        raise BusinessException(
            VALIDATION_ERROR,
            "剧本正文不能为空",
            http_status=status.HTTP_400_BAD_REQUEST,
        )
    encoded = text.encode("utf-8")
    if len(encoded) > _MAX_SCRIPT_BYTES:
        raise BusinessException(
            VALIDATION_ERROR,
            f"剧本过长，上限 {_MAX_SCRIPT_BYTES // (1024 * 1024)}MB",
            http_status=status.HTTP_400_BAD_REQUEST,
        )
    project = _resolve_owned_project(owner=owner, project_id=project_id)
    display = (title or "").strip() or default_title_from_text(text)
    if source_type not in ScriptReview.SourceType.values:
        raise BusinessException(
            VALIDATION_ERROR,
            "来源类型无效",
            http_status=status.HTTP_400_BAD_REQUEST,
        )
    return ScriptReview.objects.create(
        owner=owner,
        project=project,
        title=display[:200],
        source_type=source_type,
        source_filename=(source_filename or "")[:255],
        script_text=text,
    )


def get_owned_review(*, owner, review_id: UUID | str) -> ScriptReview:
    try:
        return ScriptReview.objects.select_related("project").get(
            id=review_id, owner=owner
        )
    except ScriptReview.DoesNotExist as exc:
        raise BusinessException(
            NOT_FOUND,
            "评审件不存在",
            http_status=status.HTTP_404_NOT_FOUND,
        ) from exc


def list_reviews(*, owner, project_id: UUID | str | None = None):
    qs = ScriptReview.objects.filter(owner=owner).select_related("project")
    if project_id:
        qs = qs.filter(project_id=project_id)
    return qs.order_by("-updated_at")


def serialize_run(run: ScriptReviewRun) -> dict[str, Any]:
    return {
        "id": str(run.id),
        "kind": run.kind,
        "status": run.status,
        "command_run_id": str(run.command_run_id) if run.command_run_id else None,
        "report_payload": run.report_payload if isinstance(run.report_payload, dict) else {},
        "error_message": run.error_message or "",
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


def serialize_review(
    review: ScriptReview,
    *,
    include_script: bool = True,
    include_runs: bool = True,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": str(review.id),
        "title": review.title,
        "source_type": review.source_type,
        "source_filename": review.source_filename or "",
        "project_id": str(review.project_id) if review.project_id else None,
        "project_title": review.project.title if review.project_id and review.project else None,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "updated_at": review.updated_at.isoformat() if review.updated_at else None,
    }
    if include_script:
        data["script_text"] = review.script_text
    else:
        data["script_preview"] = (review.script_text or "")[:240]
        data["script_char_count"] = len(review.script_text or "")

    runs_qs = ScriptReviewRun.objects.filter(review=review).order_by("-created_at")
    latest_quality = None
    latest_compliance = None
    for run in runs_qs:
        if (
            latest_quality is None
            and run.kind == ScriptReviewRun.Kind.QUALITY
            and run.status == ScriptReviewRun.Status.SUCCEEDED
        ):
            latest_quality = run
        if (
            latest_compliance is None
            and run.kind == ScriptReviewRun.Kind.COMPLIANCE
            and run.status == ScriptReviewRun.Status.SUCCEEDED
        ):
            latest_compliance = run
        if latest_quality and latest_compliance:
            break

    data["latest_quality_score"] = None
    data["latest_quality_grade"] = None
    if latest_quality and isinstance(latest_quality.report_payload, dict):
        payload = latest_quality.report_payload
        score = payload.get("overall_score")
        data["latest_quality_score"] = score if isinstance(score, (int, float)) else None
        grade = payload.get("grade")
        data["latest_quality_grade"] = str(grade) if grade else None

    data["latest_compliance_result"] = None
    if latest_compliance and isinstance(latest_compliance.report_payload, dict):
        result = latest_compliance.report_payload.get("overall_result")
        data["latest_compliance_result"] = str(result) if result else None

    if include_runs:
        data["runs"] = [serialize_run(run) for run in runs_qs[:50]]
    return data


@transaction.atomic
def enqueue_review_run(
    *,
    review: ScriptReview,
    kind: str,
) -> ScriptReviewRun:
    if kind not in ScriptReviewRun.Kind.values:
        raise BusinessException(
            VALIDATION_ERROR,
            "评审类型无效",
            http_status=status.HTTP_400_BAD_REQUEST,
        )
    command_type = _KIND_TO_COMMAND[kind]
    command_run = V3CommandRun.objects.create(
        owner=review.owner,
        project=review.project,
        command_type=command_type,
        status=V3CommandRun.Status.QUEUED,
        request_payload={
            "script_review_id": str(review.id),
            "kind": kind,
        },
    )
    review_run = ScriptReviewRun.objects.create(
        review=review,
        kind=kind,
        status=ScriptReviewRun.Status.QUEUED,
        command_run=command_run,
    )
    review.updated_at = timezone.now()
    review.save(update_fields=["updated_at"])
    return review_run


def dispatch_review_run(review_run: ScriptReviewRun) -> None:
    from apps.drama.orchestrator.script_review_runner import enqueue_script_review

    enqueue_script_review(review_run.id)


def _quality_side(payload: dict[str, Any]) -> dict[str, Any]:
    dimensions_raw = payload.get("dimensions")
    dimensions: list[dict[str, Any]] = []
    if isinstance(dimensions_raw, dict):
        for key, value in dimensions_raw.items():
            if not isinstance(value, dict):
                continue
            dimensions.append(
                {
                    "key": key,
                    "score": value.get("score"),
                    "weight": value.get("weight"),
                }
            )
    defects = payload.get("critical_defects") or payload.get("top_defects") or []
    if not isinstance(defects, list):
        defects = []
    return {
        "summary": {
            "overall_score": payload.get("overall_score"),
            "grade": payload.get("grade"),
            "verdict": payload.get("verdict")
            or payload.get("needs_revision")
            or payload.get("can_continue_next_batch"),
            "pass_threshold": payload.get("pass_threshold"),
        },
        "dimensions": dimensions,
        "top_defects": defects[:10],
    }


def _compliance_side(payload: dict[str, Any]) -> dict[str, Any]:
    blocking = payload.get("blocking_issues") or []
    risks = payload.get("risk_items") or []
    if not isinstance(blocking, list):
        blocking = []
    if not isinstance(risks, list):
        risks = []
    return {
        "summary": {
            "overall_result": payload.get("overall_result"),
            "target_platform": payload.get("target_platform"),
            "blocking_count": len(blocking),
            "risk_count": len(risks),
        },
        "dimensions": [],
        "top_defects": (blocking + risks)[:10],
    }


def _project_side(*, run: ScriptReviewRun) -> dict[str, Any]:
    payload = run.report_payload if isinstance(run.report_payload, dict) else {}
    base = {
        "run_id": str(run.id),
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }
    if run.kind == ScriptReviewRun.Kind.QUALITY:
        base.update(_quality_side(payload))
    else:
        base.update(_compliance_side(payload))
    return base


def compare_runs(
    *,
    review: ScriptReview,
    run_a_id: UUID | str,
    run_b_id: UUID | str,
) -> dict[str, Any]:
    try:
        left = ScriptReviewRun.objects.get(id=run_a_id, review=review)
        right = ScriptReviewRun.objects.get(id=run_b_id, review=review)
    except ScriptReviewRun.DoesNotExist as exc:
        raise BusinessException(
            NOT_FOUND,
            "对比记录不存在",
            http_status=status.HTTP_404_NOT_FOUND,
        ) from exc

    if left.kind != right.kind:
        raise BusinessException(
            VALIDATION_ERROR,
            "仅支持同类型记录对比",
            http_status=status.HTTP_400_BAD_REQUEST,
        )
    if left.status != ScriptReviewRun.Status.SUCCEEDED:
        raise BusinessException(
            VALIDATION_ERROR,
            "左侧记录尚未成功，无法对比",
            http_status=status.HTTP_400_BAD_REQUEST,
        )
    if right.status != ScriptReviewRun.Status.SUCCEEDED:
        raise BusinessException(
            VALIDATION_ERROR,
            "右侧记录尚未成功，无法对比",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    left_side = _project_side(run=left)
    right_side = _project_side(run=right)
    deltas: dict[str, Any] = {}
    if left.kind == ScriptReviewRun.Kind.QUALITY:
        left_score = left_side["summary"].get("overall_score")
        right_score = right_side["summary"].get("overall_score")
        if isinstance(left_score, (int, float)) and isinstance(right_score, (int, float)):
            deltas["overall_score"] = right_score - left_score
    else:
        deltas["blocking_count"] = (
            right_side["summary"].get("blocking_count", 0)
            - left_side["summary"].get("blocking_count", 0)
        )

    return {
        "kind": left.kind,
        "left": left_side,
        "right": right_side,
        "deltas": deltas,
    }
