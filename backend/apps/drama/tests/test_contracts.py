# -*- coding: utf-8 -*-
"""集中契约、工作台 API 与整数 schema_version 测试。"""
from __future__ import annotations

import json
from pathlib import Path

from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from apps.drama.models import DramaArtifactVersion
from apps.drama.services.artifact_service import ArtifactService
from apps.drama.services.skills_loader import SkillsBundleLoader, get_skills_loader
from apps.drama.tests.helpers import FIXTURES, SKILLS_ROOT, create_project, create_user


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class ArtifactsContractTests(TestCase):
    def setUp(self) -> None:
        self.loader = SkillsBundleLoader()

    def test_artifacts_contract_loaded_from_manifest(self) -> None:
        contract = self.loader.artifacts_contract
        self.assertEqual(contract["version"], "1.0.0")
        self.assertIn("project_brief", contract["artifacts"])

    def test_get_artifact_contract_returns_schema_path_and_version(self) -> None:
        definition = self.loader.get_artifact_contract("story_bible")
        self.assertEqual(
            definition["schema_path"],
            "schemas/artifacts/story_bible/1.schema.json",
        )
        self.assertEqual(definition["schema_version"], 1)
        self.assertEqual(definition["label_zh"], "故事蓝图")

    def test_get_output_artifact_by_role_from_producer(self) -> None:
        self.assertEqual(
            self.loader.get_output_artifact_by_role("drama.topic-director"),
            "project_brief",
        )
        self.assertEqual(
            self.loader.get_output_artifact_by_role("drama.story-bible"),
            "story_bible",
        )
        self.assertEqual(
            self.loader.get_output_artifact_by_role("drama.script-writer"),
            "episode_scripts",
        )

    def test_artifact_schema_path_rejects_unknown_key(self) -> None:
        with self.assertRaises(KeyError):
            self.loader.artifact_schema_path("unknown_artifact")

    def test_load_artifact_schema_uses_nested_contract_path(self) -> None:
        schema = self.loader.load_artifact_schema("project_brief")
        self.assertEqual(schema["$id"], "drama-skills://artifacts/project_brief/1")

    def test_producer_map_covers_all_production_roles(self) -> None:
        producers = self.loader.producer_artifact_map()
        for role in (
            "drama.topic-director",
            "drama.story-bible",
            "drama.episode-designer",
            "drama.script-writer",
            "drama.revision-master",
            "drama.delivery-tool",
        ):
            self.assertIn(role, producers)


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class ParametersContractTests(TestCase):
    def setUp(self) -> None:
        self.loader = SkillsBundleLoader()

    def test_parameters_contract_loaded_from_manifest(self) -> None:
        contract = self.loader.parameters_contract
        self.assertIn("episode_count", contract["parameters"])
        self.assertIn("drama.topic-director", contract["role_parameter_refs"])

    def test_get_parameter_definition_includes_type_and_default(self) -> None:
        definition = self.loader.get_parameter_definition("episode_count")
        self.assertEqual(definition["type"], "integer")
        self.assertEqual(definition["minimum"], 1)

    def test_get_role_parameter_refs_matches_contract(self) -> None:
        refs = self.loader.get_role_parameter_refs("drama.script-writer")
        self.assertIn("episode_range", refs)
        self.assertIn("production_target_band", refs)

    def test_apply_parameter_defaults_uses_contract_not_payload_metadata(self) -> None:
        settings = {"entry_type": "original_track", "title": "测试"}
        filled = self.loader.apply_parameter_defaults(settings)
        self.assertEqual(filled["target_platform"], "generic")
        self.assertEqual(filled["creation_preferences"]["batch_episode_max"], 5)
        self.assertEqual(filled["creation_preferences"]["outline_mode"], "full")


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class WorkbenchFormExportTests(TestCase):
    def test_export_workbench_form_merges_fields_and_stages(self) -> None:
        form = SkillsBundleLoader().export_workbench_form()
        self.assertEqual(form["schema_version"], "workbench-form.v1")
        self.assertEqual(form["skills_bundle_version"], "5.0.0")
        entry_type = form["project_settings"]["fields"]["entry_type"]
        self.assertEqual(entry_type["type"], "string")
        self.assertIn("original_track", entry_type["enum"])
        self.assertTrue(form["module_catalog"])

        blueprint = next(stage for stage in form["stages"] if stage["id"] == "blueprint")
        self.assertEqual(blueprint["artifact"], "story_bible")
        self.assertEqual(blueprint["artifact_label"], "故事蓝图")
        self.assertEqual(blueprint["label_zh"], "剧本蓝图")
        self.assertEqual(blueprint["role_label"], "剧本蓝图官")
        self.assertTrue(all(stage.get("label_zh") for stage in form["stages"]))

    def test_export_workbench_form_resolves_platform_options(self) -> None:
        form = SkillsBundleLoader().export_workbench_form()
        platform = form["project_settings"]["fields"]["target_platform"]
        self.assertIn("options", platform)
        values = {item["value"] for item in platform["options"]}
        self.assertIn("generic", values)


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class WorkbenchFormApiTests(APITestCase):
    def test_workbench_form_endpoint_requires_auth(self) -> None:
        resp = self.client.get("/api/v1/drama/meta/workbench-form/")
        self.assertIn(resp.data["code"], (401, 403))

    def test_workbench_form_endpoint_returns_merged_contract(self) -> None:
        user = create_user(username="workbench-user")
        self.client.force_authenticate(user=user)
        resp = self.client.get("/api/v1/drama/meta/workbench-form/")
        self.assertEqual(resp.data["code"], 0)
        data = resp.data["data"]
        self.assertEqual(data["schema_version"], "workbench-form.v1")
        self.assertEqual(data["skills_bundle_version"], "5.0.0")
        self.assertIn("project_settings", data)
        self.assertIn("module_catalog", data)
        self.assertTrue(any(stage.get("artifact") for stage in data["stages"]))


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class IntegerSchemaVersionTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user()
        self.project = create_project(self.user)
        self.svc = ArtifactService()

    def test_save_artifact_persists_integer_schema_version(self) -> None:
        self.svc.save_artifact(
            self.project,
            "project_brief",
            FIXTURES["project_brief"],
        )
        record = DramaArtifactVersion.objects.get(
            project=self.project, artifact_key="project_brief"
        )
        self.assertEqual(record.schema_version, 1)
        self.assertIsInstance(record.schema_version, int)

    def test_get_artifact_returns_integer_schema_version(self) -> None:
        self.svc.save_artifact(
            self.project,
            "story_bible",
            FIXTURES["story_bible"],
        )
        artifact = self.svc.get_artifact(self.project, "story_bible")
        self.assertEqual(artifact["schema_version"], 1)
        self.assertIsInstance(artifact["schema_version"], int)

    def test_loader_cache_invalidates_on_new_instance(self) -> None:
        get_skills_loader.cache_clear()
        loader = get_skills_loader()
        self.assertEqual(loader.artifact_schema_version("narrative_plan"), 1)
