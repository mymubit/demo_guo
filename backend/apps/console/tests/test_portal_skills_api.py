# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class PortalSkillsAdminApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            phone="13900007703",
            password="admin-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_portal_creation_form(self):
        resp = self.client.get("/api/admin/portal/creation-form/")
        self.assertEqual(resp.status_code, 200)

    def test_skills_rules_list(self):
        resp = self.client.get("/api/admin/skills/rules/")
        self.assertEqual(resp.status_code, 200)

    def test_legacy_skill_prefix_deprecated(self):
        legacy_paths = [
            "/api/admin/skill/creation-form/",
            "/api/admin/skill/themes/",
            "/api/admin/skill/hooks/",
            "/api/admin/skill/configs/",
            "/api/admin/skill/rules/",
            "/api/admin/skill/agent-registry/",
            "/api/admin/skill/llm/",
        ]
        for path in legacy_paths:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 404, path)
