"""HTML 预渲染工具（前端直接插入 DOM）。"""

import logging
from html import escape

from ..models import Project, ShareLink

logger = logging.getLogger(__name__)


def _render_progress_html(project: Project) -> str:
    """渲染项目进度卡片（Drama 工作台，不再展示 legacy 5 步主链）。"""
    status_text = dict(Project.STATUS_CHOICES).get(
        project.execution_status, project.execution_status
    )
    from apps.drama.progress_service import DramaProjectProgressService

    drama = DramaProjectProgressService.find_drama_project(project.id)
    stage = (drama.current_stage if drama else "") or "—"
    return (
        f'<div class="creation-progress-card" data-project-id="{project.id}">'
        f'<div class="progress-header">'
        f'<span class="progress-status">{escape(status_text)}</span>'
        f'<span class="progress-percent">{project.progress_percent}%</span>'
        f"</div>"
        f'<div class="progress-bar"><div class="progress-fill" style="width:{project.progress_percent}%"></div></div>'
        f'<div class="progress-stage">当前阶段：{escape(stage)}</div>'
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
        logger.warning("[Creation] 从 artifact 构建结果 HTML 失败: %s", exc)

    title = project.title or f"未命名剧本 · {project.theme}"
    return (
        f'<div class="creation-result-card" data-project-id="{project.id}">'
        f'<h3 class="result-title">{escape(title)}</h3>'
        f'<p class="result-meta">题材：{escape(project.theme)} · 集数：{project.episode_count} 集</p>'
        f'<div class="result-watermark" style="opacity:.5;font-size:12px;">'
        f"仅供 {project.user_id} 查看 · 含数字水印，禁止二次传播"
        f"</div>"
        f"</div>"
    )


def _render_share_html(share: ShareLink) -> str:
    project = share.project
    title = share.custom_title or project.title or f"未命名剧本 · {project.theme}"
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
        logger.warning("[Creation] 分享页可读 HTML 构建失败: %s", exc)

    try:
        from ..script_delivery import build_script_display_html, resolve_scripts

        if resolve_scripts(project):
            return build_script_display_html(project, watermark_token=wm)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[Creation] 分享页剧本 HTML 构建失败: %s", exc)

    return (
        f'<div class="creation-share-card" data-share-token="{escape(share.token[:12])}">'
        f"<h2>{escape(title)}</h2>"
        f"<p>题材：{escape(project.theme)} · 集数：{project.episode_count}</p>"
        f'<p style="opacity:.6;font-size:12px;">水印 {escape(wm)}</p>'
        f"</div>"
    )
