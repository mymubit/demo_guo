from __future__ import annotations

from collections.abc import Iterable, Mapping


PROTECTED_CLASSES = {"character-name", "title-or-slogan", "key-plot-structure", "signature-dialogue", "character-image-or-voiceprint", "target-market-rights"}
REWRITE_DIMENSIONS = {"character-relationships", "scene", "timing", "causal-chain"}


def validate_protected_element_coverage(elements: Iterable[Mapping]) -> list[str]:
    items = list(elements)
    classes = [item.get("class") for item in items]
    return [] if set(classes) == PROTECTED_CLASSES and len(classes) == 6 else ["each protected-element class must be checked exactly once"]


def similarity_findings(title_semantic: float, dialogue: float, episode_position_structure: float) -> list[str]:
    findings = []
    if title_semantic > 0.72:
        findings.append("title-semantic")
    if dialogue > 0.80:
        findings.append("dialogue")
    if episode_position_structure > 0.20:
        findings.append("episode-position-structure")
    return findings


def validate_comparison_conclusion(comparison_status: str, conclusion: str) -> list[str]:
    if comparison_status != "completed" and conclusion != "not-completed":
        return ["unavailable comparison must conclude not-completed"]
    return []


def validate_rewrite_plan(changed_dimensions: Iterable[str], rename_only: bool) -> list[str]:
    changed = set(changed_dimensions)
    errors = []
    if changed != REWRITE_DIMENSIONS:
        errors.append(f"rewrite must change all structural dimensions: {sorted(REWRITE_DIMENSIONS)}")
    if rename_only:
        errors.append("rename-only rewrite is prohibited")
    return errors


def validate_ai_assets(assets: Iterable[Mapping]) -> list[str]:
    errors = []
    for asset in assets:
        if asset.get("identifiable_imitation"):
            errors.append(f"{asset.get('id', '?')}: identifiable imitation is prohibited")
        if asset.get("label_required") and asset.get("label_status") != "applied":
            errors.append(f"{asset.get('id', '?')}: required AI label is missing")
    return errors
