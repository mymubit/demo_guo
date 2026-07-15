# -*- coding: utf-8 -*-
"""Drama Skills Bundle 加载器。"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from django.conf import settings


_SCOPE_TIER = {
    "global_core": 1,
    "genre_profile": 2,
    "stage_playbook": 3,
    "compliance_block": 4,
}

_RULE_FILES = [
    "foundation/rules/philosophy.yaml",
    "foundation/rules/narrative-craft.yaml",
    "foundation/rules/rhythm-rules.yaml",
    "foundation/rules/character-rules.yaml",
    "foundation/rules/dialogue-rules.yaml",
    "foundation/rules/writing-rules.yaml",
    "foundation/rules/plotting-rules.yaml",
    "foundation/rules/scoring-core.yaml",
    "foundation/rules/learned-rules.yaml",
    "foundation/rules/stage-playbook.yaml",
    "foundation/rules/compliance-core.yaml",
    "foundation/rules/originality-rules.yaml",
    "foundation/rules/concept-rules.yaml",
    "foundation/rules/structure-rules.yaml",
    "foundation/rules/world-rules.yaml",
    "foundation/rules/production-rules.yaml",
    "foundation/rules/genre-profile.yaml",
]


class SkillsBundleLoader:
    """从 DRAMA_SKILLS_ROOT 读取 manifest、编排与 schema 索引。"""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root or settings.DRAMA_SKILLS_ROOT)

    @property
    def manifest(self) -> dict[str, Any]:
        return self._load_yaml("manifest/drama-skills.manifest.yaml")

    @property
    def registry(self) -> dict[str, Any]:
        rel = self.manifest.get("registries", {}).get("roles", "registry.yaml")
        return self._load_yaml(rel)

    @property
    def modules_catalog(self) -> dict[str, Any]:
        rel = self.manifest.get("registries", {}).get("modules", "modules/catalog.yaml")
        return self._load_yaml(rel)

    @property
    def workbench(self) -> dict[str, Any]:
        rel = self.manifest.get("workbench", {}).get("definition", "workbench/workbench.yaml")
        return self._load_yaml(rel)

    @property
    def config_policy(self) -> dict[str, Any]:
        return self._load_yaml("manifest/config-policy.yaml")

    @property
    def workflow_transitions(self) -> dict[str, Any]:
        path = self.manifest.get("orchestration", {}).get("transitions")
        return self._load_yaml(path) if path else {}

    @property
    def agent_runtime(self) -> dict[str, Any]:
        rel = self.manifest.get("configuration_sources", {}).get(
            "agent_runtime", "foundation/constraints/agent-runtime.yaml"
        )
        return self._load_yaml(rel)

    @property
    def bundle_version(self) -> str:
        return str(self.manifest.get("bundle_version", "5.0.0"))

    def get_role_entry(self, agent_id: str) -> dict[str, Any]:
        for role in self.registry.get("roles", []):
            if role.get("agent_id") == agent_id:
                return role
        raise KeyError(f"未注册角色: {agent_id}")

    def get_role_contract(self, agent_id: str) -> dict[str, Any]:
        entry = self.get_role_entry(agent_id)
        skill_dir = entry.get("skill_dir") or f"roles/{agent_id.replace('.', '-')}"
        return self._load_yaml(f"{skill_dir}/role.yaml")

    def load_skill(self, agent_id: str) -> str:
        entry = self.get_role_entry(agent_id)
        skill_dir = entry.get("skill_dir") or f"roles/{agent_id.replace('.', '-')}"
        path = self.root / skill_dir / "SKILL.md"
        if not path.exists():
            return ""
        text = path.read_text(encoding="utf-8")
        return _strip_frontmatter(text)

    def load_module(self, module_id: str) -> str:
        path = self.root / "modules" / f"{module_id}.md"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def load_modules_for_role(self, agent_id: str) -> str:
        contract = self.get_role_contract(agent_id)
        parts: list[str] = []
        for module_id in contract.get("modules", []):
            body = self.load_module(module_id)
            if body:
                parts.append(f"### {module_id}\n{body}")
        return "\n\n".join(parts)

    def load_knowledge_sections_index(self) -> str:
        path = self.root / "knowledge/knowledge-sections.md"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def get_orchestration_track(self, entry_type: str) -> dict[str, Any]:
        orch = self.manifest.get("orchestration", {})
        rel = orch.get(entry_type) or orch.get("original_track")
        if not rel:
            raise FileNotFoundError(f"缺少编排轨道: {entry_type}")
        return self._load_yaml(rel)

    def artifact_schema_path(self, artifact_key: str) -> str:
        contracts = self.manifest.get("artifact_contracts", {}).get("schemas", {})
        for schema_version, rel_path in contracts.items():
            key = schema_version.split(".")[0].replace("-", "_")
            if key == artifact_key or artifact_key.replace("_", "-") in schema_version:
                return rel_path
        mapping = {
            "project_brief": "schemas/artifacts/project-brief.v1.schema.json",
            "story_bible": "schemas/artifacts/story-bible.v1.schema.json",
            "narrative_plan": "schemas/artifacts/narrative-plan.v1.schema.json",
            "episode_scripts": "schemas/artifacts/episode-scripts.v1.schema.json",
            "quality_report": "schemas/artifacts/quality-report.v1.schema.json",
            "compliance_report": "schemas/artifacts/compliance-report.v1.schema.json",
            "polished_script": "schemas/artifacts/polished-script.v1.schema.json",
            "production_package": "schemas/artifacts/production-pack.v1.schema.json",
            "external_script": "schemas/artifacts/episode-scripts.v1.schema.json",
        }
        return mapping[artifact_key]

    def load_artifact_schema(self, artifact_key: str) -> dict[str, Any]:
        return self.load_json(self.artifact_schema_path(artifact_key))

    def project_runtime_projection(
        self,
        agent_id: str,
        settings: dict[str, Any],
        workflow_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        projection_cfg = (self.workbench.get("runtime_projection") or {}).get(agent_id, {})
        if not projection_cfg:
            return {}
        when_expr = projection_cfg.get("when")
        if when_expr and not _eval_when(when_expr, settings):
            return {}
        result: dict[str, Any] = {}
        for param, source_path in projection_cfg.items():
            if param == "when":
                continue
            result[param] = _deep_get(settings, source_path)
        wf_projection = (self.workbench.get("runtime_projection") or {}).get("workflow", {})
        if workflow_state and wf_projection:
            for param, source_path in wf_projection.items():
                if param not in result:
                    result[param] = _deep_get(settings, source_path)
            result["batch_cursor"] = workflow_state.get("batch_cursor")
            result["revision_round"] = workflow_state.get("revision_round")
        return result

    def collect_rules(
        self,
        agent_id: str,
        settings: dict[str, Any],
        *,
        max_chars: int = 3200,
    ) -> str:
        contract = self.get_role_contract(agent_id)
        scopes = (contract.get("rule_policy") or {}).get("scopes", ["global_core"])
        theme_code = _resolve_theme_code(settings)
        items: list[tuple[int, str]] = []

        for rel_path in _RULE_FILES:
            data = self._load_yaml(rel_path)
            tier = data.get("tier")
            for item in data.get("items", []):
                if not _rule_matches_scope(item, tier, scopes, agent_id, theme_code):
                    continue
                body = (item.get("body") or "").strip()
                if body:
                    title = item.get("title", item.get("rule_key", ""))
                    priority = int(item.get("priority", 100))
                    items.append((priority, f"- {title}\n{body}"))

        items.sort(key=lambda pair: pair[0])
        text = "\n\n".join(body for _, body in items)
        if len(text) > max_chars:
            return text[: max_chars - 3] + "..."
        return text

    def load_seed_yaml(self, relative_path: str) -> dict[str, Any]:
        return self._load_yaml(relative_path)

    def _load_yaml(self, relative_path: str) -> dict[str, Any]:
        path = self.root / relative_path
        if not path.exists():
            raise FileNotFoundError(f"技能文件不存在: {relative_path}")
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def load_json(self, relative_path: str) -> Any:
        path = self.root / relative_path
        return json.loads(path.read_text(encoding="utf-8"))


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        match = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.DOTALL)
        if match:
            return text[match.end() :].strip()
    return text.strip()


def _deep_get(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _resolve_theme_code(settings: dict[str, Any]) -> str:
    matrix = settings.get("genre_matrix") or {}
    if matrix:
        return "-".join(
            matrix.get(axis, "")
            for axis in ("emotion", "identity", "conflict", "world")
        )
    return settings.get("preset_theme_code") or ""


def _rule_matches_scope(
    item: dict[str, Any],
    tier: int | None,
    scopes: list[str],
    agent_id: str,
    theme_code: str,
) -> bool:
    if tier == 1 and "global_core" in scopes:
        if item.get("scope_type") == "agent":
            return item.get("scope_key") == agent_id
        return item.get("scope_type") in (None, "global")
    if tier == 2 and "genre_profile" in scopes:
        scope_key = item.get("scope_key", "")
        return scope_key in ("", theme_code) or not scope_key
    if tier == 3 and "stage_playbook" in scopes:
        return item.get("scope_key") == agent_id
    if tier == 4 and "compliance_block" in scopes:
        return True
    return False


def _eval_when(expression: str, settings: dict[str, Any]) -> bool:
    match = re.match(
        r"^creation_preferences\.(\w+)\s*==\s*(true|false)$",
        expression.strip(),
    )
    if match:
        field, raw = match.groups()
        prefs = settings.get("creation_preferences") or {}
        expected = raw == "true"
        return bool(prefs.get(field)) == expected
    return True


@lru_cache(maxsize=1)
def get_skills_loader() -> SkillsBundleLoader:
    return SkillsBundleLoader()
