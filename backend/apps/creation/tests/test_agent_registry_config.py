# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase


class AgentRegistryConfigTests(SimpleTestCase):
    def test_workspace_mapping_reads_registry_meta(self):
        from apps.agent import runtime as registry

        fake_registry = {
            "_meta": {
                "workspace_modules": [
                    {"index": 1, "agent_id": "brief"},
                    {"index": 2, "agent_id": "structure"},
                    {"index": 3, "agent_id": "character"},
                    {"index": 4, "agent_id": "outline"},
                    {"index": 5, "agent_id": "script"},
                ],
            },
            "agents": [],
        }
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertEqual(registry.agent_for_workspace_index(4), "outline")
            self.assertEqual(registry.workspace_index_for_agent("script"), 5)
            self.assertIsNone(registry.agent_for_pipeline_node_index(6))

    def test_workspace_mapping_returns_none_when_unconfigured(self):
        from apps.agent import runtime as registry

        fake_registry = {"_meta": {}, "agents": []}
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertEqual(registry.agent_for_workspace_index(1), "brief")
            self.assertIsNone(registry.agent_for_pipeline_node_index(6))

    def test_workspace_mapping_reads_agents_workspace_index(self):
        from apps.agent import runtime as registry

        fake_registry = {
            "_meta": {},
            "agents": [
                {"id": "brief", "workspace_index": 1},
                {"id": "structure", "workspace_index": 2},
            ],
        }
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertEqual(registry.agent_for_workspace_index(2), "structure")

    def test_removed_post_chain_runtime_api(self):
        from apps.agent import runtime as registry

        self.assertFalse(hasattr(registry, "post_script_chain"))
        self.assertFalse(hasattr(registry, "post_script_effective_chain"))
        self.assertFalse(hasattr(registry, "should_defer_to_post_script_chain"))

    def test_explicit_post_agents_are_catalog_only(self):
        from apps.agent.catalog import portal_agent_catalog
        from apps.agent import catalog

        fake_registry = {
            "_meta": {"version": "2.0.0"},
            "agents": [
                {"id": "brief", "workspace_index": 1},
                {"id": "structure", "workspace_index": 2},
                {"id": "character", "workspace_index": 3},
                {"id": "outline", "workspace_index": 4},
                {"id": "script", "workspace_index": 5},
                {"id": "review"},
                {"id": "score"},
                {"id": "polish"},
                {"id": "marketing"},
                {"id": "insight"},
            ],
        }
        with patch.object(catalog, "get_agent_registry", return_value=fake_registry):
            out = portal_agent_catalog()

        self.assertEqual(len(out["workspaceAgents"]), 5)
        self.assertEqual(out["explicitPostAgents"], ["review", "score", "polish", "marketing", "insight"])

    def test_resolve_agent_runner_rejects_removed_python_runner_path(self):
        from apps.agent import runtime as registry

        fake_registry = {
            "_meta": {},
            "agents": [
                {
                    "id": "review",
                    "runner": "apps.creation.orchestration.review.run_review_agent",
                }
            ],
        }
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertIsNotNone(registry.resolve_agent_runner("review"))

    def test_resolve_agent_runner_rejects_unsafe_path(self):
        from apps.agent import runtime as registry

        fake_registry = {
            "_meta": {},
            "agents": [{"id": "bad", "runner": "os.system"}],
        }
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertIsNone(registry.resolve_agent_runner("bad"))

    def test_workspace_runner_uses_skill_invoker(self):
        from apps.skill.skills.invoker import get_skill_invoker

        with patch("apps.skill.skills.invoker.SkillInvoker.invoke") as mock_invoke:
            skill_result = MagicMock()
            skill_result.success = True
            skill_result.data = {"node": 1}
            skill_result.error = {}
            skill_result.skill_id = "creation.brief"
            skill_result.trace_id = "trace-brief"
            mock_invoke.return_value = skill_result

            result = get_skill_invoker().invoke(
                skill_id="creation.brief",
                payload={"project_id": "proj-1"},
                project_id="proj-1",
                user_id=1,
            )

        self.assertTrue(result.success)
        self.assertEqual(result.data["node"], 1)


class AgentRegistryDbConfigTests(TestCase):
    def tearDown(self):
        from apps.agent.runtime import get_agent_registry

        get_agent_registry.cache_clear()

    def test_active_db_registry_is_runtime_source(self):
        from apps.agent.runtime import agent_for_pipeline_node_index, agent_for_workspace_index, get_agent_registry
        from apps.agent.models import AgentRegistryConfig

        AgentRegistryConfig.objects.create(
            config_key="test-active",
            display_name="Test Agent Registry",
            is_active=True,
            registry={
                "_meta": {
                    "workspace_modules": [
                        {"index": 1, "agent_id": "brief"},
                        {"index": 2, "agent_id": "structure"},
                        {"index": 3, "agent_id": "character"},
                        {"index": 4, "agent_id": "outline"},
                        {"index": 5, "agent_id": "script"},
                    ],
                    "post_script_pipeline_index": [
                        {"index": 6, "agent_id": "review"},
                        {"index": 7, "agent_id": "score"},
                    ],
                },
                "agents": [
                    {"id": "brief", "name": "BriefAgent", "name_zh": "Brief"},
                    {"id": "structure", "name": "StructureAgent", "name_zh": "Structure"},
                ],
            },
        )
        get_agent_registry.cache_clear()

        registry = get_agent_registry()
        self.assertEqual(registry.get("_registry_source"), "db")
        self.assertEqual(agent_for_workspace_index(2), "structure")
        self.assertIsNone(agent_for_pipeline_node_index(6))
