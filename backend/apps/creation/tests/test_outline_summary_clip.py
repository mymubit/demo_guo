# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.creation.outline_skeleton import OUTLINE_SUMMARY_MAX, clip_summary_text


class OutlineSummaryClipTests(SimpleTestCase):
    def test_clip_at_comma_not_mid_clause(self):
        text = "甲" * 350 + "，" + "乙" * 100
        clipped = clip_summary_text(text, OUTLINE_SUMMARY_MAX)
        self.assertLessEqual(len(clipped), OUTLINE_SUMMARY_MAX)
        self.assertTrue(clipped.endswith("，"))

    def test_short_text_unchanged(self):
        text = "短梗概" * 10
        self.assertEqual(clip_summary_text(text), text)
