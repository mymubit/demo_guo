# -*- coding: utf-8 -*-
"""配置覆盖越权测试。"""
from django.test import TestCase, override_settings

from apps.core.exceptions import CONFIG_OVERLAY_FORBIDDEN
from apps.drama.services.config_overlay import ConfigOverlayService
from apps.drama.tests.helpers import SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class ConfigOverlayServiceTests(TestCase):
    def setUp(self):
        self.svc = ConfigOverlayService()
        self.base_overlay = {
            "schema_version": "ops-config-overlay.v1",
            "tenant_id": "test",
            "skills_version": "5.0.0",
            "overrides": {
                "foundation/constraints/quality-scoring.yaml": {
                    "grade_thresholds": {"B": 78}
                }
            },
            "audit": {
                "revision": 1,
                "updated_by": "admin",
                "updated_at": "2026-07-14T00:00:00Z",
                "change_reason": "测试",
            },
        }

    def test_allowed_overlay(self):
        result = self.svc.put_overlay(
            self.base_overlay,
            expected_revision=0,
            actor="admin",
        )
        self.assertEqual(result["audit"]["revision"], 1)

    def test_forbidden_overlay_path(self):
        from apps.core.exceptions import BusinessException

        overlay = dict(self.base_overlay)
        overlay["overrides"] = {
            "foundation/constraints/quality-scoring.yaml": {"dimensions": []}
        }
        with self.assertRaises(BusinessException) as ctx:
            self.svc.put_overlay(overlay, expected_revision=0, actor="admin")
        self.assertEqual(ctx.exception.code, CONFIG_OVERLAY_FORBIDDEN)

    def test_rollback_appends_history(self):
        self.svc.put_overlay(self.base_overlay, expected_revision=0, actor="admin")
        overlay2 = dict(self.base_overlay)
        overlay2["audit"] = dict(self.base_overlay["audit"])
        overlay2["audit"]["change_reason"] = "第二次"
        self.svc.put_overlay(overlay2, expected_revision=1, actor="admin")
        rolled = self.svc.rollback(
            target_revision=1,
            change_reason="回滚测试",
            actor="admin",
        )
        self.assertEqual(rolled["audit"]["revision"], 3)
