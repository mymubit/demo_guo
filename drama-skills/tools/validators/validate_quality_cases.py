#!/usr/bin/env python3
"""确定性质量回归用例校验。"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime.workflow_engine import detect_trend  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "optimizers"))
from synthesize_matrix_params import (  # noqa: E402
    TagConstraintError,
    synthesize_rule_params,
)

ERRORS: List[str] = []


def load_yaml(relative_path: str) -> Dict[str, Any]:
    return yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8")) or {}


def load_preset(preset: str) -> Dict[str, Any]:
    presets = load_yaml("foundation/presets/scoring-presets.yaml")["presets"]
    return presets[preset]


def production_band(tags: List[str]) -> str:
    config = load_yaml("foundation/presets/production-feasibility.yaml")
    score = sum((config["tags"].get(tag) or {}).get("weight", 0) for tag in tags)
    bands = config["complexity_bands"]
    if score <= bands["lean"]["max_score"]:
        return "lean"
    if score <= bands["standard"]["max_score"]:
        return "standard"
    return "complex"


def evaluate_case(case: Dict[str, Any]) -> Dict[str, Any]:
    category = case["category"]
    data = case["input"]
    if category == "quality_gate":
        # 质检环通过线跟随项目 scoring_preset（默认 standard）
        preset = load_preset(data.get("preset", "standard"))
        threshold = preset["pass_threshold"]
        decision = (
            "pass"
            if data["score"] >= threshold and not data["blocking_issues"]
            else "revise"
        )
        return {"decision": decision}
    if category == "delivery_gate":
        preset = load_preset(data.get("preset", "standard"))
        can_deliver = (
            data["score"] >= preset["pass_threshold"]
            and preset["delivery_eligible"] is True
            and data.get("compliance_passed") is True
        )
        return {"can_deliver": can_deliver}
    if category == "theme_synthesis":
        try:
            result = synthesize_rule_params(dict(data["dims"]))
        except TagConstraintError:
            return {"synthesized": False, "reason": "constraint"}
        output: Dict[str, Any] = {"synthesized": True}
        if "matrix_key" in case.get("expected", {}):
            output["matrix_key"] = result["matrix_key"]
        return output
    if category == "continuity":
        return {"result": "pass" if data["conflicting_facts"] == 0 else "fail"}
    if category == "compliance":
        risk = data["highest_risk"]
        if risk == "p0":
            return {"result": "不通过", "blocking": True}
        return {"result": "风险", "blocking": risk == "p1"}
    if category == "production":
        return {"band": production_band(data["tags"])}
    if category == "platform":
        verified = data["policy_status"] == "verified"
        return {
            "can_release": data["release_requested"] and verified,
            "package_allowed": not data["release_requested"],
        }
    if category == "trend":
        return {"trend": detect_trend(data["scores"])}
    raise ValueError(f"未知用例类别: {category}")


def main() -> int:
    cases = load_yaml("quality/golden-cases.yaml").get("cases") or []
    ids = [case.get("id") for case in cases]
    if len(ids) != len(set(ids)):
        ERRORS.append("golden case id 重复")
    required_categories = {
        "quality_gate",
        "delivery_gate",
        "continuity",
        "compliance",
        "production",
        "platform",
        "trend",
        "theme_synthesis",
    }
    actual_categories = {case.get("category") for case in cases}
    if required_categories - actual_categories:
        ERRORS.append("质量回归类别覆盖不完整")
    if len(cases) < 12:
        ERRORS.append("高风险质量回归用例不得少于12个")

    for case in cases:
        try:
            actual = evaluate_case(case)
            for key, expected in case["expected"].items():
                if actual.get(key) != expected:
                    ERRORS.append(
                        f"{case['id']}: {key}={actual.get(key)!r}，期望 {expected!r}"
                    )
        except (KeyError, ValueError) as exc:
            ERRORS.append(f"{case.get('id')}: {exc}")

    for message in ERRORS:
        print(f"ERROR {message}")
    print(f"\n质量回归完成：{len(cases)} 用例 · {len(ERRORS)} 错误")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
