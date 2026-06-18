"""创作进度查询。"""

import logging
from datetime import timedelta

from django.utils import timezone

from ..models import AgentExecutionRun, DownloadToken, Project, ScriptWork
from ._helpers import _get_user_project
from ._rendering import _render_progress_html, _render_result_html

logger = logging.getLogger(__name__)


def _latest_execution_run_summary(project: Project) -> dict | None:
    from ..monitoring.execution_run_service import AgentExecutionRunService

    run = (
        AgentExecutionRun.objects.filter(project=project)
        .order_by("-started_at")
        .first()
    )
    if not run:
        return None
    return AgentExecutionRunService.compact_run_summary(run)


def get_progress(project_id: str, user) -> dict:
    """查询创作进度（项目状态 + 最近一次 Agent 运行摘要）。"""
    project = _get_user_project(project_id, user)

    rendered_progress_html = _render_progress_html(project)

    download_token_str = ""
    if project.status == Project.STATUS_COMPLETED:
        try:
            dl = (
                DownloadToken.objects.filter(
                    project=project,
                    user=user,
                    file_format=ScriptWork.FORMAT_MARKDOWN,
                    is_used=False,
                    expires_at__gt=timezone.now(),
                )
                .order_by("-created_at")
                .first()
            )
            if dl is None:
                dl = DownloadToken.objects.create(
                    project=project,
                    user=user,
                    token=DownloadToken.generate_token(),
                    file_format=ScriptWork.FORMAT_MARKDOWN,
                    expires_at=timezone.now() + timedelta(minutes=15),
                )
            download_token_str = dl.token
        except Exception as exc:  # noqa: BLE001
            logger.warning("[Creation] 生成下载 token 失败: %s", exc)

    score_summary = None
    if project.overall_score is not None or project.grade:
        score_summary = {
            "overallScore": project.overall_score,
            "grade": project.grade,
        }

    return {
        "status": project.status,
        "status_text": project.get_status_display(),
        "fusion_status": project.fusion_status or "",
        "fusion_status_text": (
            dict(Project.FUSION_STATUS_CHOICES).get(project.fusion_status, "")
            if project.fusion_status
            else ""
        ),
        "overall_score": project.overall_score,
        "grade": project.grade,
        "ready_at": project.ready_at,
        "skill_version": project.skill_version,
        "score_summary": score_summary,
        "pipeline_mode": project.pipeline_mode,
        "progress_percent": project.progress_percent,
        "rendered_progress_html": rendered_progress_html,
        "rendered_result_html": (
            _render_result_html(project)
            if project.status == Project.STATUS_COMPLETED
            else ""
        ),
        "download_token": download_token_str,
        "error_message": project.error_message if project.status == Project.STATUS_FAILED else "",
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "latest_execution_run": _latest_execution_run_summary(project),
    }
