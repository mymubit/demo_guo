from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def _matches(expected: Any, actual: Any) -> bool:
    if isinstance(expected, list):
        if isinstance(actual, (list, tuple, set)):
            return bool(set(expected) & set(actual))
        return actual in expected
    return expected == actual


def resolve_advisory_patterns(
    context: Mapping[str, Any], packs: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    """Resolve optional dialogue suggestions without producing gate failures."""
    packs = list(packs)
    precedence = []
    for pack in packs:
        for key in pack.get("precedence", []):
            if key not in precedence:
                precedence.append(key)

    applied_patterns = []
    suggestions = []
    avoid = []
    for pack in packs:
        for pattern in pack.get("patterns", []):
            conditions = pattern.get("when", {})
            matches = []
            for key, expected in conditions.items():
                actual = context.get(key)
                if key == "candidate_terms" and isinstance(expected, list):
                    actual_terms = set(actual or [])
                    matches.append(len(set(expected) & actual_terms) >= 2)
                else:
                    matches.append(_matches(expected, actual))
            if not all(matches):
                continue
            applied_patterns.append(f"{pack.get('id')}#{pattern.get('id')}")
            suggestions.extend(pattern.get("suggestions", []))
            avoid.extend(pattern.get("avoid", []))

    voice_tag = context.get("character.voice_tag") or context.get("voice_tag")
    if voice_tag:
        suggestions.insert(0, f"Preserve character.voice_tag: {voice_tag}")

    return {
        "precedence": precedence,
        "applied_patterns": applied_patterns,
        "suggestions": list(dict.fromkeys(suggestions)),
        "avoid": list(dict.fromkeys(avoid)),
        "blocking_errors": [],
    }
