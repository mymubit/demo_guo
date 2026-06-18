# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.common.agent_term import (
    alias_agent_id,
    attach_api_meta,
    enrich_registry_for_api,
    normalize_agent_runner_path,
    normalize_pipeline_runner_path,
    normalize_registry_for_save,
    resolve_agent_id,
)
from apps.common.skill_term import resolve_skill_id


class AgentTermTests(SimpleTestCase):
    def test_resolve_agent_id_prefers_agent_id(self):
        self.assertEqual(resolve_agent_id({"agent_id": "world", "skill_id": "brief"}), "world")

    def test_resolve_agent_id_falls_back_to_skill_id(self):
        self.assertEqual(resolve_agent_id({"skill_id": "script"}), "script")

    def test_alias_agent_id_emits_agent_id_only(self):
        row = alias_agent_id({"skill_id": "outline", "skillId": "outline"})
        self.assertEqual(row["agent_id"], "outline")
        self.assertEqual(row["agentId"], "outline")
        self.assertNotIn("skill_id", row)

    def test_normalize_registry_workspace_modules(self):
        registry = {"_meta": {"workspace_modules": [{"index": 1, "skill_id": "brief"}]}, "agents": []}
        out = normalize_registry_for_save(registry)
        self.assertEqual(out["_meta"]["workspace_modules"][0]["agent_id"], "brief")

    def test_normalize_legacy_agent_runner_path(self):
        self.assertEqual(
            normalize_agent_runner_path("apps.creation.agents.world.run_world_agent"),
            "",
        )

    def test_normalize_orchestration_agent_runner_path(self):
        path = "apps.creation.orchestration.world.run_world_agent"
        self.assertEqual(normalize_agent_runner_path(path), "")

    def test_normalize_registry_agent_runners(self):
        registry = {
            "agents": [
                {
                    "id": "world",
                    "runner": "apps.creation.orchestration.world.run_world_agent",
                }
            ]
        }
        out = normalize_registry_for_save(registry)
        self.assertEqual(out["agents"][0]["runner"], "")

    def test_normalize_pipeline_runner_rejects_agent_runner(self):
        self.assertEqual(
            normalize_pipeline_runner_path(
                "apps.creation.agents.world.run_world_agent",
                "fusion_node",
            ),
            "",
        )
        self.assertEqual(
            normalize_pipeline_runner_path(
                "apps.creation.orchestration.review.run_review_agent",
                "fusion_review",
            ),
            "",
        )

    def test_attach_api_meta_lists_deprecations(self):
        payload = attach_api_meta({"items": []})
        self.assertEqual(payload["api_meta"]["deprecated_fields"]["skill_id"], "agent_id")

    def test_enrich_registry_adds_agent_id(self):
        registry = {
            "_meta": {"workspace_modules": [{"index": 1, "agent_id": "brief"}]},
            "agents": [{"id": "brief", "name": "Brief"}],
        }
        out = enrich_registry_for_api(registry)
        self.assertEqual(out["_meta"]["workspace_modules"][0]["agent_id"], "brief")
        self.assertEqual(out["agents"][0]["agent_id"], "brief")


class SkillTermTests(SimpleTestCase):
    def test_resolve_skill_id_sub_skill(self):
        self.assertEqual(resolve_skill_id({"skill_id": "verify-creation"}), "verify-creation")
        self.assertEqual(resolve_skill_id({"sub_skill_id": "cli-step"}), "cli-step")
