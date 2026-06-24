# -*- coding: utf-8 -*-
"""Drama Services 单元测试 - DramaWordCountService / DramaQualityService"""
from django.test import TestCase

from apps.drama.services import DramaQualityService, DramaWordCountService


class DramaWordCountServiceTests(TestCase):
    """字数校验服务测试"""

    def test_clean_non_script_removes_code_blocks(self):
        content = "正常内容\n```python\nprint('test')\n```\n更多内容"
        cleaned = DramaWordCountService.clean_non_script(content)
        self.assertNotIn("print('test')", cleaned)
        self.assertIn("正常内容", cleaned)
        self.assertIn("更多内容", cleaned)

    def test_clean_non_script_removes_html_comments(self):
        content = "正文<!-- 这是注释 -->继续"
        cleaned = DramaWordCountService.clean_non_script(content)
        self.assertNotIn("这是注释", cleaned)
        self.assertIn("正文", cleaned)
        self.assertIn("继续", cleaned)

    def test_count_cjk_counts_chinese_chars(self):
        text = "你好World123"
        count = DramaWordCountService.count_cjk(text)
        self.assertEqual(count, 2)

    def test_count_cjk_empty_string(self):
        self.assertEqual(DramaWordCountService.count_cjk(""), 0)

    def test_count_dialogue_cjk_matches_pattern(self):
        text = "张三（室内）：你好，最近怎么样？\n李四：我很好。"
        count = DramaWordCountService.count_dialogue_cjk(text)
        self.assertGreater(count, 0)

    def test_count_scenes_matches_scene_heads(self):
        text = "1-1 日 内 客厅\n一些内容\n1-2 夜 外 街道\n更多内容"
        count = DramaWordCountService.count_scenes(text)
        self.assertEqual(count, 2)

    def test_validate_episode_first_episode_normal(self):
        content = "1-1 日 内 客厅\n张三（室内）：" + "你好" * 200 + "\n李四：" + "我也好" * 200
        result = DramaWordCountService.validate_episode(content, 1)
        self.assertEqual(result["episode"], 1)
        self.assertIn("word_count", result)
        self.assertIn("dialogue_ratio", result)
        self.assertIn("scene_count", result)
        self.assertIn("overall", result)
        self.assertIn("recommendations", result)

    def test_validate_episode_other_episode_word_overflow(self):
        content = "1-1 日 内 客厅\n" + "你好" * 500
        result = DramaWordCountService.validate_episode(content, 5)
        self.assertEqual(result["episode"], 5)
        wc_status = result["word_count"]["status"]
        self.assertIsInstance(wc_status, str)
        self.assertGreater(len(wc_status), 0)

    def test_validate_episode_empty_content(self):
        result = DramaWordCountService.validate_episode("", 1)
        self.assertEqual(result["word_count"]["total"], 0)
        self.assertIn("recommendations", result)

    def test_validate_episode_scene_count_too_high(self):
        scenes = "\n".join([f"{i}-1 日 内 场景{i}" for i in range(1, 6)])
        content = scenes + "\n张三：你好" * 100
        result = DramaWordCountService.validate_episode(content, 1)
        sc_status = result["scene_count"]["status"]
        self.assertIsInstance(sc_status, str)


class DramaQualityServiceTests(TestCase):
    """质量评估服务测试"""

    def test_dimensions_have_expected_structure(self):
        dims = DramaQualityService.DIMENSIONS
        self.assertGreater(len(dims), 0)
        for dim in dims:
            self.assertIn("key", dim)
            self.assertIn("name", dim)
            self.assertIn("weight", dim)
            self.assertIn("desc", dim)

    def test_dimensions_weights_sum_close_to_one(self):
        total = sum(d["weight"] for d in DramaQualityService.DIMENSIONS)
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_build_detailed_quality_report_all_good(self):
        scores = {d["key"]: 95 for d in DramaQualityService.DIMENSIONS}
        report = DramaQualityService.build_detailed_quality_report(scores, 1)
        self.assertEqual(report["episode_number"], 1)
        self.assertGreaterEqual(report["overall_score"], 90)
        self.assertEqual(report["grade"], "S")
        self.assertIn("dimensions", report)
        self.assertEqual(len(report["dimensions"]), len(DramaQualityService.DIMENSIONS))
        self.assertIn("all_issues", report)
        self.assertIn("top_suggestions", report)
        self.assertIn("grade_desc", report)
        self.assertGreater(len(report["grade_desc"]), 0)

    def test_build_detailed_quality_report_low_scores(self):
        scores = {d["key"]: 50 for d in DramaQualityService.DIMENSIONS}
        report = DramaQualityService.build_detailed_quality_report(scores, 3)
        self.assertEqual(report["episode_number"], 3)
        self.assertLess(report["overall_score"], 70)
        self.assertEqual(report["grade"], "D")
        self.assertGreater(report["error_count"], 0)
        self.assertGreater(len(report["all_issues"]), 0)

    def test_build_detailed_quality_report_grade_boundaries(self):
        for score, expected_grade in [(95, "S"), (85, "A"), (77, "B"), (65, "C"), (50, "D")]:
            scores = {d["key"]: score for d in DramaQualityService.DIMENSIONS}
            report = DramaQualityService.build_detailed_quality_report(scores)
            self.assertEqual(report["grade"], expected_grade, f"分数 {score} 应对应等级 {expected_grade}")

    def test_build_detailed_quality_report_with_word_count(self):
        scores = {d["key"]: 80 for d in DramaQualityService.DIMENSIONS}
        word_count_result = {
            "episode": 1,
            "word_count": {"total": 1000, "status": "正常", "deviation": 0},
            "dialogue_ratio": {"ratio": "30%", "status": "正常"},
            "scene_count": {"count": 2, "status": "正常"},
        }
        report = DramaQualityService.build_detailed_quality_report(scores, 1, word_count_result)
        self.assertIsNotNone(report["word_count_info"])
        self.assertEqual(report["word_count_info"]["episode"], 1)
        self.assertEqual(report["word_count_info"]["total_words"], 1000)

    def test_build_detailed_quality_report_overall_from_weights(self):
        scores = {d["key"]: 80 for d in DramaQualityService.DIMENSIONS}
        report = DramaQualityService.build_detailed_quality_report(scores)
        self.assertAlmostEqual(report["overall_score"], 80.0, delta=0.1)

    def test_build_detailed_quality_report_explicit_overall(self):
        scores = {d["key"]: 80 for d in DramaQualityService.DIMENSIONS}
        scores["overall"] = 92
        report = DramaQualityService.build_detailed_quality_report(scores)
        self.assertEqual(report["overall_score"], 92.0)

    def test_dim_name_returns_correct_name(self):
        for dim in DramaQualityService.DIMENSIONS:
            name = DramaQualityService._dim_name(dim["key"])
            self.assertEqual(name, dim["name"])

    def test_dim_name_unknown_key_returns_key(self):
        self.assertEqual(DramaQualityService._dim_name("unknown_key"), "unknown_key")

    def test_build_dim_summary_high_score(self):
        summary = DramaQualityService._build_dim_summary("剧情", 95, [])
        self.assertIn("剧情", summary)
        self.assertGreater(len(summary), 2)

    def test_build_dim_summary_with_errors(self):
        issues = [
            {"id": "e1", "severity": "error", "desc": "错误1"},
            {"id": "w1", "severity": "warning", "desc": "警告1"},
        ]
        summary = DramaQualityService._build_dim_summary("人物", 65, issues)
        self.assertIn("人物", summary)
        self.assertGreater(len(summary), 2)

    def test_grade_desc_all_grades(self):
        for grade in ["S", "A", "B", "C", "D"]:
            desc = DramaQualityService._grade_desc(grade)
            self.assertGreater(len(desc), 0)

    def test_grade_desc_invalid_grade(self):
        self.assertEqual(DramaQualityService._grade_desc("X"), "")

    def test_detect_issues_from_score_high_score_no_issues(self):
        issues = DramaQualityService._detect_issues_from_score("character", 95)
        self.assertEqual(len(issues), 0)

    def test_detect_issues_from_score_zero_score(self):
        issues = DramaQualityService._detect_issues_from_score("hooks", 0)
        self.assertEqual(len(issues), 0)

    def test_detect_issues_from_score_low_score_has_issues(self):
        issues = DramaQualityService._detect_issues_from_score("hooks", 50)
        self.assertGreater(len(issues), 0)
        for issue in issues:
            self.assertIn("severity", issue)
            self.assertIn("desc", issue)
            self.assertIn("suggestion", issue)

    def test_build_series_quality_summary_empty(self):
        result = DramaQualityService.build_series_quality_summary([])
        self.assertEqual(result["total_episodes"], 0)
        self.assertEqual(result["evaluated_episodes"], 0)

    def test_build_series_quality_summary_with_data(self):
        episodes = [
            {"episode_number": 1, "scores": {d["key"]: 85 for d in DramaQualityService.DIMENSIONS}},
            {"episode_number": 2, "scores": {d["key"]: 70 for d in DramaQualityService.DIMENSIONS}},
        ]
        result = DramaQualityService.build_series_quality_summary(episodes)
        self.assertEqual(result["total_episodes"], 2)
        self.assertIn("series_overall_score", result)
        self.assertIn("series_grade", result)
        self.assertIn("avg_by_dimension", result)
        self.assertIn("episode_summaries", result)
        self.assertEqual(len(result["episode_summaries"]), 2)
        self.assertGreaterEqual(result["weak_count"], 0)
