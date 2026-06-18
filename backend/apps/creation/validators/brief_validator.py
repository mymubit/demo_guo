# -*- coding: utf-8 -*-
"""
Python-native brief validation and enrichment.
直接从内存 dict 操作，无文件 I/O，无 Node 依赖。

对外接口：
    validate_brief(brief) -> ValidationResult
    enrich_brief(brief, project) -> dict
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .result import ValidationResult

# 必须字段定义（来自 sub-brief/index.js brief-enricher 逻辑）
_REQUIRED_FIELDS = {
    "theme": "题材（theme）",
    "coreIdea": "核心创意（coreIdea）",
    "episodeCount": "集数（episodeCount）",
}

_MIN_CORE_IDEA_CHARS = 10


def validate_brief(brief: Dict[str, Any]) -> ValidationResult:
    """
    校验 project_brief 必要字段。

    对应 JS: sub-brief/verify-creation.js
    """
    issues = []

    for field, label in _REQUIRED_FIELDS.items():
        val = brief.get(field)
        if not val:
            issues.append(f"缺少必填字段：{label}")

    core_idea = str(brief.get("coreIdea") or "").strip()
    if core_idea and len(core_idea) < _MIN_CORE_IDEA_CHARS:
        issues.append(f"coreIdea 过短（{len(core_idea)} 字），建议 ≥{_MIN_CORE_IDEA_CHARS} 字")

    ep_count = brief.get("episodeCount")
    if ep_count is not None:
        try:
            ep_count = int(ep_count)
            if ep_count <= 0 or ep_count > 500:
                issues.append(f"episodeCount 超出合理范围：{ep_count}（期望 1-500）")
        except (TypeError, ValueError):
            issues.append(f"episodeCount 格式错误：{ep_count}")

    if issues:
        return ValidationResult.fail(issues, sub_skill="sub-brief")
    return ValidationResult.ok(sub_skill="sub-brief")


def enrich_brief(brief: Dict[str, Any], project: Optional[Any] = None) -> Dict[str, Any]:
    """
    对 brief 做基础补全（对应 sub-brief --enrich 模式）。
    从 project 对象补全缺失的基础字段，不调用 LLM。
    """
    out = dict(brief)

    if project is not None:
        out.setdefault("theme", getattr(project, "theme", "") or "")
        out.setdefault("coreIdea", getattr(project, "core_idea", "") or "")
        out.setdefault("episodeCount", getattr(project, "episode_count", 30))
        out.setdefault("audience", getattr(project, "audience", "") or "")
        out.setdefault("formatVariant", getattr(project, "format_variant", "B") or "B")

    out.setdefault("agentEnriched", True)
    out.setdefault("seedEnriched", True)
    return out
