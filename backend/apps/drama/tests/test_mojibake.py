# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.drama.services.json_parse import _repair_utf8_mojibake, strip_markdown_fence
from apps.drama.services.llm_provider import _repair_utf8_mojibake as repair_provider


class MojibakeRepairTests(SimpleTestCase):
    def test_repairs_utf8_as_latin1(self):
        original = "玉碎宫门"
        mojibake = original.encode("utf-8").decode("latin-1")
        self.assertNotEqual(mojibake, original)
        self.assertEqual(_repair_utf8_mojibake(mojibake), original)
        self.assertEqual(repair_provider(mojibake), original)

    def test_keeps_valid_chinese(self):
        text = "玉碎宫门，弃女入宫。"
        self.assertEqual(_repair_utf8_mojibake(text), text)

    def test_strip_json_fence(self):
        raw = '```json\n{"a": 1}\n```'
        self.assertEqual(strip_markdown_fence(raw), '{"a": 1}')
