# -*- coding: utf-8 -*-
"""项目设置乐观锁与派生字段测试。"""
from django.test import TestCase, override_settings

from apps.core.exceptions import OPTIMISTIC_LOCK_FAILED
from apps.drama.tests.helpers import FIXTURE_SETTINGS, create_project, create_user


@override_settings(DRAMA_SKILLS_ROOT="/workspace", LLM_ENABLED=False)
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
