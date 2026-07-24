#!/usr/bin/env python3
"""流程状态机、并发、幂等与 latest_script 回归校验。"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml


_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from lib.schema_validator import SchemaValidationError, SchemaValidator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime.workflow_engine import (  # noqa: E402
    ConcurrencyError,
    WorkflowEngine,
    detect_trend,
    resolve_latest_script,
)

ERRORS: List[str] = []


def load_yaml(relative_path: str) -> Dict[str, Any]:
    return yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8")) or {}


def main() -> int:
    transitions = load_yaml("orchestration/workflow-transitions.yaml")
    engine = WorkflowEngine(transitions)
    scenarios = load_yaml("tools/fixtures/workflow/scenarios.yaml").get(
        "scenarios", {}
    )
    validator = SchemaValidator(ROOT / "schemas")
    state_schema_path = ROOT / "schemas/workflow-state.v1.schema.json"
    state_schema = validator.load(state_schema_path)

    for name, scenario in scenarios.items():
        state = engine.create(name, scenario["entry_type"])
        seed = scenario.get("seed_artifacts") or {}
        if seed:
            state.setdefault("artifacts", {}).update(seed)
        for index, step in enumerate(scenario["events"]):
            state = engine.apply(
                state,
                step["event"],
                f"{name}-{index}",
                state["version"],
                step.get("payload"),
            )
        if state["current_phase"] != scenario["expected_phase"]:
            ERRORS.append(f"{name}: 最终阶段错误")
        if "expected_batch_cursor" in scenario and state["batch_cursor"] != scenario[
            "expected_batch_cursor"
        ]:
            ERRORS.append(f"{name}: batch_cursor 错误")
        if "expected_revision_round" in scenario and state["revision_round"] != scenario[
            "expected_revision_round"
        ]:
            ERRORS.append(f"{name}: revision_round 错误")
        if "expected_approval" in scenario and state["approvals"].get(
            "story_bible_approved"
        ) is not scenario["expected_approval"]:
            ERRORS.append(f"{name}: 蓝图审批状态错误")
        try:
            validator.validate(state, state_schema, current_file=state_schema_path)
        except SchemaValidationError as exc:
            ERRORS.append(f"{name}: {exc}")

    state = engine.create("idempotency", "original_track")
    once = engine.apply(state, "project_brief_completed", "same", 0)
    twice = engine.apply(once, "project_brief_completed", "same", 0)
    if twice != once:
        ERRORS.append("幂等命令重复改变状态")
    try:
        engine.apply(once, "story_bible_completed", "conflict", 0)
        ERRORS.append("版本冲突未被拒绝")
    except ConcurrencyError:
        pass

    # guard 回归：未通过末批质检 / 缺 total_batches 时禁止进入 delivery
    from runtime.workflow_engine import WorkflowError

    guarded = engine.create("guard-delivery", "original_track")
    for idx, (event, payload) in enumerate(
        (
            ("project_brief_completed", None),
            ("stage_confirmed", {"phase": "strategy"}),
            ("story_bible_completed", None),
            ("story_bible_approved", None),
            ("episode_plan_completed", None),
        )
    ):
        guarded = engine.apply(
            guarded, event, f"g-{idx}", guarded["version"], payload
        )
    try:
        engine.apply(guarded, "all_batches_completed", "g-skip", guarded["version"], {"total_batches": 1})
        ERRORS.append("未通过质检即进入 delivery 未被拒绝")
    except WorkflowError:
        pass
    try:
        engine.apply(guarded, "all_batches_completed", "g-nototal", guarded["version"])
        ERRORS.append("缺 total_batches 进入 delivery 未被拒绝")
    except WorkflowError:
        pass

    # story_adapt 不允许回流 strategy
    adapt = engine.create("guard-adapt", "story_adapt")
    try:
        engine.apply(adapt, "project_brief_rejected", "g-adapt", adapt["version"])
        ERRORS.append("story_adapt 回流 strategy 未被拒绝")
    except WorkflowError:
        pass

    artifacts = {
        "episode_scripts": {"1-5": "draft"},
        "polished_script": {"1-5": "polished"},
    }
    resolved = resolve_latest_script(artifacts, "1-5")
    if resolved != {"resolved_script_key": "polished_script", "value": "polished"}:
        ERRORS.append("latest_script 未优先解析修复稿")

    trend_cases = [
        ([70, 70.5], "stagnant"),
        ([75, 70], "diverging"),
        ([70, 75, 72], "oscillating"),
        ([70, 75], None),
    ]
    for scores, expected in trend_cases:
        if detect_trend(scores) != expected:
            ERRORS.append(f"趋势检测错误: {scores}")

    for message in ERRORS:
        print(f"ERROR {message}")
    print(f"\n流程校验完成：{len(scenarios)} 场景 · {len(ERRORS)} 错误")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
