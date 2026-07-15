# -*- coding: utf-8 -*-
"""按角色契约组装 LLM 提示词，不泄露无关角色 prompt。"""
from __future__ import annotations

import json
from typing import Any

from apps.drama.services.skills_loader import SkillsBundleLoader, get_skills_loader


class PromptBuilder:
    """基于 Skills SSOT 构建 system/user prompt。"""

    def __init__(self, loader: SkillsBundleLoader | None = None) -> None:
        self.loader = loader or get_skills_loader()

    def build(
        self,
        role: str,
        *,
        settings: dict[str, Any],
        workflow_state: dict[str, Any],
        artifacts: dict[str, Any],
        input_payload: dict[str, Any] | None = None,
        latest_script: dict[str, Any] | None = None,
        scoring_mode: str = "project",
    ) -> tuple[str, str]:
        contract = self.loader.get_role_contract(role)
        entry = self.loader.get_role_entry(role)
        max_chars = int((contract.get("rule_policy") or {}).get("max_chars", 3200))

        skill_text = self.loader.load_skill(role)
        modules_text = self.loader.load_modules_for_role(role)
        rules_text = self.loader.collect_rules(role, settings, max_chars=max_chars)
        runtime = self.loader.project_runtime_projection(role, settings, workflow_state)
        artifact_key = contract.get("default_output_artifact_key", "")
        schema_version = contract.get("schema_version", "")

        system_parts = [
            f"你是 {entry.get('name_zh', role)}（agent_id={role}）。",
            contract.get("role", ""),
            "",
            "## 职责与技能",
            skill_text,
        ]
        if modules_text:
            system_parts.extend(["", "## 模块步骤", modules_text])
        if rules_text:
            system_parts.extend(["", "## 规则与约束", rules_text])
        system_parts.extend(
            [
                "",
                f"## 输出契约",
                f"- artifact_key: {artifact_key}",
                f"- schema_version: {schema_version}",
                "仅输出符合 schema 的 JSON 对象，不要输出解释文字。",
            ]
        )
        system_prompt = "\n".join(part for part in system_parts if part is not None)

        user_body: dict[str, Any] = {
            "runtime_projection": runtime,
            "project_settings": _settings_subset(settings),
            "input": input_payload or {},
            "required_artifacts": _required_artifacts(contract, artifacts),
            "output": {
                "artifact_key": artifact_key,
                "schema_version": schema_version,
            },
        }
        if latest_script is not None:
            user_body["latest_script"] = latest_script
        if scoring_mode:
            user_body["scoring_mode"] = scoring_mode

        user_prompt = json.dumps(user_body, ensure_ascii=False, indent=2)
        return system_prompt, user_prompt


def _settings_subset(settings: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "entry_type",
        "title",
        "core_idea",
        "synopsis",
        "external_story",
        "adapt_notes",
        "genre_matrix",
        "episode_count",
        "target_platform",
        "creation_preferences",
        "production_context",
        "derived",
    )
    return {key: settings[key] for key in keys if key in settings}


def _required_artifacts(
    contract: dict[str, Any],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    input_contract = contract.get("input_contract") or {}
    required = list(input_contract.get("required_artifacts") or [])
    result: dict[str, Any] = {}
    for key in required:
        if key == "latest_script":
            continue
        if key in artifacts:
            result[key] = artifacts[key]
    return result
