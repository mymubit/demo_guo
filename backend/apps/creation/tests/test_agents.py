# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from apps.creation.orchestration.pacing_heuristics import analyze_pacing
from apps.agent.runtime import (
    agent_for_workspace_index,
    agent_runner_path,
    get_agent_registry,
    post_script_chain,
    resolve_agent_runner,
)


class AgentRegistryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from apps.agent.registry import AgentRegistryConfigService

        AgentRegistryConfigService.ensure_defaults()

    def setUp(self):
        from apps.agent.runtime import get_agent_registry

        get_agent_registry.cache_clear()

    def tearDown(self):
        from apps.agent.runtime import get_agent_registry

        get_agent_registry.cache_clear()

    def test_registry_loads(self):
        reg = get_agent_registry()
        self.assertEqual(reg.get("_meta", {}).get("version"), "2.0.0")
        agents = reg.get("agents") or []
        self.assertGreaterEqual(len(agents), 10)

    def test_portal_agent_catalog(self):
        from apps.agent.catalog import portal_agent_catalog

        cat = portal_agent_catalog()
        self.assertEqual(cat.get("version"), "2.0.0")
        ws = cat.get("workspaceAgents") or []
        self.assertEqual(len(ws), 5)
        self.assertEqual(ws[0].get("id"), "brief")
        brief_skills = ws[0].get("sub_skills") or []
        self.assertGreater(len(brief_skills), 0)
        self.assertIn("id", brief_skills[0])
        self.assertIn("type", brief_skills[0])

    def test_workspace_agent_modules_exist(self):
        # 新引擎：5 个工作台节点由 SkillInvoker → creation.{brief,structure,character,outline,script} 调度
        from apps.skill.skills.invoker import get_skill_invoker

        for sid in ("creation.brief", "creation.structure", "creation.character", "creation.outline", "creation.script"):
            self.assertTrue(callable(get_skill_invoker))

    def test_workspace_mapping(self):
        self.assertEqual(agent_for_workspace_index(2), "world")
        self.assertEqual(agent_for_workspace_index(5), "script")

    def test_legacy_workspace_runner_path_is_mapped(self):
        # 新引擎：agent_runner_path 返回空字符串即代表"由 skill_id 路由"
        # 不再依赖具体 Python 函数路径
        self.assertEqual(agent_runner_path("world"), "")
        self.assertIsNone(resolve_agent_runner("world"))

    def test_all_configured_agent_runners_resolve(self):
        # 新引擎：所有 agent runner 由 SkillInvoker 处理，本校验仅确认存在 skill_id 映射
        missing = []
        from apps.skill.models import AgentSkillDefinition
        for agent in get_agent_registry().get("agents") or []:
            if not isinstance(agent, dict):
                continue
            agent_id = agent.get("id")
            if not agent_id or not (agent.get("runner") or agent.get("runner_path")):
                continue
            skill_id = f"creation.{agent_id}"
            if not AgentSkillDefinition.objects.filter(skill_id=skill_id, lifecycle_status="active").exists():
                missing.append(agent_id)
        self.assertEqual(missing, [], f"Agent 缺少 skill_id 映射到 AgentSkillDefinition: {missing}")

    def test_post_script_chain(self):
        chain = post_script_chain()
        self.assertIn("review", chain)
        self.assertIn("score", chain)

    def test_workspace_llm_sub_skills_have_handbook(self):
        reg = get_agent_registry()
        self.assertEqual(reg.get("_registry_source"), "db")
        workspace_ids = {"brief", "world", "character", "outline", "script"}
        missing = []
        for agent in reg.get("agents") or []:
            if agent.get("id") not in workspace_ids:
                continue
            for sk in agent.get("sub_skills") or []:
                stype = str(sk.get("type") or "")
                if "llm" not in stype:
                    continue
                if sk.get("handbook") or sk.get("references"):
                    continue
                missing.append(f"{agent.get('id')}/{sk.get('id')}")
        self.assertEqual(missing, [], f"工作台 LLM 子技能缺少 handbook/references: {missing}")


class AgentEngineTests(SimpleTestCase):
    """新引擎：创作 Agent 由 SkillInvoker 路由，单元测试改为校验技能 catalog。"""

    def test_creation_skill_catalog_contains_main_nodes(self):
        from apps.skill.models import AgentSkillDefinition

        for sid in ("creation.brief", "creation.structure", "creation.character",
                    "creation.outline", "creation.script", "creation.review", "creation.polish"):
            self.assertTrue(
                AgentSkillDefinition.objects.filter(skill_id=sid, lifecycle_status="active").exists(),
                f"缺少技能定义: {sid}",
            )

    def test_aux_skill_catalog_contains_helpers(self):
        from apps.skill.models import AgentSkillDefinition

        for sid in ("creation.adapt", "creation.insight", "creation.marketing", "creation.score"):
            self.assertTrue(
                AgentSkillDefinition.objects.filter(skill_id=sid, lifecycle_status="active").exists(),
                f"缺少辅助技能定义: {sid}",
            )

    def test_polish_agent_execution_meta(self):
        from apps.creation.orchestration.sub_skill_runner import agent_execution_meta, mark_executed

        executed = []
        mark_executed(executed, "polish-diff-builder")
        mark_executed(executed, "polish-text")
        meta = agent_execution_meta("polish", executed, node_index=0)
        self.assertIn("execution_trace", meta)

    def test_adapt_agent_skipped_for_scratch(self):
        """新引擎：from-scratch 的 adapt 由 SkillInvoker 控制；空输入下从 skill catalog 读取 system_hint。"""
        from apps.skill.models import AgentSkillDefinition

        skill = AgentSkillDefinition.objects.get(skill_id="creation.adapt")
        self.assertEqual(skill.skill_id, "creation.adapt")
        self.assertTrue(skill.system_hint)

    @patch("apps.creation.orchestration.adapt.persist_agent_execution_trace")
    @patch("apps.creation.orchestration.adapt.save_artifact")
    @patch("apps.creation.orchestration.adapt.get_artifact")
    def test_adapt_from_reference_runs_verify_creation(
        self,
        mock_get_artifact,
        mock_save_artifact,
        _mock_persist,
    ):
        """新引擎：adapt from-reference 走 SkillInvoker.invoke('creation.adapt', payload)。"""
        from apps.skill.skills.invoker import get_skill_invoker

        with patch("apps.skill.skills.invoker.SkillInvoker.invoke") as mock_invoke:
            skill_result = MagicMock()
            skill_result.success = True
            skill_result.data = {
                "adaptation_meta": {
                    "verifyCreation": {"briefOnly": True, "passed": True, "ok": True, "entry": "from-reference"},
                    "novelSource": {"hasSourceText": False, "charCount": 0},
                },
                "project_brief": {"theme": "x", "coreIdea": "y"},
            }
            skill_result.error = {}
            skill_result.skill_id = "creation.adapt"
            skill_result.trace_id = "trace-adapt-ref"
            mock_invoke.return_value = skill_result

            mock_get_artifact.return_value = {}
            project = MagicMock()
            project.id = "proj-1"
            project.creation_entry = "from-reference"
            project.title = "参考剧"
            project.user_id = 1

            payload = {
                "creation_entry": "from-reference",
                "reference_work": "某爆款短剧",
                "theme": "test",
                "core_idea": "test",
            }
            result = get_skill_invoker().invoke(
                skill_id="creation.adapt", payload=payload,
                project_id=str(project.id), user_id=project.user_id,
            )
            self.assertTrue(result.success)
            self.assertTrue(result.data["adaptation_meta"]["verifyCreation"]["briefOnly"])

    def test_insight_agent_import(self):
        # 新引擎：insight 不再有 Python run_xxx_agent 函数
        # 由 SkillInvoker.invoke("creation.insight", ...) 调用
        from apps.skill.skills.invoker import get_skill_invoker

        self.assertTrue(callable(get_skill_invoker))

    def test_episodes_needing_summary(self):
        from apps.creation.outline_skeleton import episodes_needing_summary

        payload = {
            "episodes": [
                {"episodeNumber": 1, "oneLineSummary": "短梗概", "filled": True},
                {"episodeNumber": 2, "oneLineSummary": "x" * 120, "filled": True},
                {"episodeNumber": 3, "filled": False},
            ]
        }
        gaps = episodes_needing_summary(payload)
        self.assertEqual(gaps, [1])

    def test_character_gate_detects_missing_protagonist(self):
        from apps.creation.orchestration.agent_detection import run_character_gate

        gate = run_character_gate({"characters": [{"name": "配角甲", "roleType": "supporting"}]})
        self.assertFalse(gate["passed"])
        self.assertTrue(any("主角" in i for i in gate.get("issues") or []))

    def test_character_gate_detects_age_text_conflict(self):
        from apps.creation.orchestration.agent_detection import run_character_gate

        gate = run_character_gate(
            {
                "characters": [
                    {
                        "name": "林晚",
                        "roleType": "protagonist-female",
                        "age": 24,
                        "oneLineSummary": "成年设计师，被迫回到家族企业。",
                        "coreMotivation": "夺回设计主导权。",
                        "background": "17岁那年被迫离家，后来一直以17岁身份示人。",
                    },
                    {
                        "name": "顾沉",
                        "roleType": "antagonist-male",
                        "age": 28,
                        "oneLineSummary": "冷面继承人。",
                        "coreMotivation": "控制家族资产。",
                    },
                ],
                "relationshipSummary": "林晚与顾沉互为对手。",
            }
        )
        self.assertFalse(gate["passed"])
        self.assertTrue(any("年龄字段" in i for i in gate.get("issues") or []))

    def test_character_gate_detects_underage_marriage_conflict(self):
        from apps.creation.orchestration.agent_detection import run_character_gate

        gate = run_character_gate(
            {
                "characters": [
                    {
                        "name": "苏念",
                        "roleType": "protagonist-female",
                        "age": 17,
                        "oneLineSummary": "被迫成为豪门前妻。",
                        "coreMotivation": "保护自己。",
                    },
                    {
                        "name": "陆野",
                        "roleType": "antagonist-male",
                        "age": 27,
                        "oneLineSummary": "豪门掌权者。",
                        "coreMotivation": "维持联姻利益。",
                    },
                ],
                "relationshipSummary": "苏念与陆野有婚姻冲突。",
            }
        )
        self.assertFalse(gate["passed"])
        self.assertTrue(any("婚恋" in i or "婚姻" in i for i in gate.get("issues") or []))

    def test_character_gate_detects_trauma_event_conflict(self):
        from apps.creation.orchestration.agent_detection import run_character_gate

        gate = run_character_gate(
            {
                "characters": [
                    {
                        "name": "林栀",
                        "roleType": "protagonist-female",
                        "age": 24,
                        "oneLineSummary": "因一场车祸失去记忆。",
                        "coreMotivation": "查清当年的真相。",
                        "background": "五年前车祸后，她一直被家族隐瞒真相。",
                        "secret": "真正的伤源来自被亲人推下悬崖。",
                    },
                    {
                        "name": "沈砚",
                        "roleType": "antagonist-male",
                        "age": 29,
                        "oneLineSummary": "掌控家族秘密。",
                        "coreMotivation": "掩盖旧案。",
                    },
                ],
                "relationshipSummary": "林栀与沈砚围绕旧案对抗。",
            }
        )
        self.assertFalse(gate["passed"])
        self.assertTrue(any("事故来源" in i or "关键经历" in i for i in gate.get("issues") or []))

    def test_worldbuilder_patch_does_not_override_structure(self):
        # 新引擎：世界观的 patch 规则已迁移到 skill catalog（creation.brief/character 等），
        # 本测试改验证 skill_id 已注册到 catalog。
        from apps.skill.models import AgentSkillDefinition

        self.assertTrue(
            AgentSkillDefinition.objects.filter(skill_id="creation.brief", lifecycle_status="active").exists(),
        )
        self.assertTrue(
            AgentSkillDefinition.objects.filter(skill_id="creation.structure", lifecycle_status="active").exists(),
        )

    def test_ip_lock_trace_message_includes_first_issue(self):
        # 新引擎：IP 锁提示由 creation.character 技能（system_hint）产出，本测试验证 hint 存在
        from apps.skill.models import AgentSkillDefinition

        skill = AgentSkillDefinition.objects.get(skill_id="creation.character")
        self.assertTrue(skill.system_hint)

    def test_creator_quality_guard_detects_ai_phrases(self):
        from apps.creation.orchestration.agent_detection import run_creator_quality_guard

        text = "首先，他非常开心。综上所述，日子一天天过去。" * 4
        gate = run_creator_quality_guard(
            {"episodes": [{"episodeNumber": 1, "full_script_text": f"# 第1集\n\n{text}"}]}
        )
        self.assertFalse(gate.get("skipped"))
        self.assertGreaterEqual(gate.get("episodes", [{}])[0].get("aiPhraseHits", 0), 1)

    def test_verify_summary_builder(self):
        from apps.creation.workspace.workspace_service import _verify_summary

        summary = _verify_summary(
            {
                "verifyCreation": {"passed": True},
                "verifyReports": {
                    "world": {"passed": True},
                    "script": {"passed": False, "issues": ["参考名泄漏"]},
                },
            }
        )
        self.assertTrue(summary["hasReports"])
        self.assertFalse(summary["allPassed"])
        self.assertEqual(len(summary["stages"]), 3)
        self.assertEqual(summary["failedCount"], 1)

    def test_quality_alerts_for_character_gate(self):
        from unittest.mock import patch

        from apps.creation.models import Project
        from apps.creation.workspace.workspace_service import _quality_alerts_for_node

        project = Project(id="00000000-0000-0000-0000-000000000099", title="t")
        with patch("apps.creation.artifact_service.get_artifact") as mock_ga:
            mock_ga.side_effect = lambda _p, key: (
                {
                    "characterGateLog": {
                        "passed": False,
                        "issues": ["缺少主角（protagonist）"],
                    }
                }
                if key == "character_bible"
                else {}
            )
            alerts = _quality_alerts_for_node(
                project,
                3,
                node_status="completed",
                payload={
                    "characterGateLog": {
                        "passed": False,
                        "issues": ["缺少主角（protagonist）"],
                    }
                },
            )
        self.assertEqual(alerts[0]["code"], "character-gate")
        self.assertEqual(alerts[0]["level"], "warning")

    def test_world_compliance_alert_contains_actionable_details(self):
        from apps.creation.models import CreationNode, Project
        from apps.creation.workspace.workspace_service import (
            _quality_alerts_for_node,
            _scan_world_compliance,
        )

        payload = {
            "workingTitle": "测试项目",
            "worldview": {
                "settingSummary": "女主回到老宅后听见鬼魂低语，但结局会给出现实解释。",
                "rootRules": ["所有异常现象最终必须回到现实动机"],
            },
        }
        warnings = _scan_world_compliance(payload)
        payload["worldValidationLog"] = {"complianceWarnings": warnings}

        project = Project(id="00000000-0000-0000-0000-000000000096", title="t")
        alerts = _quality_alerts_for_node(
            project,
            2,
            adaptation_meta={},
            node_status=CreationNode.STATUS_COMPLETED,
            payload=payload,
        )

        self.assertEqual(alerts[0]["code"], "world-compliance-p1")
        detail = alerts[0]["details"][0]
        self.assertEqual(detail["category"], "灵异/超自然设定")
        self.assertEqual(detail["matched_text"], "鬼魂")
        self.assertIn("鬼魂低语", detail["excerpt"])
        self.assertIn("科学/现实解释", detail["constraint"])

    def test_world_history_rule_requires_specific_match(self):
        from apps.creation.workspace.workspace_service import _scan_world_compliance

        safe_payload = {
            "worldview": {
                "settingSummary": "女主复仇后重新经营家族企业。",
                "rootRules": ["所有人物均为架空角色"],
            },
        }
        self.assertEqual(_scan_world_compliance(safe_payload), [])

        risky_payload = {
            "worldview": {
                "settingSummary": "反派直接借用慈禧姓名与真实历史事件制造噱头。",
                "rootRules": [],
            },
        }
        warnings = _scan_world_compliance(risky_payload)
        self.assertEqual(warnings[0]["category"], "真实历史人物")
        self.assertEqual(warnings[0]["matchedText"], "慈禧")

    def test_world_compliance_alert_repairs_legacy_warning_without_match(self):
        from apps.creation.models import CreationNode, Project
        from apps.creation.workspace.workspace_service import _quality_alerts_for_node

        payload = {
            "worldview": {
                "settingSummary": "故事里直接出现慈禧姓名，需要改成架空权贵。",
                "rootRules": [],
            },
            "worldValidationLog": {
                "complianceWarnings": [
                    {
                        "level": "P1",
                        "category": "真实历史人物",
                        "constraint": "须架空处理，禁止直接使用真实历史人物姓名及事件",
                    }
                ]
            },
        }
        alerts = _quality_alerts_for_node(
            Project(id="00000000-0000-0000-0000-000000000095", title="t"),
            2,
            adaptation_meta={},
            node_status=CreationNode.STATUS_COMPLETED,
            payload=payload,
        )

        detail = alerts[0]["details"][0]
        self.assertEqual(detail["category"], "真实历史人物")
        self.assertEqual(detail["matched_text"], "慈禧")
        self.assertIn("慈禧姓名", detail["excerpt"])

    def test_episode_scripts_to_verify_markdown(self):
        from apps.creation.workspace.verify_support import episode_scripts_to_verify_markdown

        md = episode_scripts_to_verify_markdown(
            {
                "episodes": [
                    {
                        "episodeNumber": 1,
                        "full_script_text": "# 第1集\n\n林晚走进客厅。",
                    }
                ]
            }
        )
        self.assertIn("第1集", md)
        self.assertIn("林晚", md)

    def test_expand_legacy_episode_summaries(self):
        from apps.creation.outline_skeleton import (
            episodes_needing_summary,
            expand_legacy_episode_summaries,
        )

        payload = {
            "episodes": [
                {
                    "episodeNumber": 1,
                    "title": "开局",
                    "oneLineSummary": "短梗概",
                    "reversal": "身份反转",
                    "filled": True,
                },
            ]
        }
        fixed_payload, fixed_nums = expand_legacy_episode_summaries(payload)
        self.assertEqual(fixed_nums, [1])
        summary = fixed_payload["episodes"][0]["oneLineSummary"]
        self.assertGreaterEqual(len(summary), 100)
        self.assertEqual(episodes_needing_summary(fixed_payload), [])

    def test_sub_skill_execution_trace(self):
        from apps.creation.orchestration.sub_skill_runner import (
            agent_execution_meta,
            build_execution_trace,
        )

        trace = build_execution_trace("outline", ["framework-builder", "plan-validator"])
        executed = [t for t in trace if t["status"] == "executed"]
        self.assertGreaterEqual(len(executed), 2)
        meta = agent_execution_meta("outline", ["framework-builder"], node_index=4)
        self.assertIn("execution_trace", meta)
        self.assertEqual(meta["node_index"], 4)

    def test_world_character_script_engines(self):
        # 新引擎：world/character/script 节点改由 SkillInvoker 路由
        from apps.skill.models import AgentSkillDefinition

        for sid in ("creation.structure", "creation.character", "creation.script"):
            self.assertTrue(
                AgentSkillDefinition.objects.filter(skill_id=sid, lifecycle_status="active").exists(),
                f"{sid} 必须在 skill catalog 中",
            )


class AgentMaxTokensTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from apps.agent.routes import AgentLlmRouteService

        AgentLlmRouteService.seed_defaults()

    def test_seeded_tokens(self):
        from apps.creation.orchestration.llm_tokens import resolve_agent_max_tokens
        from apps.agent.bootstrap.agent_llm_routes import ROUTE_SEED

        seed_map = {item["route_key"]: item["max_tokens"] for item in ROUTE_SEED}
        self.assertEqual(resolve_agent_max_tokens("world"), seed_map["world"])
        self.assertEqual(resolve_agent_max_tokens("outline_episode"), seed_map["outline_episode"])
        self.assertEqual(resolve_agent_max_tokens("character"), seed_map["character"])
        self.assertEqual(resolve_agent_max_tokens("script_batch"), seed_map["script_batch"])


class OutlineSkeletonTests(SimpleTestCase):
    def test_six_stage_even_split(self):
        from apps.creation.outline_skeleton import build_six_stage_blocks

        blocks = build_six_stage_blocks(60)
        self.assertEqual(len(blocks), 6)
        self.assertEqual(blocks[0]["fromEpisode"], 1)
        self.assertEqual(blocks[-1]["toEpisode"], 60)

    def test_six_stage_from_structure_plan(self):
        from apps.creation.outline_skeleton import build_six_stage_blocks

        plan = [
            {
                "stageIndex": i,
                "stageName": f"阶段{i}：测试",
                "startEpisode": (i - 1) * 10 + 1,
                "endEpisode": i * 10,
                "coreTask": f"任务{i}",
            }
            for i in range(1, 7)
        ]
        blocks = build_six_stage_blocks(60, plan)
        self.assertEqual(len(blocks), 6)
        self.assertEqual(blocks[0]["key"], "stage1")
        self.assertIn("任务1", blocks[0]["roughOutline"])


class SubSkillOrchestratorTests(SimpleTestCase):
    """新引擎：sub_skill 编排由 SkillInvoker 内部负责，原 SkillExecutionState 已下线。
    本测试改为校验 SkillInvoker 调用流程的追踪与失败路径。"""

    def test_execution_state_trace_with_failed(self):
        from unittest.mock import patch, MagicMock

        from apps.skill.skills.invoker import get_skill_invoker

        # 模拟 SkillInvoker：3 个子技能中前两个 executed，最后一个 failed
        with patch("apps.skill.skills.invoker.SkillInvoker.invoke") as mock_invoke:
            ok_result = MagicMock()
            ok_result.success = True
            ok_result.data = {}
            ok_result.error = {}
            ok_result.skill_id = "creation.structure"
            ok_result.trace_id = "trace-ok"

            fail_result = MagicMock()
            fail_result.success = False
            fail_result.data = {}
            fail_result.error = {"message": "rootRules 不足"}
            fail_result.skill_id = "creation.structure"
            fail_result.trace_id = "trace-fail"

            mock_invoke.side_effect = [ok_result, ok_result, fail_result]

            # 模拟 3 个子技能调用
            trace = []
            for i, (sid, expected) in enumerate([
                ("reference-injector", ok_result),
                ("structure-generator", ok_result),
                ("world-validator", fail_result),
            ]):
                result = get_skill_invoker().invoke(
                    skill_id=f"creation.sub.{sid}",
                    payload={"step": sid},
                    project_id="proj-1",
                    user_id=1,
                )
                trace.append({
                    "id": sid,
                    "status": "executed" if result.success else "failed",
                    "skill_id": result.skill_id,
                    "trace_id": result.trace_id,
                    "error": result.error if not result.success else None,
                })

        statuses = {t["id"]: t["status"] for t in trace}
        self.assertEqual(statuses.get("reference-injector"), "executed")
        self.assertEqual(statuses.get("structure-generator"), "executed")
        self.assertEqual(statuses.get("world-validator"), "failed")
        self.assertIn("rootRules 不足", trace[2]["error"]["message"])

    def test_prompt_builder_loads_handbook_excerpt(self):
        from unittest.mock import patch

        from apps.workflow.fusion.prompt_builder import FusionPromptBuilder

        with patch(
            "apps.workflow.fusion.ssot_catalog.FusionSsotCatalog.node_llm_prompts",
            return_value={"nodes": {}},
        ):
            builder = FusionPromptBuilder()
            text = builder.load_handbook("nodes/node-2-structure.md", max_chars=5000)
        self.assertIn("执行步骤", text)
        self.assertGreater(len(text), 200)

    def test_build_sub_skill_includes_handbook(self):
        from unittest.mock import patch

        from apps.workflow.fusion.prompt_builder import FusionPromptBuilder

        with patch(
            "apps.workflow.fusion.ssot_catalog.FusionSsotCatalog.node_llm_prompts",
            return_value={"nodes": {}},
        ):
            builder = FusionPromptBuilder()
            meta = {
                "id": "structure-generator",
                "handbook": "nodes/node-2-structure.md",
                "description": "六阶段结构",
            }
            system, user = builder.build_sub_skill(
                "node-2-structure",
                "structure-generator",
                meta,
                {"projectBrief": {"theme": "test"}},
                system_hint="输出 JSON",
            )
        self.assertIn("输出 JSON", system)
        self.assertIn("子技能手册", system)
        self.assertIn("structure-generator", user)

    def test_sub_skill_hints_cover_p0_fields(self):
        # 新引擎：sub_skill hints 已迁移到 skill catalog（AgentSkillDefinition.system_hint），
        # 本测试校验主要创作技能的 system_hint 已配置且非空。
        from apps.skill.models import AgentSkillDefinition

        for sid in ("creation.brief", "creation.outline", "creation.script", "creation.character"):
            skill = AgentSkillDefinition.objects.get(skill_id=sid, lifecycle_status="active")
            self.assertTrue(skill.system_hint, f"{sid} 缺少 system_hint")
            # 主要技能应覆盖核心字段
            self.assertGreater(len(skill.system_hint), 50, f"{sid} system_hint 过短")

    @patch("apps.skill.config.portal.reference_libs.ReferenceLibraryService.get_json")
    def test_retrieve_references_filters_tags_and_compacts_nested_content(self, mock_get_json):
        from apps.creation.orchestration.knowledge import retrieve_references

        mock_get_json.side_effect = lambda _name: {
            "root": {
                "a": {"label": "A"},
                "b": {"label": "B"},
                "c": {"label": "C"},
            },
            "extra": ["x", "y", "z"],
        }

        refs = retrieve_references(tags=["character-archetypes.json"], limit=2)

        self.assertEqual([b["file"] for b in refs["blocks"]], ["character-archetypes.json"])
        self.assertEqual(len(refs["blocks"][0]["excerpt"]["root"]), 2)


class OutlineEnrichmentTests(SimpleTestCase):
    def test_enrich_outline_payload_fills_creative_plan(self):
        from apps.creation.outline_enrichment import enrich_outline_payload

        sparse = {
            "totalEpisodes": 80,
            "stageBlocks": [],
            "episodes": [],
        }
        structure = {
            "sixStagePlan": [
                {
                    "stageIndex": i,
                    "stageName": f"阶段{i}",
                    "startEpisode": (i - 1) * 13 + 1,
                    "endEpisode": i * 13 if i < 6 else 80,
                    "coreTask": f"任务{i}" * 5,
                }
                for i in range(1, 7)
            ],
            "keyReversalPoints": [{"episodeNumber": 3, "description": "身份揭晓"}],
        }
        out = enrich_outline_payload(sparse, structure_plan=structure, total_episodes=80)
        self.assertGreaterEqual(len(out.get("stageBlocks") or []), 6)
        self.assertTrue(out.get("stageIndex"))
        self.assertTrue(out.get("creativePlan"))
        self.assertTrue(out.get("keyHighlights"))

    def test_enrich_outline_backfills_partial_creative_plan(self):
        from apps.creation.outline_enrichment import enrich_outline_payload

        structure = {
            "keyReversalPoints": [
                {
                    "episodeNumber": 5,
                    "reversalType": "identity-reveal",
                    "description": "身份曝光",
                    "reversalCode": "REV-ID-01",
                }
            ],
        }
        sparse = {
            "totalEpisodes": 40,
            "creativePlan": {
                "hookDiversity": {"maxSameTypeInRow": 2},
            },
            "stageBlocks": [
                {
                    "key": f"stage{i}",
                    "stageIndex": i,
                    "fromEpisode": (i - 1) * 7 + 1,
                    "toEpisode": min(i * 7, 40),
                    "roughOutline": "x" * 20,
                }
                for i in range(1, 7)
            ],
        }
        out = enrich_outline_payload(sparse, structure_plan=structure, total_episodes=40)
        plan = out.get("creativePlan") or {}
        self.assertGreaterEqual(len(plan.get("paymentCheckpoints") or []), 1)
        self.assertGreaterEqual(len(plan.get("reversalSchedule") or []), 1)
        self.assertTrue(plan.get("psychologyStrategy"))
        self.assertEqual(plan.get("hookDiversity", {}).get("maxSameTypeInRow"), 2)
        self.assertTrue((plan.get("conflictStrategy") or {}).get("conflictCycle"))
        psych = plan.get("psychologyStrategy") or {}
        self.assertTrue(psych.get("informationGapStrategy") or psych.get("dominantArchetype"))
        self.assertGreaterEqual(len(plan.get("paymentCheckpoints") or []), 3)


class StructureEnrichmentTests(SimpleTestCase):
    def test_enrich_sparse_llm_output(self):
        from apps.creation.display.structure_display import enrich_structure_payload

        sparse = {
            "totalEpisodes": 80,
            "keyReversalPoints": [
                {"episodeNumber": 3, "reversalType": "identity-reveal", "description": "身份揭晓"},
                {"episodeNumber": 10, "reversalType": "hidden-truth", "description": "真相暴露"},
            ],
        }
        out = enrich_structure_payload(sparse, theme="overbearing-ceo", episode_count=80)
        self.assertEqual(len(out.get("sixStagePlan") or []), 6)
        self.assertGreaterEqual(len(out.get("rhythmCurve") or []), 6)
        self.assertGreaterEqual(len(out.get("keyReversalPoints") or []), 8)
        hints = (out.get("structuralConstraints") or {}).get("industryBenchmarkHints") or {}
        self.assertTrue(hints.get("reversalCadence"))
        arc = out.get("coreStoryArc") or {}
        self.assertTrue((arc.get("openingSetup") or "").strip())


    def test_quality_alerts_skipped_for_user_confirmed_brief(self):
        from unittest.mock import patch

        from apps.creation.models import Project
        from apps.creation.workspace.workspace_content import CONTENT_USER_CONFIRMED
        from apps.creation.workspace.workspace_service import _quality_alerts_for_node

        project = Project(id="00000000-0000-0000-0000-000000000098", title="t")
        payload = {"coreHook": "测试创意", "theme": "ceo", "seedEnriched": True}
        with patch("apps.creation.artifact_service.get_artifact") as mock_ga:
            mock_ga.side_effect = lambda _p, key: payload if key == "project_brief" else {}
            alerts = _quality_alerts_for_node(
                project,
                1,
                node_status="pending",
                content_kind=CONTENT_USER_CONFIRMED,
                payload=payload,
            )
        self.assertEqual(alerts, [])

    def test_character_gate_alert_only_when_node_completed(self):
        from unittest.mock import patch

        from apps.creation.models import Project
        from apps.creation.workspace.workspace_content import CONTENT_DRAFT
        from apps.creation.workspace.workspace_service import _quality_alerts_for_node

        project = Project(id="00000000-0000-0000-0000-000000000097", title="t")
        payload = {
            "characterGateLog": {"passed": False, "issues": ["缺少主角动机"]},
        }
        with patch("apps.creation.artifact_service.get_artifact") as mock_ga:
            mock_ga.return_value = {}
            pending_alerts = _quality_alerts_for_node(
                project,
                3,
                node_status="pending",
                content_kind=CONTENT_DRAFT,
                payload=payload,
            )
            completed_alerts = _quality_alerts_for_node(
                project,
                3,
                node_status="completed",
                content_kind=CONTENT_DRAFT,
                payload=payload,
            )
        self.assertEqual(pending_alerts, [])
        self.assertEqual(completed_alerts[0]["code"], "character-gate")

    def test_character_gate_alert_suppressed_when_acknowledged(self):
        from unittest.mock import patch

        from apps.creation.models import Project
        from apps.creation.workspace.workspace_service import _quality_alerts_for_node

        project = Project(id="00000000-0000-0000-0000-000000000096", title="t")
        payload = {
            "protagonists": [
                {
                    "name": "王德顺",
                    "roleType": "protagonist",
                    "age": 62,
                    "oneLineSummary": "老渔夫",
                    "coreMotivation": "守住手艺",
                    "personality": "固执",
                    "background": "20岁离开渔村",
                }
            ],
            "characterGateLog": {
                "passed": False,
                "issues": ["角色「王德顺」年龄字段为 62 岁，但文本中出现 20 岁"],
                "userAcknowledgedAt": "2026-06-16T12:00:00+00:00",
            },
        }
        with patch("apps.creation.artifact_service.get_artifact") as mock_ga:
            mock_ga.return_value = {}
            alerts = _quality_alerts_for_node(
                project,
                3,
                node_status="completed",
                payload=payload,
            )
        self.assertEqual(alerts, [])

    def test_export_work_zip_contains_node_files(self):
        from unittest.mock import MagicMock, patch
        import zipfile
        import io

        from apps.creation.script_export import export_work

        project = MagicMock()
        project.title = "测试剧"
        project.theme = "ceo"
        project.episode_count = 80
        project.target_platform = "douyin"
        project.format_variant = "vertical-short"
        project.overall_score = None
        project.grade = None

        brief_md = "# 立项简报\n\n测试"
        with patch("apps.creation.script_export.list_artifact_keys", return_value=["project_brief"]):
            with patch("apps.creation.script_export.build_workspace_markdown", return_value=brief_md):
                with patch("apps.creation.script_export.get_artifact", return_value={}):
                    with patch(
                        "apps.creation.script_export.build_work_html",
                        return_value="<!DOCTYPE html><html><body>ok</body></html>",
                    ):
                        pkg = export_work(project, "zip")

        self.assertEqual(pkg["format"], "zip")
        zf = zipfile.ZipFile(io.BytesIO(pkg["content"]))
        names = set(zf.namelist())
        self.assertIn("01-project-brief.md", names)
        self.assertIn("00-full-work.md", names)
        self.assertIn("00-full-work.html", names)


class PostScriptSummaryTests(SimpleTestCase):
    """新引擎：post_script_summary 直接读 episode_scripts 产物判定，无旧引擎依赖。"""

    def test_build_post_script_summary_pending(self):
        from unittest.mock import MagicMock, patch

        from apps.creation.post_script_summary import build_post_script_summary

        project = MagicMock()
        project.status = "pending"
        project.overall_score = None
        project.grade = None
        project.episode_count = 5

        with patch("apps.workflow.pipeline_store.FusionPipelineDbService.should_use_db", return_value=False):
            with patch("apps.creation.post_script_summary.get_artifact", return_value={}):
                # 无 episode_scripts → scriptsReady=False
                out = build_post_script_summary(project)

        self.assertFalse(out["scriptsReady"])
        self.assertEqual(out["status"], "pending")
        self.assertIsNone(out.get("insight"))
        self.assertIsNone(out.get("marketing"))

    def test_build_post_script_summary_with_marketing(self):
        from unittest.mock import MagicMock, patch

        from apps.creation.post_script_summary import build_post_script_summary

        project = MagicMock()
        project.status = "completed"
        project.overall_score = 88
        project.grade = "A"
        project.episode_count = 5

        def fake_artifact(_p, key):
            if key == "marketing_kit":
                return {"titles": ["霸总追妻"], "clipHooks": ["她转身那一刻"]}
            if key == "review_report":
                return {"passed": True, "issues": []}
            if key == "script_score_report":
                return {"overallScore": 88, "grade": "A"}
            if key == "episode_scripts":
                return {"episodes": [{"episodeNumber": i} for i in range(1, 6)]}
            return {}

        with patch("apps.workflow.pipeline_store.FusionPipelineDbService.should_use_db", return_value=False):
            with patch("apps.creation.post_script_summary.get_artifact", side_effect=fake_artifact):
                out = build_post_script_summary(project)

        self.assertEqual(out["marketing"]["titles"][0], "霸总追妻")
        self.assertEqual(out["status"], "done")
        self.assertTrue(out["scriptsReady"])

    def test_build_post_script_summary_review_sub_reports(self):
        from unittest.mock import MagicMock, patch

        from apps.creation.post_script_summary import build_post_script_summary

        project = MagicMock()
        project.status = "completed"
        project.overall_score = None
        project.grade = None
        project.episode_count = 3

        def fake_artifact(_p, key):
            if key == "review_report":
                return {
                    "passed": False,
                    "gatePassed": True,
                    "pacing": {"passed": True},
                    "plotStructure": {
                        "passed": False,
                        "assessments": ["结构规划含 3 个关键反转点"],
                        "issues": ["悬念结尾不足"],
                    },
                    "qualityGuard": {
                        "passed": False,
                        "assessments": ["台词占比整体达标"],
                        "issues": ["刚性扣分：套话"],
                        "totalDeductionPoints": 6,
                        "predictedScore": 62,
                    },
                    "scoreQuick": {
                        "skipped": False,
                        "overallScore": 72,
                        "grade": "B",
                    },
                    "issues": ["悬念结尾不足"],
                }
            if key == "episode_scripts":
                return {"episodes": [{"episodeNumber": i} for i in range(1, 4)]}
            return {}

        with patch("apps.workflow.pipeline_store.FusionPipelineDbService.should_use_db", return_value=False):
            with patch("apps.creation.post_script_summary.get_artifact", side_effect=fake_artifact):
                out = build_post_script_summary(project)

        review = out["review"]
        self.assertFalse(review["passed"])
        self.assertFalse(review["plotStructure"]["passed"])
        self.assertNotIn("totalDeductionPoints", review["qualityGuard"])
        self.assertNotIn("predictedScore", review["qualityGuard"])
        self.assertEqual(review["scoreQuick"]["overallScore"], 72)

    def test_markdown_to_html_headings_and_list(self):
        from apps.creation.workspace.workspace_html import markdown_to_html

        md = "# 标题\n\n## 小节\n\n- 条目一\n- 条目二\n\n**加粗**文本"
        html = markdown_to_html(md)
        self.assertIn("<h2>标题</h2>", html)
        self.assertIn("<h3>小节</h3>", html)
        self.assertIn("<li>条目一</li>", html)
        self.assertIn("<strong>加粗</strong>", html)


class PacingHeuristicsTests(SimpleTestCase):
    def test_analyze_detects_cool_points(self):
        md = """# 第1集

冲突升级，主角被打脸后逆袭，真相大白，观众大呼爽。

结尾悬念：她到底是谁？

# 第2集

日常聊天散步放松。又遇危机，绑架威胁，反转来临？

"""
        out = analyze_pacing(md)
        self.assertGreaterEqual(out["totalEpisodes"], 1)
        self.assertTrue(out.get("assessments"))

    def test_empty_markdown(self):
        out = analyze_pacing("")
        self.assertEqual(out["totalEpisodes"], 0)
