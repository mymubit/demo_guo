# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.creation.display.character_display import build_character_bible_view


class CharacterDisplayTests(SimpleTestCase):
    def test_secret_as_list_does_not_crash_gate_view(self):
        payload = {
            "characters": [
                {
                    "name": "林晚",
                    "roleType": "protagonist-female",
                    "secret": ["隐藏身世", "真实目的"],
                    "weakness": "过于信任他人",
                }
            ],
            "relationshipSummary": "测试关系",
        }
        view = build_character_bible_view(payload)
        self.assertEqual(len(view["characters"]), 1)
        self.assertEqual(view["characters"][0]["secret"], "隐藏身世 · 真实目的")
