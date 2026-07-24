# -*- coding: utf-8 -*-
"""干跑 vs 真实注入对比 / SkillOps 归因。"""
from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from apps.drama.services.skill_ops_service import (
    CAUSE_MODEL_ERROR,
    CAUSE_OVER_INJECTION,
    CAUSE_SCHEMA,
    infer_suspected_causes,
)
from apps.drama.services.skills_inventory_service import diff_injection_manifests
from apps.drama.tests.helpers import SKILLS_ROOT


class _FakeLog:
    def __init__(
        self,
        *,
        purpose="",
        error_message="",
        role="drama.script-writer",
        status="error",
        response_text="",
        injection_manifest=None,
    ):
        self.purpose = purpose
        self.error_message = error_message
        self.role = role
        self.status = status
        self.response_text = response_text
        self.injection_manifest = injection_manifest


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class SkillOpsAttributionTests(SimpleTestCase):
    def test_schema_without_truncation(self) -> None:
        causes = infer_suspected_causes(
            _FakeLog(error_message="产物 Schema 校验失败", purpose="artifact_generation"),
            "skill_structure",
        )
        self.assertIn(CAUSE_SCHEMA, causes)
        self.assertNotIn(CAUSE_OVER_INJECTION, causes)

    def test_schema_with_truncation_adds_over_injection(self) -> None:
        causes = infer_suspected_causes(
            _FakeLog(
                error_message="不是合法 JSON 对象",
                purpose="artifact_generation_json_repair",
                injection_manifest={
                    "layers": {"knowledge": {"chars": 100, "truncated": True}},
                    "modules": {"included": [], "skipped": []},
                },
            ),
            "skill_structure",
        )
        self.assertIn(CAUSE_SCHEMA, causes)
        self.assertIn(CAUSE_OVER_INJECTION, causes)

    def test_infra_is_model_error(self) -> None:
        causes = infer_suspected_causes(
            _FakeLog(error_message="Read timed out"),
            "infra",
        )
        self.assertEqual(causes, [CAUSE_MODEL_ERROR])


class InjectionDiffTests(SimpleTestCase):
    def test_matched_when_same(self) -> None:
        m = {
            "system_chars": 1000,
            "checksum": "abc",
            "layers": {"skill": {"chars": 1000, "truncated": False}},
            "modules": {"included": [{"id": "a"}], "skipped": []},
            "knowledge": {"included": [{"path": "knowledge/x.md"}]},
        }
        diff = diff_injection_manifests(m, m)
        self.assertTrue(diff["matched"])
        self.assertEqual(diff["mismatches"], [])

    def test_module_mismatch(self) -> None:
        dry = {
            "system_chars": 1000,
            "layers": {},
            "modules": {"included": [{"id": "a"}, {"id": "b"}]},
            "knowledge": {"included": []},
        }
        live = {
            "system_chars": 1000,
            "layers": {},
            "modules": {"included": [{"id": "a"}]},
            "knowledge": {"included": []},
        }
        diff = diff_injection_manifests(dry, live)
        self.assertFalse(diff["matched"])
        kinds = {m["kind"] for m in diff["mismatches"]}
        self.assertIn("modules", kinds)


class InjectionTodoShapeTests(SimpleTestCase):
    def test_todo_dict_supports_diagnosis_fields(self) -> None:
        """人话字段契约：severity / reason_zh / actions（不依赖 DB）。"""
        sample = {
            "kind": "often_truncated",
            "agent_id": "drama.story-bible",
            "message": "近 3 次调用中有 2 次预算截断",
            "reason_zh": "drama.story-bible 最近被预算截断",
            "severity": "warn",
            "actions": [
                {
                    "kind": "roles",
                    "label": "去装配",
                    "query": {"tab": "roles", "role": "drama.story-bible"},
                }
            ],
        }
        self.assertEqual(sample["severity"], "warn")
        self.assertIn("截断", sample["reason_zh"])
        self.assertEqual(sample["actions"][0]["kind"], "roles")
