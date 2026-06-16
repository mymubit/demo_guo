# -*- coding: utf-8 -*-
"""SkillInvoker — 统一技能调用协议

提供标准化的技能调用入口，替代各 Engine 内部散落的直接 LLM 调用：
  - 标准入参：SkillInvokeRequest
  - 标准出参：SkillInvokeResult
  - 统一错误码、超时控制、重试策略、配额扣减

当前阶段（P0→P1 过渡）：
  - system_hint 优先读取 AgentSkillDefinition.system_hint（DB），
    fallback 到代码中的 _SUB_SKILL_SYSTEM_HINTS（90天兼容窗口）
  - LLM 调用复用现有 LlmService，不做重复封装
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from apps.skill.llm.chat import LlmService, LlmServiceError
from .router import SkillRouter

logger = logging.getLogger(__name__)

# 错误码常量
ERR_SKILL_NOT_FOUND  = "ERR_SKILL_NOT_FOUND"
ERR_LLM_FAILED       = "ERR_LLM_FAILED"
ERR_TIMEOUT          = "ERR_TIMEOUT"
ERR_QUOTA_EXCEEDED   = "ERR_QUOTA_EXCEEDED"
ERR_SCHEMA_INVALID   = "ERR_SCHEMA_INVALID"


@dataclass
class SkillInvokeRequest:
    """标准技能调用入参"""
    skill_id:         str
    payload:          Dict[str, Any] = field(default_factory=dict)
    project_id:       str = ""
    execution_run_id: str = ""
    version:          str = "latest"
    timeout:          Optional[int] = None  # None 则使用 DB 配置值
    system_hint_override: Optional[str] = None  # 临时覆盖 system_hint，用于 A/B 测试


@dataclass
class SkillInvokeResult:
    """标准技能调用出参"""
    skill_id:    str
    version:     str
    status:      str    # success / failed / timeout
    output:      Dict[str, Any] = field(default_factory=dict)
    error_code:  str = ""
    error_message: str = ""
    duration_ms: int = 0
    token_used:  int = 0
    quota_cost:  float = 0.0

    @property
    def is_success(self) -> bool:
        return self.status == "success"


class SkillInvoker:
    """统一技能调用器

    使用示例：
        req = SkillInvokeRequest(
            skill_id="brief.character_extract",
            payload={"projectBrief": {...}},
            project_id=str(project.id),
        )
        result = SkillInvoker.invoke(req, agent_id="brief")
    """

    @staticmethod
    def invoke(
        req: SkillInvokeRequest,
        *,
        agent_id: str = "",
        messages: Optional[list] = None,
    ) -> SkillInvokeResult:
        """执行技能调用

        Args:
            req: 标准入参
            agent_id: 所属 Agent，用于 LLM 路由选择
            messages: 若已构造好消息列表可直接传入，否则从 payload 构造
        """
        start_ms = int(time.time() * 1000)

        # 1. 路由获取技能定义
        skill_def = SkillRouter.resolve(
            req.skill_id,
            project_id=req.project_id,
            version=req.version,
        )
        resolved_version = skill_def.version if skill_def else "unknown"

        # 2. 获取 system_hint（DB 优先，代码 fallback）
        system_hint = req.system_hint_override
        if not system_hint and skill_def:
            system_hint = skill_def.system_hint
        if not system_hint:
            system_hint = SkillInvoker._code_fallback_hint(req.skill_id)

        # 3. 执行 LLM 调用
        timeout_seconds = req.timeout
        if timeout_seconds is None and skill_def:
            timeout_seconds = skill_def.timeout_seconds
        if timeout_seconds is None:
            timeout_seconds = 60

        try:
            llm = LlmService()
            if messages is None:
                messages = SkillInvoker._build_messages(req.payload, system_hint)

            raw_output, usage = llm.chat(
                messages=messages,
                agent_id=agent_id or req.skill_id,
                timeout=timeout_seconds,
            )

            duration_ms = int(time.time() * 1000) - start_ms
            token_used  = getattr(usage, "total_tokens", 0) if usage else 0
            quota_cost  = float(skill_def.quota_cost) if skill_def else 0.0

            return SkillInvokeResult(
                skill_id=req.skill_id,
                version=resolved_version,
                status="success",
                output={"raw": raw_output},
                duration_ms=duration_ms,
                token_used=token_used,
                quota_cost=quota_cost,
            )

        except LlmServiceError as exc:
            duration_ms = int(time.time() * 1000) - start_ms
            logger.warning("技能 %r LLM 调用失败: %s", req.skill_id, exc)
            return SkillInvokeResult(
                skill_id=req.skill_id,
                version=resolved_version,
                status="failed",
                error_code=ERR_LLM_FAILED,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

        except Exception as exc:  # noqa: BLE001
            duration_ms = int(time.time() * 1000) - start_ms
            logger.exception("技能 %r 意外异常: %s", req.skill_id, exc)
            return SkillInvokeResult(
                skill_id=req.skill_id,
                version=resolved_version,
                status="failed",
                error_code=ERR_LLM_FAILED,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

    @staticmethod
    def _build_messages(payload: Dict[str, Any], system_hint: str) -> list:
        """从 payload 构造消息列表（最简形式，复杂 prompt 由 Engine 自行构造后传入）"""
        import json
        return [
            {"role": "system", "content": system_hint or "你是一位短剧剧本创作专家。"},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]

    @staticmethod
    def _code_fallback_hint(skill_id: str) -> str:
        """90 天兼容窗口：从代码硬编码 fallback（迁移完成后删除）"""
        try:
            from apps.creation.orchestration.sub_skill_orchestrator import _SUB_SKILL_SYSTEM_HINTS
            return _SUB_SKILL_SYSTEM_HINTS.get(skill_id, "")
        except ImportError:
            return ""

    @staticmethod
    def get_system_hint(skill_id: str, *, project_id: str = "") -> str:
        """仅获取 system_hint，不执行 LLM 调用（供 Engine 构造自定义 prompt 时使用）"""
        skill_def = SkillRouter.resolve(skill_id, project_id=project_id)
        if skill_def and skill_def.system_hint:
            return skill_def.system_hint
        return SkillInvoker._code_fallback_hint(skill_id)
