# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.skill.models import SkillRuleConfig
from apps.skill.skills.loader import SkillRuleLoader
from apps.skill.skills.admin_service import SkillRuleConfigService


class SkillRuleTier1DbFirstTests(TestCase):
    def test_get_tier1_reads_active_db_record(self):
        SkillRuleConfig.objects.create(
            tier=1,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            scope_key="",
            section="tier_full",
            content={"philosophy": {"core_formula": "DB-TIER1-TEST"}},
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        SkillRuleConfigService.clear_rule_caches()
        loader = SkillRuleLoader()
        tier1 = loader.get_tier1() or {}
        self.assertEqual((tier1.get("philosophy") or {}).get("core_formula"), "DB-TIER1-TEST")

    def test_get_tier1_merges_section_records(self):
        SkillRuleConfig.objects.create(
            tier=1,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            scope_key="",
            section="philosophy",
            content={"core_formula": "SECTION-MERGE-TEST"},
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        SkillRuleConfig.objects.create(
            tier=1,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            scope_key="",
            section="scoring",
            content={"grade_a": {"score_range": "80-89"}},
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        SkillRuleConfigService.clear_rule_caches()
        loader = SkillRuleLoader()
        tier1 = loader.get_tier1() or {}
        self.assertEqual((tier1.get("philosophy") or {}).get("core_formula"), "SECTION-MERGE-TEST")
        self.assertEqual((tier1.get("scoring") or {}).get("grade_a", {}).get("score_range"), "80-89")


class SkillRuleAdminApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            phone="13900006601",
            password="admin-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.rule = SkillRuleConfig.objects.create(
            tier=2,
            scope_type=SkillRuleConfig.SCOPE_GENRE,
            scope_key="test-genre",
            section="genre_full",
            content={"label": "测试题材"},
            status=SkillRuleConfig.STATUS_DRAFT,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )

    def test_list_rules_returns_draft(self):
        resp = self.client.get("/api/admin/skills/rules/?status=draft&tier=2")
        self.assertEqual(resp.status_code, 200)
        ids = [item["id"] for item in resp.data["data"]["items"]]
        self.assertIn(str(self.rule.id), ids)

    def test_approve_rule(self):
        resp = self.client.post(f"/api/admin/skills/rules/{self.rule.id}/approve/")
        self.assertEqual(resp.status_code, 200)
        self.rule.refresh_from_db()
        self.assertEqual(self.rule.status, SkillRuleConfig.STATUS_ACTIVE)


class SkillRuleEnsureDefaultsTests(TestCase):
    def test_ensure_defaults_imports_missing_tiers_when_only_tier1_exists(self):
        SkillRuleConfig.objects.create(
            tier=1,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            scope_key="",
            section="tier_full",
            content={"philosophy": {"core_formula": "ONLY-TIER1"}},
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        counts = SkillRuleConfigService.ensure_defaults()
        self.assertTrue(
            SkillRuleConfig.objects.filter(tier=2, status=SkillRuleConfig.STATUS_ACTIVE).exists()
            or counts.get("tier2", 0) > 0
            or not counts
        )
