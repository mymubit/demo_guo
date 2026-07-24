from __future__ import annotations

from collections.abc import Iterable, Mapping


ALLOWED_BLUEPRINT_FIELDS = {"main_storyline", "necessary_subplots", "stage_turns", "paywall_positions", "reversal_windows", "foreshadowing_summary", "world_rules"}


def validate_blueprint_fields(blueprint: Mapping) -> list[str]:
    extra = sorted(set(blueprint) - ALLOWED_BLUEPRINT_FIELDS)
    return [f"blueprint contains episode-scene expansion fields: {extra}"] if extra else []


def validate_opening_cross_section(scene: Mapping) -> list[str]:
    errors = []
    if not scene.get("goal") or not scene.get("conflict"):
        errors.append("episode one scene one requires immediate Goal and Conflict")
    if scene.get("mode") == "chronology" or scene.get("theme_exposition"):
        errors.append("opening must establish tone through tension, not chronology or theme exposition")
    return errors


def validate_foreshadow_density(entries: Iterable[Mapping], episode_count: int) -> list[str]:
    entries = list(entries)
    grade_value = {"C": 1, "B": 2, "A": 3, "S": 4}
    errors = []
    for start in range(1, episode_count + 1, 10):
        end = min(start + 9, episode_count)
        count = sum(start <= item.get("setup_episode", 0) <= end and grade_value.get(item.get("grade"), 0) >= 3 for item in entries)
        if count < 1:
            errors.append(f"episodes {start}-{end} contain no A-grade or stronger foreshadow entry")
    return errors


def validate_matrix_params(params: Mapping) -> list[str]:
    errors = []
    if len(params.get("emotion_curve", [])) != 8:
        errors.append("matrix emotion_curve must contain 8 target nodes")
    if len(params.get("act_ratio", [])) != 6:
        errors.append("matrix act_ratio must contain 6 stage ratios")
    if not params.get("hook_types"):
        errors.append("matrix rule_params requires hook_types")
    return errors


def validate_hook_type_alignment(designed: Iterable[str], allowed: Iterable[str]) -> list[str]:
    unknown = sorted(set(designed) - set(allowed))
    return [f"designed hook types are outside project brief parameters: {unknown}"] if unknown else []
