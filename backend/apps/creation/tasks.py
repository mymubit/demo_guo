"""
鍒涗綔鍚庡彴浠诲姟锛圖jango 6 @task + dj_queue / Postgres锛?

鏍稿績锛歳un_creation_pipeline(project_id)
  - 涓茶鎵ц铻嶅悎缂栨帓鍣ㄨ妭鐐?1鈥? + fusion 鍚庡鐞?
  - 鏇存柊鑺傜偣鐘舵€併€佽繘搴?HTML銆丼criptWork 涓嬭浇鏂囦欢

鍚姩 worker锛?
  python manage.py dj_queue --mode async   # Windows 鎺ㄨ崘
  python manage.py dj_queue                # Linux 鍙敤 fork
"""
from __future__ import annotations

import logging
import os
import time
from django.db import transaction
from django.tasks import task
from django.utils import timezone

from apps.common.user_messages import humanize_pipeline_error, humanize_user_message
from .pipeline_debug_log import log_skill_task_begin, log_skill_task_done
from .models import CreationNode, Project
from .services import PIPELINE_NODES, _render_progress_html, _render_result_html

logger = logging.getLogger(__name__)


def _refund_creation_submit_if_needed(project: Project, reason: str) -> None:
    """Refund creation submit charge when main creation fails."""
    from apps.billing.models import CoinLedger
    from apps.billing.services import BillingService

    cost = BillingService.get_price("creation.submit")
    if cost <= 0:
        return
    BillingService.credit(
        project.user,
        cost,
        action_key="creation.submit.refund",
        reference_id=str(project.id),
        remark=reason[:200],
        entry_type=CoinLedger.TYPE_REFUND,
    )


def _mark_skill_node_failed_state(project: Project, node_index: int, error_msg: str) -> None:
    """Mark project and node as failed."""
    project.status = Project.STATUS_FAILED
    project.error_message = error_msg[:500]
    project.rendered_progress_html = _render_progress_html(project)
    project.save(
        update_fields=[
            "status",
            "error_message",
            "rendered_progress_html",
            "updated_at",
        ]
    )
    CreationNode.objects.filter(project=project, node_index=node_index).update(
        status=CreationNode.STATUS_FAILED,
        error_message=error_msg[:500],
        summary_text="鐢熸垚澶辫触",
        completed_at=None,
    )


def _workspace_node_to_skill_id(node_index: int) -> str:
    """Map workspace node index to creation skill id."""
    from .workspace_skill_invoke import workspace_node_to_skill_id

    return workspace_node_to_skill_id(node_index)


def _invoke_workspace_skill(
    project: Project,
    node_index: int,
    *,
    script_from: int | None = None,
    script_to: int | None = None,
    outline_mode: str | None = None,
    outline_stage_key: str | None = None,
) -> SkillAgentResult:
    """Invoke one workspace skill."""
    from .orchestration.workspace_agent import invoke_workspace_agent

    return invoke_workspace_agent(
        project,
        node_index,
        script_from=script_from,
        script_to=script_to,
        outline_mode=outline_mode,
        outline_stage_key=outline_stage_key,
    )


def _scripts_fully_generated_for_project(project: Project) -> bool:
    """Return whether all target scripts have been generated."""
    from .artifact_service import get_artifact as _get_artifact

    scripts = _get_artifact(project, "episode_scripts") or {}
    eps = scripts.get("episodes") or []
    if not eps:
        return False
    nums = {
        int(e.get("episodeNumber") or e.get("episode") or 0)
        for e in eps
        if isinstance(e, dict)
    }
    nums.discard(0)
    target = int(project.episode_count or 0)
    if target <= 0:
        return len(nums) > 0
    return len(nums) >= target


from .workspace_skill_invoke import SkillAgentResult


def _finalize_skill_node_failure(
    project_id: str,
    node_index: int,
    error_msg: str,
    *,
    log_status: str = "exception",
    log_detail: dict | None = None,
) -> dict:
    """Finalize a skill-node failure after transaction cleanup."""
    from django.db import connection

    connection.close()
    with transaction.atomic():
        try:
            project = Project.objects.select_for_update().get(id=project_id)
        except Project.DoesNotExist:
            return {"status": "error", "message": "project not found"}

        _mark_skill_node_failed_state(project, node_index, error_msg)

    log_skill_task_done(
        project_id=project_id,
        node_index=node_index,
        status=log_status,
        detail=log_detail or {"error": error_msg},
    )
    return {"status": "failed", "node_index": node_index, "error": error_msg}


def _record_task_result_if_failed(
    *,
    task_name: str,
    result: dict,
    project_id: str,
    node_index: int | None = None,
) -> dict:
    if not isinstance(result, dict):
        return result
    status = str(result.get("status") or "")
    if status not in {"failed", "error"}:
        return result
    try:
        from apps.monitoring.services.task_error import record_background_task_failure

        record_background_task_failure(
            task_name=task_name,
            project_id=project_id,
            node_index=node_index if node_index is not None else result.get("node_index"),
            status=status,
            detail={
                "error": result.get("error") or result.get("message") or "鍚庡彴浠诲姟鎵ц澶辫触",
                "result": result,
            },
            exception_type="BackgroundTaskResultFailed",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[TaskMonitor] write skipped task=%s project=%s: %s", task_name, project_id, exc)
    return result


def _execute_pipeline_for_project(project: Project) -> dict:
    """Execute the 5-step main workflow through WorkflowEngine."""
    from apps.workflow.execution_models import WorkflowInstance
    from apps.workflow.workflow_engine import WorkflowEngine

    # 鏌ユ壘璇?Project 瀵瑰簲鐨?WorkflowInstance锛坰ubmission 鏃跺凡鍒涘缓锛?
    instance = (
        WorkflowInstance.objects
        .filter(project=project)
        .order_by("-created_at")
        .first()
    )

    if instance is None:
        raise RuntimeError(
            f"Project {project.id} has no WorkflowInstance; cannot run workflow",
        )

    if instance.status not in (
        WorkflowInstance.STATUS_PENDING,
        WorkflowInstance.STATUS_RUNNING,
        WorkflowInstance.STATUS_PAUSED,
    ):
        logger.info(
            "[Creation] Project %s instance already terminal (%s); skip",
            project.id,
            instance.status,
        )
        return _build_pipeline_result_from_instance(instance)

    engine = WorkflowEngine(instance)
    engine.run()

    # 鏂板紩鎿庡畬鎴愬悗锛屽悓姝ヨ妭鐐规墽琛岀粨鏋滃埌 Project / CreationNode
    _sync_workflow_instance_to_project(project, instance)

    return _build_pipeline_result_from_instance(instance)


def _sync_workflow_instance_to_project(project: Project, instance) -> None:
    """Sync WorkflowInstance node executions to CreationNode rows."""
    from apps.workflow.execution_models import NodeExecution
    from apps.workflow.models import FusionPipelineNode
    from django.utils import timezone as tz

    nodes = NodeExecution.objects.filter(instance=instance).order_by("started_at")
    node_map = {str(ne.node_id): ne for ne in nodes}

    # 鍚屾鑺傜偣鐘舵€佸埌 CreationNode
    for db_node in FusionPipelineNode.objects.filter(pack=instance.pack).order_by("chain_order"):
        ne: NodeExecution | None = node_map.get(db_node.fusion_node_id)
        if ne is None:
            continue

        try:
            cn = project.nodes.filter(
                fusion_node_id=db_node.fusion_node_id
            ).first()
            if cn is None:
                continue

            if ne.status == NodeExecution.STATUS_SUCCEEDED:
                cn.status = "completed"
                cn.completed_at = ne.finished_at or tz.now()
                cn.summary_text = db_node.display_name
            elif ne.status == NodeExecution.STATUS_FAILED:
                cn.status = "failed"
                cn.error_message = (ne.error_info or "")[:500]
            elif ne.status == NodeExecution.STATUS_RUNNING:
                cn.status = "running"
                cn.started_at = ne.started_at or tz.now()
            cn.save(update_fields=["status", "completed_at", "started_at",
                                   "summary_text", "error_message", "updated_at"])
        except Exception as exc:
            logger.warning("[Sync] 鍚屾鑺傜偣澶辫触 node=%s: %s", db_node.fusion_node_id, exc)

    # 鍚屾 Project 鏁翠綋杩涘害
    completed = nodes.filter(status=NodeExecution.STATUS_SUCCEEDED).count()
    total = nodes.count()
    project.progress_percent = min(100, int(completed / max(1, total) * 100))
    project.current_node_index = total
    project.updated_at = tz.now()
    project.save(update_fields=["progress_percent", "current_node_index", "updated_at"])


def _build_pipeline_result_from_instance(instance) -> dict:
    """Build pipeline result from WorkflowInstance context."""
    ctx = instance.context or {}
    nodes = ctx.get("nodes", {}) if isinstance(ctx, dict) else {}

    def node_output(*node_ids: str) -> dict:
        for node_id in node_ids:
            payload = nodes.get(node_id) or {}
            if isinstance(payload, dict):
                content = payload.get("content")
                if isinstance(content, dict):
                    return content
                return payload
        return {}

    return {
        "project_brief": node_output("node_brief", "node-1-input"),
        "structure": node_output("node_structure", "node-2-structure"),
        "characters": node_output("node_character", "node-3-character"),
        "outlines": node_output("node_outline", "node-4-outline"),
        "scripts": node_output("node_script", "node-5-script"),
        "status": "completed" if instance.status == instance.STATUS_DONE else "error",
        "errors": [instance.failure_reason] if instance.failure_reason else [],
    }


def _update_nodes_from_result(project: Project, result: dict) -> None:
    brief = result.get("project_brief") or {}
    structure = result.get("structure") or {}
    characters = result.get("characters") or {}
    outlines = result.get("outlines") or {}
    scripts = result.get("scripts") or {}
    review = result.get("review") or {}

    node_summaries = {
        1: brief.get("project_name") or f"{brief.get('theme', project.theme)} / {project.episode_count} eps",
        2: f"{structure.get('total_episodes', project.episode_count)} eps structure",
        3: f"{characters.get('character_count', 0)} characters",
        4: f"{outlines.get('total_episodes', project.episode_count)} episode outlines",
        5: f"{scripts.get('total_words', 0)} words / {scripts.get('total_scenes', 0)} scenes",
    }

    now = timezone.now()
    for node_index in range(1, len(PIPELINE_NODES) + 1):
        try:
            node = CreationNode.objects.get(project=project, node_index=node_index)
        except CreationNode.DoesNotExist:
            continue
        node.status = CreationNode.STATUS_COMPLETED
        node.completed_at = now
        node.summary_text = node_summaries.get(node_index, "鑺傜偣瀹屾垚")
        node.save(update_fields=["status", "completed_at", "summary_text"])


def _update_project_after_pipeline(
    project: Project, result: dict, started_at, *, fusion_out: dict | None = None
) -> None:
    export = result.get("export") or {}

    fusion_blocked = (
        fusion_out is not None
        and (
            fusion_out.get("fusion_status") == Project.FUSION_BLOCKED
            or fusion_out.get("ok") is False
        )
    )

    if fusion_out and fusion_out.get("fusion_status") == Project.FUSION_READY:
        project.status = Project.STATUS_COMPLETED
        project.fusion_status = Project.FUSION_READY
    elif fusion_blocked:
        project.status = Project.STATUS_FAILED
        project.fusion_status = Project.FUSION_BLOCKED
        if not project.error_message:
            project.error_message = fusion_out.get("error") or "fusion checks blocked release"
    else:
        project.status = Project.STATUS_COMPLETED

    project.current_node_index = len(PIPELINE_NODES)
    project.progress_percent = 100
    project.completed_at = timezone.now()
    project.total_duration_minutes = int(
        (project.completed_at - started_at).total_seconds() // 60
    )

    project.rendered_result_html = (
        export.get("rendered_html")
        or export.get("rendered_progress_html")
        or _render_result_html(project)
    )
    project.rendered_progress_html = (
        export.get("rendered_progress_html") or _render_progress_html(project)
    )

    project.save(
        update_fields=[
            "status",
            "fusion_status",
            "overall_score",
            "grade",
            "ready_at",
            "error_message",
            "current_node_index",
            "progress_percent",
            "completed_at",
            "total_duration_minutes",
            "rendered_result_html",
            "rendered_progress_html",
            "updated_at",
        ]
    )


def _run_creation_pipeline_core(project_id: str) -> dict:
    with transaction.atomic():
        try:
            project = Project.objects.select_for_update().get(id=project_id)
        except Project.DoesNotExist:
            logger.error("[Creation] project 涓嶅瓨鍦? %s", project_id)
            return {"status": "error", "project_id": project_id, "message": "project not found"}

        if project.status not in {Project.STATUS_PENDING, Project.STATUS_FAILED}:
            logger.info("[Creation] project 宸插湪杩愯鎴栧凡瀹屾垚: %s", project_id)
            return {"status": "skip", "project_id": project_id}

        project.status = Project.STATUS_RUNNING
        project.current_node_index = 0
        project.progress_percent = 0
        project.error_message = ""
        project.save(
            update_fields=[
                "status",
                "current_node_index",
                "progress_percent",
                "error_message",
                "updated_at",
            ]
        )

    started_at = timezone.now()

    from apps.workflow.services.pipeline_service import WorkflowPipelineService

    disabled = [
        n["index"]
        for n in WorkflowPipelineService.pipeline_nodes_for_creation()
        if not WorkflowPipelineService.is_node_enabled(n["index"])
    ]
    if disabled:
        msg = f"鑺傜偣 {disabled} 宸插叧闂紝鏃犳硶鎵ц鍒涗綔"
        project.status = Project.STATUS_FAILED
        project.error_message = msg
        project.save(update_fields=["status", "error_message", "updated_at"])
        _refund_creation_submit_if_needed(project, msg)
        return {"status": "failed", "project_id": str(project.id), "error": msg}

    try:
        result = _execute_pipeline_for_project(project)

        if result.get("status") == "error":
            error_msg = humanize_pipeline_error(
                "; ".join(result.get("errors") or ["pipeline error"])
            )
            logger.error("[Creation] pipeline 杩斿洖閿欒 project=%s: %s", project.id, error_msg)
            project.status = Project.STATUS_FAILED
            project.error_message = error_msg[:500]
            project.rendered_progress_html = _render_progress_html(project)
            project.save(
                update_fields=[
                    "status",
                    "error_message",
                    "rendered_progress_html",
                    "updated_at",
                ]
            )
            _refund_creation_submit_if_needed(project, error_msg)
            return {"status": "failed", "project_id": str(project.id), "error": error_msg}

        if not result.get("artifacts"):
            _update_nodes_from_result(project, result)

        _update_project_after_pipeline(project, result, started_at, fusion_out=None)
        from .script_delivery import persist_script_works

        persist_script_works(project, result)

        final = "completed"

        logger.info(
            "[Creation] project=%s 涓婚摼鍒涗綔瀹屾垚, 鑰楁椂 %d 鍒嗛挓",
            project.id,
            project.total_duration_minutes,
        )
        return {
            "status": final,
            "project_id": str(project.id),
            "fusion_status": project.fusion_status,
            "overall_score": project.overall_score,
        }

    except Exception as exc:  # noqa: BLE001
        error_msg = humanize_user_message(str(exc), default="鍒涗綔澶辫触锛岃绋嶅悗閲嶈瘯")[:500]
        logger.exception("[Creation] project=%s 鍒涗綔澶辫触: %s", project.id, exc)
        project.status = Project.STATUS_FAILED
        project.error_message = error_msg
        project.rendered_progress_html = _render_progress_html(project)
        project.save(
            update_fields=[
                "status",
                "error_message",
                "rendered_progress_html",
                "updated_at",
            ]
        )
        try:
            cur_node = CreationNode.objects.filter(
                project=project, node_index=project.current_node_index
            ).first()
            if cur_node:
                cur_node.status = CreationNode.STATUS_FAILED
                cur_node.error_message = error_msg
                cur_node.save(update_fields=["status", "error_message"])
        except Exception:  # noqa: BLE001
            pass

        _refund_creation_submit_if_needed(project, error_msg)
        return {"status": "failed", "project_id": str(project.id), "error": error_msg}


@task(queue_name="creation")
def run_creation_pipeline(project_id: str) -> dict:
    """Run the 5-step creation pipeline asynchronously."""
    result = _run_creation_pipeline_core(project_id)
    return _record_task_result_if_failed(
        task_name="creation.pipeline",
        result=result,
        project_id=project_id,
    )


def run_creation_pipeline_sync(project_id: str) -> dict:
    """Run creation pipeline synchronously."""
    logger.info("[Creation] 鍚屾鎵ц pipeline project=%s", project_id)
    result = _run_creation_pipeline_core(project_id)
    return _record_task_result_if_failed(
        task_name="creation.pipeline_sync",
        result=result,
        project_id=project_id,
    )


def _finalize_step_project(project: Project, pipeline_result: dict, fusion_out: dict | None) -> None:
    """Finalize step-mode project and persist ScriptWork."""
    started_at = project.created_at
    _update_project_after_pipeline(project, pipeline_result, started_at, fusion_out=fusion_out)
    from .script_delivery import persist_script_works

    persist_script_works(project, pipeline_result)


def _run_creation_step_core(project_id: str, node_index: int) -> dict:
    with transaction.atomic():
        try:
            project = Project.objects.select_for_update().get(id=project_id)
        except Project.DoesNotExist:
            return {"status": "error", "message": "project not found"}

        if project.pipeline_mode != Project.MODE_STEP:
            return {"status": "error", "message": "not in step mode"}

        if project.status not in {Project.STATUS_PENDING, Project.STATUS_FAILED}:
            if project.status == Project.STATUS_AWAITING:
                return {"status": "skip", "message": "awaiting user confirmation"}
            return {"status": "skip", "message": f"status {project.status} cannot run"}

    from .step_mode import build_pipeline_result_from_project, execute_step
    from apps.workflow.services.pipeline_service import WorkflowPipelineService

    try:
        result = execute_step(project, node_index)
        project.refresh_from_db()

        if result.get("status") == "error":
            error_msg = humanize_pipeline_error(
                "; ".join(result.get("errors") or ["鑺傜偣鎵ц澶辫触"])
            )[:500]
            project.status = Project.STATUS_FAILED
            project.error_message = error_msg
            project.rendered_progress_html = _render_progress_html(project)
            project.save(
                update_fields=[
                    "status",
                    "error_message",
                    "rendered_progress_html",
                    "updated_at",
                ]
            )
            _refund_creation_submit_if_needed(project, error_msg)
            return {"status": "failed", "node_index": node_index, "error": error_msg}

        if result.get("status") == "awaiting":
            return {
                "status": "awaiting",
                "node_index": node_index,
                "project_id": str(project.id),
            }

        if node_index == WorkflowPipelineService.creation_max_node_index():
            pipeline_result = build_pipeline_result_from_project(project)
            fusion_out = result if isinstance(result, dict) else {}
            _finalize_step_project(project, pipeline_result, fusion_out)
            return {
                "status": "completed",
                "project_id": str(project.id),
                "overall_score": project.overall_score,
            }

        return {"status": "step_done", "node_index": node_index}

    except Exception as exc:  # noqa: BLE001
        error_msg = humanize_user_message(str(exc), default="鍒涗綔澶辫触锛岃绋嶅悗閲嶈瘯")[:500]
        logger.exception("[Creation] 鍒嗘鑺傜偣澶辫触 project=%s node=%s", project_id, node_index)
        project.status = Project.STATUS_FAILED
        project.error_message = error_msg
        project.rendered_progress_html = _render_progress_html(project)
        project.save(
            update_fields=[
                "status",
                "error_message",
                "rendered_progress_html",
                "updated_at",
            ]
        )
        _refund_creation_submit_if_needed(project, error_msg)
        return {"status": "failed", "error": error_msg}


@task(queue_name="creation")
def run_creation_step(
    project_id: str,
    node_index: int,
    script_from: int | None = None,
    script_to: int | None = None,
    outline_mode: str | None = None,
    outline_stage_key: str | None = None,
) -> dict:
    """Run one main-chain node in step/workspace mode."""
    try:
        mode = (
            Project.objects.filter(id=project_id)
            .values_list("pipeline_mode", flat=True)
            .first()
        )
    except Exception:  # noqa: BLE001
        mode = None
    if mode == Project.MODE_WORKSPACE:
        return _run_skill_node_core(
            project_id,
            int(node_index),
            int(script_from) if script_from is not None else None,
            int(script_to) if script_to is not None else None,
            outline_mode=str(outline_mode) if outline_mode else None,
            outline_stage_key=str(outline_stage_key) if outline_stage_key else None,
        )
    if script_from is not None or script_to is not None:
        result = {"status": "error", "message": "step mode does not support script batch args"}
        return _record_task_result_if_failed(
            task_name="creation.step",
            result=result,
            project_id=project_id,
            node_index=int(node_index),
        )
    result = _run_creation_step_core(project_id, int(node_index))
    return _record_task_result_if_failed(
        task_name="creation.step",
        result=result,
        project_id=project_id,
        node_index=int(node_index),
    )


def run_creation_step_sync(project_id: str, node_index: int) -> dict:
    result = _run_creation_step_core(project_id, int(node_index))
    return _record_task_result_if_failed(
        task_name="creation.step_sync",
        result=result,
        project_id=project_id,
        node_index=int(node_index),
    )


def _run_skill_node_core(
    project_id: str,
    node_index: int,
    script_from: int | None = None,
    script_to: int | None = None,
    outline_mode: str | None = None,
    outline_stage_key: str | None = None,
) -> dict:
    """Run one workspace skill node."""
    node_index = int(node_index)
    from apps.billing.services import BillingService
    from apps.workflow.services.pipeline_service import WorkflowPipelineService
    from .step_mode import clear_artifacts_from_node

    max_idx = WorkflowPipelineService.creation_max_node_index()
    if node_index < 2 or node_index > max_idx:
        result = {"status": "error", "message": "invalid skill index", "node_index": node_index}
        return _record_task_result_if_failed(
            task_name="creation.skill_node",
            result=result,
            project_id=project_id,
            node_index=node_index,
        )

    with transaction.atomic():
        try:
            project = Project.objects.select_for_update().get(id=project_id)
        except Project.DoesNotExist:
            result = {"status": "error", "message": "project not found", "node_index": node_index}
            return _record_task_result_if_failed(
                task_name="creation.skill_node",
                result=result,
                project_id=project_id,
                node_index=node_index,
            )

        if project.status == Project.STATUS_RUNNING:
            logger.info("[Workspace] project=%s already running; skip node=%s", project_id, node_index)
            return {"status": "skip", "node_index": node_index, "message": "a skill is already running"}

        if project.nodes.filter(status=CreationNode.STATUS_RUNNING).exists():
            logger.info("[Workspace] project=%s has running node; skip node=%s", project_id, node_index)
            return {"status": "skip", "node_index": node_index, "message": "a skill is already running"}

        if node_index == 4:
            if outline_mode not in ("episodes", "framework"):
                clear_artifacts_from_node(project, node_index)
        elif node_index < 5:
            clear_artifacts_from_node(project, node_index)

        project.status = Project.STATUS_RUNNING
        project.current_node_index = node_index
        project.error_message = ""
        project.save(
            update_fields=[
                "status",
                "current_node_index",
                "error_message",
                "updated_at",
            ]
        )

        CreationNode.objects.filter(project=project, node_index=node_index).update(
            status=CreationNode.STATUS_RUNNING,
            started_at=timezone.now(),
            summary_text=f"姝ｅ湪鐢熸垚 路 鑺傜偣 {node_index}",
        )
        project.rendered_progress_html = _render_progress_html(project)
        project.save(update_fields=["rendered_progress_html", "updated_at"])

    from apps.agent.runtime import agent_for_workspace_index
    from .monitoring.execution_run_service import AgentExecutionRunService
    from .models import AgentExecutionRun
    from .workspace.workspace_editor import compute_script_batch_range
    from .artifact_service import list_artifact_keys

    agent_id = agent_for_workspace_index(node_index) or ""
    run_input_summary = {
        "loaded_artifacts": list_artifact_keys(project),
        "script_from": script_from,
        "script_to": script_to,
        "outline_mode": outline_mode or "",
    }

    log_skill_task_begin(
        project_id=project_id,
        node_index=node_index,
        script_from=script_from,
        script_to=script_to,
        upstream_keys=run_input_summary["loaded_artifacts"],
    )

    from .workspace.workspace_content import ensure_brief_seed_enriched

    ensure_brief_seed_enriched(project)

    try:
        with AgentExecutionRunService.run_scope(
            project,
            agent_id=agent_id,
            node_index=node_index,
            script_from=script_from,
            script_to=script_to,
            outline_mode=outline_mode,
            input_summary=run_input_summary,
        ) as execution_run:
            node_charge_cost = BillingService.get_node_coin_cost(node_index)
            charge_applied = False
            try:
                BillingService.charge_node(
                    project.user,
                    node_index,
                    reference_id=f"{project.id}:skill{node_index}",
                )
                charge_applied = node_charge_cost > 0
            except Exception as exc:  # noqa: BLE001
                error_msg = humanize_user_message(str(exc), default="鎵ｈ垂澶辫触")[:500]
                AgentExecutionRunService.finish_run(
                    execution_run,
                    AgentExecutionRun.STATUS_FAILED,
                    error_message=error_msg,
                )
                _mark_skill_node_failed_state(project, node_index, error_msg)
                log_skill_task_done(
                    project_id=project_id,
                    node_index=node_index,
                    status="failed",
                    detail={"error": error_msg, "execution_run_id": str(execution_run.id)},
                )
                return {"status": "failed", "node_index": node_index, "error": error_msg}

            kwargs: dict = {}
            if node_index == 5:
                if script_from is None or script_to is None:
                    script_from, script_to, _ = compute_script_batch_range(project)
                kwargs = {"script_from": script_from, "script_to": script_to}
            elif node_index == 4 and outline_mode == "framework":
                kwargs = {"outline_mode": "framework"}
            elif node_index == 4 and outline_mode == "stage_framework":
                kwargs = {
                    "outline_mode": "stage_framework",
                    "outline_stage_key": outline_stage_key,
                }
            elif node_index == 4 and outline_mode == "episodes":
                if script_from is None or script_to is None:
                    from .workspace.workspace_editor import compute_outline_batch_range

                    script_from, script_to, _ = compute_outline_batch_range(project, batch_size=1)
                kwargs = {
                    "outline_mode": "episodes",
                    "outline_from": script_from,
                    "outline_to": script_to,
                }
            agent_result = _invoke_workspace_skill(
                project,
                node_index,
                script_from=kwargs.get("script_from") or kwargs.get("outline_from") or script_from,
                script_to=kwargs.get("script_to") or kwargs.get("outline_to") or script_to,
                outline_mode=kwargs.get("outline_mode") or outline_mode,
                outline_stage_key=kwargs.get("outline_stage_key") or outline_stage_key,
            )
            out = agent_result.meta.get("fusion") or {
                "status": "error" if agent_result.status == "error" else "completed",
                "errors": agent_result.errors,
                "artifact_key": (agent_result.outputs or {}).get("artifact_key"),
            }
            project.refresh_from_db()

            if agent_result.status == "error" or out.get("status") == "error":
                error_msg = humanize_pipeline_error(
                    "; ".join(agent_result.errors or out.get("errors") or ["skill execution failed"])
                )[:500]
                AgentExecutionRunService.finish_run(
                    execution_run,
                    AgentExecutionRun.STATUS_FAILED,
                    agent_result=agent_result,
                    error_message=error_msg,
                )
                log_skill_task_done(
                    project_id=project_id,
                    node_index=node_index,
                    status="failed",
                    detail={"error": error_msg, "execution_run_id": str(execution_run.id)},
                )
                if charge_applied and node_charge_cost > 0:
                    try:
                        from apps.billing.models import CoinLedger

                        BillingService.credit(
                            project.user,
                            node_charge_cost,
                            action_key="ai.generate.refund",
                            reference_id=f"{project.id}:skill{node_index}",
                            remark=f"鐢熸垚澶辫触閫€杩橈細{BillingService.node_action_key(node_index)}",
                            entry_type=CoinLedger.TYPE_REFUND,
                        )
                    except Exception as refund_exc:  # noqa: BLE001
                        logger.exception(
                            "[Creation] 鑺傜偣澶辫触閫€娆惧紓甯?project=%s node=%s: %s",
                            project_id,
                            node_index,
                            refund_exc,
                        )
                _mark_skill_node_failed_state(project, node_index, error_msg)
                return {"status": "failed", "node_index": node_index, "error": error_msg}

            completed = project.nodes.filter(status=CreationNode.STATUS_COMPLETED).count()
            total = max(1, project.total_nodes)
            project.status = Project.STATUS_PENDING
            project.progress_percent = min(100, int(completed / total * 100))
            project.rendered_progress_html = _render_progress_html(project)
            project.save(
                update_fields=[
                    "status",
                    "progress_percent",
                    "rendered_progress_html",
                    "updated_at",
                ]
            )

            if node_index == 5:
                from .step_mode import build_pipeline_result_from_project
                from .script_delivery import persist_script_works

                try:
                    persist_script_works(project, build_pipeline_result_from_project(project))
                except Exception as exc:  # noqa: BLE001
                    logger.warning("[Workspace] persist scripts failed project=%s: %s", project.id, exc)

                if _scripts_fully_generated_for_project(project):
                    project.status = Project.STATUS_COMPLETED
                    if not project.completed_at:
                        project.completed_at = timezone.now()
                    project.progress_percent = 100
                    project.rendered_progress_html = _render_progress_html(project)
                    project.save(
                        update_fields=[
                            "status",
                            "completed_at",
                            "progress_percent",
                            "rendered_progress_html",
                            "updated_at",
                        ]
                    )

            trace_detail: dict = {}
            executed = agent_result.meta.get("executed_sub_skills") or []
            if executed and agent_result.agent_id:
                from .orchestration.sub_skill_runner import persist_execution_trace

                trace_detail = persist_execution_trace(
                    project,
                    node_index,
                    agent_result.agent_id,
                    executed,
                    trace_entries=agent_result.meta.get("execution_trace"),
                )

            artifact_key = str(out.get("artifact_key") or "")
            AgentExecutionRunService.finish_run(
                execution_run,
                AgentExecutionRun.STATUS_COMPLETED,
                agent_result=agent_result,
                output_artifact_key=artifact_key,
                output_summary=AgentExecutionRunService.build_output_summary(project, artifact_key),
            )
            log_skill_task_done(
                project_id=project_id,
                node_index=node_index,
                status="done",
                artifact_key=artifact_key or None,
                detail={
                    "execution_trace": trace_detail.get("execution_trace")
                    or agent_result.meta.get("execution_trace"),
                    "execution_run_id": str(execution_run.id),
                },
            )
            return {"status": "done", "node_index": node_index, "project_id": str(project.id)}

    except Exception as exc:  # noqa: BLE001
        error_msg = humanize_user_message(str(exc), default="skill execution failed")[:500]
        logger.exception("[Workspace] skill failed project=%s node=%s", project_id, node_index)
        return _finalize_skill_node_failure(
            project_id,
            node_index,
            error_msg,
            log_status="exception",
            log_detail={"error": error_msg},
        )


@task(queue_name="creation")
def run_skill_node(
    project_id: str,
    node_index: int,
    script_from: int | None = None,
    script_to: int | None = None,
) -> dict:
    """Run one workspace skill node asynchronously."""
    return _run_skill_node_core(
        project_id,
        int(node_index),
        int(script_from) if script_from is not None else None,
        int(script_to) if script_to is not None else None,
    )


def run_skill_node_sync(
    project_id: str,
    node_index: int,
    script_from: int | None = None,
    script_to: int | None = None,
) -> dict:
    return _run_skill_node_core(project_id, int(node_index), script_from, script_to)


def _ensure_script_works(project: Project, pipeline_result: dict | None = None) -> None:
    """Persist script works through script_delivery."""
    from .script_delivery import persist_script_works

    persist_script_works(project, pipeline_result)


@task(queue_name="evolve")
def run_evolve_audit_task(project_id: str) -> dict:
    """Run evolution audit task."""
    try:
        from .evolve_audit import trigger_audit_after_score
        trigger_audit_after_score(project_id)
        return {"status": "done", "project_id": project_id}
    except Exception as exc:  # noqa: BLE001
        logger.warning("[EvolveAuditTask] 澶辫触 project=%s: %s", project_id, exc)
        result = {"status": "error", "project_id": project_id, "error": str(exc)}
        return _record_task_result_if_failed(
            task_name="creation.evolve_audit",
            result=result,
            project_id=project_id,
        )
