from __future__ import annotations

from collections.abc import Iterable


def validate_character_counts(
    characters: Iterable[dict],
    protagonist_maximum: int,
    supporting_minimum: int,
    supporting_maximum: int,
) -> list[str]:
    characters = list(characters)
    protagonist_count = sum(item.get("role_type") == "protagonist" for item in characters)
    supporting_count = sum(
        item.get("role_type") == "supporting" and item.get("is_core") is True for item in characters
    )
    errors = []
    if protagonist_count > protagonist_maximum:
        errors.append(f"protagonist count is {protagonist_count}; maximum is {protagonist_maximum}")
    if not supporting_minimum <= supporting_count <= supporting_maximum:
        errors.append(
            f"core supporting count is {supporting_count}; expected {supporting_minimum}-{supporting_maximum}"
        )
    return errors


def validate_arc_ratios(character: dict, first_target: float, second_target: float, tolerance: float = 0.1) -> list[str]:
    arc = character.get("arc") or {}
    errors = []
    expected_bounds = {
        "start": (0.0, tolerance),
        "turning_point_1": (first_target - tolerance, first_target + tolerance),
        "turning_point_2": (second_target - tolerance, second_target + tolerance),
        "end": (1.0 - tolerance, 1.0),
    }
    previous = -1.0
    for key in ("start", "turning_point_1", "turning_point_2", "end"):
        point = arc.get(key) or {}
        ratio = point.get("episode_ratio")
        if not isinstance(ratio, (int, float)):
            errors.append(f"{character.get('id', '?')}.{key}: missing episode_ratio")
            continue
        lower, upper = expected_bounds[key]
        if not lower <= ratio <= upper:
            errors.append(f"{character.get('id', '?')}.{key}: ratio {ratio} outside {lower:.2f}-{upper:.2f}")
        if ratio < previous:
            errors.append(f"{character.get('id', '?')}.{key}: arc ratios are not ordered")
        previous = ratio
    return errors


def validate_relationships(characters: Iterable[dict], relationships: Iterable[dict], maximum: int) -> list[str]:
    character_ids = {item.get("id") for item in characters}
    relationships = list(relationships)
    errors = []
    if len(relationships) > maximum:
        errors.append(f"relationship count is {len(relationships)}; maximum is {maximum}")
    seen_pairs = set()
    for relationship in relationships:
        left = relationship.get("party_a")
        right = relationship.get("party_b")
        relation_id = relationship.get("id", "?")
        if left not in character_ids:
            errors.append(f"{relation_id}: unknown party_a {left!r}")
        if right not in character_ids:
            errors.append(f"{relation_id}: unknown party_b {right!r}")
        if left == right:
            errors.append(f"{relation_id}: relationship cannot connect a character to itself")
        pair = tuple(sorted((left, right))) if left and right else None
        if pair and pair in seen_pairs:
            errors.append(f"{relation_id}: duplicate relationship pair {pair}")
        if pair:
            seen_pairs.add(pair)
    return errors


def validate_motivation_chain(character: dict) -> list[str]:
    fields = ("surface_desire", "deep_need", "ghost", "lie", "flaw")
    missing = [field for field in fields if not str(character.get(field, "")).strip()]
    return [f"{character.get('id', '?')}: incomplete motivation chain {missing}"] if missing else []
