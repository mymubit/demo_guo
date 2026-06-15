# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from apps.creation.orchestration.pacing_heuristics import analyze_pacing
from apps.agent.runtime import (
    agent_for_workspace_index,
    get_agent_registry,
    post_script_chain,
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
        from apps.creation.orchestration.brief import run_brief_agent
        from apps.creation.orchestration.world import run_world_agent
        from apps.creation.orchestration.character import run_character_agent
        from apps.creation.orchestration.outline import run_outline_agent
        from apps.creation.orchestration.script import run_script_agent

        for fn in (
            run_brief_agent,
            run_world_agent,
            run_character_agent,
            run_outline_agent,
            run_script_agent,
        ):
            self.assertTrue(callable(fn))

    def test_workspace_mapping(self):
        self.assertEqual(agent_for_workspace_index(2), "world")
        self.assertEqual(agent_for_workspace_index(5), "script")

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
    def test_outline_engine_import(self):
        from apps.creation.orchestration.outline_engine import OutlineAgentEngine, AGENT_ID

        self.assertEqual(AGENT_ID, "outline")
        self.assertTrue(hasattr(OutlineAgentEngine, "generate_framework"))

    def test_brief_engine_import(self):
        from apps.creation.orchestration.brief_engine import BriefAgentEngine, AGENT_ID

        self.assertEqual(AGENT_ID, "brief")
        self.assertTrue(hasattr(BriefAgentEngine, "generate"))

    def test_polish_agent_execution_meta(self):
        from apps.creation.orchestration.polish import _build_polish_suggestions
        from apps.creation.orchestration.sub_skill_runner import agent_execution_meta, mark_executed

        executed = []
        mark_executed(executed, "polish-diff-builder")
        mark_executed(executed, "polish-text")
        suggestions = _build_polish_suggestions({"issues": ["gate 未过"], "pacing": {"assessments": []}})
        self.assertGreaterEqual(len(suggestions), 1)
        meta = agent_execution_meta("polish", executed, node_index=0)
        self.assertIn("execution_trace", meta)

    def test_adapt_agent_skipped_for_scratch(self):
        from apps.creation.orchestration.adapt import run_adapt_agent
        from apps.creation.models import Project

        project = Project(creation_entry="from-scratch", title="t")
        result = run_adapt_agent(project)
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.agent_id, "adapt")

    @patch("apps.creation.orchestration.adapt.persist_agent_execution_trace")
    @patch("apps.creation.orchestration.adapt.cli_verify_creation_brief")
    @patch("apps.creation.orchestration.adapt.save_artifact")
    @patch("apps.creation.orchestration.adapt.get_artifact")
    def test_adapt_from_reference_runs_verify_creation(
        self,
        mock_get_artifact,
        mock_save_artifact,
        mock_verify,
        _mock_persist,
    ):
        from apps.creation.orchestration.adapt import run_adapt_agent
        from apps.creation.models import Project

        mock_get_artifact.return_value = {}
        mock_verify.return_value = {"ok": True, "json": {"ok": True, "markdown": "# brief"}}
        project = Project(
            creation_entry="from-reference",
            title="参考剧",
            reference_work="某爆款短剧",
        )
        result = run_adapt_agent(project)
        self.assertEqual(result.status, "completed")
        mock_verify.assert_called_once()
        meta = result.outputs.get("adaptation_meta") or {}
        self.assertTrue(meta.get("verifyCreation", {}).get("briefOnly"))
        self.assertIn("verify-creation", result.meta.get("executed_sub_skills") or [])

    def test_insight_agent_import(self):
        from apps.creation.orchestration.insight import run_insight_agent

        self.assertTrue(callable(run_insight_agent))

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

    def test_episode_scripts_to_verify_markdown(self):
        from apps.creation.orchestration.verify_creation_support import episode_scripts_to_verify_markdown

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
        from apps.creation.orchestration.world_engine import WorldAgentEngine
        from apps.creation.orchestration.character_engine import CharacterAgentEngine
        from apps.creation.orchestration.script_engine import ScriptAgentEngine

        for cls in (WorldAgentEngine, CharacterAgentEngine, ScriptAgentEngine):
            self.assertTrue(hasattr(cls, "generate") or hasattr(cls, "generate_auto"))


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
    def test_execution_state_trace_with_failed(self):
        from unittest.mock import patch

        from apps.creation.orchestration.sub_skill_orchestrator import SkillExecutionState

        fake_agent = {
            "sub_skills": [
                {"id": "reference-injector", "type": "retrieval"},
                {"id": "structure-generator", "type": "llm"},
                {"id": "world-validator", "type": "cli", "cli": "sub-world"},
            ],
        }
        with patch(
            "apps.agent.runtime.get_agent",
            return_value=fake_agent,
        ):
            state = SkillExecutionState(agent_id="world")
            state.record("reference-injector", "executed", skill_type="retrieval")
            state.record("world-validator", "failed", skill_type="cli", message="rootRules 不足")
            trace = state.to_trace_list("world")
        statuses = {t["id"]: t["status"] for t in trace}
        self.assertEqual(statuses.get("reference-injector"), "executed")
        self.assertEqual(statuses.get("world-validator"), "failed")
        self.assertIn("structure-generator", statuses)
        self.assertEqual(statuses.get("structure-generator"), "skipped")

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
        from apps.creation.orchestration.sub_skill_orchestrator import _SUB_SKILL_SYSTEM_HINTS

        hook = _SUB_SKILL_SYSTEM_HINTS["hook-planner"]
        self.assertIn("paymentCheckpoints", hook)
        self.assertIn("reversalSchedule", hook)
        self.assertIn("psychologyStrategy", hook)

        rel = _SUB_SKILL_SYSTEM_HINTS["relationship-weaver"]
        self.assertIn("characterAId", rel)
        self.assertIn("characterBId", rel)

        script = _SUB_SKILL_SYSTEM_HINTS["episode-script-writer"]
        self.assertIn("40 字", script)
        self.assertIn("hookTypeCode", script)

        fixer = _SUB_SKILL_SYSTEM_HINTS["world-fixer"]
        self.assertIn("reversalCode", fixer)
        self.assertIn("suggestedHookCodes", fixer)


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
    def test_build_post_script_summary_pending(self):
        from unittest.mock import MagicMock, patch

        from apps.creation.post_script_summary import build_post_script_summary

        project = MagicMock()
        project.status = "pending"
        project.overall_score = None
        project.grade = None

        with patch("apps.workflow.pipeline_store.FusionPipelineDbService.should_use_db", return_value=False):
            with patch("apps.creation.post_script_summary.get_artifact", return_value={}):
                with patch(
                    "apps.creation.orchestration.orchestrator.AgentOrchestrator"
                ) as mock_orch_cls:
                    mock_orch_cls.return_value.scripts_fully_generated.return_value = True
                    out = build_post_script_summary(project)

        self.assertTrue(out["scriptsReady"])
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

        def fake_artifact(_p, key):
            if key == "marketing_kit":
                return {"titles": ["霸总追妻"], "clipHooks": ["她转身那一刻"]}
            if key == "review_report":
                return {"passed": True, "issues": []}
            if key == "script_score_report":
                return {"overallScore": 88, "grade": "A"}
            return {}

        with patch("apps.workflow.pipeline_store.FusionPipelineDbService.should_use_db", return_value=False):
            with patch("apps.creation.post_script_summary.get_artifact", side_effect=fake_artifact):
                with patch(
                    "apps.creation.orchestration.orchestrator.AgentOrchestrator"
                ) as mock_orch_cls:
                    mock_orch_cls.return_value.scripts_fully_generated.return_value = True
                    out = build_post_script_summary(project)

        self.assertEqual(out["marketing"]["titles"][0], "霸总追妻")
        self.assertEqual(out["status"], "done")

    def test_build_post_script_summary_review_sub_reports(self):
        from unittest.mock import MagicMock, patch

        from apps.creation.post_script_summary import build_post_script_summary

        project = MagicMock()
        project.status = "completed"
        project.overall_score = None
        project.grade = None

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
            return {}

        with patch("apps.workflow.pipeline_store.FusionPipelineDbService.should_use_db", return_value=False):
            with patch("apps.creation.post_script_summary.get_artifact", side_effect=fake_artifact):
                with patch(
                    "apps.creation.orchestration.orchestrator.AgentOrchestrator"
                ) as mock_orch_cls:
                    mock_orch_cls.return_value.scripts_fully_generated.return_value = True
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
