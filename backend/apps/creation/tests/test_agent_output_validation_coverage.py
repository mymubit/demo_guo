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
            "adapt": (AgentDefinitionService.get_runnable("drama.ip-adapter"), {"adaptation_plan": {}, "project_brief": {}}),
            "brief": (AgentDefinitionService.get_runnable("drama.topic-planner"), {"project_brief": {}}),
            "structure": (AgentDefinitionService.get_runnable("drama.plot-architect"), {"structure_plan": {}}),
            "character": (AgentDefinitionService.get_runnable("drama.character-designer"), {"character_bible": {}}),
            "outline": (AgentDefinitionService.get_runnable("drama.plot-architect"), {"series_outline": {}}),
            "script": (
                AgentDefinitionService.get_runnable("drama.script-writer"),
                {"episode_scripts": {"episodes": [{"episodeNumber": 1}]}},
            ),
            "review": (AgentDefinitionService.get_runnable("drama.script-reviewer"), {"review_report": {"passed": True}}),
            "score": (
                AgentDefinitionService.get_runnable("drama.quality-reporter"),
                {"script_score_report": {"overallScore": 80}},
            ),
            "marketing": (AgentDefinitionService.get_runnable("drama.marketing-officer"), {"marketing_kit": {}}),
        }
        for agent_id, (agent, output) in cases.items():
            with self.subTest(agent_id=agent_id):
                result = IndependentAgentService.validate_output(agent, output)
                self.assertTrue(result)

    def test_review_report_coerces_boolean_like_passed(self):
        """review_report.passed 为 LLM 常见布尔近似值时应归一化而非失败。"""
        from apps.creation.agent_runtime.output_schema_validation import _validate_review_report

        for raw, expected in [("通过", True), ("false", False), (1, True), ("否", False), (True, True)]:
            body = {"passed": raw}
            _validate_review_report(body)
            self.assertIs(body["passed"], expected)

    def test_review_report_rejects_unrecognized_passed(self):
        from apps.creation.agent_runtime.independent_service import AgentRuntimeError
        from apps.creation.agent_runtime.output_schema_validation import _validate_review_report

        with self.assertRaises(AgentRuntimeError):
            _validate_review_report({"summary": "无结论"})

    def test_review_report_derives_passed_from_alternative_fields(self):
        """真实 LLM 用 reviewResult / 逐项 status 表达结论时也能归一化。"""
        from apps.creation.agent_runtime.output_schema_validation import _validate_review_report

        body1 = {"reviewResult": "passed", "reviewItems": []}
        _validate_review_report(body1)
        self.assertIs(body1["passed"], True)

        body2 = {"reviewItems": [{"status": "pass"}, {"status": "fail"}]}
        _validate_review_report(body2)
        self.assertIs(body2["passed"], False)

        body3 = {"overallStatus": "PASS", "checkItems": [{"result": "通过"}]}
        _validate_review_report(body3)
        self.assertIs(body3["passed"], True)

    def test_load_knowledge_respects_budget(self):
        """绑定超大/过多知识时，注入总量受 max_prompt_tokens 预算约束。"""
        from apps.agent.models import AgentKnowledgeBinding, AgentKnowledgeItem

        agent = AgentDefinitionService.get_runnable("drama.script-writer")
        budget = int((agent.runtime_policy or {}).get("max_prompt_tokens", 40000)) * 4 * 0.4
        for i in range(5):
            item = AgentKnowledgeItem.objects.create(
                knowledge_id=f"budget-test-{i}",
                title=f"t{i}",
                category=AgentKnowledgeItem.Category.RULE,
                content_text="字" * 50000,
            )
            AgentKnowledgeBinding.objects.create(
                agent=agent,
                knowledge=item,
                binding_type=AgentKnowledgeBinding.BindingType.OPTIONAL,
                inject_position=AgentKnowledgeBinding.InjectPosition.USER,
                is_enabled=True,
            )
        rows = IndependentAgentService.load_knowledge(agent)
        total = sum(len(r["content_text"]) for r in rows)
        self.assertLessEqual(total, budget + 1)

    def test_extract_json_tolerates_control_characters(self):
        """真实 LLM 在字符串内输出裸换行/控制字符时仍能解析。"""
        from apps.creation.agent_runtime.independent_service import extract_json_object

        raw = '{"text": "第一行\n第二行\t制表"}'
        parsed = extract_json_object(raw)
        self.assertEqual(parsed["text"], "第一行\n第二行\t制表")

    def test_validate_output_falls_back_when_artifact_key_invalid(self):
        """真实 LLM 自创 artifact_key 时回退到契约默认 key，而非整链失败。"""
        agent = AgentDefinitionService.get_runnable("drama.ip-adapter")
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
        agent = AgentDefinitionService.get_runnable("drama.ip-adapter")
        _, user_prompt, _ = IndependentAgentService.render_agent_prompt(
            agent,
            {"artifacts": {}, "project": {}, "params": {}},
            [],
        )
        self.assertIn("adaptation_plan", user_prompt)
        self.assertIn("禁止自行命名", user_prompt)

    def test_resolve_overwrite_mode_reads_params(self):
        agent = AgentDefinitionService.get_runnable("drama.script-writer")
        mode = IndependentAgentService._resolve_overwrite_mode(agent, {"overwrite": "replace"})
        self.assertEqual(mode, "replace")

    def test_enqueue_run_uses_params_overwrite_mode(self):
        from apps.creation.tests.test_helpers import grant_test_coins

        user = User.objects.create_user(phone="13900008932", password="test-pass-123")
        grant_test_coins(user)
        project = Project.objects.create(
            user=user,
            title="overwrite-test",
            theme="overbearing-ceo",
            core_idea="测试",
            episode_count=10,
            format_variant="B",
        )
        from apps.creation.artifact_service import save_artifact

        save_artifact(project, "world_setting", {"settingSummary": "modern city"})
        save_artifact(project, "character_bible", {"protagonists": []})
        save_artifact(project, "series_outline", {"episodes": []})
        from apps.agent.models import AgentLlmRouteConfig
        from apps.skill.models import LlmProvider

        provider = LlmProvider.objects.create(name="ow-prov", model_name="m", is_enabled=True, is_active=True)
        route = AgentLlmRouteConfig.objects.get(route_key="drama.script-writer")
        route.llm_provider = provider
        route.save(update_fields=["llm_provider"])

        result = IndependentAgentService.enqueue_run(
            project,
            user,
              "drama.script-writer",
            {"overwrite": "replace", "episode_from": 1, "episode_to": 1},
        )
        self.assertEqual(result.run.overwrite_mode, "replace")
        self.assertEqual(result.run.status, AgentExecutionRun.STATUS_RUNNING)
