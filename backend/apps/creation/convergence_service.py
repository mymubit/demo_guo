# -*- coding: utf-8 -*-
"""Convergence stop service backed by internal defaults only."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from django.db import transaction

logger = logging.getLogger(__name__)

_DEFAULT_MAX_ROUNDS: dict[str, int] = {
    "synopsis": 3,
    "episode": 5,
    "full_script": 3,
}
_DEFAULT_STAGNATION_DELTA = 1.0
_DEFAULT_OSCILLATION_WINDOW = 3


@dataclass
class ConvergenceResult:
    state: str
    can_fix: bool
    fix_round: int
    score_history: list[float]
    reason: str


def _detect_oscillation(history: list[float], window: int) -> bool:
    if len(history) < window:
        return False
    recent = history[-window:]
    diffs = [recent[i + 1] - recent[i] for i in range(len(recent) - 1)]
    return any(d > 0 for d in diffs) and any(d < 0 for d in diffs)


class ConvergenceService:
    def __init__(
        self,
        stagnation_delta: float = _DEFAULT_STAGNATION_DELTA,
        oscillation_window: int = _DEFAULT_OSCILLATION_WINDOW,
        max_rounds_override: Optional[dict[str, int]] = None,
    ) -> None:
        self.stagnation_delta = stagnation_delta
        self.oscillation_window = oscillation_window
        self.max_rounds = {**_DEFAULT_MAX_ROUNDS, **(max_rounds_override or {})}

    @classmethod
    def from_thresholds(cls) -> "ConvergenceService":
        return cls()

    def can_fix(self, node: "CreationNode") -> tuple[bool, str]:  # type: ignore[name-defined]
        if node.convergence_state == node.CONVERGENCE_BLOCKED:
            return False, node.fix_blocked_reason or "convergence blocked"
        max_rounds = self._get_max_rounds(node)
        if node.fix_round >= max_rounds:
            return False, f"max fix rounds reached ({node.fix_round}/{max_rounds})"
        return True, ""

    @transaction.atomic
    def record_score(self, node: "CreationNode", score: float) -> ConvergenceResult:  # type: ignore[name-defined]
        from .models import CreationNode

        node = CreationNode.objects.select_for_update().get(pk=node.pk)
        history = list(node.score_history or [])
        history.append(round(float(score), 2))
        new_round = int(node.fix_round or 0) + 1
        max_rounds = self._get_max_rounds(node)
        state, can_fix, reason = self._judge(history, new_round, max_rounds)

        node.fix_round = new_round
        node.max_fix_rounds = max_rounds
        node.score_history = history
        if state == "blocked_limit":
            node.convergence_state = node.CONVERGENCE_BLOCKED
        else:
            node.convergence_state = state
        if node.convergence_state == node.CONVERGENCE_BLOCKED:
            node.fix_blocked_reason = reason
            node.project.__class__.objects.filter(pk=node.project_id).update(
                fusion_status=node.project.__class__.FUSION_BLOCKED
            )
        node.save(
            update_fields=[
                "fix_round",
                "max_fix_rounds",
                "score_history",
                "convergence_state",
                "fix_blocked_reason",
            ]
        )
        return ConvergenceResult(
            state=node.convergence_state,
            can_fix=can_fix,
            fix_round=new_round,
            score_history=history,
            reason=reason,
        )

    def reset(self, node: "CreationNode") -> None:  # type: ignore[name-defined]
        node.fix_round = 0
        node.score_history = []
        node.convergence_state = node.CONVERGENCE_PENDING
        node.fix_blocked_reason = ""
        node.save(
            update_fields=[
                "fix_round",
                "score_history",
                "convergence_state",
                "fix_blocked_reason",
            ]
        )

    def _get_max_rounds(self, node: "CreationNode") -> int:  # type: ignore[name-defined]
        if node.max_fix_rounds and node.max_fix_rounds > 0:
            return int(node.max_fix_rounds)
        node_id = node.fusion_node_id or ""
        if "synopsis" in node_id:
            return self.max_rounds.get("synopsis", 3)
        if "score" in node_id or "full" in node_id:
            return self.max_rounds.get("full_script", 3)
        return self.max_rounds.get("episode", 5)

    def _judge(
        self,
        history: list[float],
        new_round: int,
        max_rounds: int,
    ) -> tuple[str, bool, str]:
        from .models import CreationNode

        if new_round >= max_rounds:
            return "blocked_limit", False, f"max fix rounds reached ({new_round}/{max_rounds})"
        if len(history) < 2:
            return CreationNode.CONVERGENCE_PENDING, True, "first score recorded"

        previous = history[-2]
        current = history[-1]
        diff = current - previous
        if _detect_oscillation(history, self.oscillation_window):
            return CreationNode.CONVERGENCE_OSCILLATE, False, "score oscillation detected"
        if diff < -self.stagnation_delta:
            return CreationNode.CONVERGENCE_DIVERGE, False, "score diverged"
        if abs(diff) <= self.stagnation_delta:
            return CreationNode.CONVERGENCE_STAGNATE, False, "score stagnated"
        return CreationNode.CONVERGENCE_CONVERGE, True, "score converged"
