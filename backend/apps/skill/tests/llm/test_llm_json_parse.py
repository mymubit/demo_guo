# -*- coding: utf-8 -*-
import json

from django.test import SimpleTestCase

from apps.skill.llm.chat import LlmService


class LlmJsonParseTests(SimpleTestCase):
    def test_parse_json_content_with_fence(self):
        raw = '```json\n{"ok": true, "name": "测试"}\n```'
        out = LlmService._parse_json_content(raw)
        self.assertTrue(out["ok"])
        self.assertEqual(out["name"], "测试")

    def test_repair_truncated_json_closes_string_and_braces(self):
        truncated = (
            '{"protagonists": [{"id": "p1", "name": "林晚", "background": "她来自小城'
        )
        repaired = LlmService._repair_truncated_json(truncated)
        parsed = json.loads(repaired)
        self.assertIn("protagonists", parsed)
        self.assertEqual(parsed["protagonists"][0]["name"], "林晚")

    def test_parse_json_content_repairs_truncated_payload(self):
        truncated = (
            '{"summary": "总述", "protagonists": [{"id": "p1", "name": "A", "secret": "未说完'
        )
        out = LlmService._parse_json_content(truncated)
        self.assertEqual(out["summary"], "总述")
        self.assertEqual(out["protagonists"][0]["id"], "p1")
