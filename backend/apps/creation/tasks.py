"""
创作后台任务（Django 6 @task + dj_queue / Postgres）

核心：run_creation_pipeline(project_id)
  - 串行执行融合编排器节点 1–5 + fusion 后处理
  - 更新节点状态、进度 HTML、ScriptWork 下载文件

启动 worker：
  python manage.py dj_queue --mode async   # Windows 推荐
  python manage.py dj_queue                # Linux 可用 fork
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
    """创作主任务失败时退还提交费用，reference_id 保证重复失败不重复退。"""
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
    """将项目与节点同步标记为失败，避免节点卡在 running。"""
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
        summary_text="生成失败",
        completed_at=None,
    )


def _workspace_node_to_skill_id(node_index: int) -> str:
    """工作台节点索引 → 创作技能 ID（兼容旧引用）。"""
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
    """工作台单节点：优先 registry Agent 编排，回退扁平 SkillInvoker。"""
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
    """直接读 episode_scripts 产物判断剧本是否完整生成（不依赖旧引擎）。"""
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
    """事务污染后仍可靠地将工作台节点标记为失败（避免项目永久卡在 running）。"""
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
                "error": result.get("error") or result.get("message") or "后台任务执行失败",
                "result": result,
            },
            exception_type="BackgroundTaskResultFailed",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[TaskMonitor] write skipped task=%s project=%s: %s", task_name, project_id, exc)
    return result


def _execute_pipeline_for_project(project: Project) -> dict:
    """主链节点 1–7：通过新 WorkflowEngine 执行 FusionPipelinePack。

    【新引擎全量上线】所有节点统一经由 WorkflowInstance → WorkflowEngine → SkillBridge
    （skill_id → SkillInvoker；runner_path → Python 函数）。旧 FusionOrchestrator /
    AgentOrchestrator 体系已不再被任何业务路径调用。
    单一链路：WorkflowInstance → WorkflowEngine → SkillBridge → skill_id/Python 函数。

    调用路径：
      _run_creation_pipeline_core()
        → _execute_pipeline_for_project()          ← 本函数
          → WorkflowEngine(instance).run()
            → SkillBridge.run()
              ├─ skill_id   → SkillInvoker.invoke() (创作 7 技能)
              └─ runner_path → Python 函数
    """
    from apps.workflow.execution_models import WorkflowInstance
    from apps.workflow.workflow_engine import WorkflowEngine

    # 查找该 Project 对应的 WorkflowInstance（submission 时已创建）
    instance = (
        WorkflowInstance.objects
        .filter(project=project)
        .order_by("-created_at")
        .first()
    )

    if instance is None:
        raise RuntimeError(
            f"Project {project.id} 没有 WorkflowInstance，"
            f"无法走新引擎（应在 submission 时创建）",
        )

    if instance.status not in (
        WorkflowInstance.STATUS_PENDING,
        WorkflowInstance.STATUS_RUNNING,
        WorkflowInstance.STATUS_PAUSED,
    ):
        # 已经是终态（done / failed / cancelled），不再重复执行
        logger.info(
            "[Creation] Project %s 实例已是终态 (%s)，跳过",
            project.id, instance.status,
        )
        return _build_pipeline_result_from_instance(instance)

    engine = WorkflowEngine(instance)
    engine.run()

    # 新引擎完成后，同步节点执行结果到 Project / CreationNode
    _sync_workflow_instance_to_project(project, instance)

    return _build_pipeline_result_from_instance(instance)


def _sync_workflow_instance_to_project(project: Project, instance) -> None:
    """将 WorkflowInstance 的节点执行结果同步到 Project 的 CreationNode。"""
    from apps.workflow.execution_models import NodeExecution
    from apps.workflow.models import FusionPipelineNode
    from django.utils import timezone as tz

    nodes = NodeExecution.objects.filter(instance=instance).order_by("started_at")
    node_map = {str(ne.node_id): ne for ne in nodes}

    # 同步节点状态到 CreationNode
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
            logger.warning("[Sync] 同步节点失败 node=%s: %s", db_node.fusion_node_id, exc)

    # 同步 Project 整体进度
    completed = nodes.filter(status=NodeExecution.STATUS_COMPLETED).count()
    total = nodes.count()
    project.progress_percent = min(100, int(completed / max(1, total) * 100))
    project.current_node_index = total
    project.updated_at = tz.now()


def _build_pipeline_result_from_instance(instance) -> dict:
    """将 WorkflowInstance 的上下文整理为 pipeline 兼容的 result dict。"""
    ctx = instance.context or {}

    return {
        "project_brief": ctx.get("nodes", {}).get("node_brief", {}).get("output", {}),
        "structure": ctx.get("nodes", {}).get("node_outline", {}).get("output", {}),
        "characters": ctx.get("nodes", {}).get("node_character", {}).get("output", {}),
        "outlines": ctx.get("nodes", {}).get("node_outline", {}).get("output", {}),
        "scripts": ctx.get("nodes", {}).get("node_script", {}).get("output", {}),
        "review": ctx.get("nodes", {}).get("node_review", {}).get("output", {}),
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
        1: (
            brief.get("project_name")
            or f"{brief.get('theme', project.theme)} · {project.episode_count}集"
        ),
        2: (
            f"{structure.get('total_episodes', project.episode_count)}集 × "
            f"{structure.get('acts', 6)}幕结构, "
            f"{structure.get('reversal_count', 0)}个反转点"
        ),
        3: (
            f"共{characters.get('character_count', 0)}个角色, "
            f"主角「{characters.get('protagonist', '')[:16]}」"
        ),
        4: (
            f"{outlines.get('total_episodes', project.episode_count)}集大纲, "
            f"{outlines.get('reversal_count', 0)}个反转点"
        ),
        5: (
            f"{scripts.get('total_words', 0)}字, "
            f"{scripts.get('total_scenes', 0)}个场景, "
            f"格式变体 {scripts.get('format_variant', project.format_variant)}"
        ),
        6: (
            f"综合评分 {review.get('overall_score', 0)}分 "
            f"({review.get('grade', '')}级)"
        ),
        7: (
            f"8维评分 {review.get('overall_score', 0)}分 "
            f"({review.get('grade', '')}级)"
        ),
    }

    now = timezone.now()
    for node_index in range(1, len(PIPELINE_NODES) + 1):
        try:
            node = CreationNode.objects.get(project=project, node_index=node_index)
        except CreationNode.DoesNotExist:
            continue
        node.status = CreationNode.STATUS_COMPLETED
        node.completed_at = now
        node.summary_text = node_summaries.get(node_index, "节点完成")
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
            project.error_message = fusion_out.get("error") or "融合质检/评分未达放行线"
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
            logger.error("[Creation] project 不存在: %s", project_id)
            return {"status": "error", "project_id": project_id, "message": "project not found"}

        if project.status not in {Project.STATUS_PENDING, Project.STATUS_FAILED}:
            logger.info("[Creation] project 已在运行或已完成: %s", project_id)
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
        msg = f"节点 {disabled} 已关闭，无法执行创作"
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
            logger.error("[Creation] pipeline 返回错误 project=%s: %s", project.id, error_msg)
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

        fusion_out = None
        try:
            from django.conf import settings as dj_settings

            if getattr(dj_settings, "FUSION_SKILL_ENABLED", True):
                from .fusion.fusion_pipeline import run_fusion_for_project

                fusion_out = run_fusion_for_project(project, result)
                logger.info(
                    "[Creation] fusion 后处理 project=%s status=%s score=%s",
                    project.id,
                    fusion_out.get("fusion_status"),
                    fusion_out.get("overall_score"),
                )
        except Exception as fusion_exc:  # noqa: BLE001
            logger.exception("[Creation] fusion 后处理失败 project=%s: %s", project.id, fusion_exc)
            project.fusion_status = Project.FUSION_BLOCKED
            project.error_message = humanize_user_message(
                str(fusion_exc), default="融合质检失败，请稍后重试"
            )[:500]
            project.save(update_fields=["fusion_status", "error_message", "updated_at"])

        _update_project_after_pipeline(project, result, started_at, fusion_out=fusion_out)
        from .script_delivery import persist_script_works

        persist_script_works(project, result)

        final = "completed"
        if fusion_out and fusion_out.get("ok") is False:
            final = "failed"
        elif fusion_out and fusion_out.get("fusion_status") == Project.FUSION_BLOCKED:
            final = "failed"
        if final == "failed":
            _refund_creation_submit_if_needed(
                project,
                project.error_message or "融合质检/评分未达放行线",
            )

        logger.info(
            "[Creation] project=%s 创作完成, 耗时 %d 分钟 fusion=%s",
            project.id,
            project.total_duration_minutes,
            project.fusion_status,
        )
        return {
            "status": final,
            "project_id": str(project.id),
            "fusion_status": project.fusion_status,
            "overall_score": project.overall_score,
        }

    except Exception as exc:  # noqa: BLE001
        error_msg = humanize_user_message(str(exc), default="创作失败，请稍后重试")[:500]
        logger.exception("[Creation] project=%s 创作失败: %s", project.id, exc)
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
    """7 节点创作流水线（dj_queue worker 异步执行）。"""
    result = _run_creation_pipeline_core(project_id)
    return _record_task_result_if_failed(
        task_name="creation.pipeline",
        result=result,
        project_id=project_id,
    )


def run_creation_pipeline_sync(project_id: str) -> dict:
    """同步执行（仅 CREATION_FORCE_SYNC_PIPELINE 或管理命令调试）。"""
    logger.info("[Creation] 同步执行 pipeline project=%s", project_id)
    result = _run_creation_pipeline_core(project_id)
    return _record_task_result_if_failed(
        task_name="creation.pipeline_sync",
        result=result,
        project_id=project_id,
    )


def _finalize_step_project(project: Project, pipeline_result: dict, fusion_out: dict | None) -> None:
    """分步模式最后一步：标记完成并写入 ScriptWork。"""
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
            return {"status": "error", "message": "非分步模式"}

        if project.status not in {Project.STATUS_PENDING, Project.STATUS_FAILED}:
            if project.status == Project.STATUS_AWAITING:
                return {"status": "skip", "message": "等待用户确认"}
            return {"status": "skip", "message": f"状态 {project.status} 不可执行"}

    from .step_mode import build_pipeline_result_from_project, execute_step
    from apps.workflow.services.pipeline_service import WorkflowPipelineService

    try:
        result = execute_step(project, node_index)
        project.refresh_from_db()

        if result.get("status") == "error":
            error_msg = humanize_pipeline_error(
                "; ".join(result.get("errors") or ["节点执行失败"])
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
        error_msg = humanize_user_message(str(exc), default="创作失败，请稍后重试")[:500]
        logger.exception("[Creation] 分步节点失败 project=%s node=%s", project_id, node_index)
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
    """分步 / 工作台：执行单个主链节点（workspace 走 _run_skill_node_core）。"""
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
        result = {"status": "error", "message": "分步模式不支持剧本批次参数"}
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
    """技能工作台：仅执行单个主链节点。"""
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

    from apps.agent.runtime import agent_for_pipeline_node_index, should_defer_to_post_script_chain

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
            logger.info("[Workspace] project=%s 已有技能运行，跳过 node=%s", project_id, node_index)
            return {"status": "skip", "node_index": node_index, "message": "有技能正在执行"}

        if project.nodes.filter(status=CreationNode.STATUS_RUNNING).exists():
            logger.info("[Workspace] project=%s 已有运行中节点，跳过 node=%s", project_id, node_index)
            return {"status": "skip", "node_index": node_index, "message": "有技能正在执行"}

        if should_defer_to_post_script_chain(project, node_index):
            return {
                "status": "skipped",
                "node_index": node_index,
                "reason": "workspace_post_script_chain",
                "agent_id": agent_for_pipeline_node_index(node_index) or "",
                "message": "工作台模式下质检/评分由剧本完成后的后处理链统一执行，请勿单独触发该节点。",
            }

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
            summary_text=f"正在生成 · 节点 {node_index}",
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
                error_msg = humanize_user_message(str(exc), default="扣费失败")[:500]
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
                    "; ".join(agent_result.errors or out.get("errors") or ["技能执行失败"])
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
                            remark=f"生成失败退还：{BillingService.node_action_key(node_index)}",
                            entry_type=CoinLedger.TYPE_REFUND,
                        )
                    except Exception as refund_exc:  # noqa: BLE001
                        logger.exception(
                            "[Creation] 节点失败退款异常 project=%s node=%s: %s",
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
                    from dj_queue.api import enqueue_on_commit

                    enqueue_on_commit(run_agent_post_chain, str(project.id))

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
        error_msg = humanize_user_message(str(exc), default="技能执行失败")[:500]
        logger.exception("[Workspace] skill failed project=%s node=%s", project_id, node_index)
        return _finalize_skill_node_failure(
            project_id,
            node_index,
            error_msg,
            log_status="exception",
            log_detail={"error": error_msg},
        )


def _run_post_script_chain_via_skill_invoker(project: Project) -> dict:
    """新引擎：post-script 链（review → polish → review → score → marketing）通过 SkillInvoker 调用。
    返回 dict 形如 {status, chain, results, errors}。
    """
    from apps.skill.skills.invoker import get_skill_invoker
    from apps.agent.runtime import post_script_effective_chain, polish_max_rounds
    from .skill_invoke_payload import build_creation_skill_invoke_payload

    chain = list(post_script_effective_chain() or [])
    invoker = get_skill_invoker()
    results: list[dict] = []
    polish_rounds = 0
    review_passed = False
    errors: list[str] = []
    for step in chain:
        if step == "polish" and polish_rounds >= polish_max_rounds():
            results.append({"agent_id": "polish", "status": "skipped", "reason": "max_rounds"})
            continue
        skill_id = f"creation.{step}"
        skill_result = invoker.invoke(
            skill_id=skill_id,
            payload=build_creation_skill_invoke_payload(project, skill_id),
            project_id=str(project.id),
            user_id=project.user_id,
        )
        if skill_result.success:
            results.append({
                "agent_id": step,
                "status": "completed",
                "outputs": skill_result.data or {},
                "skill_id": skill_id,
                "trace_id": skill_result.trace_id,
            })
            if step == "review":
                review_passed = bool((skill_result.data or {}).get("passed"))
        else:
            err_msg = skill_result.error.get("message", "skill failed")
            errors.append(err_msg)
            results.append({
                "agent_id": step,
                "status": "error",
                "errors": [err_msg],
                "skill_id": skill_id,
                "trace_id": skill_result.trace_id,
            })
        if step == "polish":
            polish_rounds += 1

    ok = all(r.get("status") in ("completed", "skipped") for r in results)
    return {
        "status": "completed" if ok else "partial",
        "chain": chain,
        "results": results,
        "errors": errors,
        "review_passed": review_passed,
    }


@task(queue_name="creation")
def run_agent_post_chain(project_id: str) -> dict:
    """剧本全量生成后：review → polish → review → score → marketing（新引擎：SkillInvoker 串联）。"""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        result = {"status": "error", "message": "project not found"}
        return _record_task_result_if_failed(
            task_name="creation.post_chain",
            result=result,
            project_id=project_id,
        )

    if not _scripts_fully_generated_for_project(project):
        return {"status": "skipped", "reason": "scripts_incomplete"}

    project.status = Project.STATUS_RUNNING
    project.save(update_fields=["status", "updated_at"])
    try:
        out = _run_post_script_chain_via_skill_invoker(project)
        project.refresh_from_db()
        if out.get("status") == "completed" and project.pipeline_mode == Project.MODE_WORKSPACE:
            project.status = Project.STATUS_COMPLETED
            if not project.completed_at:
                project.completed_at = timezone.now()
            project.fusion_status = project.fusion_status or Project.FUSION_READY
            project.save(
                update_fields=["status", "completed_at", "fusion_status", "updated_at"]
            )
        else:
            project.status = Project.STATUS_PENDING
            project.save(update_fields=["status", "updated_at"])
        project.rendered_progress_html = _render_progress_html(project)
        project.save(update_fields=["rendered_progress_html", "updated_at"])

        # 进化审计挂钩：score完成后异步触发（不阻塞主流程）
        if out.get("status") == "completed" and project.overall_score is not None:
            try:
                from apps.skill.config.portal.runtime_config import RuntimeConfigService

                if "evolve" in RuntimeConfigService.dj_queue_queues():
                    from dj_queue.api import enqueue_on_commit

                    enqueue_on_commit(run_evolve_audit_task, project_id)
            except Exception as _e:  # noqa: BLE001
                logger.warning("[PostChain] 进化审计入队失败 project=%s: %s", project_id, _e)

        result = {"status": "done", "chain": out}
        if out.get("status") == "error":
            result = {"status": "failed", "chain": out, "error": "; ".join(out.get("errors") or [])}
        return _record_task_result_if_failed(
            task_name="creation.post_chain",
            result=result,
            project_id=project_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[Agent] post chain failed project=%s", project_id)
        project.status = Project.STATUS_FAILED
        project.error_message = humanize_user_message(str(exc), default="后处理失败")[:500]
        project.save(update_fields=["status", "error_message", "updated_at"])
        result = {"status": "failed", "error": str(exc)}
        return _record_task_result_if_failed(
            task_name="creation.post_chain",
            result=result,
            project_id=project_id,
        )


@task(queue_name="creation")
def run_skill_node(
    project_id: str,
    node_index: int,
    script_from: int | None = None,
    script_to: int | None = None,
) -> dict:
    """技能工作台：异步执行单个技能。"""
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
    """兼容旧调用：委托 script_delivery.persist_script_works。"""
    from .script_delivery import persist_script_works

    persist_script_works(project, pipeline_result)


@task(queue_name="evolve")
def run_evolve_audit_task(project_id: str) -> dict:
    """
    进化审计异步任务（dj_queue queue=evolve）。
    ScoreAgent 完成后自动触发，也可在 management command 中手动入队。
    不影响主线程性能，失败时仅记录日志不影响用户侧。
    """
    try:
        from .evolve_audit import trigger_audit_after_score
        trigger_audit_after_score(project_id)
        return {"status": "done", "project_id": project_id}
    except Exception as exc:  # noqa: BLE001
        logger.warning("[EvolveAuditTask] 失败 project=%s: %s", project_id, exc)
        result = {"status": "error", "project_id": project_id, "error": str(exc)}
        return _record_task_result_if_failed(
            task_name="creation.evolve_audit",
            result=result,
            project_id=project_id,
        )
