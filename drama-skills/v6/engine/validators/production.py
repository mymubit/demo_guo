from __future__ import annotations

from collections.abc import Iterable, Mapping


def validate_high_complexity_alternatives(assessments: Iterable[Mapping]) -> list[str]:
    return [f"{item.get('scene_id', '?')}: high complexity requires an alternative" for item in assessments if item.get("complexity") == "high" and not item.get("alternatives")]


def validate_budget_boundary(verified_quotes: bool, estimate: Mapping) -> list[str]:
    if not verified_quotes and estimate.get("mode") != "band":
        return ["amount estimate requires verified region, schedule, personnel, and supplier quotes"]
    if estimate.get("mode") == "amount":
        required = {"currency", "region", "price_version", "excluded_items"}
        missing = sorted(required - set(estimate))
        if missing:
            return [f"amount estimate missing provenance: {missing}"]
    return []


def validate_release_policy(release_check: Mapping) -> list[str]:
    status = release_check.get("policy_status")
    ready = release_check.get("release_ready")
    if status != "verified-current" and ready:
        return [f"release cannot be ready with policy status {status!r}"]
    return []


def validate_release_evidence(release_check: Mapping) -> list[str]:
    evidence = ["ai_content_labeling", "filing_materials", "title_check", "rights_authorization", "quality_report", "compliance_report"]
    missing = [key for key in evidence if not release_check.get(key)]
    if missing and release_check.get("release_ready"):
        return [f"release-ready conclusion missing evidence: {missing}"]
    return []
