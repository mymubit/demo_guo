# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.workflow.fusion.upstream_context import (
    dedupe_upstream_aliases,
    pick_upstream_for_sub_skill,
    summarize_upstream_for_trace,
)


class UpstreamContextTests(SimpleTestCase):
    def test_dedupe_aliases(self):
        brief = {"theme": "x"}
        upstream = {
            "projectBrief": brief,
            "project_brief": brief,
            "structurePlan": {"totalEpisodes": 80},
            "structure_plan": {"totalEpisodes": 80},
            "theme": "x",
        }
        out = dedupe_upstream_aliases(upstream)
        self.assertIn("projectBrief", out)
        self.assertNotIn("project_brief", out)
        self.assertIn("structurePlan", out)
        self.assertNotIn("structure_plan", out)

    def test_pick_upstream_for_structure_generator(self):
        upstream = {
            "projectBrief": {"theme": "a"},
            "structurePlan": {"totalEpisodes": 80},
            "characterBible": {"characters": []},
            "theme": "a",
            "episodeCount": 80,
        }
        picked = pick_upstream_for_sub_skill(upstream, "structure-generator", {})
        self.assertIn("projectBrief", picked)
        self.assertNotIn("structurePlan", picked)
        self.assertNotIn("characterBible", picked)

    def test_summarize_upstream_for_trace(self):
        upstream = {
            "nodeId": "node-2-structure",
            "theme": "trace",
            "projectBrief": {"workingTitle": "t", "theme": "trace", "episodeCount": 10},
            "structurePlan": {"totalEpisodes": 10, "worldview": {"rootRules": ["a"]}},
        }
        summary = summarize_upstream_for_trace(upstream, extra={"sub_skill_id": "world-builder"})
        self.assertEqual(summary["theme"], "trace")
        self.assertIn("projectBrief", summary)
        self.assertIn("structurePlan", summary)
        self.assertNotIn("worldview", summary.get("structurePlan", {}))
