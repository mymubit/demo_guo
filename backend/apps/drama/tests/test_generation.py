# -*- coding: utf-8 -*-
"""生成闭环、技能加载与门禁测试。"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings

from apps.core.exceptions import IDEMPOTENCY_CONFLICT, WORKFLOW_GATE_BLOCKED
from apps.drama.models import DramaArtifactVersion, DramaGenerationJob
from apps.drama.services.artifact_service import ArtifactService
from apps.drama.services.generation_gate import GenerationGate
from apps.drama.services.generation_service import GenerationService
from apps.drama.services.json_parse import JsonParseError, parse_llm_json, strip_markdown_fence
from apps.drama.services.project_settings import ProjectSettingsService
from apps.drama.services.prompt_builder import PromptBuilder
from apps.drama.services.quality_gate import quality_gate_passed
from apps.drama.services.skills_loader import SkillsBundleLoader
from apps.drama.services.workflow_service import WorkflowService
from apps.drama.tests.helpers import FIXTURES, SKILLS_ROOT, create_project, create_user


def _mock_llm_response(payload: dict) -> dict:
    return {
        "choices": [
            {"message": {"content": json.dumps(payload, ensure_ascii=False)}}
        ]
    }


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    LLM_ENABLED=False,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class SkillsLoaderTests(TestCase):
    def test_registry_and_role_contract(self):
        loader = SkillsBundleLoader()
        entry = loader.get_role_entry("drama.topic-director")
        self.assertEqual(entry["agent_id"], "drama.topic-director")
        contract = loader.get_role_contract("drama.topic-director")
        self.assertIn("rule_policy", contract)
        self.assertIn("input_contract", contract)

    def test_load_skill_module_and_schema(self):
        loader = SkillsBundleLoader()
        skill = loader.load_skill("drama.topic-director")
        self.assertIn("选题定调官", skill)
        module = loader.load_module("concept-development")
        self.assertIn("概念", module)
        schema = loader.load_artifact_schema("project_brief")
        self.assertEqual(schema["$id"], "drama-skills://artifacts/project_brief/1")

    def test_output_artifact_from_producer_contract(self):
        loader = SkillsBundleLoader()
        self.assertEqual(
            loader.get_output_artifact_by_role("drama.topic-director"),
            "project_brief",
        )

    def test_runtime_projection_from_settings(self):
        loader = SkillsBundleLoader()
        settings = {
            "episode_count": 24,
            "target_platform": "generic",
            "core_idea": "测试",
            "creation_preferences": {"scoring_preset": "standard"},
        }
        runtime = loader.project_runtime_projection("drama.topic-director", settings)
        self.assertEqual(runtime["episode_count"], 24)
        self.assertEqual(runtime["core_idea"], "测试")


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class PromptBuilderTests(TestCase):
    def test_builds_role_scoped_prompt_without_other_roles(self):
        user = create_user()
        project = create_project(user)
        builder = PromptBuilder()
        system, user_prompt, _manifest = builder.build(
            "drama.topic-director",
            settings=project.settings,
            workflow_state=project.workflow_state.state,
            artifacts={},
            input_payload={},
        )
        self.assertIn("drama.topic-director", system)
        self.assertNotIn("drama.story-bible", system)
        self.assertIn("runtime_projection", user_prompt)
        self.assertIn("输出反例", system)
        self.assertLessEqual(
            len(builder.loader.collect_rules("drama.topic-director", project.settings)),
            2703,
        )

    def test_story_bible_skips_adapt_module_on_original_track(self):
        user = create_user()
        project = create_project(user)
        builder = PromptBuilder()
        modules = builder.loader.load_modules_for_role(
            "drama.story-bible", project.settings
        )
        self.assertNotIn("adaptation-originality", modules)
        adapt_settings = {
            **project.settings,
            "entry_type": "story_adapt",
            "external_story": "古早小说大纲……",
        }
        modules_adapt = builder.loader.load_modules_for_role(
            "drama.story-bible", adapt_settings
        )
        self.assertIn("adaptation-originality", modules_adapt)


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class JsonParseTests(SimpleTestCase):
    def test_strip_markdown_fence(self):
        raw = '```json\n{"a": 1}\n```'
        self.assertEqual(strip_markdown_fence(raw), '{"a": 1}')

    def test_parse_llm_json_rejects_array(self):
        with self.assertRaises(JsonParseError):
            parse_llm_json("[1,2]")

    def test_parse_llm_json_rejects_prose_wrapped_json(self):
        raw = '下面是结果：\n{"title": "玉碎宫门", "ok": true}\n谢谢。'
        with self.assertRaises(JsonParseError):
            parse_llm_json(raw)

    def test_parse_llm_json_repairs_trailing_comma(self):
        raw = '{"a": 1, "b": [2, 3,],}'
        self.assertEqual(parse_llm_json(raw), {"a": 1, "b": [2, 3]})

    def test_parse_llm_json_rejects_single_quotes(self):
        raw = "{'title': '玉碎宫门', 'ok': true}"
        with self.assertRaises(JsonParseError):
            parse_llm_json(raw)

    def test_parse_llm_json_rejects_inline_fence_with_prose(self):
        raw = '先看 {草稿}：\n```json\n{"score": 88}\n```'
        with self.assertRaises(JsonParseError):
            parse_llm_json(raw)


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class GenerationGateTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.project = create_project(self.user)
        self.gate = GenerationGate()

    def test_blocks_role_in_wrong_phase(self):
        from apps.core.exceptions import BusinessException

        with self.assertRaises(BusinessException) as ctx:
            self.gate.validate_start(
                self.project,
                role="drama.story-bible",
                command_id="gate-1",
                expected_version=0,
            )
        self.assertEqual(ctx.exception.code, WORKFLOW_GATE_BLOCKED)

    def test_story_adapt_requires_external_story(self):
        from apps.core.exceptions import BusinessException

        adapt = ProjectSettingsService().create_project(
            self.user,
            "改编项目",
            entry_type="story_adapt",
            external_story="",
        )
        adapt.settings = {
            **adapt.settings,
            "preset_theme_code": "family-revenge",
            "genre_matrix": {
                "emotion": "爽",
                "identity": "强者",
                "conflict": "复仇",
                "world": "都市",
            },
        }
        adapt.save(update_fields=["settings"])
        with self.assertRaises(BusinessException) as ctx:
            self.gate.validate_start(
                adapt,
                role="drama.story-bible",
                command_id="gate-adapt",
                expected_version=0,
            )
        self.assertEqual(ctx.exception.code, WORKFLOW_GATE_BLOCKED)
        self.assertIn("external_story", str(ctx.exception))

    def test_story_adapt_requires_theme_any_of(self):
        from apps.core.exceptions import BusinessException

        adapt = ProjectSettingsService().create_project(
            self.user,
            "改编无题材",
            entry_type="story_adapt",
            external_story="古早小说大纲……",
        )
        # 清空题材相关设定
        settings = dict(adapt.settings)
        settings.pop("genre_matrix", None)
        settings["preset_theme_code"] = None
        adapt.settings = settings
        adapt.save(update_fields=["settings"])
        with self.assertRaises(BusinessException) as ctx:
            self.gate.validate_start(
                adapt,
                role="drama.story-bible",
                command_id="gate-adapt-theme",
                expected_version=0,
            )
        self.assertEqual(ctx.exception.code, WORKFLOW_GATE_BLOCKED)
        self.assertIn("genre_matrix", str(ctx.exception))
        self.assertIn("preset_theme_code", str(ctx.exception))

    def test_story_adapt_allows_preset_theme_code(self):
        adapt = ProjectSettingsService().create_project(
            self.user,
            "改编预设题材",
            entry_type="story_adapt",
            external_story="古早小说大纲……",
        )
        settings = dict(adapt.settings)
        settings.pop("genre_matrix", None)
        settings["preset_theme_code"] = "family-revenge"
        adapt.settings = settings
        adapt.save(update_fields=["settings"])
        artifact_key = self.gate.validate_start(
            adapt,
            role="drama.story-bible",
            command_id="gate-adapt-ok",
            expected_version=0,
        )
        self.assertEqual(artifact_key, "story_bible")

    def test_idempotent_job_conflict(self):
        from apps.core.exceptions import BusinessException

        DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.QUEUED,
            command_id="idem-1",
            role="drama.topic-director",
            request_payload={
                "role": "drama.topic-director",
                "expected_version": 0,
            },
        )
        with self.assertRaises(BusinessException) as ctx:
            self.gate.find_idempotent_job(
                self.project,
                "idem-1",
                role="drama.episode-designer",
                expected_version=0,
            )
        self.assertEqual(ctx.exception.code, IDEMPOTENCY_CONFLICT)


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    LLM_ENABLED=False,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class GenerationServiceTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.project = create_project(self.user)
        self.svc = GenerationService()

    def test_start_generation_records_metadata(self):
        job = self.svc.start_generation(
            self.project,
            command_id="gen-meta",
            expected_version=0,
            role="drama.topic-director",
            input_payload={},
            actor=self.user.username,
        )
        self.assertEqual(job.command_id, "gen-meta")
        self.assertEqual(job.role, "drama.topic-director")
        self.assertEqual(job.artifact_key, "project_brief")
        self.assertEqual(job.workflow_version, 0)

    def test_start_generation_idempotent(self):
        first = self.svc.start_generation(
            self.project,
            command_id="gen-idem",
            expected_version=0,
            role="drama.topic-director",
            input_payload={},
            actor=self.user.username,
        )
        second = self.svc.start_generation(
            self.project,
            command_id="gen-idem",
            expected_version=0,
            role="drama.topic-director",
            input_payload={},
            actor=self.user.username,
        )
        self.assertEqual(first.id, second.id)
        self.assertEqual(
            DramaGenerationJob.objects.filter(
                project=self.project, command_id="gen-idem"
            ).count(),
            1,
        )

    def test_execute_generation_disabled_without_llm(self):
        job = self.svc.start_generation(
            self.project,
            command_id="gen-disabled",
            expected_version=0,
            role="drama.topic-director",
            input_payload={},
            actor=self.user.username,
        )
        job.refresh_from_db()
        self.assertEqual(job.status, DramaGenerationJob.Status.DISABLED)
        self.project.workflow_state.refresh_from_db()
        self.assertEqual(self.project.workflow_state.state["current_phase"], "strategy")

    @patch("apps.drama.services.generation_service.LlmProvider.chat_completion")
    def test_execute_generation_saves_artifact_and_advances_workflow(self, mock_llm):
        mock_llm.return_value = _mock_llm_response(FIXTURES["project_brief"])
        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.QUEUED,
            command_id="gen-exec",
            role="drama.topic-director",
            artifact_key="project_brief",
            workflow_version=0,
            request_payload={
                "command_id": "gen-exec",
                "expected_version": 0,
                "role": "drama.topic-director",
                "input": {},
                "actor": self.user.username,
            },
        )
        with override_settings(LLM_ENABLED=True, LLM_API_BASE_URL="http://test", LLM_API_KEY="k"):
            self.svc.execute_generation(str(job.id))
        job.refresh_from_db()
        self.assertEqual(job.status, DramaGenerationJob.Status.COMPLETED)
        self.assertIn("artifact_key", job.result_payload)
        self.project.workflow_state.refresh_from_db()
        self.assertEqual(self.project.workflow_state.state["current_phase"], "blueprint")
        self.assertTrue(
            DramaArtifactVersion.objects.filter(
                project=self.project, artifact_key="project_brief"
            ).exists()
        )

    @patch("apps.drama.services.generation_service.LlmProvider.chat_completion")
    def test_execute_generation_fails_invalid_json_without_repair(self, mock_llm):
        mock_llm.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "这是说明文字\n{not json",
                    }
                }
            ]
        }
        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.QUEUED,
            command_id="gen-repair",
            role="drama.topic-director",
            artifact_key="project_brief",
            workflow_version=0,
            request_payload={
                "command_id": "gen-repair",
                "expected_version": 0,
                "role": "drama.topic-director",
                "input": {},
                "actor": self.user.username,
            },
        )
        with override_settings(
            LLM_ENABLED=True, LLM_API_BASE_URL="http://test", LLM_API_KEY="k"
        ):
            self.svc.execute_generation(str(job.id))
        job.refresh_from_db()
        self.assertEqual(job.status, DramaGenerationJob.Status.FAILED)
        self.assertEqual(mock_llm.call_count, 1)

    @patch("apps.drama.services.generation_service.LlmProvider.chat_completion")
    def test_writing_triggers_quality_and_gate(self, mock_llm):
        wf = WorkflowService()
        artifact_svc = ArtifactService()
        artifact_svc.save_artifact(
            self.project, "project_brief", FIXTURES["project_brief"]
        )
        wf.apply_command(
            self.project,
            command_id="w-brief",
            event="project_brief_completed",
            expected_version=0,
            actor=self.user.username,
        )
        self.project.refresh_from_db()
        artifact_svc.save_artifact(
            self.project, "story_bible", FIXTURES["story_bible"]
        )
        wf.apply_command(
            self.project,
            command_id="w-bible",
            event="story_bible_completed",
            expected_version=self.project.workflow_state.version,
            actor=self.user.username,
        )
        self.project.refresh_from_db()
        wf.apply_command(
            self.project,
            command_id="w-approve",
            event="story_bible_approved",
            expected_version=self.project.workflow_state.version,
            actor=self.user.username,
        )
        self.project.refresh_from_db()

        artifact_svc.save_artifact(
            self.project, "narrative_plan", FIXTURES["narrative_plan"]
        )
        wf.apply_command(
            self.project,
            command_id="w-plan",
            event="narrative_plan_completed",
            expected_version=self.project.workflow_state.version,
            actor=self.user.username,
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.workflow_state.state["current_phase"], "writing")

        def llm_side_effect(*, system_prompt, user_prompt, json_mode=True):
            if "剧本评分官" in system_prompt or "script-scorer" in system_prompt:
                return _mock_llm_response(FIXTURES["quality_report"])
            if "合规审查官" in system_prompt or "compliance-guard" in system_prompt:
                return _mock_llm_response(FIXTURES["compliance_report"])
            return _mock_llm_response(FIXTURES["episode_scripts"])

        mock_llm.side_effect = llm_side_effect
        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.QUEUED,
            command_id="gen-write",
            role="drama.script-writer",
            artifact_key="episode_scripts",
            workflow_version=self.project.workflow_state.version,
            request_payload={
                "command_id": "gen-write",
                "expected_version": self.project.workflow_state.version,
                "role": "drama.script-writer",
                "input": {"episode_range": {"start": 1, "count": 1}},
                "actor": self.user.username,
            },
        )
        with override_settings(LLM_ENABLED=True, LLM_API_BASE_URL="http://test", LLM_API_KEY="k"):
            self.svc.execute_generation(str(job.id))

        judge = DramaGenerationJob.objects.filter(
            project=self.project, command_id="gen-write-quality"
        ).first()
        self.assertIsNotNone(judge)
        judge.refresh_from_db()
        self.assertEqual(judge.status, DramaGenerationJob.Status.COMPLETED)
        self.assertIn("quality_report", judge.result_payload)
        self.assertNotIn("raw", judge.result_payload.get("quality_report", {}))
        self.project.workflow_state.refresh_from_db()
        phase = self.project.workflow_state.state["current_phase"]
        self.assertIn(phase, ("writing", "revision"))


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class QualityGateTests(TestCase):
    def test_quality_gate_passed(self):
        self.assertTrue(
            quality_gate_passed(
                FIXTURES["quality_report"],
                FIXTURES["compliance_report"],
            )
        )

    def test_quality_gate_failed_on_low_score(self):
        report = dict(FIXTURES["quality_report"])
        report["overall_score"] = 50
        self.assertFalse(quality_gate_passed(report, FIXTURES["compliance_report"]))


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class ProjectCreateFieldsTests(TestCase):
    def test_create_project_with_initial_fields(self):
        user = create_user()
        project = ProjectSettingsService().create_project(
            user,
            "新项目",
            entry_type="story_adapt",
            episode_count=12,
            core_idea="核心",
            external_story="外部故事原文",
        )
        self.assertEqual(project.settings["episode_count"], 12)
        self.assertEqual(project.settings["core_idea"], "核心")
        self.assertEqual(project.settings["external_story"], "外部故事原文")
