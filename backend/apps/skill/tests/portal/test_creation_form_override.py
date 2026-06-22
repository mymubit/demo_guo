# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.skill.config.portal.creation_form import CreationFormOverrideService
from apps.skill.models import CreationFormOverrideConfig


class CreationFormOverrideServiceTests(TestCase):
    def setUp(self):
        CreationFormOverrideConfig.objects.filter(config_key="default").delete()
        from apps.skill.config.portal.creation_catalog import clear_creation_catalog_cache

        clear_creation_catalog_cache()

    def tearDown(self):
        from apps.skill.config.portal.creation_catalog import clear_creation_catalog_cache

        clear_creation_catalog_cache()

    def test_ensure_defaults_imports_disk_catalog_to_db(self):
        self.assertTrue(CreationFormOverrideService.ensure_defaults())
        row = CreationFormOverrideConfig.objects.get(config_key="default")
        overrides = row.overrides or {}
        profiles = overrides.get("creationEntryProfiles") or {}
        self.assertIn("from-reference", profiles)
        self.assertEqual((profiles["from-reference"].get("show") or {}).get("referenceBlock"), "required")
        platforms = overrides.get("platforms") or []
        self.assertTrue(any(p.get("key") == "douyin" for p in platforms))

    def test_runtime_profiles_read_db_not_disk(self):
        CreationFormOverrideConfig.objects.create(
            config_key="default",
            overrides={
                "platforms": [{"key": "douyin", "name": "抖音", "description": ""}],
                "creationEntryProfiles": {
                    "from-reference": {
                        "show": {"referenceBlock": "hidden"},
                        "tag": "自定义",
                    }
                },
            },
        )
        profiles = CreationFormOverrideService.get_creation_entry_profiles()
        self.assertEqual(
            (profiles["from-reference"].get("show") or {}).get("referenceBlock"),
            "hidden",
        )
        self.assertEqual(profiles["from-reference"].get("tag"), "自定义")

    def test_get_creation_entry_profiles_reads_db_only(self):
        CreationFormOverrideService.ensure_defaults()
        profiles = CreationFormOverrideService.get_creation_entry_profiles()
        self.assertEqual(profiles["from-scratch"].get("tag"), "原创")
        hints = (profiles.get("from-outline") or {}).get("pipelineHints") or {}
        self.assertEqual(hints.get("prefilledSteps"), [1])

    def test_ensure_defaults_seeds_sections_from_disk(self):
        self.assertTrue(CreationFormOverrideService.ensure_defaults())
        sections = CreationFormOverrideService.get_sections()
        self.assertEqual(sections.get("theme", {}).get("title"), "选择题材")


class CreationFormImportApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            phone="13900007702",
            password="admin-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        CreationFormOverrideConfig.objects.filter(config_key="default").delete()

    def test_import_endpoint_seeds_catalog(self):
        resp = self.client.post(
            "/api/admin/portal/creation-form/import/",
            {"mode": "import", "overwrite": True},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        profiles = resp.data["data"]["catalog"]["creationEntryProfiles"]
        self.assertEqual(
            (profiles.get("from-reference") or {}).get("show", {}).get("referenceBlock"),
            "required",
        )
