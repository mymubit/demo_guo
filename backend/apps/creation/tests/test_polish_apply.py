# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.creation.polish_apply import _normalize_suggestion


class PolishApplyTests(SimpleTestCase):
    def test_normalize_llm_suggestion(self):
        out = _normalize_suggestion(
            {"episodeNumber": 3, "field": "dialogue", "advice": "缩短开场对白"},
            1,
        )
        self.assertEqual(out["episodeNumber"], 3)
        self.assertEqual(out["field"], "dialogue")
        self.assertIn("缩短", out["advice"])

    def test_normalize_text_suggestion(self):
        out = _normalize_suggestion("节奏偏慢", 0)
        self.assertEqual(out["text"], "节奏偏慢")
