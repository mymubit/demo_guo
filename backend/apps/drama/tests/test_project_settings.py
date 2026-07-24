# -*- coding: utf-8 -*-
"""项目设置乐观锁与派生字段测试。"""
from django.test import TestCase, override_settings

from apps.core.exceptions import OPTIMISTIC_LOCK_FAILED
from apps.drama.tests.helpers import FIXTURE_SETTINGS, SKILLS_ROOT, create_project, create_user


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class ProjectSettingsServiceTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.project = create_project(self.user)

    def test_update_settings_increments_revision(self):
        payload = dict(FIXTURE_SETTINGS)
        payload["project_id"] = str(self.project.id)
        payload["title"] = "更新标题"
        from apps.drama.services.project_settings import ProjectSettingsService

        svc = ProjectSettingsService()
        result = svc.update_settings(
            self.project,
            payload,
            expected_revision=1,
            actor=self.user.username,
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.settings_revision, 2)
        self.assertEqual(result["audit"]["revision"], 2)
        self.assertIn("matrix_key", result["derived"])

    def test_optimistic_lock_conflict(self):
        from apps.core.exceptions import BusinessException
        from apps.drama.services.project_settings import ProjectSettingsService

        svc = ProjectSettingsService()
        payload = dict(FIXTURE_SETTINGS)
        payload["project_id"] = str(self.project.id)
        with self.assertRaises(BusinessException) as ctx:
            svc.update_settings(
                self.project,
                payload,
                expected_revision=99,
                actor=self.user.username,
            )
        self.assertEqual(ctx.exception.code, OPTIMISTIC_LOCK_FAILED)

    def test_platform_policy_unverified_does_not_block_project_settings(self):
        from apps.drama.services.project_settings import ProjectSettingsService

        svc = ProjectSettingsService()
        payload = dict(FIXTURE_SETTINGS)
        payload["project_id"] = str(self.project.id)
        payload["target_platform"] = "douyin"
        result = svc.update_settings(
            self.project,
            payload,
            expected_revision=1,
            actor=self.user.username,
        )
        self.assertEqual(result["target_platform"], "douyin")
        self.assertIsNone(result["platform_policy"]["verified_at"])

    def test_matrix_key_includes_channel_and_structure(self):
        """matrix_key 与技能仓合成器规则一致：携带频道/结构/标签段。"""
        from apps.drama.services.project_settings import ProjectSettingsService

        svc = ProjectSettingsService()
        payload = dict(FIXTURE_SETTINGS)
        payload["project_id"] = str(self.project.id)
        payload["audience_channel"] = "male"
        payload["protagonist_structure"] = "single-male"
        payload["flavor_tags"] = ["war-god", "angst-revenge"]
        result = svc.update_settings(
            self.project,
            payload,
            expected_revision=1,
            actor=self.user.username,
        )
        self.assertEqual(
            result["derived"]["matrix_key"],
            "revenge-reborn-family-modern|ch:male|ps:single-male|angst-revenge+war-god",
        )

    def test_general_channel_keeps_plain_matrix_key(self):
        from apps.drama.services.project_settings import ProjectSettingsService

        svc = ProjectSettingsService()
        payload = dict(FIXTURE_SETTINGS)
        payload["project_id"] = str(self.project.id)
        payload["audience_channel"] = "general"
        payload["flavor_tags"] = []
        result = svc.update_settings(
            self.project,
            payload,
            expected_revision=1,
            actor=self.user.username,
        )
        self.assertEqual(
            result["derived"]["matrix_key"], "revenge-reborn-family-modern"
        )

    def test_mutually_exclusive_tags_rejected(self):
        from apps.core.exceptions import VALIDATION_ERROR, BusinessException
        from apps.drama.services.project_settings import ProjectSettingsService

        svc = ProjectSettingsService()
        payload = dict(FIXTURE_SETTINGS)
        payload["project_id"] = str(self.project.id)
        payload["flavor_tags"] = ["sweet-heavy", "melo-heavy"]
        with self.assertRaises(BusinessException) as ctx:
            svc.update_settings(
                self.project,
                payload,
                expected_revision=1,
                actor=self.user.username,
            )
        self.assertEqual(ctx.exception.code, VALIDATION_ERROR)

    def test_world_dependent_tag_rejected(self):
        """harem 要求古代世界观，modern 下必须拒绝。"""
        from apps.core.exceptions import VALIDATION_ERROR, BusinessException
        from apps.drama.services.project_settings import ProjectSettingsService

        svc = ProjectSettingsService()
        payload = dict(FIXTURE_SETTINGS)
        payload["project_id"] = str(self.project.id)
        payload["flavor_tags"] = ["harem"]
        with self.assertRaises(BusinessException) as ctx:
            svc.update_settings(
                self.project,
                payload,
                expected_revision=1,
                actor=self.user.username,
            )
        self.assertEqual(ctx.exception.code, VALIDATION_ERROR)

    def test_matrix_theme_rules_injected(self):
        """genre_matrix 设置下 theme_code=matrix，四轴合成规则必须注入。"""
        from apps.drama.services.skills_loader import get_skills_loader

        loader = get_skills_loader()
        rules_text = loader.collect_rules(
            "drama.story-bible", dict(FIXTURE_SETTINGS), max_chars=8000
        )
        self.assertIn("四轴合成", rules_text)
