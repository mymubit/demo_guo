from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable


def validate_world_references(world_system: dict) -> list[str]:
    rules = world_system.get("rules") or []
    rule_ids = [item.get("id") for item in rules]
    errors = []
    duplicates = sorted({rule_id for rule_id in rule_ids if rule_ids.count(rule_id) > 1})
    if duplicates:
        errors.append(f"duplicate world rule ids: {duplicates}")
    known = set(rule_ids)
    for loophole in (world_system.get("power_structure") or {}).get("loopholes", []):
        if loophole.get("rule_id") not in known:
            errors.append(f"{loophole.get('id', '?')}: unknown rule_id {loophole.get('rule_id')!r}")
    for index, reveal in enumerate(world_system.get("reveal_plan") or []):
        if reveal.get("rule_id") not in known:
            errors.append(f"reveal {index}: unknown rule_id {reveal.get('rule_id')!r}")
    return errors


def validate_reveal_layer_count(reveal_plan: Iterable[dict], maximum_per_episode: int) -> list[str]:
    layers_by_episode: dict[int, set[str]] = defaultdict(set)
    for item in reveal_plan:
        layers_by_episode[item.get("episode")].add(item.get("layer"))
    return [
        f"episode {episode}: introduces {len(layers)} world-rule layers; maximum is {maximum_per_episode}"
        for episode, layers in sorted(layers_by_episode.items())
        if len(layers) > maximum_per_episode
    ]


def validate_condition_consequence_consistency(events: Iterable[dict]) -> list[str]:
    observed: dict[tuple[str, str], str] = {}
    errors = []
    for event in events:
        key = (event.get("rule_id"), event.get("condition_key"))
        consequence = event.get("consequence_key")
        if key in observed and observed[key] != consequence:
            errors.append(
                f"{key[0]} under condition {key[1]!r} has inconsistent consequences: "
                f"{observed[key]!r} vs {consequence!r}"
            )
        observed[key] = consequence
    return errors


def validate_registered_rule_usage(registered_rule_ids: Iterable[str], used_rule_ids: Iterable[str]) -> list[str]:
    unknown = sorted(set(used_rule_ids) - set(registered_rule_ids))
    return [f"downstream uses unregistered world rules: {unknown}"] if unknown else []


def validate_rule_choice_coverage(world_system: dict) -> list[str]:
    revealed = {item.get("rule_id") for item in world_system.get("reveal_plan") or [] if item.get("affected_choice")}
    active = {item.get("id") for item in world_system.get("rules") or []}
    missing = sorted(active - revealed)
    return [f"world rules without a planned affected choice: {missing}"] if missing else []
