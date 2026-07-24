# -*- coding: utf-8 -*-
"""P4-W1：Templates API（builtin + custom CRUD + create_project 挂钩）。"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.drama.models import V3Project, V3ProjectTemplate
from apps.drama.services.skills_loader import get_skills_loader
from apps.drama.tests.helpers import SKILLS_ROOT

_TEMPLATES = "/api/v3/templates/"
_CUSTOM = "/api/v3/templates/custom/"
_PROJECTS = "/api/v3/projects/"


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class V3TemplatesApiTests(APITestCase):
    def setUp(self) -> None:
        get_skills_loader.cache_clear()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tpl_user", password="pass12345"
        )
        self.staff = user_model.objects.create_user(
            username="tpl_staff", password="pass12345", is_staff=True
        )
        self.client.force_authenticate(user=self.user)

    def tearDown(self) -> None:
        get_skills_loader.cache_clear()

    def test_list_builtin_and_custom(self) -> None:
        V3ProjectTemplate.objects.create(
            name="自定义甜宠",
            theme_code="custom-sweet",
            label_zh="自定义甜宠",
            dims={"emotion": "love"},
            description="unit",
            created_by=self.staff,
        )
        resp = self.client.get(_TEMPLATES)
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertIn("builtin", data)
        self.assertIn("custom", data)
        self.assertGreaterEqual(len(data["builtin"]), 1)
        codes = {item["theme_code"] for item in data["builtin"]}
        self.assertIn("family-revenge", codes)
        self.assertEqual(len(data["custom"]), 1)
        self.assertEqual(data["custom"][0]["name"], "自定义甜宠")
        self.assertEqual(data["custom"][0]["kind"], "custom")
        self.assertEqual(data["builtin"][0]["kind"], "builtin")

    def test_staff_crud_custom_template(self) -> None:
        self.client.force_authenticate(user=self.staff)
        create_resp = self.client.post(
            _CUSTOM,
            {
                "name": "staff-tpl",
                "theme_code": "staff-theme",
                "label_zh": "员工模板",
                "dims": {"emotion": "revenge", "world": "modern"},
                "description": "desc",
            },
            format="json",
        )
        self.assertEqual(create_resp.status_code, 200, create_resp.content)
        created = create_resp.json()["data"]
        self.assertEqual(created["name"], "staff-tpl")
        self.assertEqual(created["theme_code"], "staff-theme")
        self.assertEqual(created["created_by"], "tpl_staff")
        template_id = created["id"]

        patch_resp = self.client.patch(
            f"{_CUSTOM}{template_id}/",
            {"label_zh": "已改名", "description": "new"},
            format="json",
        )
        self.assertEqual(patch_resp.status_code, 200, patch_resp.content)
        self.assertEqual(patch_resp.json()["data"]["label_zh"], "已改名")
        self.assertEqual(patch_resp.json()["data"]["description"], "new")

        delete_resp = self.client.delete(f"{_CUSTOM}{template_id}/")
        self.assertEqual(delete_resp.status_code, 200, delete_resp.content)
        self.assertFalse(V3ProjectTemplate.objects.filter(id=template_id).exists())

    def test_non_staff_write_forbidden(self) -> None:
        create_resp = self.client.post(
            _CUSTOM,
            {
                "name": "nope",
                "theme_code": "nope",
                "label_zh": "禁止",
                "dims": {},
            },
            format="json",
        )
        self.assertEqual(create_resp.status_code, 403)

        obj = V3ProjectTemplate.objects.create(
            name="exist",
            theme_code="exist",
            label_zh="存在",
            dims={},
            created_by=self.staff,
        )
        patch_resp = self.client.patch(
            f"{_CUSTOM}{obj.id}/",
            {"name": "hack"},
            format="json",
        )
        self.assertEqual(patch_resp.status_code, 403)
        delete_resp = self.client.delete(f"{_CUSTOM}{obj.id}/")
        self.assertEqual(delete_resp.status_code, 403)
        self.assertTrue(V3ProjectTemplate.objects.filter(id=obj.id).exists())

    def test_create_project_with_theme_code_seeds_settings(self) -> None:
        resp = self.client.post(
            _PROJECTS,
            {
                "title": "题材种子项目",
                "entry_type": "original",
                "theme_code": "family-revenge",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        project_id = resp.json()["data"]["id"]
        project = V3Project.objects.get(id=project_id)
        seed = (project.settings or {}).get("template_seed")
        self.assertIsInstance(seed, dict)
        self.assertEqual(seed["source"], "builtin")
        self.assertEqual(seed["theme_code"], "family-revenge")
        self.assertEqual(seed["label_zh"], "家庭伦理复仇")
        self.assertIn("dims", seed)
        self.assertEqual(seed["dims"].get("emotion"), "revenge")

    def test_create_project_with_template_id_seeds_settings(self) -> None:
        tpl = V3ProjectTemplate.objects.create(
            name="custom-seed",
            theme_code="custom-seed-code",
            label_zh="自定义种子",
            dims={"emotion": "healing", "world": "modern"},
            description="d",
            created_by=self.staff,
        )
        resp = self.client.post(
            _PROJECTS,
            {
                "title": "自定义模板项目",
                "entry_type": "adapt",
                "template_id": str(tpl.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        project = V3Project.objects.get(id=resp.json()["data"]["id"])
        seed = project.settings["template_seed"]
        self.assertEqual(seed["source"], "custom")
        self.assertEqual(seed["template_id"], str(tpl.id))
        self.assertEqual(seed["theme_code"], "custom-seed-code")
        self.assertEqual(seed["dims"]["emotion"], "healing")
