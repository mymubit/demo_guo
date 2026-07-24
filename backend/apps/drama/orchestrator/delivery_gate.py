# -*- coding: utf-8 -*-
"""V3 交付门禁（纯 Python，无 LLM）。"""
from __future__ import annotations

from typing import Any

from apps.drama.models import V3ArtifactVersion, V3Project, V3QualityFinding
from apps.drama.orchestrator.artifacts import latest
from apps.drama.orchestrator.report_meta import is_report_stale

_PASS_GRADES = frozenset({"S", "A", "B"})
_PASS_VERDICTS = frozenset({"通过", "条件通过"})


def evaluate_delivery_gate(project: V3Project) -> dict[str, Any]:
    """
    判定项目是否可打包交付。

    返回: { "passed": bool, "blockers": list[str] }
    """
    scripts = latest(
        project, "episode_scripts", status=V3ArtifactVersion.Status.COMMITTED
    )
    if scripts is None:
        return {"passed": False, "blockers": ["请先确认正文后再交付"]}

    blockers: list[str] = []

    quality = latest(
        project, "quality_report", status=V3ArtifactVersion.Status.COMMITTED
    )
    if quality is None or is_report_stale(
        report_payload=quality.payload if isinstance(quality.payload, dict) else {},
        current_script=scripts,
    ):
        blockers.append("需要有效的质量报告，请重新评分")
    elif not _quality_passes(
        quality.payload if isinstance(quality.payload, dict) else {}
    ):
        blockers.append("质量报告未通过门禁")

    compliance = latest(
        project, "compliance_report", status=V3ArtifactVersion.Status.COMMITTED
    )
    compliance_payload: dict[str, Any] = (
        compliance.payload
        if compliance is not None and isinstance(compliance.payload, dict)
        else {}
    )
    if compliance is None or is_report_stale(
        report_payload=compliance_payload,
        current_script=scripts,
    ):
        blockers.append("需要有效的合规报告，请重新审查")
    elif compliance_payload.get("overall_result") != "通过":
        blockers.append("合规审查未通过")
    else:
        blockers.extend(
            _blocking_issue_blockers(project=project, payload=compliance_payload)
        )

    return {"passed": not blockers, "blockers": blockers}


def _quality_passes(payload: dict[str, Any]) -> bool:
    verdict = payload.get("verdict")
    if verdict in _PASS_VERDICTS:
        return True
    grade = payload.get("grade")
    return grade in _PASS_GRADES and payload.get("needs_revision") is False


def _blocking_issue_key(issue: Any, index: int) -> str:
    if isinstance(issue, dict):
        for field in ("finding_key", "id", "title"):
            value = issue.get(field)
            if value is not None and str(value).strip():
                return str(value).strip()[:128]
    return f"blocking:{index}"


def _blocking_issue_blockers(
    *, project: V3Project, payload: dict[str, Any]
) -> list[str]:
    raw = payload.get("blocking_issues")
    if not isinstance(raw, list) or not raw:
        return []

    accepted_keys = set(
        V3QualityFinding.objects.filter(
            project=project,
            source=V3QualityFinding.Source.COMPLIANCE,
            status=V3QualityFinding.Status.ACCEPTED,
        ).values_list("finding_key", flat=True)
    )
    for index, issue in enumerate(raw):
        key = _blocking_issue_key(issue, index)
        if key not in accepted_keys:
            return ["存在未接受的合规阻断项，请先接受后再交付"]
    return []
