# -*- coding: utf-8 -*-
"""quality_report.revision_route 分流。"""
from __future__ import annotations

from django.test import SimpleTestCase

from apps.drama.services.artifact_normalize import (
    normalize_quality_report,
    resolve_revision_route,
)


def _dims(**scores: float) -> dict:
    base = {
        "format": 80,
        "narrative": 80,
        "conflict": 80,
        "character": 80,
        "emotion": 80,
        "logic": 80,
        "satisfaction": 80,
        "hooks": 80,
        "paywall": 80,
        "genre_fit": 80,
    }
    base.update(scores)
    return {k: {"score": v, "analysis": "x" * 120} for k, v in base.items()}


class RevisionRouteTests(SimpleTestCase):
    def test_pass_when_not_needs_revision(self) -> None:
        self.assertEqual(
            resolve_revision_route(
                needs_revision=False,
                dimensions=_dims(),
                pass_threshold=75,
            ),
            "pass",
        )

    def test_rewrite_when_structure_dims_dominate(self) -> None:
        route = resolve_revision_route(
            needs_revision=True,
            dimensions=_dims(narrative=40, conflict=40, hooks=40, format=80),
            pass_threshold=75,
        )
        self.assertEqual(route, "rewrite_batch")

    def test_polish_when_format_dominates(self) -> None:
        route = resolve_revision_route(
            needs_revision=True,
            dimensions=_dims(format=40, emotion=50, narrative=80),
            pass_threshold=75,
        )
        self.assertEqual(route, "text_polish")

    def test_normalize_writes_revision_route(self) -> None:
        out = normalize_quality_report(
            {
                "drama_title": "t",
                "overall_score": 50,
                "needs_revision": True,
                "verdict": "需要修改",
                "dimensions": _dims(narrative=30, conflict=30, hooks=30),
                "defects": [],
                "continuity_summary": {"result": "pass", "issues": []},
                "revision_priorities": [],
            },
            {"title": "t"},
        )
        self.assertEqual(out["revision_route"], "rewrite_batch")
        self.assertNotEqual(out["revision_route"], "text_polish")
