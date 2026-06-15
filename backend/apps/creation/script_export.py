# -*- coding: utf-8 -*-
"""作品 Markdown / ZIP 导出（聚合 fusion artifact + 工作台可读 Markdown）。"""
from __future__ import annotations

import io
import zipfile
from typing import Any, Dict, List, Tuple

from apps.creation.artifact_service import get_artifact, list_artifact_keys
from apps.creation.models import Project
from apps.creation.workspace.workspace_html import build_workspace_html_body, wrap_html_document
from apps.creation.workspace.workspace_markdown import build_workspace_markdown

_EXPORTABLE_KEYS = frozenset(
    {
        "project_brief",
        "structure_plan",
        "character_bible",
        "series_outline",
        "episode_scripts",
    }
)

_NODE_EXPORT_FILES: Tuple[Tuple[int, str], ...] = (
    (1, "01-project-brief.md"),
    (2, "02-structure-plan.md"),
    (3, "03-character-bible.md"),
    (4, "04-series-outline.md"),
    (5, "05-episode-scripts.md"),
)


def project_has_exportable_content(project: Project) -> bool:
    keys = set(list_artifact_keys(project))
    return bool(keys & _EXPORTABLE_KEYS)


def _episode_lines(episode_scripts: dict) -> List[str]:
    lines: List[str] = []
    for ep in episode_scripts.get("episodes") or []:
        num = ep.get("episodeNumber") or ep.get("episode") or "?"
        title = ep.get("title") or ""
        lines.append(f"\n## 第{num}集 {title}\n")
        body = (
            ep.get("scriptMarkdown")
            or ep.get("full_script_text")
            or ep.get("scriptText")
            or ep.get("content")
            or ""
        )
        if body:
            lines.append(str(body).strip())
            lines.append("")
    return lines


def build_work_markdown(project: Project) -> str:
    """全量合集 Markdown（优先 workspace_markdown 各节点，剧本段保留正文）。"""
    parts: List[str] = []
    title = (
        (get_artifact(project, "project_brief") or {}).get("workingTitle")
        or project.title
        or project.theme
        or "未命名作品"
    )
    parts.extend(
        [
            f"# {title}",
            "",
            f"- 题材：{project.theme}",
            f"- 集数：{project.episode_count}",
            f"- 平台：{project.target_platform or '—'}",
            f"- 格式：{project.format_variant}",
            "",
        ]
    )

    for node_idx, _fname in _NODE_EXPORT_FILES:
        md = build_workspace_markdown(project, node_idx)
        if md.strip():
            parts.append(md)
            parts.append("")

    scripts = get_artifact(project, "episode_scripts") or {}
    if scripts.get("episodes") and not build_workspace_markdown(project, 5).strip():
        parts.extend(["## 剧本正文", ""])
        parts.extend(_episode_lines(scripts))

    score = get_artifact(project, "script_score_report") or {}
    overall = score.get("overallScore") or project.overall_score
    grade = score.get("grade") or project.grade
    if overall is not None or grade:
        parts.extend(["## 质量评分", "", f"- 综合分：{overall or '—'}", f"- 等级：{grade or '—'}", ""])

    return "\n".join(parts).strip() + "\n"


def build_work_html(project: Project, *, watermark_token: str = "") -> str:
    body = build_workspace_html_body(
        project,
        watermark_token=watermark_token,
        max_section_chars=None,
        max_script_episodes=9999,
        include_scripts=True,
    )
    return wrap_html_document(project, body, watermark_token=watermark_token)


def build_work_zip(project: Project) -> bytes:
    """ZIP 打包：各节点可读 Markdown + 全量合集。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for node_idx, filename in _NODE_EXPORT_FILES:
            md = build_workspace_markdown(project, node_idx)
            if md.strip():
                zf.writestr(filename, md.encode("utf-8"))
        full_md = build_work_markdown(project)
        if full_md.strip():
            zf.writestr("00-full-work.md", full_md.encode("utf-8"))
        full_html = build_work_html(project)
        if full_html.strip():
            zf.writestr("00-full-work.html", full_html.encode("utf-8"))
    return buf.getvalue()


def export_work(project: Project, fmt: str = "md") -> Dict[str, Any]:
    fmt = (fmt or "md").lower()
    safe_title = (project.title or project.theme or "script").replace(" ", "_").replace("/", "_")[:40]

    if fmt == "zip":
        content = build_work_zip(project)
        if not content:
            raise ValueError("暂无可导出内容")
        return {
            "format": "zip",
            "filename": f"{safe_title}_package.zip",
            "content": content,
            "content_type": "application/zip",
        }

    if fmt in {"md", "markdown"}:
        content = build_work_markdown(project)
        if not content.strip():
            raise ValueError("暂无可导出内容")
        return {
            "format": "md",
            "filename": f"{safe_title}.md",
            "content": content,
            "content_type": "text/markdown; charset=utf-8",
        }

    if fmt == "html":
        content = build_work_html(project)
        if not content.strip():
            raise ValueError("暂无可导出内容")
        return {
            "format": "html",
            "filename": f"{safe_title}.html",
            "content": content,
            "content_type": "text/html; charset=utf-8",
        }

    raise ValueError(f"暂不支持 format={fmt}")
