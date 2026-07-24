# -*- coding: utf-8 -*-
"""V3 知识库：只读扫描 drama-skills/knowledge/**。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from django.conf import settings

from apps.core.exceptions import NOT_FOUND, VALIDATION_ERROR, BusinessException

_EXCERPT_MAX = 200
_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def _knowledge_root() -> Path:
    return (Path(settings.DRAMA_SKILLS_ROOT) / "knowledge").resolve()


def _section_of(rel_path: str) -> str:
    parts = rel_path.replace("\\", "/").split("/")
    if len(parts) > 1:
        return parts[0]
    return ""


def _title_and_excerpt(text: str, *, fallback: str) -> tuple[str, str]:
    title = fallback
    match = _HEADING_RE.search(text)
    if match:
        title = match.group(1).strip() or fallback
    # 摘录：跳过标题行后的首段非空文本
    body = text
    if match:
        body = text[match.end() :]
    excerpt = ""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(">"):
            continue
        excerpt = stripped
        break
    if not excerpt:
        excerpt = " ".join(text.split())
    if len(excerpt) > _EXCERPT_MAX:
        excerpt = excerpt[:_EXCERPT_MAX].rstrip() + "…"
    return title, excerpt


def _iter_md_files() -> list[tuple[str, Path]]:
    root = _knowledge_root()
    if not root.is_dir():
        return []
    items: list[tuple[str, Path]] = []
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        items.append((rel, path))
    return items


def _resolve_safe(rel_path: str) -> Path:
    raw = (rel_path or "").strip().replace("\\", "/")
    if not raw:
        raise BusinessException(
            VALIDATION_ERROR, "缺少 path 参数", http_status=400
        )
    if raw.startswith("/") or raw.startswith("~") or re.match(r"^[A-Za-z]:", raw):
        raise BusinessException(
            VALIDATION_ERROR, "非法 path：禁止绝对路径", http_status=400
        )
    parts = [p for p in raw.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise BusinessException(
            VALIDATION_ERROR, "非法 path：禁止目录穿越", http_status=400
        )
    if not parts or not parts[-1].endswith(".md"):
        raise BusinessException(
            VALIDATION_ERROR, "path 须为相对 .md 文件", http_status=400
        )
    root = _knowledge_root()
    candidate = (root.joinpath(*parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise BusinessException(
            VALIDATION_ERROR, "非法 path：越出知识库根目录", http_status=400
        ) from exc
    return candidate


def list_docs(
    q: str | None = None, section: str | None = None
) -> list[dict[str, Any]]:
    """列出知识文档；可选 q（path/title/excerpt）与 section（首路径段）过滤。"""
    query = (q or "").strip().lower()
    section_filter = (section or "").strip()
    results: list[dict[str, Any]] = []
    for rel, path in _iter_md_files():
        doc_section = _section_of(rel)
        if section_filter and doc_section != section_filter:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        title, excerpt = _title_and_excerpt(text, fallback=Path(rel).stem)
        item = {
            "path": rel,
            "title": title,
            "section": doc_section,
            "excerpt": excerpt,
        }
        if query:
            haystack = f"{rel}\n{title}\n{excerpt}".lower()
            if query not in haystack:
                continue
        results.append(item)
    return results


def read_doc(path: str) -> dict[str, Any]:
    """按相对 path 读取 markdown；防穿越。"""
    target = _resolve_safe(path)
    if not target.is_file():
        raise BusinessException(NOT_FOUND, "知识文档不存在", http_status=404)
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise BusinessException(
            NOT_FOUND, "知识文档不可读", http_status=404
        ) from exc
    rel = target.relative_to(_knowledge_root()).as_posix()
    title, _ = _title_and_excerpt(text, fallback=Path(rel).stem)
    return {"path": rel, "title": title, "content": text}
