"""创作任务提交。

【P1】新引擎对接：
  • 创建 Project 时同步创建 WorkflowInstance
  • run_creation_pipeline 通过 WorkflowInstance → WorkflowEngine → SkillBridge
  • 旧引擎 _execute_pipeline_for_project_legacy 仅在 WorkflowInstance 不存在时兜底
"""

import logging
from typing import Tuple

from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.membership.services import MembershipService

from ..models import CreationNode, Project
from ._helpers import _get_user_project
from ._rendering import _render_progress_html

logger = logging.getLogger(__name__)


def _estimate_minutes(episode_count: int) -> int:
    base = 3
    per_episode = 0.3
    return max(1, int(base + episode_count * per_episode))


def _create_workflow_instance(project: Project, pack, user_id: str) -> None:
    """为 Project 创建对应的 WorkflowInstance（新引擎唯一入口）。

    在 Project 创建之后立即执行。如果项目已有 WorkflowInstance 则跳过。
    该实例将由 run_creation_pipeline 中的 WorkflowEngine 消费。
    """
    from apps.workflow.execution_models import WorkflowInstance

    if WorkflowInstance.objects.filter(project=project).exists():
        logger.info("[Creation] Project %s 已有 WorkflowInstance，跳过", project.id)
        return

    instance = WorkflowInstance.objects.create(
        pack=pack,
        project=project,
        user_id=user_id,
        trigger_type=WorkflowInstance.TRIGGER_USER,
        context={"submit_data": {"theme": project.theme}},
    )
    logger.info(
        "[Creation] 为 Project %s 创建 WorkflowInstance=%s pack=%s",
        project.id, instance.id, pack.id if pack else "default",
    )


@transaction.atomic
def submit(user, data: dict) -> Tuple[Project, int]:
    """提交创作任务（新引擎全量切换）。"""
    from apps.billing.services import BillingService, InsufficientCoins

    BillingService.ensure_can_create(user)

    current_membership = MembershipService.get_current_membership(user)

    from apps.workflow.fusion.ssot_catalog import get_ssot_catalog
    from apps.workflow.pipeline_store import FusionPipelineDbService
    from apps.workflow.services.pipeline_service import WorkflowPipelineService

    catalog = get_ssot_catalog()
    platform = catalog.normalize_platform(data.get("target_platform", "douyin"))

    pack = FusionPipelineDbService.resolve_pack_for_creation(data.get("pipeline_pack_id"))
    pack_id = str(pack.id) if pack else None
    pipeline_nodes = WorkflowPipelineService.pipeline_nodes_for_creation(pack_id=pack_id)
    if not pipeline_nodes:
        from ..services._pipeline import _load_pipeline_nodes

        pipeline_nodes = _load_pipeline_nodes()

    project = Project.objects.create(
        user=user,
        theme=data["theme"],
        core_idea=data["core_idea"],
        episode_count=data["episode_count"],
        format_variant=data["format_variant"],
        audience=data.get("audience", ""),
        reference_work=data.get("reference_work", ""),
        target_platform=platform,
        episode_duration_minutes=data.get("episode_duration_minutes", 2.0),
        creation_entry=data.get("creation_entry", "from-scratch"),
        budget_level=data.get("budget_level", "medium"),
        global_market=data.get("global_market", "domestic"),
        user_membership=current_membership,
        pipeline_mode=data.get("pipeline_mode", Project.MODE_WORKSPACE),
        pipeline_pack=pack,
        status=Project.STATUS_PENDING,
        current_node_index=0,
        total_nodes=len(pipeline_nodes),
        progress_percent=0,
        title=catalog.theme_display_name(data["theme"]) or data["theme"],
        total_duration_minutes=0,
    )

    try:
        BillingService.charge(
            user,
            "creation.submit",
            reference_id=str(project.id),
            remark="发起创作",
        )
    except InsufficientCoins as exc:
        raise PermissionDenied(str(exc)) from exc

    try:
        from ..artifact_service import save_artifact
        from ..schema_mappers import build_project_brief

        brief_payload = build_project_brief(
            project, submit_data=data, status="confirmed",
        )
        save_artifact(project, "project_brief", brief_payload)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[Creation] 写入 project_brief 产物失败: %s", exc)

    CreationNode.objects.bulk_create(
        [
            CreationNode(
                project=project,
                node_index=meta["index"],
                fusion_node_id=meta.get("fusion_node_id", ""),
                node_name=meta["name"],
                node_description=meta.get("description", ""),
                status=CreationNode.STATUS_PENDING,
            )
            for meta in pipeline_nodes
        ]
    )

    # ──【P1 新增】为 Project 创建 WorkflowInstance（新引擎唯一入口）
    if pack:
        _create_workflow_instance(project, pack, str(user.id))

    project.fusion_status = Project.FUSION_DRAFT
    project.save(update_fields=["fusion_status", "updated_at"])

    project.rendered_progress_html = _render_progress_html(project)
    project.save(update_fields=["rendered_progress_html"])

    mode = project.pipeline_mode

    # ── Adapt 预处理（保留）
    try:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService
        from ..orchestration.orchestrator import AgentOrchestrator

        requires_adapt = CreationFormOverrideService.creation_entry_requires_adapt(
            project.creation_entry or "from-scratch"
        )
        adapt_result = AgentOrchestrator(project).invoke_adapt_on_create(submit_data=data)
        if requires_adapt and getattr(adapt_result, "status", "") == "error":
            msg = "; ".join(getattr(adapt_result, "errors", []) or []) or "改编入场预处理失败"
            raise PermissionDenied(msg)
    except Exception as exc:  # noqa: BLE001
        if requires_adapt:
            raise PermissionDenied(f"改编入场预处理失败：{exc}") from exc
        logger.warning("[Creation] AdaptAgent 预处理失败: %s", exc)

    if mode == Project.MODE_WORKSPACE:
        from ..workspace.workspace_service import finalize_workspace_brief

        finalize_workspace_brief(project)
        logger.info(
            "[Creation] 工作台项目已创建 project=%s user=%s",
            project.id,
            user.id,
        )
    else:
        from dj_queue.api import enqueue_on_commit

        from ..tasks import run_creation_pipeline, run_creation_step

        if mode == Project.MODE_STEP:
            enqueue_on_commit(run_creation_step, str(project.id), 1)
        else:
            enqueue_on_commit(run_creation_pipeline, str(project.id))
        logger.info(
            "[Creation] 已入队创作任务 project=%s mode=%s user=%s",
            project.id,
            project.pipeline_mode,
            user.id,
        )

    estimated_minutes = _estimate_minutes(project.episode_count)
    return project, estimated_minutes
