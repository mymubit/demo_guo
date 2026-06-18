# -*- coding: utf-8 -*-
from django.test import SimpleTestCase, TestCase

from apps.creation.episode_gate import summarize_episode_gates
from apps.workflow.fusion import evaluate_project_readiness, get_artifact_registry
from apps.workflow.pipeline_store import FusionPipelineDbService


class EpisodeGateSummaryTests(SimpleTestCase):
    def test_empty_episodes(self):
        s = summarize_episode_gates({"episodes": []})
        self.assertEqual(s["total"], 0)
        self.assertEqual(s["passed"], 0)

    def test_all_passed(self):
        eps = [
            {"episodeNumber": 1, "gateLog": {"passed": True}},
            {"episodeNumber": 2, "gateLog": {"passed": True}},
        ]
        s = summarize_episode_gates({"episodes": eps})
        self.assertEqual(s["total"], 2)
        self.assertEqual(s["passed"], 2)
        self.assertEqual(s["failed"], 0)

    def test_partial_failed(self):
        eps = [
            {"episodeNumber": 1, "gateLog": {"passed": True}},
            {"episodeNumber": 2, "gateLog": {"passed": False, "issues": ["字数不足"]}},
        ]
        s = summarize_episode_gates({"episodes": eps})
        self.assertEqual(s["passed"], 1)
        self.assertEqual(len(s["failedEpisodes"]), 1)

    def test_missing_gate_log_counts_as_not_passed(self):
        eps = [{"episodeNumber": 1}, {"episodeNumber": 2, "gateLog": {"passed": True}}]
        s = summarize_episode_gates({"episodes": eps})
        self.assertEqual(s["passed"], 1)


class ReadinessTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from apps.skill.config.portal.review_scoring import ReviewScoringService

        ReviewScoringService.import_thresholds_from_disk()
    def test_ready_when_all_checks_pass(self):
        r = evaluate_project_readiness(
            project_brief_confirmed=True,
            has_structure=True,
            has_characters=True,
            has_outline=True,
            all_episodes_gate_passed=True,
            quality_final_verdict="pass",
            score_report={"overallScore": 90, "eightDimensionScores": {}},
            compliance_fuse=False,
        )
        self.assertTrue(r["ready"])
        self.assertEqual(r["status"], "ready")

    def test_blocked_on_compliance_fuse(self):
        r = evaluate_project_readiness(
            project_brief_confirmed=True,
            has_structure=True,
            has_characters=True,
            has_outline=True,
            all_episodes_gate_passed=True,
            quality_final_verdict="pass",
            score_report={"overallScore": 90},
            compliance_fuse=True,
        )
        self.assertFalse(r["ready"])
        self.assertEqual(r["status"], "blocked")

    def test_not_ready_when_episode_gates_incomplete(self):
        r = evaluate_project_readiness(
            project_brief_confirmed=True,
            has_structure=True,
            has_characters=True,
            has_outline=True,
            all_episodes_gate_passed=False,
            quality_final_verdict="pass",
            score_report={"overallScore": 90},
        )
        self.assertFalse(r["ready"])

    def test_score_below_release_line(self):
        r = evaluate_project_readiness(
            project_brief_confirmed=True,
            has_structure=True,
            has_characters=True,
            has_outline=True,
            all_episodes_gate_passed=True,
            quality_final_verdict="pass",
            score_report={"overallScore": 50},
        )
        self.assertFalse(r["ready"])


class ArtifactRegistryTests(TestCase):
    def setUp(self):
        FusionPipelineDbService.ensure_builtin_default_pack()
        FusionPipelineDbService.clear_caches()

    def tearDown(self):
        FusionPipelineDbService.clear_caches()

    def test_main_chain_has_five_steps(self):
        reg = get_artifact_registry()
        self.assertEqual(reg.total_main_nodes(), 5)
        self.assertEqual(reg.artifact_key_for_index(1), "project_brief")
        self.assertEqual(reg.artifact_key_for_index(5), "episode_scripts")

    def test_progress_percent_uses_total_nodes(self):
        reg = get_artifact_registry()
        self.assertEqual(reg.progress_percent_for_node(5), 100)
        self.assertLess(reg.progress_percent_for_node(3, awaiting=True), 99)
