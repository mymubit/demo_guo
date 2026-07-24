from __future__ import annotations

from collections.abc import Iterable, Mapping


DIMENSIONS = {"format", "narrative", "conflict", "character", "emotion", "logic", "satisfaction", "hooks", "paywall", "genre_fit"}
GRADE_THRESHOLDS = [("S", 90), ("A", 80), ("B", 75), ("C", 60), ("D", 0)]


def validate_dimensions(dimensions: Iterable[Mapping]) -> list[str]:
    items = list(dimensions)
    names = [item.get("name") for item in items]
    errors = []
    if set(names) != DIMENSIONS or len(names) != 10:
        errors.append("quality report must contain each canonical dimension exactly once")
    if abs(sum(float(item.get("weight", 0)) for item in items) - 1.0) > 1e-6:
        errors.append("quality dimension weights must sum to 1.0")
    if any(not item.get("evidence") for item in items):
        errors.append("every quality dimension requires observable evidence")
    return errors


def calculate_grade(score: float) -> str:
    return next(grade for grade, threshold in GRADE_THRESHOLDS if score >= threshold)


def revision_dimensions(dimensions: Iterable[Mapping]) -> list[str]:
    return [item.get("name") for item in dimensions if float(item.get("score", 0)) <= 40]


def apply_sa_veto(candidate_grade: str, opening_impact_seconds: float, harmful_acts: int, has_series_suspense: bool) -> tuple[str, list[str]]:
    vetoes = []
    if opening_impact_seconds > 3:
        vetoes.append("opening-impact")
    if harmful_acts < 3:
        vetoes.append("antagonist-harmful-acts")
    if not has_series_suspense:
        vetoes.append("series-spanning-suspense")
    if vetoes and candidate_grade in {"S", "A"}:
        return "B", vetoes
    return candidate_grade, vetoes


def validate_revision_scope(changed_paths: Iterable[str]) -> list[str]:
    protected = ("project_brief", "story_bible", "episode_plan")
    return [f"revision may not overturn approved artifact: {path}" for path in changed_paths if path.startswith(protected)]


def evolution_decision(history: list[Mapping]) -> dict:
    log_batch = bool(history and float(history[-1].get("overall_score", 100)) < 70)
    proposal_dimensions = []
    if len(history) >= 2:
        previous = history[-2].get("dimensions", {})
        current = history[-1].get("dimensions", {})
        proposal_dimensions = sorted(name for name in DIMENSIONS if float(previous.get(name, 100)) < 70 and float(current.get(name, 100)) < 70)
    return {"log_batch": log_batch, "proposal_dimensions": proposal_dimensions}


def delivery_decision(preset: Mapping, quality: Mapping, compliance: Mapping, production: Mapping) -> dict:
    gaps = []
    if not preset.get("delivery_eligible"):
        gaps.append("scoring preset is not delivery eligible")
    if float(quality.get("overall_score", 0)) < float(preset.get("pass_threshold", 101)):
        gaps.append("quality score is below preset pass threshold")
    if compliance.get("conclusion") != "pass" or not compliance.get("downstream_allowed"):
        gaps.append("compliance report has not passed")
    release = production.get("release_check", {})
    if not production.get("production_assessments") or not production.get("budget_estimate"):
        gaps.append("production complexity or budget band is missing")
    if release.get("policy_status") != "verified-current" or not release.get("release_ready"):
        gaps.append("platform policy or release checklist is not ready")
    return {"deliverable": not gaps, "gaps": gaps, "marketing_assets_allowed": not gaps}
