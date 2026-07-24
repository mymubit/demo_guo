# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.core.exceptions import SCHEMA_VALIDATION_FAILED, BusinessException
from apps.drama.services.artifact_ingest import ingest_llm_artifact
from apps.drama.services.substance_gates import registered_gate_keys, run_substance_gate


class SubstanceGatesTests(SimpleTestCase):
    def test_quality_and_compliance_gates_registered(self) -> None:
        keys = registered_gate_keys()
        self.assertIn("quality_report", keys)
        self.assertIn("compliance_report", keys)
        self.assertIn("project_brief", keys)

    def test_unknown_artifact_is_noop(self) -> None:
        run_substance_gate("unknown_artifact_xyz", {"title": "x"})

    def test_thin_project_brief_raises(self) -> None:
        with self.assertRaises(BusinessException) as ctx:
            run_substance_gate(
                "project_brief",
                {
                    "title": "归园田居",
                    "competitor_references": [{"title": "竞品1"}],
                    "differentiation_strategy": "质量更好",
                    "first_episode_hook": "婚礼现场反击",
                },
            )
        self.assertEqual(ctx.exception.code, SCHEMA_VALIDATION_FAILED)

    def test_empty_quality_dimensions_raises(self) -> None:
        with self.assertRaises(BusinessException) as ctx:
            run_substance_gate(
                "quality_report",
                {"drama_title": "t", "overall_score": 80, "dimensions": {}},
            )
        self.assertEqual(ctx.exception.code, SCHEMA_VALIDATION_FAILED)


class ArtifactIngestTests(SimpleTestCase):
    def test_ingest_rejects_non_json(self) -> None:
        with self.assertRaises(Exception):
            ingest_llm_artifact(
                content="not json at all",
                artifact_key="project_brief",
                settings={"title": "demo"},
                schema_path="schemas/artifacts/project_brief/1.schema.json",
            )

    def test_ingest_sparse_quality_fails_substance_gate(self) -> None:
        # Schema 允许短 evidence；substance 门禁仍拒绝空壳/过短分析
        content = """
        {
          "drama_title": "demo",
          "scored_artifact": "latest_script",
          "resolved_script_key": "external_script",
          "scoring_preset": "standard",
          "pass_threshold": 75,
          "overall_score": 80,
          "grade": "A",
          "can_continue_next_batch": true,
          "needs_revision": false,
          "verdict": "通过",
          "verdict_detail": "too short",
          "dimensions": {
            "format": {"score": 80, "evidence": ["ep1 format ok"], "deductions": []},
            "narrative": {"score": 80, "evidence": ["ep1 narrative"], "deductions": []},
            "conflict": {"score": 80, "evidence": ["ep1 conflict"], "deductions": []},
            "character": {"score": 80, "evidence": ["ep1 character"], "deductions": []},
            "emotion": {"score": 80, "evidence": ["ep1 emotion"], "deductions": []},
            "logic": {"score": 80, "evidence": ["ep1 logic ok"], "deductions": []},
            "satisfaction": {"score": 80, "evidence": ["ep1 satisfy"], "deductions": []},
            "hooks": {"score": 80, "evidence": ["ep1 hooks ok"], "deductions": []},
            "paywall": {"score": 80, "evidence": ["ep1 paywall"], "deductions": []},
            "genre_fit": {"score": 80, "evidence": ["ep1 genre ok"], "deductions": []}
          },
          "defects": [],
          "continuity_summary": {"result": "pass", "issues": []},
          "revision_priorities": []
        }
        """
        with self.assertRaises(BusinessException) as ctx:
            ingest_llm_artifact(
                content=content,
                artifact_key="quality_report",
                settings={},
                schema_path="schemas/artifacts/quality_report/1.schema.json",
            )
        self.assertEqual(ctx.exception.code, SCHEMA_VALIDATION_FAILED)
        msg = str(ctx.exception)
        self.assertTrue(
            "evidence" in msg or "空壳" in msg or "总评" in msg or "篇幅" in msg,
            msg,
        )
