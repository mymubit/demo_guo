from __future__ import annotations

from collections.abc import Iterable, Mapping


def validate_one_core_action(actions: Iterable[str]) -> list[str]:
    values = [item for item in actions if item]
    return [] if len(values) == 1 else [f"concept must contain exactly one core dramatic action; found {len(values)}"]


def validate_elevator_pitch(pitch: Mapping) -> list[str]:
    required = {"protagonist_identity", "urgent_goal", "core_obstacle", "differentiating_mechanism", "without_proper_nouns"}
    missing = sorted(key for key in required if not pitch.get(key))
    return [f"elevator pitch missing elements: {missing}"] if missing else []


def validate_market_fields(brief: Mapping) -> list[str]:
    required = {"synopsis", "audience_channel", "market_opportunity", "blockbuster_factors", "competitor_references", "differentiation_strategy", "first_episode_hook", "first_paywall_direction", "subject_sensitivity_precheck"}
    missing = sorted(key for key in required if not brief.get(key))
    return [f"project brief missing market fields: {missing}"] if missing else []


def validate_concept_risk_boundary(precheck: Mapping) -> list[str]:
    return [] if precheck.get("compliance_verdict") is None else ["concept precheck must not issue a compliance verdict"]
