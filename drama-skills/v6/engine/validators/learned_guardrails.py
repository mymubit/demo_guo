from __future__ import annotations

from collections.abc import Iterable, Mapping


STATE_CHANGE_KEYS = {"goal", "obstacle", "information", "relationship", "resource", "irreversible_consequence"}
FORBIDDEN_METADATA = {"artifact_key", "schema_version", "rule_params"}


def validate_revenge_opening(oppression_at_seconds: float | None) -> list[str]:
    return [] if oppression_at_seconds is not None and 0 <= oppression_at_seconds <= 30 else ["revenge opening must show oppression within 30 seconds"]


def validate_monologue_run(max_consecutive_lines: int) -> list[str]:
    return [] if max_consecutive_lines <= 3 else [f"internal monologue run is {max_consecutive_lines} lines; maximum is 3"]


def validate_identity_reveal(setup_episodes: int, first_hint_episode: int, reveal_ratio: float) -> list[str]:
    errors = []
    if setup_episodes < 5:
        errors.append("S-grade identity reveal requires at least 5 setup episodes")
    if first_hint_episode > 3:
        errors.append("S-grade identity reveal requires a hint within the first 3 episodes")
    if not 0.55 <= reveal_ratio <= 0.75:
        errors.append("S-grade identity reveal must occur in the 0.55-0.75 series window")
    return errors


def validate_progressive_beats(beats: Iterable[Mapping]) -> list[str]:
    beats = list(beats)
    if not beats:
        return ["episode contains no beats"]
    progressive = [item for item in beats if item.get("kind") == "progressive"]
    errors = []
    if len(progressive) / len(beats) < 0.60:
        errors.append("progressive beat ratio is below 0.60")
    for index, beat in enumerate(progressive):
        if not (set(beat.get("changes", [])) & STATE_CHANGE_KEYS):
            errors.append(f"progressive beat {index} changes no canonical story state")
    return errors


def validate_breathing_density(episodes: Iterable[int]) -> list[str]:
    values = sorted(set(episodes))
    errors = []
    if any(right == left + 1 for left, right in zip(values, values[1:])):
        errors.append("breathing episodes may not be consecutive")
    for start in values:
        window = [episode for episode in values if start <= episode <= start + 9]
        if len(window) > 1:
            errors.append(f"rolling episodes {start}-{start + 9} contain {len(window)} breathing episodes; maximum is 1")
            break
    return errors


def validate_crisis_rhythm(kind: str, plot_rhythm: str, emotional_rhythm: str) -> list[str]:
    crisis = {"major-reversal", "identity-reveal", "relationship-break"}
    if kind in crisis and (plot_rhythm, emotional_rhythm) != ("tight", "heavy"):
        return [f"crisis episode {kind} requires tight-heavy rhythm"]
    return []


def validate_structured_output(payload: object, canonical_enums: Mapping[str, set[str]]) -> list[str]:
    if not isinstance(payload, dict):
        return ["artifact payload must be a JSON object"]
    errors = []
    forbidden = sorted(FORBIDDEN_METADATA & set(payload))
    if forbidden:
        errors.append(f"artifact payload contains forbidden runtime metadata: {forbidden}")
    for field, allowed in canonical_enums.items():
        if field in payload and payload[field] not in allowed:
            errors.append(f"{field} uses noncanonical enum value {payload[field]!r}")
    return errors
