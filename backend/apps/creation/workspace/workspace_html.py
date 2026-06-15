# -*- coding: utf-8 -*-
"""工作台 Markdown → HTML（导出与分享可读预览）。"""
from __future__ import annotations

import re
from html import escape
from typing import Optional

from ..artifact_service import get_artifact
from ..models import Project
from ..script_delivery import build_script_display_html, resolve_scripts
from .workspace_markdown import build_workspace_markdown

_NODE_SECTIONS = (
    (1, "立项简报"),
    (2, "结构与世界观"),
    (3, "人物圣经"),
    (4, "分集大纲与创作规划"),
    (5, "剧集剧本"),
)


def _inline_markdown(text: str) -> str:
    safe = escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)


def markdown_to_html(md: str) -> str:
    """轻量 Markdown → HTML（标题、列表、粗体、段落）。"""
    if not (md or "").strip():
        return ""

    lines = md.split("\n")
    parts: list[str] = []
    in_ul = False

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            parts.append("</ul>")
            in_ul = False

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            close_ul()
            continue

        if stripped.startswith("### "):
            close_ul()
            parts.append(f"<h4>{_inline_markdown(stripped[4:])}</h4>")
        elif stripped.startswith("## "):
            close_ul()
            parts.append(f"<h3>{_inline_markdown(stripped[3:])}</h3>")
        elif stripped.startswith("# "):
            close_ul()
            parts.append(f"<h2>{_inline_markdown(stripped[2:])}</h2>")
        elif stripped.startswith("- "):
            if not in_ul:
                parts.append("<ul>")
                in_ul = True
            parts.append(f"<li>{_inline_markdown(stripped[2:])}</li>")
        else:
            close_ul()
            parts.append(f"<p>{_inline_markdown(stripped)}</p>")

    close_ul()
    return "".join(parts)


def _truncate_markdown(md: str, max_chars: int) -> str:
    if len(md) <= max_chars:
        return md
    return md[:max_chars].rstrip() + "\n\n…（分享预览已截断，完整内容请下载）"


def build_workspace_html_body(
    project: Project,
    *,
    watermark_token: str = "",
    max_section_chars: Optional[int] = None,
    max_script_episodes: int = 20,
    include_scripts: bool = True,
) -> str:
    """各节点可读 HTML 正文（不含 html/head 外壳）。"""
    title = escape(
        project.title
        or (get_artifact(project, "project_brief") or {}).get("workingTitle")
        or project.theme
        or "未命名作品"
    )
    parts = [
        f'<div class="workspace-readable" data-project-id="{project.id}">',
        f'<header class="ws-header">',
        f'<h1 class="ws-title">{title}</h1>',
        f'<p class="ws-meta">题材：{escape(project.theme)} · {project.episode_count} 集 · '
        f'格式 {escape(project.format_variant or "—")}</p>',
        "</header>",
    ]

    script_via_display = include_scripts and bool(resolve_scripts(project).get("episodes"))

    for node_idx, label in _NODE_SECTIONS:
        if node_idx == 5 and script_via_display:
            continue
        if node_idx == 5 and not include_scripts:
            continue
        md = build_workspace_markdown(project, node_idx)
        if not md.strip():
            continue
        if max_section_chars:
            md = _truncate_markdown(md, max_section_chars)
        body = markdown_to_html(md)
        if not body:
            continue
        parts.append(
            f'<section class="ws-section ws-node-{node_idx}">'
            f'<h2 class="ws-section-title">{escape(label)}</h2>'
            f'<div class="ws-section-body">{body}</div>'
            f"</section>"
        )

    scripts = resolve_scripts(project)
    if script_via_display and scripts.get("episodes"):
        script_inner = build_script_display_html(
            project,
            watermark_token=watermark_token,
            max_episodes=max_script_episodes,
        )
        if script_inner and "script-episodes" in script_inner:
            parts.append(
                '<section class="ws-section ws-scripts">'
                '<h2 class="ws-section-title">剧本分集预览</h2>'
                f"{script_inner}"
                "</section>"
            )

    wm = watermark_token or f"p{str(project.id)[:8]}"
    parts.append(
        f'<footer class="ws-watermark" style="opacity:.55;font-size:12px;margin-top:2rem;">'
        f"仅供授权查看 · 水印 {escape(wm)}"
        f"</footer></div>"
    )
    return "".join(parts)


def wrap_html_document(project: Project, body_inner_html: str, *, watermark_token: str = "") -> str:
    from ..script_delivery import build_download_html_document

    return build_download_html_document(
        project,
        body_inner_html,
        watermark_token=watermark_token or f"p{str(project.id)[:8]}",
    )


def build_workspace_share_html(project: Project, *, watermark_token: str) -> str:
    """分享页：各节点摘要 + 前若干集剧本。"""
    return build_workspace_html_body(
        project,
        watermark_token=watermark_token,
        max_section_chars=5000,
        max_script_episodes=5,
        include_scripts=True,
    )
