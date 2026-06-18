"""HTML 预渲染工具（前端直接插入 DOM）。"""

import logging
from html import escape

from ..models import Project, ShareLink
from ._pipeline import PIPELINE_NODES

logger = logging.getLogger(__name__)

_NODE_STATUS_CLASS = {
    "pending": "pending",
    "running": "running",
    "completed": "completed",
    "failed": "failed",
}


def _render_progress_html(project: Project) -> str:
    """渲染项目进度卡片 HTML 片段（基于流水线元数据，不依赖 CreationNode）。"""
    nodes_html_parts = []
    for meta in PIPELINE_NODES:
        nodes_html_parts.append(
            f'<div class="creation-node pending">'
            f'<span class="node-index">{meta["index"]}</span>'
            f'<span class="node-name">{escape(meta["name"])}</span>'
            f'<span class="node-status">待处理</span>'
            f"</div>"
        )

    status_text = project.get_status_display()
    return (
        f'<div class="creation-progress-card" data-project-id="{project.id}">'
        f'<div class="progress-header">'
        f'<span class="progress-status">{escape(status_text)}</span>'
        f'<span class="progress-percent">{project.progress_percent}%</span>'
        f'</div>'
        f'<div class="progress-bar"><div class="progress-fill" style="width:{project.progress_percent}%"></div></div>'
        f'<div class="progress-nodes">{"".join(nodes_html_parts)}</div>'
        f"</div>"
    )


def render_progress_html(project: Project) -> str:
    """生成进度卡片 HTML（不持久化）。"""
    return _render_progress_html(project)


def refresh_project_progress(project: Project, *, progress_percent: int | None = None) -> None:
    """刷新进度条与预渲染 HTML，供前端轮询增量展示。"""
    fields = ["updated_at"]
    if progress_percent is not None:
        project.progress_percent = min(100, max(0, int(progress_percent)))
        fields.append("progress_percent")
    project.rendered_progress_html = _render_progress_html(project)
    fields.append("rendered_progress_html")
    project.save(update_fields=fields)


def _render_result_html(project: Project) -> str:
    """渲染剧本结果 HTML（优先已落库的完整剧本，否则从 artifact 构建）。"""
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
    nodes_html = "".join(
        f'<li class="result-node-item">'
        f'<span class="idx">{meta["index"]}.</span> '
        f'<span class="name">{escape(meta["name"])}</span>'
        f"</li>"
        for meta in PIPELINE_NODES
    )
    return (
        f'<div class="creation-result-card" data-project-id="{project.id}">'
        f'<h3 class="result-title">{escape(title)}</h3>'
        f'<p class="result-meta">题材：{escape(project.theme)} · 集数：{project.episode_count} 集</p>'
        f'<ul class="result-nodes">{nodes_html}</ul>'
        f'<div class="result-watermark" style="opacity:.5;font-size:12px;">'
        f'仅供 {project.user_id} 查看 · 含数字水印，禁止二次传播'
        f"</div>"
        f"</div>"
    )


def _render_share_html(share: ShareLink) -> str:
    """渲染分享页 HTML（全链路可读预览 + 剧本节选，不含用户身份信息）。"""
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
        f'<h2>{escape(title)}</h2>'
        f'<p>题材：{escape(project.theme)} · 集数：{project.episode_count}</p>'
        f'<p style="opacity:.6;font-size:12px;">水印 {escape(wm)}</p>'
        f"</div>"
    )
