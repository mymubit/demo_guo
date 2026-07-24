# -*- coding: utf-8 -*-
"""V3 系统配置修订与 resolve/save 测试。"""
from __future__ import annotations

from django.test import TestCase, override_settings

from apps.core.exceptions import BusinessException, VALIDATION_ERROR
from apps.drama.models import V3SystemConfigRevision
from apps.drama.orchestrator.system_config import resolve_system_config, save_system_overlay
from apps.drama.tests.helpers import SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class V3SystemConfigResolverTests(TestCase):
    def test_resolve_without_revision_returns_defaults(self) -> None:
        state = resolve_system_config()
        self.assertEqual(state["revision"], 0)
        self.assertEqual(state["overlay"], {})
        effective = state["effective"]
        self.assertEqual(effective["target_platform"], "generic")
        self.assertEqual(effective["scoring_preset"], "standard")
        self.assertEqual(effective["pass_threshold"], 75)
        self.assertEqual(effective["platform_label_zh"], "通用")
        self.assertIsNone(effective["daily_cost_alert_cny"])

    def test_save_increments_revision_and_updates_effective(self) -> None:
        state = save_system_overlay(
            overlay={"scoring_preset": "strict"},
            actor="admin",
            change_reason="收紧阈值",
        )
        self.assertEqual(state["revision"], 1)
        self.assertEqual(state["overlay"], {"scoring_preset": "strict"})
        self.assertEqual(state["effective"]["scoring_preset"], "strict")
        self.assertEqual(state["effective"]["pass_threshold"], 80)
        self.assertEqual(V3SystemConfigRevision.objects.count(), 1)

        again = resolve_system_config()
        self.assertEqual(again["revision"], 1)
        self.assertEqual(again["effective"]["scoring_preset"], "strict")

    def test_platform_recommendation_when_preset_omitted(self) -> None:
        state = save_system_overlay(
            overlay={"target_platform": "douyin"},
            actor="ops",
        )
        self.assertEqual(state["effective"]["target_platform"], "douyin")
        self.assertEqual(state["effective"]["scoring_preset"], "rhythm_first")
        self.assertEqual(state["effective"]["platform_label_zh"], "抖音")
        self.assertEqual(state["effective"]["pass_threshold"], 75)

    def test_quality_pass_threshold_overrides_preset(self) -> None:
        state = save_system_overlay(
            overlay={
                "scoring_preset": "standard",
                "quality_pass_threshold": 90,
            },
            actor="ops",
        )
        self.assertEqual(state["overlay"]["quality_pass_threshold"], 90)
        self.assertEqual(state["effective"]["pass_threshold"], 90)
        self.assertEqual(state["effective"]["scoring_preset"], "standard")

    def test_unknown_overlay_keys_ignored(self) -> None:
        state = save_system_overlay(
            overlay={
                "scoring_preset": "relaxed",
                "unknown_key": "drop-me",
                "agent_runtime": {},
            },
            actor="ops",
        )
        self.assertEqual(state["overlay"], {"scoring_preset": "relaxed"})
        self.assertEqual(state["effective"]["scoring_preset"], "relaxed")
        self.assertEqual(state["effective"]["pass_threshold"], 60)

    def test_invalid_scoring_preset_rejected(self) -> None:
        with self.assertRaises(BusinessException) as ctx:
            save_system_overlay(overlay={"scoring_preset": "ultra"}, actor="ops")
        self.assertEqual(ctx.exception.code, VALIDATION_ERROR)

    def test_invalid_platform_rejected(self) -> None:
        with self.assertRaises(BusinessException) as ctx:
            save_system_overlay(overlay={"target_platform": "tiktok"}, actor="ops")
        self.assertEqual(ctx.exception.code, VALIDATION_ERROR)

    def test_invalid_threshold_rejected(self) -> None:
        with self.assertRaises(BusinessException) as ctx:
            save_system_overlay(
                overlay={"quality_pass_threshold": 101},
                actor="ops",
            )
        self.assertEqual(ctx.exception.code, VALIDATION_ERROR)

    def test_overlay_partial_update_merges_previous(self) -> None:
        save_system_overlay(
            overlay={"target_platform": "douyin", "scoring_preset": "strict"},
            actor="ops",
        )
        state = save_system_overlay(
            overlay={"scoring_preset": "relaxed"},
            actor="ops",
            change_reason="仅改预设",
        )
        self.assertEqual(state["revision"], 2)
        self.assertEqual(
            state["overlay"],
            {"target_platform": "douyin", "scoring_preset": "relaxed"},
        )
        self.assertEqual(state["effective"]["target_platform"], "douyin")
        self.assertEqual(state["effective"]["scoring_preset"], "relaxed")

    def test_quality_pass_threshold_null_clears_overlay(self) -> None:
        save_system_overlay(
            overlay={
                "scoring_preset": "standard",
                "quality_pass_threshold": 90,
            },
            actor="ops",
        )
        state = save_system_overlay(
            overlay={"quality_pass_threshold": None},
            actor="ops",
            change_reason="清除阈值覆盖",
        )
        self.assertEqual(state["revision"], 2)
        self.assertEqual(state["overlay"], {"scoring_preset": "standard"})
        self.assertNotIn("quality_pass_threshold", state["overlay"])
        self.assertEqual(state["effective"]["pass_threshold"], 75)

    def test_daily_cost_alert_cny_saved_and_effective(self) -> None:
        state = save_system_overlay(
            overlay={"daily_cost_alert_cny": 12.5},
            actor="ops",
        )
        self.assertEqual(state["overlay"]["daily_cost_alert_cny"], 12.5)
        self.assertEqual(state["effective"]["daily_cost_alert_cny"], 12.5)

    def test_daily_cost_alert_cny_null_clears(self) -> None:
        save_system_overlay(overlay={"daily_cost_alert_cny": 10}, actor="ops")
        state = save_system_overlay(
            overlay={"daily_cost_alert_cny": None},
            actor="ops",
        )
        self.assertNotIn("daily_cost_alert_cny", state["overlay"])
        self.assertIsNone(state["effective"]["daily_cost_alert_cny"])

    def test_daily_cost_alert_cny_rejects_negative(self) -> None:
        with self.assertRaises(BusinessException) as ctx:
            save_system_overlay(overlay={"daily_cost_alert_cny": -1}, actor="ops")
        self.assertEqual(ctx.exception.code, VALIDATION_ERROR)
