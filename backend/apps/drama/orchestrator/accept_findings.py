# -*- coding: utf-8 -*-
"""V3 同步命令：接受质检/合规问题（无 LLM）。

finding_key 约定（与 delivery_gate._blocking_issue_key 对齐）：
- compliance.blocking_issues：优先 issue.finding_key → id → title，否则 `blocking:{index}`
- quality.defects：由调用方传入稳定键（如 defect:{index} 或报告内 id/finding_key）
- 门禁比对：V3QualityFinding(source=compliance, status=accepted).finding_key
  须与上述规则算出的 key 一致，否则仍阻断交付
"""
from __future__ import annotations

from django.db import transaction

from apps.drama.models import V3CommandRun, V3Project, V3QualityFinding

_VALID_SOURCES = frozenset(
    {
        V3QualityFinding.Source.QUALITY,
        V3QualityFinding.Source.COMPLIANCE,
    }
)


class AcceptFindingsError(Exception):
    """接受问题失败（人话消息）。"""


def _resolve_project(*, owner, payload: dict) -> V3Project:
    project_id = (payload or {}).get("project_id")
    if not project_id:
        raise AcceptFindingsError("缺少项目，请先打开一个创作项目")
    try:
        return V3Project.objects.get(id=project_id, owner=owner)
    except (V3Project.DoesNotExist, ValueError, TypeError) as exc:
        raise AcceptFindingsError("项目不存在或无权访问") from exc


def accept_findings(*, owner, payload: dict) -> dict:
    """
    upsert V3QualityFinding，status=accepted。

    payload: { project_id, findings: [{ source, finding_key, title?, severity? }] }
    """
    project = _resolve_project(owner=owner, payload=payload)
    raw_findings = (payload or {}).get("findings")
    if not isinstance(raw_findings, list) or not raw_findings:
        raise AcceptFindingsError("请至少选择一条要接受的问题")

    finding_ids: list[str] = []
    with transaction.atomic():
        for index, item in enumerate(raw_findings):
            if not isinstance(item, dict):
                raise AcceptFindingsError(f"第 {index + 1} 条问题格式无效")
            source = str(item.get("source") or "").strip()
            finding_key = str(item.get("finding_key") or "").strip()[:128]
            if source not in _VALID_SOURCES:
                raise AcceptFindingsError(
                    f"第 {index + 1} 条问题来源无效，应为 quality 或 compliance"
                )
            if not finding_key:
                raise AcceptFindingsError(f"第 {index + 1} 条问题缺少 finding_key")
            title = str(item.get("title") or "").strip()[:256] or finding_key
            severity = str(item.get("severity") or "").strip()[:32]
            finding, _created = V3QualityFinding.objects.update_or_create(
                project=project,
                source=source,
                finding_key=finding_key,
                defaults={
                    "title": title,
                    "severity": severity,
                    "status": V3QualityFinding.Status.ACCEPTED,
                },
            )
            finding_ids.append(str(finding.id))

    return {"finding_ids": finding_ids}


def run_accept_findings_command(
    *,
    owner,
    command_type: str,
    payload: dict,
    idempotency_key: str = "",
) -> V3CommandRun:
    """同步 accept_findings 入口：创建 run 并执行 upsert。"""
    with transaction.atomic():
        run = V3CommandRun.objects.create(
            owner=owner,
            command_type=command_type,
            status=V3CommandRun.Status.RUNNING,
            idempotency_key=idempotency_key or "",
            request_payload=payload or {},
        )
        try:
            if command_type != "accept_findings":
                raise AcceptFindingsError("未知同步变更命令")
            project = _resolve_project(owner=owner, payload=payload or {})
            run.project = project
            run.save(update_fields=["project", "updated_at"])
            result = accept_findings(owner=owner, payload=payload or {})
            run.status = V3CommandRun.Status.SUCCEEDED
            run.result_payload = result
            run.error_message = ""
            run.save(
                update_fields=[
                    "status",
                    "result_payload",
                    "error_message",
                    "updated_at",
                ]
            )
        except AcceptFindingsError as exc:
            run.status = V3CommandRun.Status.FAILED
            run.error_message = str(exc)
            run.save(update_fields=["status", "error_message", "updated_at"])
        return run
