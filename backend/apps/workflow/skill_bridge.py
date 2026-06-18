# -*- coding: utf-8 -*-
"""Bridge WorkflowEngine nodes to ScriptForge SkillInvoker/runtime functions."""
from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from apps.workflow.runtime_contract import (
    RuntimeBudgetExceeded,
    enforce_input_budget,
    project_seed_context,
)

logger = logging.getLogger(__name__)


# =========================================================
# SkillBridgeResult 鈥?鑺傜偣鎵ц缁撴灉鐨勭粺涓€鏍煎紡
# =========================================================
@dataclass
class SkillBridgeResult:
    """Normalized result returned by SkillBridge."""
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    errors: list = field(default_factory=list)
    coin_cost: int = 0
    llm_token_in: int = 0
    llm_token_out: int = 0
    duration_ms: int = 0
    run_ids: list = field(default_factory=list)   # 瀹¤鐢紙AgentExecutionRun IDs锛?
    retryable: bool = False                       # 鍛婄煡寮曟搸鏄惁鍙噸璇?


# =========================================================
# SkillBridge 鈥?缁熶竴鍏ュ彛
# =========================================================
class SkillBridge:
    """Bridge one workflow node to runtime execution."""

    def __init__(self, project: Any, node_config: Any, context: Dict[str, Any]):
        self.project = project
        self.node_config = node_config
        self.context = context
        self._invoker = None

    # 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    # 缁熶竴鍏ュ彛锛堝紩鎿庡敮涓€璋冪敤鐐癸級
    # 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    def run(self, dry_run: bool = False) -> SkillBridgeResult:
        """Run a node skill and return a normalized result."""
        skill_id = getattr(self.node_config, "skill_id", None) or ""
        runner_path = getattr(self.node_config, "runner_path", None) or ""
        node_id = getattr(self.node_config, "node_id", "?")
        extra_config = getattr(self.node_config, "extra_config", None) or {}
        coin_cost = getattr(self.node_config, "coin_cost", 0) or 0

        if dry_run:
            return SkillBridgeResult(
                success=True,
                output={"content": f"(dry-run output for {node_id})"},
                coin_cost=coin_cost,
                duration_ms=0,
            )

        # 璺敱 A: skill_id 鈫?LLM 鍨嬫妧鑳斤紙閫氳繃 SkillInvoker锛?
        if skill_id:
            return self._run_via_skill_invoker(
                skill_id=skill_id,
                node_id=node_id,
                extra_config=extra_config,
                coin_cost=coin_cost,
            )

        # 璺敱 B: runner_path 鈫?鐩存帴 Python 鍑芥暟
        if runner_path:
            return self._run_via_runner_path(
                runner_path=runner_path,
                node_id=node_id,
                extra_config=extra_config,
                coin_cost=coin_cost,
            )

        # 鍏滃簳锛氫袱鑰呴兘娌℃湁
        logger.error("[SkillBridge] 鑺傜偣 %s 鏃㈡棤 skill_id 涔熸棤 runner_path", node_id)
        return SkillBridgeResult(
            success=False,
            errors=[f"鑺傜偣 {node_id} 鏈敞鍐?skill_id 鎴?runner_path"],
            retryable=False,
        )

    # 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    # 璺敱 A: SkillInvoker锛圠LM 鍨嬫妧鑳斤級
    # 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    def _run_via_skill_invoker(
        self,
        skill_id: str,
        node_id: str,
        extra_config: Dict[str, Any],
        coin_cost: int,
    ) -> SkillBridgeResult:
        """Invoke an LLM-backed skill through SkillInvoker."""
        import time
        t0 = time.time()

        try:
            from apps.skill.skills.invoker import get_skill_invoker

            invoker = get_skill_invoker()

            # 鏋勫缓 payload锛氫粠 context 涓彁鍙栫浉鍏充笂涓嬫枃 + extra_config
            payload = self._build_skill_payload(skill_id, extra_config)
            input_snapshot = enforce_input_budget(payload, self.node_config)

            result = invoker.invoke(
                skill_id=skill_id,
                payload=payload,
                project_id=str(self.project.id) if self.project else None,
                user_id=self._extract_user_id(),
            )

            duration_ms = int((time.time() - t0) * 1000)
            llm_in = result.meta.get("llm_token_in", 0)
            llm_out = result.meta.get("llm_token_out", 0)
            actual_cost = coin_cost
            output = dict(result.data or {})
            if result.success:
                artifact_key = self._persist_creation_skill_output(skill_id, output)
                if artifact_key:
                    output["artifact_key"] = artifact_key
            output.setdefault("skill_id", skill_id)
            output.setdefault("trace_id", result.trace_id)
            output.setdefault("input_snapshot", input_snapshot)

            return SkillBridgeResult(
                success=result.success,
                output=output,
                errors=[result.error.get("message", "")] if result.error else [],
                coin_cost=actual_cost,
                llm_token_in=llm_in,
                llm_token_out=llm_out,
                duration_ms=duration_ms,
                run_ids=[result.meta.get("trace_id", "")],
                retryable=(
                    result.error.get("code") not in (
                        _get_code("SKILL_NOT_FOUND"),
                        _get_code("SKILL_DISABLED"),
                        _get_code("SKILL_LIFECYCLE_ERROR"),
                        _get_code("SKILL_VALIDATION_ERROR"),
                        _get_code("SKILL_QUOTA_EXCEEDED"),
                    )
                    if result.error else True
                ),
            )

        except RuntimeBudgetExceeded as exc:
            duration_ms = int((time.time() - t0) * 1000)
            return SkillBridgeResult(
                success=False,
                errors=[str(exc)],
                coin_cost=0,
                duration_ms=duration_ms,
                retryable=False,
            )
        except Exception as exc:
            duration_ms = int((time.time() - t0) * 1000)
            logger.exception("[SkillBridge] SkillInvoker 璋冪敤澶辫触 skill=%s", skill_id)
            return SkillBridgeResult(
                success=False,
                errors=[f"{type(exc).__name__}:{exc}"],
                coin_cost=coin_cost,
                duration_ms=duration_ms,
                retryable=True,
            )

    def _build_skill_payload(
        self,
        skill_id: str,
        extra_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build a skill payload from project/context data."""
        ctx = self.context or {}

        if skill_id.startswith("creation.") and self.project is not None:
            try:
                from apps.creation.skill_invoke_payload import build_creation_skill_invoke_payload

                payload = build_creation_skill_invoke_payload(self.project, skill_id)
                payload.update(dict(extra_config or {}))
                return payload
            except Exception as exc:  # noqa: BLE001
                logger.warning("[SkillBridge] creation payload builder fallback skill=%s: %s", skill_id, exc)

        # 鍩虹 payload锛氫粠 extra_config 鍚堝苟
        payload = dict(extra_config)
        payload.update({k: v for k, v in project_seed_context(self.project).items() if v not in (None, "")})

        for key in ("theme", "topic", "format", "duration", "episode_count", "core_idea"):
            if key in ctx:
                payload[key] = ctx[key]

        # 娉ㄥ叆鍓嶄竴鑺傜偣杈撳嚭
        prev_output = ctx.get("prev", {})
        if prev_output:
            payload["prev_output"] = prev_output

        # 娉ㄥ叆宸插畬鎴愮殑鑺傜偣杈撳嚭
        nodes_output = ctx.get("nodes", {})
        if nodes_output:
            payload["completed_nodes"] = nodes_output

        return payload

    def _persist_creation_skill_output(self, skill_id: str, skill_data: Dict[str, Any]) -> str:
        if not skill_id.startswith("creation.") or self.project is None:
            return ""
        try:
            from apps.creation.skill_invoke_payload import apply_creation_skill_output

            node_index = int(
                getattr(self.node_config, "website_index", None)
                or getattr(self.node_config, "chain_order", 0)
                or 0
            )
            if node_index <= 0:
                return ""
            return apply_creation_skill_output(self.project, node_index, skill_id, skill_data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[SkillBridge] persist creation output skipped skill=%s: %s", skill_id, exc)
            return ""

    def _extract_user_id(self) -> Optional[int]:
        """Extract project user id."""
        try:
            return int(getattr(self.project, "user_id", None)
                      or getattr(self.project, "user", None))
        except Exception:
            return None

    # 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    # 璺敱 B: Python 鍑芥暟锛堝厹搴曞吋瀹瑰眰锛?
    # 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    def _run_via_runner_path(
        self,
        runner_path: str,
        node_id: str,
        extra_config: Dict[str, Any],
        coin_cost: int,
    ) -> SkillBridgeResult:
        """Run a Python function runner path."""
        import time
        t0 = time.time()

        try:
            # 閫氱敤璺敱锛氱洿鎺?import + 璋冪敤 Python 鍑芥暟
            module_name, func_name = runner_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            func = getattr(module, func_name, None)
            if func is None:
                raise AttributeError(f"妯″潡 {module_name} 涓病鏈?{func_name}")

            # 鍏煎澶氱鏃х鍚?
            import inspect
            sig = inspect.signature(func)
            if len(sig.parameters) >= 4:
                raw_result = func(self.project, self.node_config, self.context, extra_config)
            elif len(sig.parameters) >= 3:
                raw_result = func(self.project, self.node_config, self.context)
            else:
                raw_result = func(self.project)

            return self._normalize_result(raw_result, coin_cost, t0)

        except Exception as exc:
            duration_ms = int((time.time() - t0) * 1000)
            logger.exception("[SkillBridge] runner_path 璋冪敤澶辫触 path=%s", runner_path)
            return SkillBridgeResult(
                success=False,
                errors=[f"{type(exc).__name__}:{exc}"],
                coin_cost=coin_cost,
                duration_ms=duration_ms,
                retryable=True,
            )

    def _normalize_result(
        self,
        raw: Any,
        coin_cost: int,
        t0: float,
    ) -> SkillBridgeResult:
        """Normalize legacy runner results."""
        import time

        # 鎯呭喌 1: 宸茬粡鏄?SkillBridgeResult
        if isinstance(raw, SkillBridgeResult):
            return raw

        # 鎯呭喌 2: 瀛楀吀锛堣妭鐐硅緭鍑猴級
        if isinstance(raw, dict):
            status = str(raw.get("status") or "").lower()
            return SkillBridgeResult(
                success=bool(raw.get("ok") or raw.get("success") or status in {"completed", "success", "done"}),
                output=raw,
                errors=list(raw.get("errors") or ([raw.get("error")] if raw.get("error") else [])),
                coin_cost=int(raw.get("coin_cost", coin_cost) or coin_cost),
                llm_token_in=int(raw.get("llm_token_in", 0) or 0),
                llm_token_out=int(raw.get("llm_token_out", 0) or 0),
                duration_ms=int(raw.get("duration_ms", duration_ms) or duration_ms),
            )

        # 鎯呭喌 3: 鏈?status 灞炴€х殑瀵硅薄锛堝吋瀹规棫 AgentResult锛?
        if hasattr(raw, "status"):
            status = getattr(raw, "status", "")
            success = status in ("completed", "success", "done")
            outputs = getattr(raw, "outputs", {}) or {}
            return SkillBridgeResult(
                success=success,
                output=dict(outputs) if isinstance(outputs, dict) else {},
                errors=list(getattr(raw, "errors", None) or []),
                coin_cost=int(outputs.get("coin_cost", coin_cost) or coin_cost),
                llm_token_in=int(outputs.get("llm_token_in", 0) or 0),
                llm_token_out=int(outputs.get("llm_token_out", 0) or 0),
                duration_ms=duration_ms,
            )

        # 鍏滃簳
        return SkillBridgeResult(
            success=True,
            output={"content": str(raw)},
            coin_cost=coin_cost,
            duration_ms=duration_ms,
        )


# =========================================================
# 宸ュ叿鍑芥暟
# =========================================================
_code_cache: Dict[str, int] = {}


def _get_code(name: str) -> int:
    if name not in _code_cache:
        try:
            from apps.common.exceptions import _CODES
            _code_cache[name] = _CODES.get(name, 0)
        except Exception:
            _code_cache[name] = 0
    return _code_cache[name]


# =========================================================
# 渚挎嵎鍏ュ彛锛堜緵 workflow_engine._default_agent_runner 璋冪敤锛?
# =========================================================
def run_workflow_node(
    project: Any,
    node_config: Any,
    context: Dict[str, Any],
    dry_run: bool = False,
) -> SkillBridgeResult:
    """Convenience entry point for WorkflowEngine."""
    return SkillBridge(project, node_config, context).run(dry_run=dry_run)
__all__ = [
    "SkillBridge",
    "SkillBridgeResult",
    "run_workflow_node",
]
