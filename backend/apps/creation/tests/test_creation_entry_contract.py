# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from apps.creation.models import Project
from apps.creation.serializers import CreationSubmitSerializer


class CreationEntrySerializerContractTests(SimpleTestCase):
    def _payload(self, **overrides):
        data = {
            "theme": "overbearing-ceo",
            "core_idea": "一个被误解的女主重回豪门，在权力与情感夹缝中反击。",
            "episode_count": 80,
            "format_variant": "B",
            "target_platform": "douyin",
            "budget_level": "medium",
            "pipeline_mode": "workspace",
        }
        data.update(overrides)
        return data

    def test_from_reference_requires_reference_work(self):
        serializer = CreationSubmitSerializer(
            data=self._payload(creation_entry="from-reference")
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("reference_work", serializer.errors)

    def test_special_entries_accept_required_payloads(self):
        valid_cases = [
            self._payload(
                creation_entry="from-reference",
                reference_work="参考某爆款短剧的台词节奏和反转密度",
            ),
            self._payload(
                creation_entry="from-outline",
                outline_text="第1集：女主被陷害赶出家门，发现隐藏证据。\n第2集：女主找到盟友，开始反击并埋下身份反转伏笔。",
            ),
            self._payload(
                creation_entry="novel-adaptation",
                novel_text="小说正文" * 40,
            ),
            self._payload(
                creation_entry="ip-sequel",
                ip_keep_rules="保持主角姓名、公司设定和核心关系",
            ),
        ]
        for payload in valid_cases:
            with self.subTest(entry=payload["creation_entry"]):
                serializer = CreationSubmitSerializer(data=payload)
                self.assertTrue(serializer.is_valid(), serializer.errors)


class CreationEntryConfigurableValidationTests(TestCase):
    def _payload(self, **overrides):
        data = {
            "theme": "overbearing-ceo",
            "core_idea": "一个被误解的女主重回豪门，在权力与情感夹缝中反击。",
            "episode_count": 80,
            "format_variant": "B",
            "target_platform": "douyin",
            "budget_level": "medium",
            "pipeline_mode": "workspace",
        }
        data.update(overrides)
        return data

    def test_serializer_reads_entry_validation_from_admin_config(self):
        from apps.skill.models import CreationFormOverrideConfig

        CreationFormOverrideConfig.objects.update_or_create(
            config_key="default",
            defaults={
                "overrides": {
                    "platforms": [{"key": "douyin", "name": "抖音", "description": ""}],
                    "creationEntryProfiles": {
                        "from-scratch": {
                            "validation": {
                                "requiredFields": {
                                    "reference_work": {"minLength": 6, "label": "后台配置参考说明"}
                                }
                            }
                        }
                    }
                },
                "episode_settings": {},
            },
        )

        serializer = CreationSubmitSerializer(data=self._payload(creation_entry="from-scratch"))

        self.assertFalse(serializer.is_valid())
        self.assertIn("reference_work", serializer.errors)


class CreationEntryCatalogContractTests(TestCase):
    def test_catalog_keeps_from_reference_required_reference_block(self):
        from apps.workflow.fusion.ssot_catalog import get_ssot_catalog

        catalog = get_ssot_catalog().public_catalog()
        profile = (catalog.get("creationEntryProfiles") or {}).get("from-reference") or {}
        self.assertEqual((profile.get("show") or {}).get("referenceBlock"), "required")

    def test_catalog_includes_entry_display_meta_defaults(self):
        from apps.workflow.fusion.ssot_catalog import get_ssot_catalog

        catalog = get_ssot_catalog().public_catalog()
        profile = (catalog.get("creationEntryProfiles") or {}).get("from-scratch") or {}
        self.assertEqual(profile.get("tag"), "原创")
        self.assertEqual(profile.get("headline"), "原创短剧")
        self.assertEqual(profile.get("iconKey"), "sparkles")
        self.assertIsInstance(profile.get("steps"), list)
        self.assertGreaterEqual(len(profile.get("steps") or []), 3)

    def test_catalog_includes_pipeline_hints_defaults(self):
        from apps.workflow.fusion.ssot_catalog import get_ssot_catalog

        catalog = get_ssot_catalog().public_catalog()
        profile = (catalog.get("creationEntryProfiles") or {}).get("from-outline") or {}
        hints = profile.get("pipelineHints") or {}
        self.assertEqual(hints.get("prefilledSteps"), [1])
        self.assertTrue(hints.get("caption"))

    def test_portal_catalog_includes_execution_plan(self):
        from apps.portal.creation.fusion_views import _portal_catalog

        catalog = _portal_catalog()
        self.assertIn("executionPlan", catalog)
        plan = catalog["executionPlan"]
        self.assertIn("stages", plan)
        self.assertIn("edges", plan)


class CreationEntrySubmitContractTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            phone="13900008801",
            password="test-pass-123",
        )

    def _payload(self, **overrides):
        data = {
            "theme": "overbearing-ceo",
            "core_idea": "一个被误解的女主重回豪门，在权力与情感夹缝中反击。",
            "episode_count": 20,
            "format_variant": "B",
            "target_platform": "douyin",
            "budget_level": "medium",
            "pipeline_mode": Project.MODE_WORKSPACE,
        }
        data.update(overrides)
        return data

    @patch("apps.creation.services.submission.MembershipService.get_current_membership", return_value=None)
    @patch("apps.billing.services.BillingService.charge")
    @patch("apps.billing.services.BillingService.ensure_can_create")
    def test_special_entry_submit_does_not_run_adapt(
        self,
        _mock_can_create,
        _mock_charge,
        _mock_membership,
    ):
        from apps.creation.services import CreationService

        project, _minutes = CreationService.submit(
            self.user,
            self._payload(
                creation_entry="from-reference",
                reference_work="参考某爆款短剧的节奏和反转密度",
            ),
        )

        self.assertEqual(project.execution_status, Project.STATUS_PENDING)
        self.assertEqual(project.pipeline_mode, Project.MODE_WORKSPACE)

    @patch("apps.creation.services.submission.MembershipService.get_current_membership", return_value=None)
    @patch("apps.billing.services.BillingService.charge")
    @patch("apps.billing.services.BillingService.ensure_can_create")
    def test_scratch_entry_submit_creates_project_only(
        self,
        _mock_can_create,
        _mock_charge,
        _mock_membership,
    ):
        from apps.creation.services import CreationService

        project, _minutes = CreationService.submit(
            self.user,
            self._payload(creation_entry="from-scratch"),
        )
        self.assertEqual(project.creation_entry, "from-scratch")

    @patch("apps.creation.services.submission.MembershipService.get_current_membership", return_value=None)
    @patch("apps.billing.services.BillingService.charge")
    @patch("apps.billing.services.BillingService.ensure_can_create")
    def test_requires_adapt_config_does_not_block_submit_in_independent_agent_mode(
        self,
        _mock_can_create,
        _mock_charge,
        _mock_membership,
    ):
        from apps.creation.services import CreationService
        from apps.skill.models import CreationFormOverrideConfig

        CreationFormOverrideConfig.objects.update_or_create(
            config_key="default",
            defaults={
                "overrides": {
                    "platforms": [{"key": "douyin", "name": "抖音", "description": ""}],
                    "creationEntryProfiles": {
                        "from-scratch": {"requiresAdapt": True}
                    }
                },
                "episode_settings": {},
            },
        )
        project, _minutes = CreationService.submit(
            self.user,
            self._payload(creation_entry="from-scratch"),
        )
        self.assertEqual(project.execution_status, Project.STATUS_PENDING)
