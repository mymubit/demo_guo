from __future__ import annotations

from collections.abc import Iterable, Mapping
from math import floor


REQUIRED_CARD_FIELDS = {
    "episode",
    "title",
    "core_event",
    "goal_conflict",
    "opening_hook",
    "ending_hook",
    "emotion_nodes",
    "satisfaction_points",
    "reversal",
    "paywall_hook",
    "foreshadowing",
    "rhythm_tag",
}

READONLY_GLOBAL_PREFIXES = (
    "story_bible.major_reversal_positions",
    "story_bible.foreshadowing_table",
    "story_bible.paywall_distribution",
    "story_bible.series_structure",
)
HOOK_GRADES = {"C": 1, "B": 2, "A": 3, "S": 4}
CONFRONTATION_FIELDS = {"power_balance", "stated_demand", "real_intent", "power_shift", "ending_value_change"}


def validate_global_structure_readonly(changed_paths: Iterable[str]) -> list[str]:
    return [
        f"readonly global structure changed: {path}"
        for path in changed_paths
        if path.startswith(READONLY_GLOBAL_PREFIXES)
    ]


def validate_required_card_content(cards: Iterable[dict]) -> list[str]:
    errors = []
    for card in cards:
        episode = card.get("episode", "?")
        missing = sorted(REQUIRED_CARD_FIELDS - set(card))
        if missing:
            errors.append(f"episode {episode}: missing fields {missing}")
        for field in REQUIRED_CARD_FIELDS - {"episode", "emotion_nodes", "foreshadowing"}:
            if field in card and card[field] in (None, "", []):
                errors.append(f"episode {episode}: empty field {field}")
    return errors


def validate_foreshadow_tracking(cards: Iterable[dict]) -> list[str]:
    errors = []
    for card in cards:
        episode = card.get("episode", "?")
        foreshadowing = card.get("foreshadowing") or {}
        for index, item in enumerate(foreshadowing.get("entries", [])):
            if not item.get("setup_episode"):
                errors.append(f"episode {episode} foreshadow {index}: missing setup_episode")
            if not item.get("payoff_episode"):
                errors.append(f"episode {episode} foreshadow {index}: missing payoff_episode")
    return errors


def validate_rhythm_run(cards: Iterable[dict], maximum_run: int) -> list[str]:
    errors = []
    previous = None
    run = 0
    start_episode = None
    for card in cards:
        tag = card.get("rhythm_tag")
        if tag == previous:
            run += 1
        else:
            previous = tag
            run = 1
            start_episode = card.get("episode")
        if tag and run > maximum_run:
            errors.append(
                f"rhythm {tag!r} repeats from episode {start_episode} for {run} episodes; maximum is {maximum_run}"
            )
    return errors


def validate_hook_grade(actual: str, required: str) -> list[str]:
    if actual not in HOOK_GRADES:
        return [f"unknown hook grade: {actual!r}"]
    if required not in HOOK_GRADES:
        return [f"unknown required hook grade: {required!r}"]
    if HOOK_GRADES[actual] < HOOK_GRADES[required]:
        return [f"hook grade {actual} is below required grade {required}"]
    return []


def validate_hook_count(grades: Iterable[str], minimum_count: int, minimum_grade: str) -> list[str]:
    if minimum_grade not in HOOK_GRADES:
        return [f"unknown minimum hook grade: {minimum_grade!r}"]
    count = sum(HOOK_GRADES.get(grade, 0) >= HOOK_GRADES[minimum_grade] for grade in grades)
    if count < minimum_count:
        return [f"counted {count} hooks at or above {minimum_grade}; minimum is {minimum_count}"]
    return []


def validate_conflict_type_coverage(conflict_types: Iterable[str], minimum: int) -> list[str]:
    allowed = {"external", "interpersonal", "internal", "fate"}
    actual = set(conflict_types)
    unknown = sorted(actual - allowed)
    errors = [f"unknown conflict types: {unknown}"] if unknown else []
    if len(actual & allowed) < minimum:
        errors.append(f"conflict design covers {len(actual & allowed)} types; minimum is {minimum}")
    return errors


def validate_confrontation(confrontation: dict) -> list[str]:
    missing = sorted(CONFRONTATION_FIELDS - set(confrontation))
    return [f"confrontation missing fields: {missing}"] if missing else []


def validate_payment_window(episode: int, minimum: int, maximum: int, label: str) -> list[str]:
    if minimum <= episode <= maximum:
        return []
    return [f"{label} checkpoint episode {episode} is outside {minimum}-{maximum}"]


def validate_payment_payoff(checkpoint_episode: int, payoff_episode: int, maximum_delay: int) -> list[str]:
    delay = payoff_episode - checkpoint_episode
    if 0 <= delay <= maximum_delay:
        return []
    return [f"payment payoff delay is {delay} episodes; maximum is {maximum_delay}"]


def allocate_stages(episode_count: int, ratios: list[float], minimum_per_stage: int = 1) -> list[int]:
    if episode_count < len(ratios) * minimum_per_stage:
        raise ValueError("episode count cannot satisfy minimum episodes per stage")
    if not ratios or sum(ratios) <= 0:
        raise ValueError("stage ratios must have a positive total")
    normalized = [ratio / sum(ratios) for ratio in ratios]
    raw = [episode_count * ratio for ratio in normalized]
    result = [max(minimum_per_stage, floor(value)) for value in raw]
    while sum(result) < episode_count:
        candidates = sorted(range(len(result)), key=lambda i: (raw[i] - floor(raw[i]), -i), reverse=True)
        result[candidates[(episode_count - sum(result) - 1) % len(candidates)]] += 1
    while sum(result) > episode_count:
        candidates = sorted(
            (i for i, value in enumerate(result) if value > minimum_per_stage),
            key=lambda i: (raw[i] - floor(raw[i]), i),
        )
        if not candidates:
            raise ValueError("cannot reduce stage allocation without violating minimum")
        result[candidates[0]] -= 1
    return result


def validate_foreshadow_type(actual: str) -> list[str]:
    allowed = {"identity", "motivation", "relationship", "situation", "truth"}
    return [] if actual in allowed else [f"unknown foreshadow type: {actual!r}"]


def validate_foreshadow_payoff_delay(setup_episode: int, payoff_episode: int, maximum_delay: int) -> list[str]:
    delay = payoff_episode - setup_episode
    if 0 <= delay <= maximum_delay:
        return []
    return [f"foreshadow emotional payoff delay is {delay} episodes; maximum is {maximum_delay}"]


def validate_episode_context(context: Mapping[str, object]) -> list[str]:
    required = {
        "previous_episode",
        "memory_checkpoint",
        "current_episode_card",
        "unresolved_foreshadowing",
        "active_global_constraints",
    }
    missing = sorted(required - set(context))
    extra = sorted(set(context) - required)
    errors = []
    if missing:
        errors.append(f"episode context missing keys: {missing}")
    if extra:
        errors.append(f"episode context contains disallowed keys: {extra}")
    return errors


def validate_overdue_foreshadow_checkpoint(overdue_ids: Iterable[str], checkpoint_ids: Iterable[str]) -> list[str]:
    missing = sorted(set(overdue_ids) - set(checkpoint_ids))
    return [f"overdue foreshadow entries missing from checkpoint: {missing}"] if missing else []
