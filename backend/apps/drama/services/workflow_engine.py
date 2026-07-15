# -*- coding: utf-8 -*-
"""流程状态机（移植自 runtime/workflow_engine.py）。"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any


class WorkflowError(ValueError):
    """非法流程操作。"""


class ConcurrencyError(WorkflowError):
    """状态版本冲突。"""


def detect_trend(scores: list[float]) -> str | None:
    if len(scores) < 2:
        return None
    previous, current = scores[-2:]
    if abs(current - previous) < 1:
        return "stagnant"
    if len(scores) >= 3:
        first, second, third = scores[-3:]
        if (second - first) * (third - second) < 0:
            return "oscillating"
    if current < previous:
        return "diverging"
    return None


def resolve_latest_script(
    artifacts: dict[str, Any],
    episode_range: str | None = None,
) -> dict[str, Any]:
    for key in ("polished_script", "episode_scripts", "external_script"):
        value = artifacts.get(key)
        if value is None:
            continue
        if episode_range and isinstance(value, dict) and episode_range in value:
            return {"resolved_script_key": key, "value": value[episode_range]}
        return {"resolved_script_key": key, "value": value}
    raise WorkflowError("不存在可解析的 latest_script")


@dataclass
class WorkflowEngine:
    transitions: dict[str, Any]
    max_revision_rounds: int = 3

    def create(self, project_id: str, entry_type: str) -> dict[str, Any]:
        initial = (self.transitions.get("initial_phase") or {}).get(entry_type)
        if not initial:
            raise WorkflowError(f"未知入口: {entry_type}")
        return {
            "schema_version": "workflow-state.v1",
            "project_id": project_id,
            "version": 0,
            "entry_type": entry_type,
            "status": "active",
            "current_phase": initial,
            "approvals": {},
            "batch_cursor": 1,
            "revision_round": 0,
            "score_history": [],
            "quality_results": {},
            "artifacts": {},
            "processed_commands": [],
            "blocked_reason": None,
            "pending_user_options": [],
        }

    def apply(
        self,
        state: dict[str, Any],
        event: str,
        command_id: str,
        expected_version: int,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if command_id in state["processed_commands"]:
            return copy.deepcopy(state)
        if state["version"] != expected_version:
            raise ConcurrencyError(
                f"期望版本 {expected_version}，实际 {state['version']}"
            )
        payload = payload or {}
        transition = self._select_transition(state, event)
        if transition is None:
            raise WorkflowError(
                f"阶段 {state['current_phase']} 不接受事件 {event}"
            )
        result = copy.deepcopy(state)
        self._run_action(result, transition.get("action"), payload)
        result["current_phase"] = transition["to"]
        result["status"] = transition.get("status", "active")
        result["processed_commands"].append(command_id)
        result["version"] += 1
        return result

    def decide(
        self,
        state: dict[str, Any],
        decision: str,
        command_id: str,
        expected_version: int,
    ) -> dict[str, Any]:
        if state["status"] != "waiting_user":
            raise WorkflowError("当前不等待用户决策")
        definition = (self.transitions.get("user_decisions") or {}).get(decision)
        if not definition:
            raise WorkflowError(f"未知用户决策: {decision}")
        synthetic = {
            "to": definition["to"],
            "status": definition.get("status", "active"),
            "action": definition.get("action"),
        }
        runtime = copy.deepcopy(self.transitions)
        runtime.setdefault("transitions", []).insert(
            0,
            {
                "from": state["current_phase"],
                "event": f"user:{decision}",
                **synthetic,
            },
        )
        return WorkflowEngine(runtime, self.max_revision_rounds).apply(
            state,
            f"user:{decision}",
            command_id,
            expected_version,
        )

    def _select_transition(
        self, state: dict[str, Any], event: str
    ) -> dict[str, Any] | None:
        for transition in self.transitions.get("transitions", []):
            if transition.get("event") != event:
                continue
            if transition.get("from") not in ("*", state["current_phase"]):
                continue
            if self._guard_passes(state, transition.get("guard")):
                return transition
        return None

    def _guard_passes(self, state: dict[str, Any], guard: str | None) -> bool:
        if guard is None:
            return True
        if guard == "quality_join_complete":
            return {"score", "compliance"} <= set(state["quality_results"])
        if guard == "can_auto_revise":
            return (
                state["revision_round"] < self.max_revision_rounds
                and detect_trend(state["score_history"]) is None
            )
        if guard == "must_stop":
            return not self._guard_passes(state, "can_auto_revise")
        raise WorkflowError(f"未知 guard: {guard}")

    def _run_action(
        self,
        state: dict[str, Any],
        action: str | None,
        payload: dict[str, Any],
    ) -> None:
        if action is None:
            return
        if action == "approve_story_bible":
            state["approvals"]["story_bible_approved"] = True
        elif action == "reset_quality_join":
            state["quality_results"] = {}
        elif action == "record_quality_score":
            score = float(payload["overall_score"])
            state["score_history"].append(score)
            state["quality_results"]["score"] = payload
        elif action == "record_compliance":
            state["quality_results"]["compliance"] = payload
        elif action == "increment_revision_round":
            state["revision_round"] += 1
        elif action == "advance_batch":
            state["batch_cursor"] += 1
            state["revision_round"] = 0
            state["quality_results"] = {}
        elif action == "require_user_decision":
            state["pending_user_options"] = [
                "accept_current",
                "manual_revision",
                "abandon_batch",
            ]
            state["blocked_reason"] = detect_trend(state["score_history"]) or (
                "max_revision_rounds"
            )
        elif action == "invalidate_downstream":
            state["approvals"]["story_bible_approved"] = False
            for key in (
                "narrative_plan",
                "episode_scripts",
                "polished_script",
                "quality_report",
                "compliance_report",
                "production_package",
            ):
                state["artifacts"].pop(key, None)
            state["revision_round"] = 0
            state["quality_results"] = {}
        else:
            raise WorkflowError(f"未知 action: {action}")
