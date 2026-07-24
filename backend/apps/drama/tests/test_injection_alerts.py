# -*- coding: utf-8 -*-
"""injection_alerts 读时计算回归。"""
from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from apps.drama.services.injection_alerts import (
    ALERT_BUDGET_TRUNCATED,
    ALERT_BUNDLE_VERSION_DRIFT,
    ALERT_ENABLE_SKIPPED_CORE,
    ALERT_LAYER_DOMINANT,
    ALERT_SYSTEM_CHARS_HIGH,
    compute_injection_alerts,
    highest_alert_level,
)
from apps.drama.services.llm_call_log_service import LlmCallLogService


def _base_manifest(**overrides):
    data = {
        "version": 1,
        "agent_id": "drama.story-bible",
        "system_chars": 10_000,
        "layers": {
            "skill": {"chars": 2000, "truncated": False},
            "modules": {"chars": 3000, "truncated": False},
            "knowledge": {"chars": 2000, "truncated": False},
            "rules": {"chars": 3000, "truncated": False},
        },
        "modules": {"included": [], "skipped": []},
        "knowledge": {},
        "rules": {},
        "policies": {},
    }
    data.update(overrides)
    return data


@override_settings(INJECTION_ALERT_SYSTEM_CHARS_ABS=50_000, INJECTION_ALERT_LAYER_DOMINANT_RATIO=0.45)
class InjectionAlertsTests(SimpleTestCase):
    def test_null_manifest_returns_empty(self) -> None:
        self.assertEqual(compute_injection_alerts(None), [])

    def test_bundle_version_drift(self) -> None:
        alerts = compute_injection_alerts(
            _base_manifest(bundle_version="1.0.0"),
            current_bundle_version="2.0.0",
        )
        ids = {a["id"] for a in alerts}
        self.assertIn(ALERT_BUNDLE_VERSION_DRIFT, ids)

    def test_bundle_version_match_no_drift(self) -> None:
        alerts = compute_injection_alerts(
            _base_manifest(bundle_version="2.0.0"),
            current_bundle_version="2.0.0",
        )
        ids = {a["id"] for a in alerts}
        self.assertNotIn(ALERT_BUNDLE_VERSION_DRIFT, ids)

    def test_system_chars_high(self) -> None:
        alerts = compute_injection_alerts(_base_manifest(system_chars=60_000))
        ids = {a["id"] for a in alerts}
        self.assertIn(ALERT_SYSTEM_CHARS_HIGH, ids)

    def test_layer_dominant(self) -> None:
        alerts = compute_injection_alerts(
            _base_manifest(
                system_chars=10_000,
                layers={"knowledge": {"chars": 6000, "truncated": False}},
            )
        )
        ids = {a["id"] for a in alerts}
        self.assertIn(ALERT_LAYER_DOMINANT, ids)

    def test_budget_truncated(self) -> None:
        alerts = compute_injection_alerts(
            _base_manifest(
                layers={"knowledge": {"chars": 1000, "truncated": True}},
            )
        )
        ids = {a["id"] for a in alerts}
        self.assertIn(ALERT_BUDGET_TRUNCATED, ids)

    def test_enable_skipped_core_only_on_failure(self) -> None:
        manifest = _base_manifest(
            modules={
                "included": [],
                "skipped": [{"id": "character-system", "reason": "enable_when"}],
            }
        )
        cores = frozenset({"character-system"})
        ok = compute_injection_alerts(manifest, call_status="success", core_module_ids=cores)
        self.assertNotIn(ALERT_ENABLE_SKIPPED_CORE, {a["id"] for a in ok})
        fail = compute_injection_alerts(manifest, call_status="error", core_module_ids=cores)
        self.assertIn(ALERT_ENABLE_SKIPPED_CORE, {a["id"] for a in fail})

    def test_highest_alert_level(self) -> None:
        self.assertIsNone(highest_alert_level([]))
        self.assertEqual(
            highest_alert_level([{"id": "x", "level": "info"}]),
            "info",
        )
        self.assertEqual(
            highest_alert_level(
                [{"id": "a", "level": "info"}, {"id": "b", "level": "warn"}]
            ),
            "warn",
        )

    def test_serialize_detail_attaches_alerts(self) -> None:
        class _Log:
            id = "00000000-0000-0000-0000-000000000001"
            project_id = None
            generation_job_id = None
            v3_command_run_id = None
            v3_project_id = None
            actor = "system"
            role = "drama.story-bible"
            purpose = "artifact_generation"
            status = "success"
            model_name = "m"
            base_url = ""
            latency_ms = 1
            http_status = 200
            prompt_tokens = 1
            completion_tokens = 1
            total_tokens = 2
            error_message = ""
            seq_in_job = 1
            created_at = None
            system_prompt = "x"
            user_prompt = "y"
            response_text = "{}"
            response_body = {}
            provider_request_id = ""
            injection_manifest = _base_manifest(
                system_chars=60_000,
                layers={"knowledge": {"chars": 1000, "truncated": True}},
            )
            project = None
            generation_job = None

        detail = LlmCallLogService.serialize_detail(_Log())  # type: ignore[arg-type]
        self.assertIsInstance(detail.get("injection_alerts"), list)
        ids = {a["id"] for a in detail["injection_alerts"]}
        self.assertIn(ALERT_SYSTEM_CHARS_HIGH, ids)
        self.assertIn(ALERT_BUDGET_TRUNCATED, ids)
        self.assertEqual(detail.get("injection_alert_level"), "warn")
