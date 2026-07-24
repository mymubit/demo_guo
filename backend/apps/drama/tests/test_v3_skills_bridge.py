# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings

from apps.drama.models import V3ArtifactVersion, V3CommandRun, V3Project
from apps.drama.services.skills_loader import get_skills_loader
from apps.drama.skills_bridge.executor import GenerationError, execute_generation
from apps.drama.skills_bridge.recipe_map import COMMAND_RECIPES, recipe_for
from apps.drama.skills_bridge.validate import validate_artifact_payload
from apps.drama.tests.helpers import SKILLS_ROOT

_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "v3_project_brief_candidate.json"
_BLUEPRINT_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "v3_blueprint_bundle.json"
_EPISODE_PLAN_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "v3_episode_plan_candidate.json"
_EPISODE_SCRIPTS_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "v3_episode_scripts_candidate.json"
_MEMORY_CHECKPOINT_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "v3_memory_checkpoint_candidate.json"
_QUALITY_REPORT_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "v3_quality_report.json"
_COMPLIANCE_REPORT_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "v3_compliance_report.json"
_PRODUCTION_PACKAGE_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "v3_production_package.json"


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class RecipeMapTests(SimpleTestCase):
    def setUp(self) -> None:
        get_skills_loader.cache_clear()

    def test_generate_topic_brief_writes_project_brief(self) -> None:
        recipe = recipe_for("generate_topic_brief")
        self.assertEqual(recipe["writes"], ["project_brief"])
        self.assertEqual(recipe["recipe_id"], "create-project-brief")
        self.assertEqual(recipe["role"], "drama-topic-director")

    def test_generate_blueprint_writes_five_artifacts(self) -> None:
        recipe = recipe_for("generate_blueprint")
        self.assertEqual(
            recipe["writes"],
            [
                "story_bible",
                "character_system",
                "world_system",
                "emotion_system",
                "originality_report",
            ],
        )
        self.assertEqual(recipe["recipe_id"], "compose-story-bible")
        self.assertEqual(recipe["role"], "drama-story-bible")

    def test_command_recipes_keys(self) -> None:
        self.assertEqual(
            set(COMMAND_RECIPES.keys()),
            {
                "generate_topic_brief",
                "generate_blueprint",
                "generate_episode_plan",
                "revise_episode_plan",
                "write_episode_batch",
                "score_quality",
                "check_compliance",
                "revise_from_findings",
                "prepare_delivery",
            },
        )

    def test_generate_episode_plan_recipe(self) -> None:
        recipe = recipe_for("generate_episode_plan")
        self.assertEqual(recipe["writes"], ["episode_plan"])
        self.assertEqual(recipe["recipe_id"], "design-episode-plan")
        self.assertEqual(recipe["role"], "drama-episode-designer")
        self.assertEqual(recipe["requires_committed"], ["project_brief", "story_bible"])

    def test_revise_episode_plan_recipe(self) -> None:
        recipe = recipe_for("revise_episode_plan")
        self.assertEqual(recipe["writes"], ["episode_plan"])
        self.assertEqual(recipe["recipe_id"], "revise-episode-plan")
        self.assertEqual(recipe["role"], "drama-episode-designer")
        self.assertEqual(recipe["requires_committed"], ["episode_plan"])

    def test_write_episode_batch_recipe(self) -> None:
        recipe = recipe_for("write_episode_batch")
        self.assertEqual(recipe["writes"], ["episode_scripts", "memory_checkpoint"])
        self.assertEqual(recipe["recipe_id"], "write-episodes")
        self.assertEqual(recipe["role"], "drama-script-writer")
        self.assertEqual(
            recipe["requires_committed"],
            ["episode_plan", "story_bible", "project_brief"],
        )

    def test_score_quality_recipe(self) -> None:
        recipe = recipe_for("score_quality")
        self.assertEqual(recipe["recipe_id"], "score-script")
        self.assertEqual(recipe["role"], "drama-script-scorer")
        self.assertEqual(recipe["writes"], ["quality_report"])
        self.assertEqual(
            recipe["requires_committed"],
            ["episode_scripts", "episode_plan", "project_brief"],
        )
        self.assertEqual(recipe["commit_mode"], "direct")

    def test_check_compliance_recipe(self) -> None:
        recipe = recipe_for("check_compliance")
        self.assertEqual(recipe["recipe_id"], "check-compliance")
        self.assertEqual(recipe["role"], "drama-compliance-guard")
        self.assertEqual(recipe["writes"], ["compliance_report"])
        self.assertEqual(
            recipe["requires_committed"],
            ["episode_scripts", "episode_plan", "project_brief"],
        )
        self.assertEqual(recipe["commit_mode"], "direct")

    def test_revise_from_findings_recipe(self) -> None:
        recipe = recipe_for("revise_from_findings")
        self.assertEqual(recipe["recipe_id"], "revise-script")
        self.assertEqual(recipe["role"], "drama-revision-master")
        self.assertEqual(recipe["writes"], ["episode_scripts", "memory_checkpoint"])
        self.assertEqual(
            recipe["requires_committed"],
            ["episode_scripts", "episode_plan", "story_bible"],
        )
        self.assertEqual(recipe["commit_mode"], "candidate")

    def test_prepare_delivery_recipe(self) -> None:
        recipe = recipe_for("prepare_delivery")
        self.assertEqual(recipe["recipe_id"], "prepare-delivery")
        self.assertEqual(recipe["role"], "drama-delivery-tool")
        self.assertEqual(recipe["writes"], ["production_package"])
        self.assertEqual(
            recipe["requires_committed"],
            ["episode_scripts", "quality_report", "compliance_report"],
        )
        self.assertEqual(recipe["commit_mode"], "direct")
        self.assertTrue(recipe["requires_delivery_gate"])

    def test_unknown_command_raises(self) -> None:
        with self.assertRaises(KeyError):
            recipe_for("unknown_command")


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class ValidateArtifactPayloadTests(SimpleTestCase):
    def setUp(self) -> None:
        get_skills_loader.cache_clear()
        self.valid_payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_invalid_payload_returns_errors(self) -> None:
        errors = validate_artifact_payload("project_brief", {"title": ""})
        self.assertTrue(errors)
        self.assertTrue(any("title" in err.lower() or "required" in err.lower() for err in errors))

    def test_fixture_payload_passes(self) -> None:
        errors = validate_artifact_payload("project_brief", self.valid_payload)
        self.assertEqual(errors, [])

    def test_unknown_artifact_key_returns_error(self) -> None:
        errors = validate_artifact_payload("not_a_real_artifact", {})
        self.assertTrue(errors)
        self.assertIn("未知产物", errors[0])

    def test_blueprint_component_fixtures_pass(self) -> None:
        bundle = json.loads(_BLUEPRINT_FIXTURE_PATH.read_text(encoding="utf-8"))
        for key in (
            "story_bible",
            "character_system",
            "world_system",
            "emotion_system",
            "originality_report",
        ):
            with self.subTest(key=key):
                self.assertEqual(validate_artifact_payload(key, bundle[key]), [])

    def test_episode_plan_fixture_passes(self) -> None:
        payload = json.loads(_EPISODE_PLAN_FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(validate_artifact_payload("episode_plan", payload), [])

    def test_episode_scripts_fixture_passes(self) -> None:
        payload = json.loads(_EPISODE_SCRIPTS_FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(validate_artifact_payload("episode_scripts", payload), [])

    def test_memory_checkpoint_fixture_passes(self) -> None:
        payload = json.loads(_MEMORY_CHECKPOINT_FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(validate_artifact_payload("memory_checkpoint", payload), [])

    def test_quality_report_fixture_passes(self) -> None:
        payload = json.loads(_QUALITY_REPORT_FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(validate_artifact_payload("quality_report", payload), [])
        dims = payload["dimensions"]
        self.assertEqual(len(dims), 10)
        for key, dim in dims.items():
            with self.subTest(dimension=key):
                self.assertIn("score", dim)
                self.assertIn("weight", dim)
                self.assertIn("evidence", dim)
                self.assertIn("deductions", dim)

    def test_compliance_report_fixture_passes(self) -> None:
        payload = json.loads(_COMPLIANCE_REPORT_FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(validate_artifact_payload("compliance_report", payload), [])

    def test_production_package_fixture_passes(self) -> None:
        payload = json.loads(_PRODUCTION_PACKAGE_FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(validate_artifact_payload("production_package", payload), [])


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class ExecuteGenerationTests(TestCase):
    def setUp(self) -> None:
        get_skills_loader.cache_clear()
        self.user = get_user_model().objects.create_user(username="execu", password="pass12345")
        self.project = V3Project.objects.create(
            owner=self.user,
            title="Executor 项目",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        self.brief_payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
        self.blueprint_bundle = json.loads(_BLUEPRINT_FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_generate_topic_brief_writes_one_candidate(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.RUNNING,
        )
        captured: list[str] = []

        def fake_llm(prompt: str) -> str:
            captured.append(prompt)
            return json.dumps(self.brief_payload, ensure_ascii=False)

        created = execute_generation(
            command_type="generate_topic_brief",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        self.assertEqual(len(created), 1)
        art = created[0]
        self.assertEqual(art.artifact_key, "project_brief")
        self.assertEqual(art.status, V3ArtifactVersion.Status.CANDIDATE)
        self.assertEqual(art.command_run_id, run.id)
        self.assertEqual(art.payload["title"], self.brief_payload["title"])
        self.assertEqual(validate_artifact_payload("project_brief", art.payload), [])
        self.assertEqual(len(captured), 1)
        self.assertIn("选题定调官", captured[0])
        self.assertIn(self.project.title, captured[0])

    def test_generate_topic_brief_normalizes_missing_theme_code(self) -> None:
        """LLM 省略 theme_code/matrix_key/rule_params 时由 normalize 注入后再校验。"""
        thin = dict(self.brief_payload)
        for key in ("theme_code", "matrix_key", "rule_params"):
            thin.pop(key, None)
        self.assertNotIn("theme_code", thin)

        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.RUNNING,
        )

        def fake_llm(_prompt: str) -> str:
            return json.dumps(thin, ensure_ascii=False)

        created = execute_generation(
            command_type="generate_topic_brief",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        self.assertEqual(len(created), 1)
        payload = created[0].payload
        self.assertEqual(payload["theme_code"], "matrix")
        self.assertTrue(payload.get("matrix_key"))
        self.assertIn("reversal_density", payload.get("rule_params") or {})
        self.assertEqual(validate_artifact_payload("project_brief", payload), [])

    def test_generate_topic_brief_uses_template_seed_when_genre_matrix_omitted(
        self,
    ) -> None:
        self.project.settings = {
            "template_seed": {
                "source": "builtin",
                "theme_code": "family-revenge",
                "dims": {
                    "emotion": "revenge",
                    "identity": "underdog",
                    "conflict": "family",
                    "world": "modern",
                    "audience_channel": "female",
                },
            }
        }
        self.project.save(update_fields=["settings", "updated_at"])

        thin = dict(self.brief_payload)
        for key in ("theme_code", "matrix_key", "rule_params", "genre_matrix"):
            thin.pop(key, None)

        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.RUNNING,
        )

        def fake_llm(prompt: str) -> str:
            self.assertIn("genre_matrix", prompt)
            self.assertIn("family-revenge", prompt)
            return json.dumps(thin, ensure_ascii=False)

        created = execute_generation(
            command_type="generate_topic_brief",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        gm = created[0].payload["genre_matrix"]
        self.assertEqual(gm["emotion"], "revenge")
        self.assertEqual(gm["conflict"], "family")
        self.assertEqual(validate_artifact_payload("project_brief", created[0].payload), [])

    def test_generate_topic_brief_missing_genre_matrix_raises_friendly_error(
        self,
    ) -> None:
        thin = {
            "title": "无矩阵",
            "core_idea": "只有卖点没有题材矩阵",
            "target_audience": "都市女性",
            "core_conflict": "冲突",
            "hook_concept": "钩子",
            "compliance_risk": "low",
            "episode_count": 30,
        }
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.RUNNING,
        )

        def fake_llm(_prompt: str) -> str:
            return json.dumps(thin, ensure_ascii=False)

        with self.assertRaises(GenerationError) as ctx:
            execute_generation(
                command_type="generate_topic_brief",
                project=self.project,
                run=run,
                llm_call=fake_llm,
            )
        self.assertIn("genre_matrix", str(ctx.exception))

    def test_generate_blueprint_writes_five_candidates(self) -> None:
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=1,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=self.brief_payload,
        )
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_blueprint",
            status=V3CommandRun.Status.RUNNING,
        )

        def fake_llm(prompt: str) -> str:
            self.assertIn("剧本蓝图", prompt)
            self.assertIn(self.brief_payload["title"], prompt)
            return json.dumps(self.blueprint_bundle, ensure_ascii=False)

        created = execute_generation(
            command_type="generate_blueprint",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        keys = [item.artifact_key for item in created]
        self.assertEqual(
            keys,
            [
                "story_bible",
                "character_system",
                "world_system",
                "emotion_system",
                "originality_report",
            ],
        )
        for item in created:
            self.assertEqual(item.status, V3ArtifactVersion.Status.CANDIDATE)
            self.assertEqual(item.command_run_id, run.id)
            self.assertEqual(validate_artifact_payload(item.artifact_key, item.payload), [])

    def test_invalid_payload_raises_generation_error(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.RUNNING,
        )

        def fake_llm(_prompt: str) -> str:
            return json.dumps({"title": ""}, ensure_ascii=False)

        with self.assertRaises(GenerationError):
            execute_generation(
                command_type="generate_topic_brief",
                project=self.project,
                run=run,
                llm_call=fake_llm,
            )
        self.assertFalse(V3ArtifactVersion.objects.filter(project=self.project).exists())

    def test_default_llm_without_provider_raises_friendly_error(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.RUNNING,
        )
        with self.assertRaises(GenerationError) as ctx:
            execute_generation(
                command_type="generate_topic_brief",
                project=self.project,
                run=run,
                llm_call=None,
            )
        self.assertIn("请先在模型配置中配置并启用供应商", str(ctx.exception))

    def test_generate_episode_plan_requires_committed_blueprint(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_episode_plan",
            status=V3CommandRun.Status.RUNNING,
        )
        with self.assertRaises(GenerationError) as ctx:
            execute_generation(
                command_type="generate_episode_plan",
                project=self.project,
                run=run,
                llm_call=lambda _prompt: "{}",
            )
        self.assertIn("请先确认选题简报", str(ctx.exception))
