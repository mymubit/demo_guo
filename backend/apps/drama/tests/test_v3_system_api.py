# -*- coding: utf-8 -*-
"""W5 Task 3：System REST GET/PUT /api/v3/system/config/。"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.drama.models import V3SystemConfigRevision
from apps.drama.orchestrator.system_config import resolve_system_config
from apps.drama.services.skills_loader import get_skills_loader
from apps.drama.tests.helpers import SKILLS_ROOT

_BASE = "/api/v3/system/config/"


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class V3SystemConfigApiTests(APITestCase):
    def setUp(self) -> None:
        get_skills_loader.cache_clear()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="system_api", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)

    def test_get_defaults_without_revision(self) -> None:
        resp = self.client.get(_BASE)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertEqual(data["revision"], 0)
        self.assertEqual(data["overlay"], {})
        effective = data["effective"]
        self.assertEqual(effective["target_platform"], "generic")
        self.assertEqual(effective["scoring_preset"], "standard")
        self.assertIn("pass_threshold", effective)
        self.assertIn("platform_label_zh", effective)
        self.assertIsNone(effective["daily_cost_alert_cny"])

    def test_put_creates_revision_and_get_reflects(self) -> None:
        resp = self.client.put(
            _BASE,
            {
                "overlay": {
                    "target_platform": "douyin",
                    "scoring_preset": "strict",
                },
                "change_reason": "抖音严苛",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertEqual(data["revision"], 1)
        self.assertEqual(data["overlay"]["scoring_preset"], "strict")
        self.assertEqual(data["overlay"]["target_platform"], "douyin")
        self.assertEqual(data["effective"]["scoring_preset"], "strict")
        self.assertEqual(data["effective"]["target_platform"], "douyin")
        self.assertEqual(V3SystemConfigRevision.objects.count(), 1)

        got = self.client.get(_BASE).json()["data"]
        self.assertEqual(got["revision"], 1)
        self.assertEqual(got["effective"]["scoring_preset"], "strict")
        self.assertEqual(resolve_system_config()["effective"]["scoring_preset"], "strict")

    def test_put_rejects_invalid_scoring_preset(self) -> None:
        resp = self.client.put(
            _BASE,
            {"overlay": {"scoring_preset": "ultra"}},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertNotEqual(body["code"], 0)
        self.assertIn("scoring_preset", body["message"])

    def test_put_ignores_unknown_overlay_keys(self) -> None:
        resp = self.client.put(
            _BASE,
            {
                "overlay": {
                    "scoring_preset": "relaxed",
                    "unknown_knob": True,
                }
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["overlay"], {"scoring_preset": "relaxed"})
        self.assertNotIn("unknown_knob", data["overlay"])

    def test_put_partial_overlay_merges_previous(self) -> None:
        first = self.client.put(
            _BASE,
            {
                "overlay": {
                    "target_platform": "douyin",
                    "scoring_preset": "strict",
                    "quality_pass_threshold": 88,
                }
            },
            format="json",
        )
        self.assertEqual(first.status_code, 200)

        second = self.client.put(
            _BASE,
            {"overlay": {"scoring_preset": "relaxed"}},
            format="json",
        )
        self.assertEqual(second.status_code, 200)
        data = second.json()["data"]
        self.assertEqual(data["revision"], 2)
        self.assertEqual(data["overlay"]["target_platform"], "douyin")
        self.assertEqual(data["overlay"]["scoring_preset"], "relaxed")
        self.assertEqual(data["overlay"]["quality_pass_threshold"], 88)
        self.assertEqual(data["effective"]["target_platform"], "douyin")

        cleared = self.client.put(
            _BASE,
            {"overlay": {"quality_pass_threshold": None}},
            format="json",
        )
        self.assertEqual(cleared.status_code, 200)
        cleared_data = cleared.json()["data"]
        self.assertNotIn("quality_pass_threshold", cleared_data["overlay"])
        self.assertEqual(cleared_data["overlay"]["scoring_preset"], "relaxed")
        self.assertEqual(cleared_data["overlay"]["target_platform"], "douyin")

    def test_put_daily_cost_alert_cny_roundtrip(self) -> None:
        resp = self.client.put(
            _BASE,
            {"overlay": {"daily_cost_alert_cny": 20}},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["overlay"]["daily_cost_alert_cny"], 20)
        self.assertEqual(data["effective"]["daily_cost_alert_cny"], 20)

        cleared = self.client.put(
            _BASE,
            {"overlay": {"daily_cost_alert_cny": None}},
            format="json",
        )
        self.assertEqual(cleared.status_code, 200)
        cleared_data = cleared.json()["data"]
        self.assertNotIn("daily_cost_alert_cny", cleared_data["overlay"])
        self.assertIsNone(cleared_data["effective"]["daily_cost_alert_cny"])

    def test_put_rejects_negative_daily_cost_alert(self) -> None:
        resp = self.client.put(
            _BASE,
            {"overlay": {"daily_cost_alert_cny": -0.01}},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertNotEqual(body["code"], 0)
        self.assertIn("daily_cost_alert_cny", body["message"])

    def test_unauthenticated_rejected(self) -> None:
        self.client.force_authenticate(user=None)
        resp = self.client.get(_BASE)
        self.assertIn(resp.status_code, (401, 403))
