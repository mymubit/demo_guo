# -*- coding: utf-8 -*-
"""产物实质门禁（substance gates）：按 artifact_key 注册，统一由 ingest 调用。

角色 / SKILL 不直接调用本模块；仅 runtime 落库管线使用。
阈值优先从 drama-skills 约束 YAML 读取（见 quality-scoring.yaml）。
"""
from __future__ import annotations

from typing import Any, Callable

from apps.core.exceptions import SCHEMA_VALIDATION_FAILED, BusinessException
from apps.drama.services.artifact_normalize import (
    compliance_report_too_thin,
    project_brief_too_thin,
    quality_report_evidence_too_sparse,
)

GateChecker = Callable[[dict[str, Any]], bool]

_GATES: dict[str, tuple[GateChecker, str]] = {}


def register_gate(artifact_key: str, checker: GateChecker, message: str) -> None:
    """注册实质门禁；checker 返回 True 表示过薄/不合格。"""
    _GATES[artifact_key] = (checker, message)


def run_substance_gate(artifact_key: str, payload: dict[str, Any]) -> None:
    """执行已注册门禁；不通过则抛 SCHEMA_VALIDATION_FAILED。未知产物 no-op。"""
    entry = _GATES.get(artifact_key)
    if not entry:
        return
    checker, message = entry
    if checker(payload):
        raise BusinessException(
            SCHEMA_VALIDATION_FAILED,
            message,
            http_status=422,
        )


def registered_gate_keys() -> list[str]:
    return sorted(_GATES.keys())


# 内置门禁（模块 import 时注册）
register_gate(
    "quality_report",
    quality_report_evidence_too_sparse,
    "十维评分缺少有效 evidence 或总评过短（禁止空壳分数报告）。"
    "每个维度至少需要若干条可读证据（含集数/场景/台词等）；"
    "并须提供 verdict_detail 总评。篇幅目标见 quality-scoring.yaml#output_length。",
)
register_gate(
    "compliance_report",
    compliance_report_too_thin,
    "合规报告缺少具体阻断/风险描述（title+description）。禁止空标题或空话。",
)
register_gate(
    "project_brief",
    project_brief_too_thin,
    "选题简报过空：竞品须为真实作品名（禁止「竞品1」），每条含可执行的借鉴/避雷；"
    "市场机会与差异化须具体到情节/人设切口（禁止口号）；首集钩子与付费方向须可感知动作。"
    "字段口径见 modules/market-radar.md。",
)
