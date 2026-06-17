# -*- coding: utf-8 -*-
"""创作校验支持函数（原 orchestration/verify_creation_support.py）。

新引擎全量上线后，这些纯函数工具被业务代码 / 测试继续使用。
迁移到 apps.creation.workspace.verify_support 命名空间，避免与旧模块耦合。
"""
from __future__ import annotations

from typing import Any, Dict, List


def episode_scripts_to_verify_markdown(scripts: Dict[str, Any]) -> str:
    """将 episode_scripts 序列化为 verify 用 markdown。

    用于创作校验 / 质检报告 / 提示工程上下文。
    """
    if not isinstance(scripts, dict):
        scripts = {}
    eps = scripts.get("episodes") or []
    if not isinstance(eps, list):
        eps = []
    lines: List[str] = ["# 剧本正文校验视图\n"]
    for ep in eps:
        if not isinstance(ep, dict):
            continue
        num = ep.get("episodeNumber") or ep.get("episode") or "?"
        title = ep.get("title") or ""
        text = ep.get("full_script_text") or ep.get("script_text") or ep.get("content") or ""
        lines.append(f"## 第{num}集 {title}".rstrip())
        if text:
            lines.append(str(text).strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
