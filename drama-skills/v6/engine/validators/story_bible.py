from __future__ import annotations

from collections.abc import Mapping


STAGE_ORDER = ["opening", "warming", "climax", "turning", "sprint", "ending"]
COMPONENTS = {"project_brief", "character_system", "world_system", "originality_report"}


def validate_mode_source(mode: str, source_kind: str, treatment: Mapping | None) -> list[str]:
    if mode == "original":
        return [] if source_kind == "project_brief" and treatment is None else ["original mode requires project_brief and no adaptation treatment"]
    required = {"extracted_characters", "extracted_conflict", "extracted_structure", "retained", "enhanced", "rewritten", "originality_report_version"}
    if source_kind != "external_story" or treatment is None or not required <= set(treatment):
        return ["adaptation mode requires external_story and complete treatment"]
    return []


def validate_component_references(components: Mapping) -> list[str]:
    if set(components) != COMPONENTS:
        return ["story-bible must reference exactly the canonical components"]
    for name, reference in components.items():
        if not all(reference.get(key) for key in ("schema", "schema_version", "artifact_version")):
            return [f"component {name} has incomplete version reference"]
    return []


def validate_stage_ranges(stages: list[Mapping], episode_count: int) -> list[str]:
    if [item.get("name") for item in stages] != STAGE_ORDER:
        return ["story-bible stages use noncanonical order"]
    expected_start = 1
    for stage in stages:
        if stage.get("start_episode") != expected_start or stage.get("end_episode", 0) < expected_start:
            return [f"stage {stage.get('name')} is not contiguous"]
        expected_start = stage["end_episode"] + 1
    return [] if expected_start == episode_count + 1 else ["stage ranges do not cover the full episode count"]
