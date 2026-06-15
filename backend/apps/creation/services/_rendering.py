"""HTML 预渲染工具（前端直接插入 DOM）。"""

import logging
from html import escape

from ..models import CreationNode, Project, ShareLink
from ._pipeline import PIPELINE_NODES

logger = logging.getLogger(__name__)


def _render_progress_html(project: Project) -> str:
    """渲染项目进度卡片 HTML 片段。"""
    nodes_html_parts = []
    nodes = list(project.nodes.all().order_by("node_index"))

    if not nodes:
        for meta in PIPELINE_NODES:
            nodes_html_parts.append(
                f'<div class="creation-node pending">'
                f'<span class="node-index">{meta["index"]}</span>'
                f'<span class="node-name">{escape(meta["name"])}</span>'
                f'<span class="node-status">待处理</span>'
                f"</div>"
            )
    else:
        for node in nodes:
            status_class = {
                CreationNode.STATUS_PENDING: "pending",
                CreationNode.STATUS_RUNNING: "running",
                CreationNode.STATUS_COMPLETED: "completed",
                CreationNode.STATUS_FAILED: "failed",
            }.get(node.status, "pending")
            status_text = node.get_status_display()
            summary = escape(node.summary_text or "")
            nodes_html_parts.append(
                f'<div class="creation-node {status_class}">'
                f'<span class="node-index">{node.node_index}</span>'
                f'<span class="node-name">{escape(node.node_name)}</span>'
                f'<span class="node-status">{status_text}</span>'
                f'<div class="node-summary">{summary}</div>'
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


def refresh_project_progress(project: Project, *, progress_percent: int | None = None) -> None:
    """编排器/融合流水线中途刷新进度条与预渲染 HTML，供前端轮询增量展示。"""
    fields = ["updated_at"]
    if progress_percent is not None:
        project.progress_percent = min(99, int(progress_percent))
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
        f'<span class="idx">{n.node_index}.</span> '
        f'<span class="name">{escape(n.node_name)}</span>'
        f'<span class="status">{escape(n.get_status_display())}</span>'
        f"</li>"
        for n in project.nodes.all().order_by("node_index")
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
            html = build_script_display_html(
                project,
                watermark_token=wm,
                max_episodes=5,
            )
            if share.custom_title:
                html = html.replace(
                    escape(project.title or ""),
                    escape(share.custom_title),
                    1,
                )
            return html
    except Exception as exc:  # noqa: BLE001
        logger.warning("[Creation] 分享页剧本 HTML 构建失败: %s", exc)

    return (
        f'<div class="share-result-card" data-share-token="{share.token}">'
        f'<h3 class="share-title">{escape(title)}</h3>'
        f'<p class="share-meta">题材：{escape(project.theme)} · 集数：{project.episode_count} 集</p>'
        f'<div class="share-body">'
        f'<p>此内容为分享视图，含分享者不可见的数字水印以防止恶意传播。</p>'
        f"</div>"
        f'<div class="share-watermark" style="opacity:.45;font-size:12px;">'
        f'分享 token: {share.token[:8]}… · 仅供查看'
        f"</div>"
        f"</div>"
    )
