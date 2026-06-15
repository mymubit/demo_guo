# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase


class AgentRegistryConfigTests(SimpleTestCase):
    def test_workspace_mapping_reads_registry_meta(self):
        from apps.agent import runtime as registry

        fake_registry = {
            "_meta": {
                "workspace_modules": [
                    {"index": 1, "agent_id": "brief"},
                    {"index": 2, "agent_id": "world"},
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

    def test_workspace_mapping_returns_none_when_unconfigured(self):
        from apps.agent import runtime as registry

        fake_registry = {"_meta": {}, "agents": []}
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertIsNone(registry.agent_for_workspace_index(1))
            self.assertIsNone(registry.agent_for_pipeline_node_index(6))

    def test_workspace_mapping_reads_agents_workspace_index(self):
        from apps.agent import runtime as registry

        fake_registry = {
            "_meta": {},
            "agents": [
                {"id": "brief", "workspace_index": 1},
                {"id": "world", "workspace_index": 2},
            ],
        }
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertEqual(registry.agent_for_workspace_index(2), "world")

    def test_post_script_pipeline_index_reads_registry_meta(self):
        from apps.agent import runtime as registry

        fake_registry = {
            "_meta": {
                "workspace_modules": [{"index": 1, "agent_id": "brief"}],
                "post_script_pipeline_index": [
                    {"index": 6, "agent_id": "review"},
                    {"index": 7, "agent_id": "score"},
                ],
            },
            "agents": [],
        }
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertEqual(registry.agent_for_pipeline_node_index(6), "review")
            self.assertEqual(registry.agent_for_pipeline_node_index(7), "score")

    def test_post_script_chain_reads_registry_meta_first(self):
        from apps.agent import runtime as registry

        fake_registry = {
            "_meta": {"post_script_chain": ["review", "score"]},
            "post_script_chain": ["review", "polish", "review", "score"],
            "agents": [],
        }
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertEqual(registry.post_script_chain(), ["review", "score"])

    def test_post_script_effective_chain_appends_configured_agents(self):
        from apps.agent import runtime as registry

        fake_registry = {
            "_meta": {
                "post_script_chain": ["review", "score"],
                "post_script_append_agents": ["marketing"],
            },
            "agents": [],
        }
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertEqual(registry.post_script_effective_chain(), ["review", "score", "marketing"])

    def test_resolve_agent_runner_reads_configured_safe_path(self):
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
            runner = registry.resolve_agent_runner("review")

        self.assertIsNotNone(runner)
        self.assertEqual(runner.__name__, "run_review_agent")

    def test_resolve_agent_runner_rejects_unsafe_path(self):
        from apps.agent import runtime as registry

        fake_registry = {
            "_meta": {},
            "agents": [{"id": "bad", "runner": "os.system"}],
        }
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertIsNone(registry.resolve_agent_runner("bad"))

    def test_workspace_runner_uses_configured_agent_id(self):
        from apps.creation.orchestration import base
        from apps.creation.orchestration.types import AgentResult, WorkspaceInvokeOptions

        def fake_brief(project, *, options):
            return AgentResult(agent_id="brief", status="completed", outputs={"node": options.node_index})

        with patch("apps.creation.orchestration.base.agent_for_workspace_index", return_value="brief"):
            with patch("apps.creation.orchestration.base.resolve_agent_runner", return_value=fake_brief):
                result = base.run_workspace_agent(
                    project=None,
                    options=WorkspaceInvokeOptions(node_index=1),
                )

        self.assertEqual(result.agent_id, "brief")
        self.assertEqual(result.status, "completed")

    def test_should_defer_to_post_script_chain_in_workspace_mode(self):
        from apps.agent import runtime as registry
        from apps.creation.models import Project

        fake_registry = {
            "_meta": {
                "post_script_pipeline_index": [
                    {"index": 6, "agent_id": "review"},
                    {"index": 7, "agent_id": "score"},
                ],
            },
            "agents": [],
        }
        project = Project(pipeline_mode=Project.MODE_WORKSPACE)
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertTrue(registry.should_defer_to_post_script_chain(project, 6))
            self.assertFalse(registry.should_defer_to_post_script_chain(project, 5))

        project_step = Project(pipeline_mode=Project.MODE_STEP)
        with patch.object(registry, "get_agent_registry", return_value=fake_registry):
            self.assertFalse(registry.should_defer_to_post_script_chain(project_step, 6))


class AgentRegistryDbConfigTests(TestCase):
    def tearDown(self):
        from apps.agent.runtime import get_agent_registry

        get_agent_registry.cache_clear()

    def test_active_db_registry_is_runtime_source(self):
        from apps.agent.runtime import agent_for_workspace_index, get_agent_registry
        from apps.agent.models import AgentRegistryConfig

        AgentRegistryConfig.objects.create(
            config_key="test-active",
            display_name="测试 Agent 注册表",
            is_active=True,
            registry={
                "_meta": {
                    "workspace_modules": [
                        {"index": 1, "agent_id": "brief"},
                        {"index": 2, "agent_id": "world"},
                    ],
                    "post_script_pipeline_index": [
                        {"index": 6, "agent_id": "review"},
                        {"index": 7, "agent_id": "score"},
                    ],
                    "post_script_chain": ["review", "score"],
                },
                "post_script_chain": ["review", "score"],
                "agents": [
                    {"id": "brief", "name": "BriefAgent", "name_zh": "立项"},
                    {"id": "world", "name": "WorldAgent", "name_zh": "世界观"},
                ],
            },
        )
        get_agent_registry.cache_clear()

        registry = get_agent_registry()
        self.assertEqual(registry.get("_registry_source"), "db")
        self.assertEqual(agent_for_workspace_index(2), "world")
