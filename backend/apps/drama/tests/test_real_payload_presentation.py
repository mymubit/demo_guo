# -*- coding: utf-8 -*-
"""基于 E2E 真实 payload 快照的 presenter 回归测试。"""
from __future__ import annotations

import json
from pathlib import Path

from django.test import SimpleTestCase

from apps.drama.defaults import DRAMA_ROLE_DEFAULTS
from apps.drama.presentation.presenters import present_artifact

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "scripts"
ARTIFACT_SCHEMA = {
    role["default_output_artifact_key"]: role["output_contract"]["schema_version"]
    for role in DRAMA_ROLE_DEFAULTS
    if role.get("default_output_artifact_key") and (role.get("output_contract") or {}).get("schema_version")
}


class RealPayloadPresentationTests(SimpleTestCase):
    def _load_fixture(self, name: str) -> dict:
        path = FIXTURE_DIR / name
        if not path.exists():
            self.skipTest(f"fixture missing: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _assert_project_payloads(self, fixture_name: str) -> None:
        payloads = self._load_fixture(fixture_name)
        for artifact_key, payload in payloads.items():
            schema = ARTIFACT_SCHEMA.get(artifact_key)
            self.assertIsNotNone(schema, msg=f"unknown artifact_key: {artifact_key}")
            view = present_artifact(artifact_key, schema, payload)
            self.assertTrue(view["blocks"], msg=f"{artifact_key} blocks empty")
            block_types = {b["type"] for b in view["blocks"]}
            self.assertNotEqual(block_types, {"kv"}, msg=f"{artifact_key} only generic kv")

    def test_expert_real_payloads(self):
        self._assert_project_payloads("e2e_payloads_e2e_drama_expert.json")

    def test_fast_real_payloads(self):
        self._assert_project_payloads("e2e_payloads_e2e_drama_fast.json")

    def test_visual_prompts_episode_structure(self):
        payloads = self._load_fixture("e2e_payloads_e2e_drama_expert.json")
        view = present_artifact("visual_prompts", "visual-prompts.v1", payloads["visual_prompts"])
        types = [b["type"] for b in view["blocks"]]
        self.assertIn("cards", types)
        self.assertTrue(any("第" in b.get("title", "") for b in view["blocks"] if b["type"] == "cards"))

    def test_marketing_kit_synopses_dict(self):
        payloads = self._load_fixture("e2e_payloads_e2e_drama_expert.json")
        view = present_artifact("marketing_kit", "marketing-kit.v1", payloads["marketing_kit"])
        kv_titles = [b["title"] for b in view["blocks"] if b["type"] == "kv"]
        self.assertIn("剧情简介", kv_titles)
        self.assertIn("付费文案", kv_titles)

    def test_psychology_guide_labels_are_chinese(self):
        payloads = self._load_fixture("e2e_payloads_e2e_drama_expert.json")
        view = present_artifact("psychology_guide", "psychology-guide.v1", payloads["psychology_guide"])
        import re

        for block in view["blocks"]:
            if block["type"] != "kv":
                continue
            self.assertNotRegex(block["title"], r"^[a-zA-Z_\s]+$")
            for row in block["rows"]:
                self.assertNotRegex(row["key"], r"^[a-zA-Z_\s]+$")

    def test_no_episode_english_or_raw_dict_in_expert_outputs(self):
        import re

        payloads = self._load_fixture("e2e_payloads_e2e_drama_expert.json")
        episode_re = re.compile(r"\bEpisode\s+\d+", re.I)
        raw_dict_re = re.compile(r"^\s*\{'[a-zA-Z_]+'")
        for artifact_key, payload in payloads.items():
            schema = ARTIFACT_SCHEMA[artifact_key]
            view = present_artifact(artifact_key, schema, payload)

            def walk_strings(obj):
                if isinstance(obj, str):
                    yield obj
                elif isinstance(obj, dict):
                    for v in obj.values():
                        yield from walk_strings(v)
                elif isinstance(obj, list):
                    for v in obj:
                        yield from walk_strings(v)

            for text in walk_strings(view):
                self.assertFalse(episode_re.search(text), msg=f"{artifact_key} 含 Episode 英文: {text[:80]}")
                if raw_dict_re.match(text):
                    self.fail(f"{artifact_key} 含裸 dict 展示: {text[:120]}")

    def test_formula_paid_card_episode_label_chinese(self):
        payloads = self._load_fixture("e2e_payloads_e2e_drama_expert.json")
        view = present_artifact("formula_analysis", "formula-analysis.v1", payloads["formula_analysis"])
        paid = next(b for b in view["blocks"] if b.get("title") == "付费卡点设计")
        self.assertTrue(paid["items"][0]["title"].startswith("第1集"))
        self.assertNotIn("Episode", paid["items"][0]["title"])

    def test_emotion_audit_deviation_not_raw_dict(self):
        payloads = self._load_fixture("e2e_payloads_e2e_drama_expert.json")
        view = present_artifact("emotion_audit", "emotion-audit.v1", payloads["emotion_audit"])
        dev_block = next(b for b in view["blocks"] if b.get("title") == "偏离集数")
        body_text = dev_block["items"][0]["body"]
        self.assertIn("节点", body_text)
        self.assertIn("实际", body_text)
        self.assertNotIn("{", body_text)
        self.assertNotIn("node_index", body_text)

    def test_post_assets_dubbing_timeline_readable(self):
        payloads = self._load_fixture("e2e_payloads_e2e_drama_expert.json")
        view = present_artifact("post_assets", "post-assets.v1", payloads["post_assets"])
        dub = next(b for b in view["blocks"] if b.get("title") == "配音情绪脚本")
        body = dub["items"][0]["body"]
        self.assertIn("情绪", body)
        self.assertNotIn("{'volume'", body)

    def test_fast_character_bible_relationship_pair(self):
        payloads = self._load_fixture("e2e_payloads_e2e_drama_fast.json")
        view = present_artifact("character_bible", "character-bible.v1", payloads["character_bible"])
        rel_block = next(b for b in view["blocks"] if b["type"] == "cards" and b["title"] == "关系网络")
        self.assertTrue(any("↔" in item["title"] or item.get("body") for item in rel_block["items"]))
