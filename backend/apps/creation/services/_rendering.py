# -*- coding: utf-8 -*-
"""HTML ???????????? DOM??"""

import logging
from html import escape

from ..models import Project, ShareLink

logger = logging.getLogger(__name__)


def _render_progress_html(project: Project) -> str:
    """?????????Drama ???????? legacy 5 ?????"""
    status_text = dict(Project.STATUS_CHOICES).get(
        project.execution_status, project.execution_status
    )
    from apps.drama.progress_service import DramaProgressService

    stage = project.get_drama_stage_display() if project.is_drama_workspace else "?"
    return (
        f'<div class="creation-progress-card" data-project-id="{project.id}">'
        f'<div class="progress-header">'
        f'<span class="progress-status">{escape(status_text)}</span>'
        f'<span class="progress-percent">{project.progress_percent}%</span>'
        f"</div>"
        f'<div class="progress-bar"><div class="progress-fill" style="width:{project.progress_percent}%"></div></div>'
        f'<div class="progress-stage">?????{escape(stage)}</div>'
        f"</div>"
    )


def render_progress_html(project: Project) -> str:
    return _render_progress_html(project)


def refresh_project_progress(project: Project, *, progress_percent: int | None = None) -> None:
    fields = ["updated_at"]
    if progress_percent is not None:
        project.progress_percent = min(100, max(0, int(progress_percent)))
        fields.append("progress_percent")
    project.rendered_progress_html = _render_progress_html(project)
    fields.append("rendered_progress_html")
    project.save(update_fields=fields)


def _render_result_html(project: Project) -> str:
    if project.rendered_result_html and "creation-script-result" in project.rendered_result_html:
        return project.rendered_result_html
    if project.rendered_result_html and len(project.rendered_result_html) > 400:
        return project.rendered_result_html

    try:
        from ..script_delivery import build_script_display_html, resolve_scripts

        if resolve_scripts(project):
            return build_script_display_html(project)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[Creation] ? artifact ???? HTML ??: %s", exc)

    title = project.title or ("theme: " + str(project.theme))
    return (
        f'<div class="creation-result-card" data-project-id="{project.id}">'
        f'<h3 class="result-title">{escape(title)}</h3>'
        f'<p class="result-meta">theme: {escape(project.theme)} / episodes: {project.episode_count}</p>'
        f'<div class="result-watermark" style="opacity:.5;font-size:12px;">'
        f"user {project.user_id}"
        f"</div>"
        f"</div>"
    )


def _render_share_html(share: ShareLink) -> str:
    project = share.project
    title = share.custom_title or project.title or f"????? ? {project.theme}"
    wm = f"share-{share.token[:12]}"

    try:
        from ..script_export import project_has_exportable_content
        from ..workspace.workspace_html import build_workspace_share_html

        if project_has_exportable_content(project):
            html = build_workspace_share_html(project, watermark_token=wm)
            if share.custom_title:
                html = html.replace(
                    escape(project.title or project.theme or ""),
                    escape(share.custom_title),
                    1,
                )
            return html
    except Exception as exc:  # noqa: BLE001
        logger.warning("[Creation] ????? HTML ????: %s", exc)

    try:
        from ..script_delivery import build_script_display_html, resolve_scripts

        if resolve_scripts(project):
            return build_script_display_html(project, watermark_token=wm)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[Creation] ????? HTML ????: %s", exc)

    return (
        f'<div class="creation-share-card" data-share-token="{escape(share.token[:12])}">'
        f"<h2>{escape(title)}</h2>"
        f"<p>???{escape(project.theme)} ? ???{project.episode_count}</p>"
        f'<p style="opacity:.6;font-size:12px;">?? {escape(wm)}</p>'
        f"</div>"
    )
