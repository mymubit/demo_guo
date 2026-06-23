# -*- coding: utf-8 -*-
"""保留少量手工构造 payload 的专项回归（不再依赖 expert/fast E2E 快照）。"""
from __future__ import annotations

import json
from pathlib import Path

from django.test import SimpleTestCase

from apps.drama.presentation.presenters import present_artifact

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "scripts"


class RealPayloadPresentationTests(SimpleTestCase):
    def _load_fixture(self, name: str) -> dict:
        path = FIXTURE_DIR / name
        if not path.exists():
            self.skipTest(f"fixture missing: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_plot_architect_series_outline_real_shape(self):
        payloads = self._load_fixture("e2e_payloads_series_outline_plot_architect_sample.json")
        view = present_artifact("series_outline", "series-outline.v1", payloads)
        types = [b["type"] for b in view["blocks"]]
        self.assertIn("outline_overview", types)
        self.assertIn("stage_outlines", types)
        overview = next(b for b in view["blocks"] if b["type"] == "outline_overview")
        self.assertEqual(overview["total_episodes"], "30")

    def test_character_bible_localizes_role_type(self):
        payload = {
            "characters": [
                {
                    "name": "苏晴",
                    "role_type": "main_antagonist",
                    "surface_desire": "夺回控制权",
                    "voice_tag": {"tone": "尖细", "speed": "fast"},
                }
            ]
        }
        view = present_artifact("character_bible", "character-bible.v1", payload)
        corpus = str(view["blocks"])
        self.assertIn("核心反派", corpus)
        self.assertNotIn("main_antagonist", corpus)
        roster = next(b for b in view["blocks"] if b["type"] == "character_roster")
        self.assertTrue(roster["characters"][0]["rows"])

    def test_relationship_type_english_phrase_localized(self):
        payload = {
            "characters": [{"name": "苏晴", "character_id": "C001"}],
            "relationship_network": [
                {
                    "source_id": "C001",
                    "target_id": "C002",
                    "relationship_type": "former daughter-in-law / arch-enemy",
                    "interaction_rule": "前期对立",
                }
            ],
        }
        view = present_artifact("character_bible", "character-bible.v1", payload)
        rel = next(b for b in view["blocks"] if b["type"] == "relationship_graph")
        self.assertIn("前儿媳", rel["items"][0]["subtitle"])
        item = rel["items"][0]
        self.assertEqual(item["source_name"], "苏晴")
        self.assertEqual(item["target_name"], "C002")
        self.assertEqual(item["interaction_rule"], "前期对立")

    def test_world_setting_canonical_payload(self):
        payload = {
            "era_background": "2026年沪城",
            "power_structure": ["目前掌握权力者：顶层创投决策层"],
            "core_spaces": ["竖屏近景适配的豪门宴会厅"],
            "core_world_rules": ["规则一"],
        }
        view = present_artifact("world_setting", "world-setting.v1", payload)
        types = {b["type"] for b in view["blocks"]}
        self.assertIn("hero", types)
        self.assertIn("cards", types)
        corpus = str(view["blocks"])
        self.assertIn("目前掌握权力者", corpus)
        self.assertIn("竖屏近景", corpus)

    def test_emotion_audit_payload(self):
        payload = {
            "over_deviation_episodes": [
                {
                    "episodeNumber": 3,
                    "deviation_nodes": [
                        {
                            "node_index": 1,
                            "emotion_tag": "EV",
                            "actual_value": 8,
                            "target_value": 6,
                            "deviation_gap": 2,
                            "trigger_event": "反转揭晓",
                        }
                    ],
                }
            ]
        }
        view = present_artifact("emotion_audit", "emotion-audit.v1", payload)
        dev_block = next(b for b in view["blocks"] if b.get("title") == "偏离集数")
        body_text = dev_block["items"][0]["body"]
        self.assertIn("节点", body_text)
        self.assertIn("实际", body_text)
