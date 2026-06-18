# -*- coding: utf-8 -*-
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.models import AgentExecutionRun, Project

User = get_user_model()


class AgentOutputValidationCoverageTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()

    def test_validate_output_accepts_all_chain_artifacts(self):
        cases = {
            "adapt": (AgentDefinitionService.get_runnable("adapt"), {"adaptation_meta": {}, "project_brief": {}}),
            "brief": (AgentDefinitionService.get_runnable("brief"), {"project_brief": {}}),
            "structure": (AgentDefinitionService.get_runnable("structure"), {"structure_plan": {}}),
            "character": (AgentDefinitionService.get_runnable("character"), {"character_bible": {}}),
            "outline": (AgentDefinitionService.get_runnable("outline"), {"series_outline": {}}),
            "script": (
                AgentDefinitionService.get_runnable("script"),
                {"episode_scripts": {"episodes": [{"episodeNumber": 1}]}},
            ),
            "review": (AgentDefinitionService.get_runnable("review"), {"review_report": {"passed": True}}),
            "score": (
                AgentDefinitionService.get_runnable("score"),
                {"script_score_report": {"overallScore": 80}},
            ),
            "marketing": (AgentDefinitionService.get_runnable("marketing"), {"marketing_kit": {}}),
        }
        for agent_id, (agent, output) in cases.items():
            with self.subTest(agent_id=agent_id):
                result = IndependentAgentService.validate_output(agent, output)
                self.assertTrue(result)

    def test_validate_output_falls_back_when_artifact_key_invalid(self):
        """真实 LLM 自创 artifact_key 时回退到契约默认 key，而非整链失败。"""
        agent = AgentDefinitionService.get_runnable("adapt")
        output = {
            "artifact_key": "overbearing-ceo-drama-adaptation",
            "payload": {"logline": "x", "tone": "y"},
        }
        result = IndependentAgentService.validate_output(agent, output)
        self.assertIn(agent.default_output_artifact_key, result)
        self.assertNotIn("overbearing-ceo-drama-adaptation", result)

    def test_render_template_allows_braces_in_injected_data(self):
        """注入的产物内容含 {{ }} 时不应触发模板渲染失败。"""
        ctx = {
            "agent": SimpleNamespace(agent_id="x", name="x", name_zh="x"),
            "input": {"artifacts": {"x": "含有{{占位}}的真实内容"}, "project": {}, "params": {}},
            "knowledge": [],
        }
        rendered = IndependentAgentService._render_template("前缀 {{artifacts.x}} 后缀", ctx)
        self.assertIn("含有{{占位}}的真实内容", rendered)

    def test_render_template_rejects_unresolved_template_var(self):
        from apps.creation.agent_runtime.independent_service import AgentRuntimeError

        ctx = {
            "agent": SimpleNamespace(agent_id="x", name="x", name_zh="x"),
            "input": {"artifacts": {}, "project": {}, "params": {}},
            "knowledge": [],
        }
        with self.assertRaises(AgentRuntimeError):
            IndependentAgentService._render_template("坏模板 {{ 非法 变量 }}", ctx)

    def test_render_prompt_injects_allowed_artifact_keys(self):
        agent = AgentDefinitionService.get_runnable("adapt")
        _, user_prompt, _ = IndependentAgentService.render_agent_prompt(
            agent,
            {"artifacts": {}, "project": {}, "params": {}},
            [],
        )
        self.assertIn("adaptation_meta", user_prompt)
        self.assertIn("禁止自行命名", user_prompt)

    def test_resolve_overwrite_mode_reads_params(self):
        agent = AgentDefinitionService.get_runnable("script")
        mode = IndependentAgentService._resolve_overwrite_mode(agent, {"overwrite": "replace"})
        self.assertEqual(mode, "replace")

    def test_enqueue_run_uses_params_overwrite_mode(self):
        user = User.objects.create_user(phone="13900008932", password="test-pass-123")
        project = Project.objects.create(
            user=user,
            title="overwrite-test",
            theme="overbearing-ceo",
            core_idea="测试",
            episode_count=10,
            format_variant="B",
        )
        from apps.creation.artifact_service import save_artifact

        save_artifact(project, "series_outline", {"episodes": []})
        save_artifact(project, "character_bible", {"characters": []})
        from apps.agent.models import AgentLlmRouteConfig
        from apps.skill.models import LlmProvider

        provider = LlmProvider.objects.create(name="ow-prov", model_name="m", is_enabled=True, is_active=True)
        route = AgentLlmRouteConfig.objects.get(route_key="script")
        route.llm_provider = provider
        route.save(update_fields=["llm_provider"])

        result = IndependentAgentService.enqueue_run(
            project,
            user,
            "script",
            {"overwrite": "replace", "episode_from": 1, "episode_to": 1},
        )
        self.assertEqual(result.run.overwrite_mode, "replace")
        self.assertEqual(result.run.status, AgentExecutionRun.STATUS_RUNNING)
