# -*- coding: utf-8 -*-
"""角色 / 原子技能库存 API 测例。"""
from __future__ import annotations

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APITestCase

from apps.drama.services.skills_inventory_service import (
    build_prompt_breakdown,
    build_skills_inventory,
)
from apps.drama.services.skills_loader import SkillsBundleLoader
from apps.drama.tests.helpers import SKILLS_ROOT, create_project, create_user


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class SkillsInventoryServiceTests(SimpleTestCase):
    """纯服务层测例，不依赖数据库。"""

    def setUp(self) -> None:
        self.loader = SkillsBundleLoader(root=SKILLS_ROOT)

    def test_inventory_lists_roles_and_modules(self) -> None:
        data = build_skills_inventory(self.loader)
        self.assertTrue(data["skills_bundle_version"])
        agent_ids = {r["agent_id"] for r in data["roles"]}
        self.assertIn("drama.topic-director", agent_ids)
        self.assertIn("drama.story-bible", agent_ids)
        module_ids = {m["id"] for m in data["modules"]}
        self.assertIn("concept-development", module_ids)
        self.assertIn("adaptation-originality", module_ids)

    def test_module_reverse_index_matches_catalog(self) -> None:
        data = build_skills_inventory(self.loader)
        concept = next(m for m in data["modules"] if m["id"] == "concept-development")
        self.assertIn("drama.topic-director", concept["target_roles"])
        self.assertIn("drama.topic-director", concept["mounted_by"])
        self.assertEqual(concept["mismatch"], [])
        self.assertGreater(concept["file_chars"], 0)

    def test_role_attachments_have_file_totals(self) -> None:
        data = build_skills_inventory(self.loader)
        topic = next(r for r in data["roles"] if r["agent_id"] == "drama.topic-director")
        self.assertGreater(topic["file_total_chars"], 0)
        modules = topic["attachments"]["modules"]
        self.assertTrue(any(m["id"] == "concept-development" for m in modules))
        tear = next(m for m in modules if m["id"] == "tear-down-6d")
        self.assertFalse(tear["enabled_default"])
        self.assertIn("enable_when", tear["skip_reason"] or "")

    def test_prompt_breakdown_skips_conditional_modules_by_default(self) -> None:
        data = build_prompt_breakdown("drama.topic-director", settings={}, loader=self.loader)
        self.assertGreater(data["system_total"], 0)
        skipped_ids = {m["id"] for m in data["modules_skipped"]}
        self.assertIn("tear-down-6d", skipped_ids)
        included_ids = {m["id"] for m in data["modules_included"]}
        self.assertIn("concept-development", included_ids)
        self.assertIn("layers", data)
        self.assertGreater(data["layers"]["skill"]["chars"], 0)

    def test_prompt_breakdown_includes_when_settings_match(self) -> None:
        settings = {"reference_dramas": ["某爆款剧"]}
        data = build_prompt_breakdown(
            "drama.topic-director", settings=settings, loader=self.loader
        )
        included_ids = {m["id"] for m in data["modules_included"]}
        self.assertIn("tear-down-6d", included_ids)

    def test_read_module_content(self) -> None:
        from apps.drama.services.skills_inventory_service import read_skills_content

        data = read_skills_content(
            kind="module", module_id="concept-development", loader=self.loader
        )
        self.assertEqual(data["kind"], "module")
        self.assertGreater(data["chars"], 0)
        self.assertTrue(data["content"].strip())

    def test_path_traversal_rejected(self) -> None:
        from apps.drama.services.skills_inventory_service import read_skills_content

        with self.assertRaises(ValueError):
            read_skills_content(kind="path", path="../secrets.txt", loader=self.loader)

    def test_role_bundle_includes_skill_and_modules(self) -> None:
        from apps.drama.services.skills_inventory_service import build_role_bundle_content

        data = build_role_bundle_content("drama.topic-director", loader=self.loader)
        self.assertGreater(data["skill_md"]["chars"], 0)
        self.assertTrue(any(m["id"] == "concept-development" for m in data["modules"]))
        self.assertTrue(any(m["content"] for m in data["modules"]))


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class SkillsInventoryApiTests(APITestCase):
    def test_inventory_requires_auth(self) -> None:
        resp = self.client.get("/api/v1/drama/meta/skills-inventory/")
        self.assertIn(resp.data["code"], (401, 403))

    def test_inventory_endpoint(self) -> None:
        user = create_user(username="skills-inv-user")
        self.client.force_authenticate(user=user)
        resp = self.client.get("/api/v1/drama/meta/skills-inventory/")
        self.assertEqual(resp.data["code"], 0)
        data = resp.data["data"]
        self.assertTrue(data["roles"])
        self.assertTrue(data["modules"])

    def test_prompt_breakdown_with_project(self) -> None:
        user = create_user(username="skills-bd-user")
        project = create_project(user)
        project.settings = {
            **(project.settings or {}),
            "reference_dramas": ["参考剧"],
        }
        project.save(update_fields=["settings"])
        self.client.force_authenticate(user=user)
        resp = self.client.get(
            f"/api/v1/drama/meta/roles/drama.topic-director/prompt-breakdown/"
            f"?project_id={project.id}"
        )
        self.assertEqual(resp.data["code"], 0)
        data = resp.data["data"]
        self.assertEqual(data["settings_mode"], "project")
        self.assertEqual(data["project_id"], str(project.id))
        included = {m["id"] for m in data["modules_included"]}
        self.assertIn("tear-down-6d", included)

    def test_skills_content_and_bundle_endpoints(self) -> None:
        user = create_user(username="skills-content-user")
        self.client.force_authenticate(user=user)
        mod = self.client.get(
            "/api/v1/drama/meta/skills-content/?kind=module&id=concept-development"
        )
        self.assertEqual(mod.data["code"], 0)
        self.assertGreater(mod.data["data"]["chars"], 0)

        bundle = self.client.get(
            "/api/v1/drama/meta/roles/drama.topic-director/bundle-content/"
        )
        self.assertEqual(bundle.data["code"], 0)
        self.assertIn("skill_md", bundle.data["data"])
        self.assertTrue(bundle.data["data"]["modules"])
