# -*- coding: utf-8 -*-
"""创作交付：pipeline 产物 → Markdown / HTML / ScriptWork / 展示 HTML。"""
from __future__ import annotations

import logging
import os
import re
import time
from html import escape
from typing import Any, Dict, Optional

from django.conf import settings
from django.utils import timezone

from .artifact_renderer import episode_scripts_to_legacy_scripts
from .artifact_service import get_artifact
from .fusion.fusion_pipeline import scripts_result_to_markdown
from .models import Project, ScriptWork

logger = logging.getLogger(__name__)


def resolve_scripts(project: Project, pipeline_result: Optional[dict] = None) -> dict:
    """从 pipeline 结果或 fusion artifact 解析 legacy scripts 结构。"""
    if pipeline_result:
        scripts = pipeline_result.get("scripts") or {}
        if scripts.get("episodes"):
            return scripts
        artifacts = pipeline_result.get("artifacts") or {}
        episode_scripts = artifacts.get("episode_scripts")
        if episode_scripts:
            return episode_scripts_to_legacy_scripts(episode_scripts)

    episode_scripts = get_artifact(project, "episode_scripts")
    if episode_scripts:
        return episode_scripts_to_legacy_scripts(episode_scripts)

    return {}


def build_script_markdown(project: Project, pipeline_result: Optional[dict] = None, *, watermark_token: str = "") -> str:
    scripts = resolve_scripts(project, pipeline_result)
    body = scripts_result_to_markdown(scripts) if scripts else ""

    title = project.title or f"{project.theme} · 剧本"
    header_lines = [
        f"# {title}",
        "",
        f"- 题材: {project.theme}",
        f"- 集数: {project.episode_count}",
        f"- 格式变体: {project.format_variant}",
        f"- 核心创意: {project.core_idea or '—'}",
    ]
    if project.overall_score is not None:
        header_lines.append(f"- 综合评分: {project.overall_score} 分 ({project.grade or '—'})")
    header_lines.append(f"- 生成时间: {project.completed_at or timezone.now()}")
    if watermark_token:
        header_lines.extend(["", f"> [数字水印] {watermark_token}"])

    if body.strip():
        return "\n".join(header_lines) + "\n\n---\n\n" + body.strip() + "\n"

    header_lines.extend(["", "> 剧本正文生成中或暂无 LLM 产出，请确认 worker 与 LLM 配置。"])
    return "\n".join(header_lines) + "\n"


def build_script_display_html(
    project: Project,
    pipeline_result: Optional[dict] = None,
    *,
    watermark_token: str = "",
    max_episodes: int = 20,
) -> str:
    scripts = resolve_scripts(project, pipeline_result)
    episodes = scripts.get("episodes") or []
    title = escape(project.title or f"{project.theme} · 剧本")

    parts = [
        f'<div class="creation-script-result" data-project-id="{project.id}">',
        f'<header class="script-result-header">',
        f'<h2 class="script-result-title">{title}</h2>',
        f'<p class="script-result-meta">题材：{escape(project.theme)} · '
        f'{project.episode_count} 集 · 格式 {escape(project.format_variant or "—")}</p>',
    ]
    if project.core_idea:
        parts.append(f'<p class="script-result-idea">{escape(project.core_idea)}</p>')
    if project.overall_score is not None:
        parts.append(
            f'<p class="script-result-score">综合评分 {project.overall_score} 分 '
            f'（{escape(project.grade or "—")}）</p>'
        )
    parts.append("</header>")

    if episodes:
        parts.append('<div class="script-episodes">')
        shown = episodes[:max_episodes]
        for ep in shown:
            ep_num = ep.get("episode") or "?"
            ep_title = escape(str(ep.get("title") or f"第{ep_num}集"))
            raw = ep.get("full_script_text") or ""
            body_html = _script_text_to_html(raw)
            parts.append(
                f'<section class="script-episode" id="ep-{ep_num}">'
                f'<h3 class="script-episode-title">第{ep_num}集 · {ep_title}</h3>'
                f'<div class="script-episode-body">{body_html}</div>'
                f"</section>"
            )
        if len(episodes) > max_episodes:
            parts.append(
                f'<p class="script-more-hint">共 {len(episodes)} 集，'
                f"此处展示前 {max_episodes} 集，完整内容请下载 Markdown。</p>"
            )
        parts.append("</div>")
    else:
        parts.append(
            '<div class="script-empty">'
            "<p>暂无剧本正文。请确认创作 worker 已启动且 LLM 配置有效。</p>"
            "</div>"
        )

    wm = watermark_token or f"p{str(project.id)[:8]}"
    parts.append(
        f'<footer class="script-watermark" style="opacity:.55;font-size:12px;margin-top:1.5rem;">'
        f"仅供授权用户查看 · 水印 {escape(wm)} · 禁止未授权传播"
        f"</footer></div>"
    )
    return "".join(parts)


def _script_text_to_html(text: str) -> str:
    """将剧本文本转为安全 HTML（保留段落与标题）。"""
    if not text:
        return "<p>（本集暂无正文）</p>"
    blocks = re.split(r"\n{2,}", text.strip())
    html_parts = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("#"):
            level = min(3, len(block) - len(block.lstrip("#")))
            content = escape(block.lstrip("#").strip())
            html_parts.append(f"<h{level + 2}>{content}</h{level + 2}>")
        else:
            lines = [escape(line) for line in block.split("\n")]
            html_parts.append(
                f'<div class="script-block" style="white-space:pre-wrap;line-height:1.7;">'
                f"{'<br/>'.join(lines)}</div>"
            )
    return "".join(html_parts) or f'<div style="white-space:pre-wrap">{escape(text)}</div>'


def build_download_html_document(project: Project, body_inner_html: str, *, watermark_token: str) -> str:
    title = escape(project.title or "script")
    return (
        f"<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>"
        f"<title>{title}</title>"
        f"<style>"
        f"body{{font-family:system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;color:#1a1a1a;}}"
        f".script-episode{{margin-bottom:2rem;padding-bottom:1rem;border-bottom:1px solid #eee;}}"
        f"h2{{color:#111;}} h3{{color:#333;margin-top:0;}}"
        f".script-watermark{{color:#888;font-size:12px;margin-top:2rem;}}"
        f".ws-section{{margin:2rem 0;padding-bottom:1.5rem;border-bottom:1px solid #eee;}}"
        f".ws-section-title{{color:#222;font-size:1.25rem;margin:0 0 1rem;}}"
        f".ws-section-body p{{line-height:1.75;margin:.6rem 0;}}"
        f".ws-section-body ul{{padding-left:1.25rem;margin:.5rem 0;}}"
        f"</style></head><body>"
        f"{body_inner_html}"
        f"<p class='script-watermark'>数字水印: {escape(watermark_token)}</p>"
        f"</body></html>"
    )


def persist_script_works(project: Project, pipeline_result: Optional[dict] = None) -> None:
    """写入 ScriptWork 文件并刷新 project.rendered_result_html。"""
    base_dir = str(
        getattr(settings, "CREATION_SCRIPT_DIR", None)
        or getattr(settings, "BASE_DIR", ".") / "tmp" / "creation_scripts"
    )
    project_dir = os.path.join(base_dir, project.id.hex)
    os.makedirs(project_dir, exist_ok=True)

    watermark_token = f"u{project.user_id}-p{project.id.hex[:8]}-t{int(time.time())}"
    base_title = (project.title or "script").replace("/", "_").replace("\\", "_")

    markdown = build_script_markdown(project, pipeline_result, watermark_token=watermark_token)
    display_html = build_script_display_html(project, pipeline_result, watermark_token=watermark_token)
    download_html = build_download_html_document(project, display_html, watermark_token=watermark_token)

    files = {
        ScriptWork.FORMAT_MARKDOWN: (markdown.encode("utf-8"), f"{base_title}_{project.id.hex[:8]}.md"),
        ScriptWork.FORMAT_HTML: (download_html.encode("utf-8"), f"{base_title}_{project.id.hex[:8]}.html"),
    }

    for fmt, (content_bytes, file_name) in files.items():
        full_path = os.path.join(project_dir, file_name)
        try:
            with open(full_path, "wb") as f:
                f.write(content_bytes)
        except OSError as exc:
            logger.warning("[Creation] 写入 script work 文件失败 fmt=%s: %s", fmt, exc)
            continue

        ScriptWork.objects.update_or_create(
            project=project,
            file_format=fmt,
            defaults={
                "storage_path": full_path,
                "file_name": file_name,
                "size_bytes": len(content_bytes),
                "watermark_token": f"{watermark_token}-{fmt}",
            },
        )

    project.rendered_result_html = display_html
    project.save(update_fields=["rendered_result_html", "updated_at"])
    logger.info(
        "[Creation] script works persisted project=%s md_bytes=%s episodes=%s",
        project.id,
        len(markdown.encode("utf-8")),
        len(resolve_scripts(project, pipeline_result).get("episodes") or []),
    )
