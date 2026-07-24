from __future__ import annotations

from collections.abc import Iterable


def validate_segments(segments: Iterable[dict], tolerance: float = 1e-6) -> list[str]:
    segments = list(segments)
    expected = {"hook", "situation", "escalation", "cliffhanger"}
    actual = [item.get("kind") for item in segments]
    errors = []
    if set(actual) != expected or len(actual) != 4:
        errors.append(f"episode segments must contain each canonical kind exactly once: {sorted(expected)}")
    total = sum(float(item.get("ratio", 0)) for item in segments)
    if abs(total - 1.0) > tolerance:
        errors.append(f"episode segment ratios sum to {total}, expected 1.0")
    return errors


def validate_information_gaps(gaps: Iterable[dict]) -> list[str]:
    errors = []
    for gap in gaps:
        overlap = sorted(set(gap.get("knowers") or []) & set(gap.get("nonknowers") or []))
        if overlap:
            errors.append(f"{gap.get('id', '?')}: actors both know and do not know the secret: {overlap}")
    return errors


def validate_scene_value_changes(scenes: Iterable[dict]) -> list[str]:
    return [
        f"{scene.get('id', '?')}: value state does not change"
        for scene in scenes
        if scene.get("value_before") == scene.get("value_after")
    ]


def validate_dialogue_speakers(scenes: Iterable[dict], character_ids: Iterable[str]) -> list[str]:
    known = set(character_ids)
    errors = []
    for scene in scenes:
        for index, line in enumerate(scene.get("dialogue") or []):
            if line.get("speaker") not in known:
                errors.append(f"{scene.get('id', '?')} dialogue {index}: unknown speaker {line.get('speaker')!r}")
    return errors


def validate_scene_power_shift(scenes: Iterable[dict]) -> list[str]:
    errors = []
    for scene in scenes:
        dialogue = scene.get("dialogue") or []
        if dialogue and not any(line.get("power_before") != line.get("power_after") for line in dialogue):
            errors.append(f"{scene.get('id', '?')}: dialogue contains no observable power shift")
    return errors
