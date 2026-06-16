# -*- coding: utf-8 -*-
"""Agent 工作台：五步创作 Agent 独立生成，非串行流水线。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.billing.services import BillingService
from apps.workflow.services.pipeline_service import WorkflowPipelineService
from apps.common.user_messages import humanize_pipeline_error, safe_api_message
from apps.common.agent_term import alias_agent_id

from ..models import CreationNode, Project
from ..node_preview import build_node_preview
from ..services import _render_progress_html
from ..step_mode import artifact_key_for_node, clear_artifacts_from_node, reset_nodes_from_index
from ..pipeline_debug_log import log_skill_enqueue
from .workspace_editor import apply_editor_save, build_editor_view, compute_script_batch_range
from ..display.structure_display import workspace_display_title

logger = logging.getLogger(__name__)

_AGENT_HINTS = {
    1: "创作参数已确认；题材趋势与写作指引由系统根据你的故事策划自动匹配，可直接编辑保存",
    2: "WorldAgent · 基于立项简报生成六阶段结构与世界观",
    3: "CharacterAgent · 基于结构与简报生成人物体系",
    4: "OutlineAgent · 按六阶段生成分集大纲（梗概 100–200 字）",
    5: "ScriptAgent · 基于大纲与人物生成剧本正文",
}


def _verify_summary(adaptation_meta: dict) -> Dict[str, Any]:
    """改编/参考创作复核摘要，供 C 端展示。"""
    reports = adaptation_meta.get("verifyReports") or {}
    brief = adaptation_meta.get("verifyCreation") or {}
    stages: List[Dict[str, Any]] = []
    labels = {
        "world": "世界观",
        "characters": "人设",
        "outline": "大纲",
        "script": "剧本",
    }
    if brief and not brief.get("skipped"):
        stages.append(
            {
                "key": "brief",
                "label": "动笔前禁令",
                "passed": brief.get("passed"),
                "skipped": False,
            }
        )
    for key, label in labels.items():
        row = reports.get(key)
        if not isinstance(row, dict):
            continue
        stages.append(
            {
                "key": key,
                "label": label,
                "passed": row.get("passed"),
                "skipped": bool(row.get("skipped")),
                "issues": (row.get("issues") or [])[:3],
            }
        )
    failed = [s for s in stages if s.get("passed") is False and not s.get("skipped")]
    return {
        "stages": stages,
        "allPassed": len(stages) > 0 and len(failed) == 0,
        "hasReports": bool(stages),
        "failedCount": len(failed),
    }


_VERIFY_STAGE_BY_NODE = {
    2: ("world", "世界观原创复核"),
    3: ("characters", "人设原创复核"),
    4: ("outline", "大纲原创复核"),
    5: ("script", "剧本原创复核"),
}


def _quality_alerts_for_node(
    project: Project,
    node_index: int,
    *,
    adaptation_meta: Optional[dict] = None,
    editor: Optional[dict] = None,
    node_status: str = CreationNode.STATUS_PENDING,
    content_kind: str = "empty",
    payload: Optional[dict] = None,
) -> List[Dict[str, Any]]:
    """节点级质检/复核告警，供 C 端醒目提示。"""
    from ..artifact_service import get_artifact
    from ..episode_gate import summarize_episode_gates
    from .workspace_content import should_emit_quality_alert

    alerts: List[Dict[str, Any]] = []
    meta = adaptation_meta if adaptation_meta is not None else get_artifact(project, "adaptation_meta") or {}

    verify = _VERIFY_STAGE_BY_NODE.get(node_index)
    if verify:
        key, title = verify
        report = (meta.get("verifyReports") or {}).get(key)
        if isinstance(report, dict) and not report.get("skipped") and report.get("passed") is False:
            issues = report.get("issues") or []
            if isinstance(issues, list) and issues and not isinstance(issues[0], str):
                issues = [str(i) for i in issues]
            alert = {
                "level": "error",
                "code": f"verify-{key}",
                "title": title,
                "message": "参考创作原创复核未通过，建议修订后重新生成",
                "issues": [str(i) for i in issues][:5],
            }
            if should_emit_quality_alert(
                node_index, alert["code"], node_status=node_status, payload=payload, content_kind=content_kind
            ):
                alerts.append(alert)

    if payload is None:
        artifact_key = artifact_key_for_node(node_index)
        payload = get_artifact(project, artifact_key) if artifact_key else {}

    if node_index == 2 and isinstance(payload, dict):
        val_log = payload.get("worldValidationLog") or {}
        compliance_warnings = val_log.get("complianceWarnings") or []
        if compliance_warnings and any(
            isinstance(w, dict) and not (w.get("matchedText") or w.get("excerpt"))
            for w in compliance_warnings
        ):
            from ..orchestration.world_engine import _scan_world_compliance

            compliance_warnings = _scan_world_compliance(payload)
        if compliance_warnings:
            details = []
            issues = []
            for warning in compliance_warnings[:4]:
                if not isinstance(warning, dict):
                    continue
                category = str(warning.get("category") or "未知分类")
                matched = str(warning.get("matchedText") or "").strip()
                constraint = str(warning.get("constraint") or "").strip()
                excerpt = str(warning.get("excerpt") or "").strip()
                suggestion = str(warning.get("suggestion") or "").strip()
                issues.append(
                    f"{category}"
                    f"{f'（命中：{matched}）' if matched else ''}"
                    f"：{constraint}"
                )
                details.append(
                    {
                        "category": category,
                        "matched_text": matched,
                        "excerpt": excerpt,
                        "constraint": constraint,
                        "suggestion": suggestion,
                    }
                )
            alert = {
                "level": "warning",
                "code": "world-compliance-p1",
                "title": f"世界观合规提示（P1·共{len(compliance_warnings)}项）",
                "message": "以下设定触发平台合规扫描，请按命中片段逐项确认。生成不中断，但后续大纲/剧本必须遵守对应约束。",
                "issues": issues,
                "details": details,
            }
            if should_emit_quality_alert(
                node_index, alert["code"], node_status=node_status, payload=payload, content_kind=content_kind
            ):
                alerts.append(alert)

    if node_index == 3 and isinstance(payload, dict):
        from .workspace_content import resolve_character_gate_log

        gate = resolve_character_gate_log(payload)
        if gate.get("passed") is False and not gate.get("userAcknowledgedAt"):
            alert = {
                "level": "warning",
                "code": "character-gate",
                "title": "人设完整性待补全",
                "message": "人物档案或关系网信息不完整，建议重新生成或手动编辑",
                "issues": [str(i) for i in (gate.get("issues") or [])][:5],
                "acknowledgable": True,
            }
            if should_emit_quality_alert(
                node_index, alert["code"], node_status=node_status, payload=payload, content_kind=content_kind
            ):
                alerts.append(alert)

    if node_index == 4:
        gaps = (editor or {}).get("summaryGaps") or []
        if gaps:
            min_len = (editor or {}).get("summaryMinLength") or 100
            alert = {
                "level": "warning",
                "code": "outline-summary-gap",
                "title": "分集梗概字数不足",
                "message": f"第 {'、'.join(str(n) for n in gaps)} 集梗概须不少于 {min_len} 字",
                "issues": [f"第{n}集" for n in gaps[:8]],
            }
            if should_emit_quality_alert(
                node_index, alert["code"], node_status=node_status, payload=payload, content_kind=content_kind
            ):
                alerts.append(alert)

        if isinstance(payload, dict):
            plan_log = payload.get("planValidationLog") or {}
            if plan_log.get("passed") is False and not plan_log.get("skipped"):
                alert = {
                    "level": "warning",
                    "code": "plan-validation",
                    "title": "大纲结构校验待修",
                    "message": "sub-plan 校验未完全通过，建议重新生成框架或手动补全 creativePlan",
                    "issues": [str(i) for i in (plan_log.get("issues") or [])][:5],
                }
                if should_emit_quality_alert(
                    node_index, alert["code"], node_status=node_status, payload=payload, content_kind=content_kind
                ):
                    alerts.append(alert)

    if node_index == 5 and isinstance(payload, dict):
        quality = payload.get("creatorQualityGuardLog") or {}
        if quality and not quality.get("skipped") and quality.get("passed") is False:
            alert = {
                "level": "warning",
                "code": "creator-quality-guard",
                "title": "剧本 AI 套话偏多",
                "message": "对白存在模板化表达，建议润色或重新生成",
                "issues": [str(i) for i in (quality.get("issues") or [])][:5],
            }
            if should_emit_quality_alert(
                node_index, alert["code"], node_status=node_status, payload=payload, content_kind=content_kind
            ):
                alerts.append(alert)
        gate_summary = summarize_episode_gates(payload) if payload.get("episodes") else None
        if gate_summary and gate_summary.get("failed"):
            failed_eps = gate_summary.get("failedEpisodes") or []
            issues = []
            for ep in failed_eps[:5]:
                num = ep.get("episodeNumber")
                ep_issues = ep.get("issues") or []
                if num is not None and ep_issues:
                    issues.append(f"第{num}集：{ep_issues[0]}")
                elif num is not None:
                    issues.append(f"第{num}集未通过质检")
            alert = {
                "level": "error" if gate_summary.get("failed", 0) > 2 else "warning",
                "code": "episode-gate",
                "title": f"逐集质检 {gate_summary.get('failed')}/{gate_summary.get('total')} 集未通过",
                "message": "部分集数未达字数/格式/大纲对齐要求",
                "issues": issues,
            }
            if should_emit_quality_alert(
                node_index, alert["code"], node_status=node_status, payload=payload, content_kind=content_kind
            ):
                alerts.append(alert)

    return alerts


def _has_artifact_content(project: Project, node_index: int) -> bool:
    from ..artifact_readiness import node_has_meaningful_content

    return node_has_meaningful_content(project, node_index)


def _reconcile_stale_running_nodes(project: Project) -> bool:
    """项目已结束但节点仍 running 时回退（依赖快速失败等路径曾漏更新节点）。"""
    if project.status == Project.STATUS_RUNNING:
        return False
    stale_nodes = list(project.nodes.filter(status=CreationNode.STATUS_RUNNING))
    if not stale_nodes:
        return False
    err = _workspace_error_message(project)
    for node in stale_nodes:
        if project.status == Project.STATUS_FAILED:
            node.status = CreationNode.STATUS_FAILED
            node.error_message = err or node.error_message or ""
            node.summary_text = "生成失败"
        else:
            node.status = CreationNode.STATUS_PENDING
            node.error_message = ""
            node.summary_text = ""
        node.completed_at = None
        node.save(
            update_fields=[
                "status",
                "error_message",
                "summary_text",
                "completed_at",
            ]
        )
        logger.warning(
            "[Workspace] reconciled stale running node=%s project=%s project_status=%s",
            node.node_index,
            project.id,
            project.status,
        )
    return True


def _reconcile_workspace_node_status(project: Project) -> bool:
    """节点标为已完成但无实质产物时回退，避免 Tab 误显示绿勾。"""
    changed = False
    for node in project.nodes.filter(status=CreationNode.STATUS_COMPLETED):
        if _has_artifact_content(project, node.node_index):
            continue
        node.status = CreationNode.STATUS_PENDING
        node.error_message = ""
        node.summary_text = ""
        node.completed_at = None
        node.save(
            update_fields=[
                "status",
                "error_message",
                "summary_text",
                "completed_at",
            ]
        )
        changed = True
        logger.warning(
            "[Workspace] reconciled phantom completed node=%s project=%s",
            node.node_index,
            project.id,
        )

    if changed and project.status == Project.STATUS_FAILED:
        project.status = Project.STATUS_PENDING
        project.error_message = ""
        project.save(update_fields=["status", "error_message", "updated_at"])
        changed = True
    return changed


def reconcile_workspace_brief_status(project: Project) -> bool:
    """立项整理是用户提交确认内容，已有有效 brief 时状态应为 completed。"""
    try:
        node = project.nodes.get(node_index=1)
    except CreationNode.DoesNotExist:
        return False
    if node.status == CreationNode.STATUS_COMPLETED:
        return False
    if not _has_artifact_content(project, 1):
        return False

    now = timezone.now()
    node.status = CreationNode.STATUS_COMPLETED
    node.summary_text = node.summary_text or "立项参数已确认"
    node.error_message = ""
    if not node.completed_at:
        node.completed_at = now
    node.save(
        update_fields=[
            "status",
            "summary_text",
            "error_message",
            "completed_at",
        ]
    )
    logger.info("[Workspace] reconciled brief node completed project=%s", project.id)
    return True


def _workspace_error_message(project: Project) -> str:
    from apps.common.user_messages import humanize_pipeline_error

    if project.status != Project.STATUS_FAILED:
        return ""
    return humanize_pipeline_error(project.error_message or "")


def _skill_display_name(node_index: int, meta: dict) -> str:
    name = meta.get("name") or WorkflowPipelineService.display_name_for_index(node_index)
    if node_index == 1 or "信息收集" in name:
        return "立项整理"
    return name.replace("节点", "").strip() or name


def recover_stale_workspace_running_state(
    project: Project,
    *,
    stale_minutes_override: int | None = None,
) -> bool:
    """Worker 异常退出后解除遗留的 running 锁（避免无法点击「AI 生成」）。"""
    stale_minutes = (
        stale_minutes_override
        if stale_minutes_override is not None
        else int(getattr(settings, "FUSION_STALE_RUNNING_MINUTES", 25) or 25)
    )
    content_grace = int(getattr(settings, "FUSION_STALE_RUNNING_CONTENT_GRACE_MINUTES", 3) or 3)
    now = timezone.now()
    changed = False

    running_nodes = list(
        project.nodes.filter(
            status=CreationNode.STATUS_RUNNING,
            node_index__lte=WorkflowPipelineService.creation_max_node_index(),
        )
    )
    for node in running_nodes:
        started = node.started_at
        if started:
            age_min = (now - started).total_seconds() / 60.0
        else:
            age_min = float(stale_minutes + 1)

        has_content = _has_artifact_content(project, node.node_index)
        should_recover = age_min >= stale_minutes or (has_content and age_min >= content_grace)
        if not should_recover:
            continue

        if has_content:
            node.status = CreationNode.STATUS_COMPLETED
            node.error_message = ""
            if not node.completed_at:
                node.completed_at = now
            if started and not node.duration_seconds:
                node.duration_seconds = max(0, int((now - started).total_seconds()))
        else:
            node.status = CreationNode.STATUS_FAILED
            node.error_message = "生成任务异常中断，请重试"
        node.save(
            update_fields=[
                "status",
                "error_message",
                "completed_at",
                "duration_seconds",
            ]
        )
        changed = True
        logger.warning(
            "[Workspace] recovered stale running node=%s project=%s has_content=%s",
            node.node_index,
            project.id,
            has_content,
        )

    if project.status == Project.STATUS_RUNNING:
        still_running = project.nodes.filter(status=CreationNode.STATUS_RUNNING).exists()
        if not still_running:
            project.status = Project.STATUS_PENDING
            project.save(update_fields=["status", "updated_at"])
            changed = True
            logger.warning("[Workspace] recovered stale project running lock project=%s", project.id)

    return changed


def _workspace_running_blocker(project: Project) -> Optional[Dict[str, Any]]:
    """当前阻止新任务入队的执行中状态（供前端提示）。"""
    running_node = (
        project.nodes.filter(status=CreationNode.STATUS_RUNNING)
        .order_by("node_index")
        .first()
    )
    if running_node:
        return {
            "kind": "node",
            "node_index": running_node.node_index,
            "node_name": running_node.node_name,
            "summary": running_node.summary_text or "",
        }
    if project.status == Project.STATUS_RUNNING:
        return {"kind": "project", "message": "项目正在处理中"}
    return None


def build_workspace_payload(project: Project) -> Dict[str, Any]:
    """C 端 Agent 工作台快照。"""
    from apps.agent.catalog import portal_agent_catalog
    from apps.agent.runtime import agent_for_workspace_index, get_agent
    from ..monitoring.execution_run_service import AgentExecutionRunService
    from ..display.portal_display import portal_execution_run
    from ..models import AgentExecutionRun
    from .workspace_content import (
        CONTENT_AGENT_GENERATED,
        count_agent_ready_skills,
        ensure_brief_seed_enriched,
        get_node_payload,
        skill_content_kind,
    )
    from .workspace_markdown import build_workspace_markdown

    ensure_brief_seed_enriched(project)
    if recover_stale_workspace_running_state(project):
        project.refresh_from_db()
    if _reconcile_stale_running_nodes(project):
        project.refresh_from_db()
    if _reconcile_workspace_node_status(project):
        project.refresh_from_db()
    if reconcile_workspace_brief_status(project):
        project.refresh_from_db()

    meta_by_index = WorkflowPipelineService.node_meta_by_index()
    node_rows = {
        n.node_index: n for n in project.nodes.all().order_by("node_index")
    }
    running_skill_index: Optional[int] = None
    skills: List[Dict[str, Any]] = []

    from ..artifact_service import get_artifact

    adaptation_meta = get_artifact(project, "adaptation_meta") or {}

    latest_run_by_node: Dict[int, AgentExecutionRun] = {}
    for run in (
        AgentExecutionRun.objects.filter(project=project, node_index__isnull=False)
        .prefetch_related("sub_skill_logs")
        .order_by("-started_at")
    ):
        if run.node_index not in latest_run_by_node:
            latest_run_by_node[run.node_index] = run

    for meta in WorkflowPipelineService.portal_main_chain():
        idx = meta["index"]
        node = node_rows.get(idx)
        status = node.status if node else CreationNode.STATUS_PENDING
        if status == CreationNode.STATUS_RUNNING:
            running_skill_index = idx

        preview = None
        has_content = _has_artifact_content(project, idx)
        node_payload = get_node_payload(project, idx)
        content_kind = skill_content_kind(
            idx,
            node_payload,
            has_content=has_content,
            node_status=status,
        )
        if has_content or status == CreationNode.STATUS_COMPLETED:
            try:
                preview = build_node_preview(project, idx)
            except Exception as exc:  # noqa: BLE001
                logger.warning("[Workspace] preview failed node=%s: %s", idx, exc)

        editor = None
        try:
            if idx == 4:
                from ..outline_skeleton import ensure_outline_skeleton

                ensure_outline_skeleton(project)
            editor = build_editor_view(project, idx)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[Workspace] editor failed node=%s: %s", idx, exc)

        agent_id = agent_for_workspace_index(idx) or ""
        agent_def = get_agent(agent_id) if agent_id else {}
        latest_run = latest_run_by_node.get(idx)
        serialized_run = (
            AgentExecutionRunService.serialize_run(latest_run) if latest_run else None
        )
        module = alias_agent_id({
            "index": idx,
            "agent_id": agent_id,
            "agent_name": agent_def.get("name") or "",
            "agent_name_zh": agent_def.get("name_zh") or _skill_display_name(idx, meta),
            "name": _skill_display_name(idx, meta),
            "fusion_node_id": meta.get("fusion_node_id") or "",
            "artifact_key": artifact_key_for_node(idx) or meta.get("output_key") or "",
            "output_key": meta.get("output_key") or "",
            "output_artifacts": agent_def.get("outputs") or [],
            "sub_skill_count": len(agent_def.get("sub_skills") or []),
            "execution_run": portal_execution_run(serialized_run),
            "status": status,
            "status_text": node.get_status_display() if node else "待生成",
            "error_message": (
                humanize_pipeline_error(node.error_message)
                if node and node.status == CreationNode.STATUS_FAILED and node.error_message
                else ""
            ),
            "summary": (node.summary_text if node else "") or "",
            "coin_cost": meta.get("coin_cost")
            or BillingService.get_node_coin_cost(idx),
            "has_content": has_content,
            "content_kind": content_kind,
            "agent_generated": content_kind == CONTENT_AGENT_GENERATED,
            "can_generate": idx >= 2,
            "can_edit": idx >= 1,
            "hint": _AGENT_HINTS.get(idx, ""),
            "description": agent_def.get("description") or meta.get("description") or "",
            "orchestration_stage_type": meta.get("orchestration_stage_type"),
            "orchestration_stage_label": meta.get("orchestration_stage_label"),
            "orchestration_parallel_peers": meta.get("orchestration_parallel_peers") or [],
            "orchestration_has_branch": bool(meta.get("orchestration_has_branch")),
            "preview_html": (preview or {}).get("preview_html") or "",
            "readable_markdown": build_workspace_markdown(project, idx) if has_content else "",
            "editor": editor,
            "quality_alerts": _quality_alerts_for_node(
                project,
                idx,
                adaptation_meta=adaptation_meta,
                editor=editor,
                node_status=status,
                content_kind=content_kind,
                payload=node_payload,
            ),
        })
        skills.append(module)

    completed_count = count_agent_ready_skills(skills)
    confirmed_count = sum(1 for s in skills if s.get("has_content"))
    total = max(1, len(skills))

    adapt_run = AgentExecutionRunService.latest_run_for_agent(project, agent_id="adapt", node_index=0)
    scripts_ready = _has_artifact_content(project, 5)
    post_script_data = _build_post_script_summary(project)

    # 可选节点状态汇总（4.2/4.3：adapt + insight + marketing 统一展示入口）
    from ..post_script_summary import _optional_node_status
    adapt_has_meta = bool(adaptation_meta)
    adapt_status = _optional_node_status(
        adapt_run if isinstance(adapt_run, dict) else None,
        adapt_has_meta,
    )
    optional_nodes = {
        "adapt": {
            "agentId": "adapt",
            "label": "创意适配",
            "status": adapt_status,
            "executionRun": portal_execution_run(adapt_run) if isinstance(adapt_run, dict) else None,
            "hasContent": adapt_has_meta,
        },
        "insight": {
            "agentId": "insight",
            "label": "拉片分析",
            "status": post_script_data.get("insightStatus", "not_run"),
            "canGenerate": post_script_data.get("insightCanGenerate", False),
            "executionRun": (post_script_data.get("insight") or {}).get("executionRun"),
            "hasContent": post_script_data.get("insight") is not None,
        },
        "marketing": {
            "agentId": "marketing",
            "label": "营销素材",
            "status": post_script_data.get("marketingStatus", "not_run"),
            "canGenerate": post_script_data.get("marketingCanGenerate", False),
            "executionRun": (post_script_data.get("marketing") or {}).get("executionRun"),
            "hasContent": post_script_data.get("marketing") is not None,
        },
    }

    from apps.workflow.services.flow_graph_service import FlowGraphPlanService

    return {
        "project_id": str(project.id),
        "title": workspace_display_title(project),
        "theme": project.theme,
        "episode_count": project.episode_count,
        "format_variant": project.format_variant,
        "status": project.status,
        "status_text": project.get_status_display(),
        "pipeline_mode": project.pipeline_mode,
        "progress_percent": project.progress_percent
        or int(completed_count / total * 100),
        "error_message": _workspace_error_message(project),
        "failed_node_index": (
            project.current_node_index
            if project.status == Project.STATUS_FAILED and project.current_node_index
            else None
        ),
        "running_skill_index": running_skill_index,
        "running_agent_index": running_skill_index,
        "running_blocker": _workspace_running_blocker(project),
        "skills": skills,
        "agents": skills,
        "completed_skill_count": completed_count,
        "completed_agent_count": completed_count,
        "confirmed_skill_count": confirmed_count,
        "total_skills": len(skills),
        "total_agents": len(skills),
        "agent_catalog_version": portal_agent_catalog().get("version"),
        "creation_entry": project.creation_entry or "",
        "adaptation": {
            "meta": adaptation_meta,
            "execution_run": portal_execution_run(adapt_run) if isinstance(adapt_run, dict) else None,
            "verify_summary": _verify_summary(adaptation_meta),
        } if adaptation_meta else None,
        "optional_nodes": optional_nodes,
        "can_download": _has_artifact_content(project, 5),
        "can_export_zip": _project_can_export_zip(project),
        "can_share": _project_can_share(project),
        "post_script": post_script_data,
        "execution_plan": FlowGraphPlanService.execution_plan_payload(),
    }


def _project_can_share(project: Project) -> bool:
    return project.status == Project.STATUS_COMPLETED


def _build_post_script_summary(project: Project) -> Dict[str, Any]:
    from ..post_script_summary import build_post_script_summary

    return build_post_script_summary(project)


def _project_can_export_zip(project: Project) -> bool:
    from ..script_export import project_has_exportable_content

    return project_has_exportable_content(project)


def finalize_workspace_brief(project: Project) -> None:
    """提交后：立项整理视为已完成，并预搭建分集大纲骨架。"""
    from ..outline_skeleton import ensure_outline_skeleton

    ensure_outline_skeleton(project)
    now = timezone.now()
    CreationNode.objects.filter(project=project, node_index=1).update(
        status=CreationNode.STATUS_COMPLETED,
        summary_text="立项参数已确认",
        completed_at=now,
        started_at=now,
    )
    total = max(1, project.total_nodes or len(WorkflowPipelineService.portal_main_chain()))
    project.current_node_index = 1
    project.progress_percent = max(project.progress_percent, int(1 / total * 100))
    project.pipeline_mode = Project.MODE_WORKSPACE
    project.status = Project.STATUS_PENDING
    project.fusion_status = project.fusion_status or Project.FUSION_DRAFT
    project.rendered_progress_html = _render_progress_html(project)
    project.save(
        update_fields=[
            "current_node_index",
            "progress_percent",
            "pipeline_mode",
            "status",
            "fusion_status",
            "rendered_progress_html",
            "updated_at",
        ]
    )


def save_skill_content(project: Project, node_index: int, data: dict) -> Dict[str, Any]:
    if node_index < 1 or node_index > WorkflowPipelineService.creation_max_node_index():
        raise PermissionDenied("无效技能")
    try:
        apply_editor_save(project, node_index, data or {})
    except ValueError as exc:
        raise PermissionDenied(str(exc)) from exc
    return {"project_id": str(project.id), "node_index": node_index, "status": "saved"}


def acknowledge_quality_alert(project: Project, node_index: int, alert_code: str) -> Dict[str, Any]:
    """人工确认质检告警（当前仅支持 character-gate）。"""
    if alert_code != "character-gate":
        raise PermissionDenied("该告警不支持人工确认")
    if node_index != 3:
        raise PermissionDenied("无效节点")

    from ..artifact_service import get_artifact, save_artifact
    from ..step_mode import artifact_key_for_node
    from .workspace_content import resolve_character_gate_log

    key = artifact_key_for_node(node_index)
    if not key:
        raise PermissionDenied("无效节点")

    payload = dict(get_artifact(project, key) or {})
    gate = resolve_character_gate_log(payload)
    if gate.get("passed"):
        raise PermissionDenied("质检已通过，无需确认")
    if gate.get("userAcknowledgedAt"):
        return {
            "project_id": str(project.id),
            "node_index": node_index,
            "alert_code": alert_code,
            "status": "already_acknowledged",
        }

    gate["userAcknowledgedAt"] = timezone.now().isoformat()
    payload["characterGateLog"] = gate
    save_artifact(project, key, payload)
    return {
        "project_id": str(project.id),
        "node_index": node_index,
        "alert_code": alert_code,
        "status": "acknowledged",
    }


def generate_skill(
    project: Project,
    node_index: int,
    *,
    script_from: Optional[int] = None,
    script_to: Optional[int] = None,
    batch_size: Optional[int] = None,
    regenerate: bool = False,
    outline_mode: Optional[str] = None,
    outline_stage_key: Optional[str] = None,
) -> Dict[str, Any]:
    """触发单个技能 AI 生成（异步 worker）。"""
    max_idx = WorkflowPipelineService.creation_max_node_index()
    if node_index < 2 or node_index > max_idx:
        raise PermissionDenied("该技能不支持单独生成")

    if not WorkflowPipelineService.is_node_enabled(node_index):
        raise PermissionDenied("该技能已由运营关闭")

    recover_stale_workspace_running_state(project)
    project.refresh_from_db()

    from .workspace_content import ensure_brief_seed_enriched

    ensure_brief_seed_enriched(project)

    if project.status == Project.STATUS_RUNNING:
        raise PermissionDenied("有技能正在执行，请稍候")

    running = project.nodes.filter(status=CreationNode.STATUS_RUNNING).exists()
    if running:
        blocker = _workspace_running_blocker(project)
        if blocker and blocker.get("kind") == "node":
            raise PermissionDenied(
                f"「{blocker.get('node_name') or '其他技能'}」正在执行，请稍候"
            )
        raise PermissionDenied("有技能正在执行，请稍候")

    if not _has_artifact_content(project, 1):
        raise PermissionDenied("请先完成立项整理（创建项目时已写入）")

    if node_index >= 3 and not _has_artifact_content(project, 2):
        raise PermissionDenied("请先生成结构与世界观")
    if node_index >= 4 and not _has_artifact_content(project, 3):
        raise PermissionDenied("请先生成角色设计")

    if node_index == 5:
        for dep_idx, label in ((2, "结构与世界观"), (3, "人设开发"), (4, "分集大纲")):
            if not _has_artifact_content(project, dep_idx):
                raise PermissionDenied(f"请先生成{label}")

    # ── 收敛停机硬卡点（来自 StoryForge 四态控制模型） ────────────────────
    # 若任何上游 review/fix 节点已触发停机（convergence_state=blocked），
    # 禁止启动下游节点，防止在未收敛状态下继续生成。
    _enforce_convergence_gate(project, node_index)

    from apps.billing.services import BillingService

    BillingService.ensure_node_chargeable(project.user, node_index)

    batch_meta: Dict[str, Any] = {}
    if node_index == 4:
        from .workspace_editor import (
            compute_outline_batch_range,
            compute_outline_fill_all_range,
            _outline_framework_ready,
        )
        from ..artifact_service import get_artifact

        outline_payload = get_artifact(project, "series_outline") or {}
        mode = outline_mode or "auto"

        if regenerate:
            clear_artifacts_from_node(project, 4)
            reset_nodes_from_index(project, 4)
            outline_payload = {}

        if mode == "framework":
            batch_meta = {"outline_mode": "framework"}
        elif mode == "stage_framework":
            stage_key = str(outline_stage_key or "").strip()
            if not stage_key:
                raise PermissionDenied("请指定大纲阶段")
            batch_meta = {"outline_mode": "stage_framework", "stage_key": stage_key}
        elif mode == "fill_all":
            if not _outline_framework_ready(outline_payload):
                raise PermissionDenied("请先生成集纲框架")
            try:
                o_from, o_to, _ = compute_outline_fill_all_range(project)
            except ValueError as exc:
                raise PermissionDenied(str(exc)) from exc
            batch_meta = {
                "outline_mode": "episodes",
                "from_episode": o_from,
                "to_episode": o_to,
            }
        elif mode == "block":
            if not _outline_framework_ready(outline_payload):
                raise PermissionDenied("请先生成集纲框架")
            try:
                o_from, o_to, _ = compute_outline_batch_range(
                    project,
                    block_from=script_from,
                    block_to=script_to,
                    batch_size=batch_size or 1,
                )
            except ValueError as exc:
                raise PermissionDenied(str(exc)) from exc
            batch_meta = {
                "outline_mode": "episodes",
                "from_episode": o_from,
                "to_episode": o_to,
            }
        elif mode == "next":
            if not _outline_framework_ready(outline_payload):
                raise PermissionDenied("请先填写或 AI 生成起承转合粗纲")
            try:
                o_from, o_to, _ = compute_outline_batch_range(project, batch_size=1)
            except ValueError as exc:
                raise PermissionDenied(str(exc)) from exc
            batch_meta = {
                "outline_mode": "episodes",
                "from_episode": o_from,
                "to_episode": o_to,
            }
        else:
            batch_meta = {"outline_mode": "auto"}
            if not outline_payload or regenerate:
                reset_nodes_from_index(project, 4)
    elif node_index == 5:
        if regenerate:
            clear_artifacts_from_node(project, 5)
        try:
            script_from, script_to, _ = compute_script_batch_range(
                project,
                from_episode=script_from,
                to_episode=script_to,
                batch_size=batch_size,
            )
        except ValueError as exc:
            raise PermissionDenied(str(exc)) from exc
        batch_meta = {
            "from_episode": script_from,
            "to_episode": script_to,
        }
        if not regenerate:
            pass  # 增量：不清空已有剧本
        else:
            reset_nodes_from_index(project, 5)
    else:
        # 产物清空推迟到 worker 真正执行时，避免入队失败导致内容丢失
        reset_nodes_from_index(project, node_index)

    project.status = Project.STATUS_PENDING
    project.error_message = ""
    project.current_node_index = node_index
    project.save(
        update_fields=[
            "status",
            "error_message",
            "current_node_index",
            "updated_at",
        ]
    )

    CreationNode.objects.filter(project=project, node_index=node_index).update(
        status=CreationNode.STATUS_PENDING,
        summary_text="排队中…",
        error_message="",
        completed_at=None,
        started_at=None,
    )

    from dj_queue.api import enqueue_on_commit

    from ..tasks import run_creation_step

    if node_index in (4, 5) and batch_meta:
        enqueue_on_commit(
            run_creation_step,
            str(project.id),
            node_index,
            batch_meta.get("from_episode"),
            batch_meta.get("to_episode"),
            batch_meta.get("outline_mode"),
            batch_meta.get("stage_key"),
        )
    else:
        enqueue_on_commit(run_creation_step, str(project.id), node_index)
    log_skill_enqueue(
        project_id=project.id,
        node_index=node_index,
        regenerate=regenerate,
        batch=batch_meta or None,
    )
    return {
        "project_id": str(project.id),
        "node_index": node_index,
        "status": "queued",
        **batch_meta,
    }


# ============================================================
# 收敛停机硬卡点 — _enforce_convergence_gate
# 上游节点已停机时，拒绝启动下游节点（移植自 StoryForge 硬卡点模式）
# ============================================================

# node_index → 需要检查收敛状态的直接前置节点
# 只检查有 fix 回路的节点（review/scoring 类），不检查初始创作节点
_CONVERGENCE_GATE_DEPS: dict[int, list[int]] = {
    5: [3, 4],  # 剧本正文：依赖 node3（人设）、node4（大纲）收敛通过
    6: [5],     # 审核修订：依赖 node5（剧本）收敛通过
    7: [5, 6],  # 剧本评分：依赖 node5/6 收敛通过
}


def _enforce_convergence_gate(project: "Project", node_index: int) -> None:  # type: ignore[name-defined]
    """
    收敛停机硬卡点。

    若任何直接前置节点的 convergence_state = "blocked"，
    抛出 PermissionDenied，阻止下游节点启动。

    调用者（generate_skill）在所有 artifact 依赖检查之后调用此函数。
    """
    dep_indices = _CONVERGENCE_GATE_DEPS.get(node_index)
    if not dep_indices:
        return

    blocked = (
        project.nodes
        .filter(node_index__in=dep_indices, convergence_state=CreationNode.CONVERGENCE_BLOCKED)
        .values_list("node_index", "node_name", "fix_blocked_reason")
    )
    for idx, name, reason in blocked:
        label = name or f"节点{idx}"
        detail = reason or "收敛算法触发停机"
        raise PermissionDenied(
            f"上游「{label}」已停机：{detail}。"
            "如需继续，请在工作台重置该节点的收敛状态，或联系管理员。"
        )
