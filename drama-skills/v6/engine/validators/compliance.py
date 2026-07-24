from __future__ import annotations

from collections.abc import Iterable, Mapping


DIMENSIONS = {"values", "character-portrayal", "minor-protection", "copyright", "social-sensitivity", "false-promotion", "horror", "crime-display", "platform-redlines"}
HORROR_DISPOSITIONS = {"extreme": "P0", "high-risk": "P1", "medium-risk": "P2"}


def classify_horror(level: str) -> str:
    if level not in HORROR_DISPOSITIONS:
        raise ValueError(f"unknown horror level: {level}")
    return HORROR_DISPOSITIONS[level]


def validate_dimensions(dimensions: Iterable[Mapping]) -> list[str]:
    items = list(dimensions)
    names = [item.get("name") for item in items]
    errors = []
    if set(names) != DIMENSIONS or len(names) != len(DIMENSIONS):
        errors.append("risk assessment must cover each canonical dimension exactly once")
    return errors


def validate_platform_declaration(target_platform: str | None, rule_version: str | None, status: str) -> list[str]:
    if target_platform and (not rule_version or status != "verified"):
        return ["declared platform requires a verified rule version"]
    if not target_platform and status != "not-checked":
        return ["missing platform must remain not-checked"]
    return []


def validate_delivery_materials(materials: Mapping, conclusion: str) -> list[str]:
    missing = sorted(key for key, present in materials.items() if not present)
    return [f"delivery pass missing materials: {missing}"] if conclusion == "pass" and missing else []


def decide_compliance(findings: Iterable[Mapping], dimensions: Iterable[Mapping], materials_complete: bool = True) -> dict:
    findings = list(findings)
    has_p0 = any(item.get("severity") == "P0" for item in findings)
    has_open_p1 = any(item.get("severity") == "P1" and item.get("status") != "resolved" for item in findings)
    has_unchecked = any(item.get("status") == "not-checked" for item in dimensions)
    if has_p0:
        return {"conclusion": "block", "downstream_allowed": False}
    if has_open_p1 or has_unchecked or not materials_complete:
        return {"conclusion": "revise", "downstream_allowed": False}
    return {"conclusion": "pass", "downstream_allowed": True}


def validate_justice_closure(crime_evidence: Iterable[Mapping], justice_closures: Iterable[Mapping]) -> list[str]:
    crime_items = list(crime_evidence)
    closures = list(justice_closures)
    if len(crime_items) < 2:
        return []
    required = 3 if len(crime_items) >= 5 else 2
    errors = []
    if len(closures) < required:
        errors.append(f"crime evidence count {len(crime_items)} requires {required} justice closures; found {len(closures)}")
    if not any(float(item.get("story_progress", -1)) >= 0.65 for item in closures):
        errors.append("justice closure required in final 35 percent of story")
    return errors


def validate_whitewash_markers(markers: Iterable[Mapping]) -> list[str]:
    errors = []
    for marker in markers:
        if not marker.get("responsibility_retained") or not marker.get("consequence_present"):
            errors.append(f"{marker.get('id', '?')}: sympathy marker removes responsibility or consequence")
    return errors


def validate_harmful_behavior_framing(items: Iterable[Mapping]) -> list[str]:
    errors = []
    for item in items:
        if item.get("glorified") and (not item.get("responsibility_retained") or not item.get("consequence_present")):
            errors.append(f"{item.get('id', '?')}: harmful behavior is glorified without accountability")
    return errors
