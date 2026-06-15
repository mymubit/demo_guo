"""
收敛停机算法服务

移植自 StoryForge 的四态判定模型，适配 ScriptForge DB 驱动架构。

四态定义：
  converge  — 当轮总分高于上一轮（S₂ > S₁），可继续修复
  stagnate  — 当轮与上轮分数差 ≤ delta（|S₂-S₁| ≤ δ），停机
  diverge   — 当轮总分低于上一轮（S₂ < S₁），立即停机
  oscillate — 窗口内序列有涨有跌，停机

所有停机状态（stagnate/diverge/oscillate）及达到硬上限时均写入
convergence_state = "blocked"，并填写 fix_blocked_reason。
"""

import logging
from dataclasses import dataclass
from typing import Optional

from django.db import transaction

logger = logging.getLogger(__name__)

# 默认配置（与 skill-thresholds.json#maxFixRounds 保持一致）
_DEFAULT_MAX_ROUNDS: dict[str, int] = {
    "synopsis": 3,
    "episode": 5,
    "full_script": 3,
}
_DEFAULT_STAGNATION_DELTA: float = 1.0
_DEFAULT_OSCILLATION_WINDOW: int = 3


@dataclass
class ConvergenceResult:
    """单次 record_score 的判定结果"""
    state: str                  # converge / stagnate / diverge / oscillate / blocked
    can_fix: bool               # 是否允许继续修复
    fix_round: int              # 完成后的轮次
    score_history: list[float]
    reason: str                 # 人类可读说明


def _detect_oscillation(history: list[float], window: int) -> bool:
    """检测最近 window 轮内是否振荡（有涨有跌）。"""
    if len(history) < window:
        return False
    recent = history[-window:]
    diffs = [recent[i + 1] - recent[i] for i in range(len(recent) - 1)]
    has_up = any(d > 0 for d in diffs)
    has_down = any(d < 0 for d in diffs)
    return has_up and has_down


class ConvergenceService:
    """
    收敛停机算法服务。

    调用时序（由 auto-fix-chain 编排层调用）：
      1. can_fix(node)           ← 修复前先检查是否允许
      2. <执行修复 + 评分>
      3. record_score(node, score) ← 写入新分数并判定状态
      4. 根据 result.can_fix 决定是否继续循环
    """

    def __init__(
        self,
        stagnation_delta: float = _DEFAULT_STAGNATION_DELTA,
        oscillation_window: int = _DEFAULT_OSCILLATION_WINDOW,
        max_rounds_override: Optional[dict[str, int]] = None,
    ) -> None:
        self.stagnation_delta = stagnation_delta
        self.oscillation_window = oscillation_window
        self.max_rounds = {**_DEFAULT_MAX_ROUNDS, **(max_rounds_override or {})}

    # ── 读取 skill-thresholds.json 的工厂方法 ──────────────────────────
    @classmethod
    def from_thresholds(cls) -> "ConvergenceService":
        """
        从 ai-drama-skills-v2/config/skill-thresholds.json 读取配置。
        若文件不存在或字段缺失，回退到内置默认值。
        """
        import json
        import os

        thresholds_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..",
            "ai-drama-skills-v2", "config", "skill-thresholds.json",
        )
        thresholds_path = os.path.normpath(thresholds_path)
        try:
            with open(thresholds_path, encoding="utf-8") as f:
                data = json.load(f)
            max_rounds = data.get("maxFixRounds", {})
            delta = float(data.get("stagnation_delta", _DEFAULT_STAGNATION_DELTA))
            window = int(data.get("oscillation_window", _DEFAULT_OSCILLATION_WINDOW))
            return cls(
                stagnation_delta=delta,
                oscillation_window=window,
                max_rounds_override=max_rounds,
            )
        except Exception as exc:
            logger.warning("ConvergenceService: 读取 skill-thresholds.json 失败，使用默认配置: %s", exc)
            return cls()

    # ── 核心方法 ───────────────────────────────────────────────────────

    def can_fix(self, node: "CreationNode") -> tuple[bool, str]:  # type: ignore[name-defined]
        """
        检查节点是否允许启动下一轮修复。

        返回 (allowed: bool, reason: str)。
        allowed=False 时应拒绝启动修复并告知原因。
        """
        if node.convergence_state == node.CONVERGENCE_BLOCKED:
            return False, f"节点已停机：{node.fix_blocked_reason or '收敛算法触发停机'}"
        if node.fix_round >= self._get_max_rounds(node):
            return False, f"已达最大修复轮次上限（{node.fix_round}/{self._get_max_rounds(node)}）"
        return True, ""

    @transaction.atomic
    def record_score(
        self,
        node: "CreationNode",  # type: ignore[name-defined]
        score: float,
    ) -> ConvergenceResult:
        """
        记录本轮修复后的评分，执行四态判定，更新节点状态。

        应在每次修复+评分完成后调用。
        """
        from .models import CreationNode  # 延迟导入，避免循环

        # 重新加载 with 行锁，防止并发重复写入
        node = CreationNode.objects.select_for_update().get(pk=node.pk)

        history: list[float] = list(node.score_history or [])
        history.append(round(float(score), 2))
        new_round = node.fix_round + 1
        max_rounds = self._get_max_rounds(node)

        state, can_fix, reason = self._judge(history, new_round, max_rounds)

        node.fix_round = new_round
        node.score_history = history
        node.convergence_state = state if state != "blocked_limit" else node.CONVERGENCE_BLOCKED

        if state in (
            node.CONVERGENCE_STAGNATE,
            node.CONVERGENCE_DIVERGE,
            node.CONVERGENCE_OSCILLATE,
            "blocked_limit",
        ):
            node.convergence_state = node.CONVERGENCE_BLOCKED
            node.fix_blocked_reason = reason
            # 同步上层 Project 状态
            node.project.__class__.objects.filter(pk=node.project_id).update(
                fusion_status=node.project.__class__.FUSION_BLOCKED
            )
            # 触发跨项目经验沉淀检测
            try:
                from .learned_rules import record_convergence_failure

                failed_dims = list(node.last_failed_dimensions or [])
                genre = ""
                try:
                    brief = node.project.artifacts.filter(artifact_key="project_brief").first()
                    if brief:
                        import json as _json
                        genre = _json.loads(brief.content or "{}").get("genre") or ""
                except Exception:  # noqa: BLE001
                    pass
                record_convergence_failure(
                    project_id=node.project_id,
                    project_title=str(node.project.title or ""),
                    failed_dimensions=failed_dims,
                    convergence_state=node.CONVERGENCE_BLOCKED,
                    fix_round=new_round,
                    score_history=history,
                    genre=genre,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("ConvergenceService: 经验沉淀检测失败: %s", exc)
        else:
            node.convergence_state = state

        node.save(update_fields=[
            "fix_round", "max_fix_rounds", "score_history",
            "convergence_state", "fix_blocked_reason",
        ])

        logger.info(
            "ConvergenceService: project=%s node=%s round=%d score=%.2f state=%s",
            node.project_id, node.pk, new_round, score, node.convergence_state,
        )

        return ConvergenceResult(
            state=node.convergence_state,
            can_fix=can_fix,
            fix_round=new_round,
            score_history=history,
            reason=reason,
        )

    def reset(self, node: "CreationNode") -> None:  # type: ignore[name-defined]
        """重置节点收敛状态（跨集切换或项目重启时调用）。"""
        node.fix_round = 0
        node.score_history = []
        node.convergence_state = node.CONVERGENCE_PENDING
        node.fix_blocked_reason = ""
        node.save(update_fields=[
            "fix_round", "score_history", "convergence_state", "fix_blocked_reason",
        ])

    # ── 私有辅助 ──────────────────────────────────────────────────────

    def _get_max_rounds(self, node: "CreationNode") -> int:  # type: ignore[name-defined]
        """
        优先取节点自身 max_fix_rounds，再根据 fusion_node_id 匹配
        skill-thresholds.json 配置，最后回退内置默认值。
        """
        if node.max_fix_rounds and node.max_fix_rounds > 0:
            return node.max_fix_rounds
        node_id = node.fusion_node_id or ""
        if "synopsis" in node_id:
            return self.max_rounds.get("synopsis", 3)
        if "episode" in node_id or "fix" in node_id:
            return self.max_rounds.get("episode", 5)
        if "score" in node_id or "full" in node_id:
            return self.max_rounds.get("full_script", 3)
        return self.max_rounds.get("episode", 5)

    def _judge(
        self,
        history: list[float],
        new_round: int,
        max_rounds: int,
    ) -> tuple[str, bool, str]:
        """
        核心四态判定逻辑。

        返回 (state, can_fix, reason)。
        state 取值：converge / stagnate / diverge / oscillate / blocked_limit / pending
        """
        from .models import CreationNode

        # 硬上限检查（优先级最高）
        if new_round >= max_rounds:
            return (
                "blocked_limit",
                False,
                f"已达最大修复轮次上限（{new_round}/{max_rounds}）",
            )

        # 数据不足（首轮或历史过短），暂时标记 pending
        if len(history) < 2:
            return CreationNode.CONVERGENCE_PENDING, True, "首轮评分，数据不足，继续修复"

        s_prev = history[-2]
        s_curr = history[-1]
        diff = s_curr - s_prev

        # 振荡检测（窗口检测优先于单步判定，防止抖动掩盖趋势）
        if _detect_oscillation(history, self.oscillation_window):
            return (
                CreationNode.CONVERGENCE_OSCILLATE,
                False,
                f"检测到振荡：最近 {self.oscillation_window} 轮分数序列 {history[-self.oscillation_window:]} 有涨有跌",
            )

        # 发散：当轮分 < 上轮分
        if diff < -self.stagnation_delta:
            return (
                CreationNode.CONVERGENCE_DIVERGE,
                False,
                f"分数发散：{s_prev:.2f} → {s_curr:.2f}（下降 {abs(diff):.2f}）",
            )

        # 停滞：差值 ≤ delta
        if abs(diff) <= self.stagnation_delta:
            return (
                CreationNode.CONVERGENCE_STAGNATE,
                False,
                f"分数停滞：{s_prev:.2f} → {s_curr:.2f}（变化 {diff:+.2f} ≤ δ={self.stagnation_delta}）",
            )

        # 收敛：当轮分 > 上轮分
        return (
            CreationNode.CONVERGENCE_CONVERGE,
            True,
            f"分数收敛：{s_prev:.2f} → {s_curr:.2f}（+{diff:.2f}），继续修复（{new_round}/{max_rounds}）",
        )
