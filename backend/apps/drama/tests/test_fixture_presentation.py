# -*- coding: utf-8 -*-
"""基于 fixtures/presentation 真实 JSON 的 presenter 回归测试。"""
from __future__ import annotations

import json
import re
from pathlib import Path

from django.test import SimpleTestCase

from apps.drama.presentation.presenters import present_artifact

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "scripts" / "fixtures" / "presentation"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"

# 各 schema 期望至少出现的 block 类型（fixture 真实形态）
EXPECTED_BLOCK_TYPES: dict[str, set[str]] = {
    "series-outline.v1": {"outline_overview", "stage_outlines"},
    "episode-scripts.v1": {"script_episodes"},
    "review-report.v1": {"review_overview"},
    "quality-report.v1": {"quality_report"},
    "compliance-report.v1": {"compliance_report"},
    "character-bible.v1": {"character_roster", "relationship_graph"},
    "world-setting.v1": {"world_sections"},
    "project-review.v1": {"assessment_report"},
    "dream-check.v1": {"assessment_report"},
    "style-check.v1": {"assessment_report"},
    "hook-plan.v1": {"plan_overview", "plan_items"},
    "conflict-plan.v1": {"plan_overview", "plan_items"},
    "reversal-plan.v1": {"plan_items"},
    "emotion-curve.v1": {"plan_overview", "plan_items"},
    "emotion-blueprint.v1": {"metrics", "episode_metrics_list"},
    "emotion-audit.v1": {"cards", "episode_metrics_list"},
    "word-count-report.v1": {"kv", "episode_metrics_list"},
    "marketing-kit.v1": {"deliverable_sections"},
    "delivery-pack.v1": {"deliverable_sections"},
    "market-analysis.v1": {"metrics"},
    "formula-analysis.v1": {"metrics"},
    "project-brief.v1": {"hero"},
}


class FixturePresentationTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not MANIFEST_PATH.exists():
            cls.entries = []
            return
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.entries = manifest.get("entries") or []

    def _load_fixture(self, schema_version: str) -> dict:
        path = FIXTURE_DIR / f"{schema_version}.json"
        self.assertTrue(path.exists(), msg=f"fixture missing: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_all_fixtures_have_manifest_entry(self):
        files = sorted(p.stem for p in FIXTURE_DIR.glob("*.v1.json"))
        manifest_schemas = {e["schema_version"] for e in self.entries}
        self.assertEqual(len(files), 31)
        self.assertEqual(len(manifest_schemas), 31)
        for schema in files:
            self.assertIn(schema, manifest_schemas)

    def test_all_fixtures_produce_blocks(self):
        for entry in self.entries:
            schema = entry["schema_version"]
            artifact_key = entry["artifact_key"]
            payload = self._load_fixture(schema)
            view = present_artifact(artifact_key, schema, payload)
            self.assertTrue(view["blocks"], msg=f"{schema} blocks empty")

    def test_expected_block_types_per_schema(self):
        for schema, expected in EXPECTED_BLOCK_TYPES.items():
            entry = next(e for e in self.entries if e["schema_version"] == schema)
            payload = self._load_fixture(schema)
            view = present_artifact(entry["artifact_key"], schema, payload)
            block_types = {b["type"] for b in view["blocks"]}
            missing = expected - block_types
            self.assertFalse(missing, msg=f"{schema} missing block types: {missing}")

    def test_no_snake_case_title_leak_in_fixtures(self):
        snake_re = re.compile(r"^[a-z][a-z0-9_]*$")
        for entry in self.entries:
            schema = entry["schema_version"]
            payload = self._load_fixture(schema)
            view = present_artifact(entry["artifact_key"], schema, payload)

            def walk_titles(obj, path=""):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if k in ("title", "label", "key") and isinstance(v, str) and snake_re.match(v):
                            if v not in ("kv",):
                                yield f"{schema}:{path}.{k}={v}"
                        yield from walk_titles(v, f"{path}.{k}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        yield from walk_titles(item, f"{path}[{i}]")

            leaks = list(walk_titles(view))
            self.assertFalse(leaks, msg=f"snake_case leak: {leaks[:3]}")

    def test_series_outline_real_shape(self):
        payload = self._load_fixture("series-outline.v1")
        view = present_artifact("series_outline", "series-outline.v1", payload)
        overview = next(b for b in view["blocks"] if b["type"] == "outline_overview")
        self.assertIsNotNone(overview.get("total_episodes"))
        staged = next(b for b in view["blocks"] if b["type"] == "stage_outlines")
        self.assertTrue(staged.get("stages"))

    def test_episode_scripts_script_content(self):
        payload = self._load_fixture("episode-scripts.v1")
        view = present_artifact("episode_scripts", "episode-scripts.v1", payload)
        block = next(b for b in view["blocks"] if b["type"] == "script_episodes")
        self.assertTrue(block["episodes"])
        first = block["episodes"][0]
        self.assertIn("beats", first)

    def test_character_bible_roster_and_graph(self):
        payload = self._load_fixture("character-bible.v1")
        view = present_artifact("character_bible", "character-bible.v1", payload)
        roster = next(b for b in view["blocks"] if b["type"] == "character_roster")
        rel = next(b for b in view["blocks"] if b["type"] == "relationship_graph")
        self.assertGreaterEqual(len(roster["characters"]), 1)
        self.assertTrue(any("↔" in item["title"] for item in rel["items"]))

    def test_emotion_audit_nested_audit_result(self):
        payload = self._load_fixture("emotion-audit.v1")
        view = present_artifact("emotion_audit", "emotion-audit.v1", payload)
        self.assertTrue(any(b["type"] == "episode_metrics_list" for b in view["blocks"]))

    def test_project_brief_project_content(self):
        payload = self._load_fixture("project-brief.v1")
        view = present_artifact("project_brief", "project-brief.v1", payload)
        self.assertEqual(view["blocks"][0]["type"], "hero")

    def test_no_field_alias_chains_in_presenters(self):
        import ast
        from pathlib import Path

        source = Path("apps/drama/presentation/schema_presenters.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        violations: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.BoolOp) or not isinstance(node.op, ast.Or):
                continue
            for value in node.values:
                if (
                    isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Attribute)
                    and value.func.attr == "get"
                    and isinstance(value.func.value, ast.Call)
                    and isinstance(value.func.value.func, ast.Attribute)
                    and value.func.value.func.attr == "get"
                ):
                    violations.append(ast.get_source_segment(source, node) or "or-get chain")
        self.assertFalse(violations, msg=f"field alias chains: {violations[:5]}")

    def test_market_analysis_data_wrapper(self):
        payload = self._load_fixture("market-analysis.v1")
        view = present_artifact("market_analysis", "market-analysis.v1", payload)
        self.assertIn("metrics", {b["type"] for b in view["blocks"]})
