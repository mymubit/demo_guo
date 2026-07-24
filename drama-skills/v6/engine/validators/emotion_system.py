from __future__ import annotations

from collections.abc import Iterable


def validate_episode_profile(profile: dict) -> list[str]:
    nodes = profile.get("nodes") or []
    indexes = [item.get("index") for item in nodes]
    errors = []
    if sorted(indexes) != list(range(1, 9)):
        errors.append(f"episode {profile.get('episode', '?')}: emotion node indexes must be exactly 1-8")
    by_index = {item.get("index"): item for item in nodes}
    landmarks = profile.get("landmarks") or {}
    for key in ("EV", "ET", "TP"):
        if landmarks.get(key) not in by_index:
            errors.append(f"episode {profile.get('episode', '?')}: {key} references a missing node")
    et_index = landmarks.get("ET")
    if et_index in by_index and nodes:
        minimum = min(item.get("value") for item in nodes)
        if by_index[et_index].get("value") != minimum:
            errors.append(f"episode {profile.get('episode', '?')}: ET does not reference the minimum value")
    return errors


def validate_ev_platform(episode_values: Iterable[tuple[int, int]], window: int, difference_threshold: int) -> list[str]:
    values = list(episode_values)
    errors = []
    for offset in range(len(values) - window + 1):
        group = values[offset : offset + window]
        scores = [score for _, score in group]
        if max(scores) - min(scores) < difference_threshold:
            errors.append(
                f"EV platform across episodes {group[0][0]}-{group[-1][0]}: range {max(scores) - min(scores)}"
            )
    return errors


def validate_trough_and_recovery(series_curve: Iterable[dict]) -> list[str]:
    points = list(series_curve)
    trough_indexes = [index for index, point in enumerate(points) if point.get("kind") == "trough"]
    if not trough_indexes:
        return ["series emotion curve has no declared trough"]
    for index in trough_indexes:
        value = points[index].get("target_value")
        if any(point.get("target_value", 0) > value for point in points[index + 1 :]):
            return []
    return ["series emotion curve has no recovery after a trough"]


def validate_payment_rising_edges(series_curve: Iterable[dict]) -> list[str]:
    points = list(series_curve)
    errors = []
    for index, point in enumerate(points):
        if not point.get("payment_checkpoint"):
            continue
        if index == 0 or point.get("target_value", 0) <= points[index - 1].get("target_value", 0):
            errors.append(f"episode {point.get('episode')}: payment checkpoint is not on a rising edge")
    return errors


def validate_breathing_runs(series_curve: Iterable[dict]) -> list[str]:
    points = list(series_curve)
    return [
        f"episodes {left.get('episode')} and {right.get('episode')}: consecutive breathing episodes"
        for left, right in zip(points, points[1:])
        if left.get("kind") == right.get("kind") == "breathing"
    ]
