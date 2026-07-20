# -*- coding: utf-8 -*-
"""产物 normalize 合成补全测试（零兼容：不做别名/形状改写）。"""
from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from apps.core.schema_validator import SchemaValidator
from apps.drama.services.artifact_normalize import (
    normalize_compliance_report,
    normalize_narrative_plan,
    normalize_project_brief,
    normalize_quality_report,
    normalize_story_bible,
    quality_report_evidence_too_sparse,
)
from apps.drama.tests.helpers import FIXTURES, SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class ProjectBriefNormalizeTests(SimpleTestCase):
    def setUp(self) -> None:
        self.validator = SchemaValidator()
        self.settings = {
            "title": "test1",
            "core_idea": "弃女入宫操盘朝局",
            "episode_count": 40,
            "audience_channel": "female",
            "protagonist_structure": "single-female",
            "flavor_tags": ["palace"],
            "genre_matrix": {
                "emotion": "ambition",
                "identity": "hidden-elite",
                "conflict": "power",
                "world": "ancient",
            },
            "derived": {
                "matrix_key": "ambition-hidden-elite-power-ancient|ch:female|ps:single-female|palace",
                "rule_params_ref": "project_brief.rule_params",
            },
            "preset_theme_code": None,
        }

    def test_fills_structural_fields_from_settings(self) -> None:
        raw = {
            "core_idea": "以弃女身份建立权力基本盘",
            "core_conflict": "生存渴望 vs 阶层壁垒",
            "hook_concept": "棋子入局却执棋",
            "target_audience": "女频权谋观众",
            "audience_channel": "female",
            "genre_matrix": {
                "world": "ancient",
                "emotion": "ambition",
                "conflict": "power",
                "identity": "hidden-elite",
            },
            "rule_params": {
                "reversal_density": "high",
                "emotion_curve": {"nodes": 8},
                "act_ratio": {"act1": 0.1},
                "hook_types": ["suspense"],
            },
            "blockbuster_factors": ["身份反转"],
            "compliance_risk": "medium",
            "market_opportunity": "女频权谋热度高",
            "differentiation_strategy": "不靠恩宠靠情报网",
            "first_episode_hook": "送亲遇刺",
            "paywall_direction": "打脸前夜",
            "artifact_key": "project_brief",
            "schema_version": 1,
        }
        out = normalize_project_brief(raw, self.settings)
        self.assertEqual(out["title"], "test1")
        self.assertEqual(out["theme_code"], "matrix")
        self.assertEqual(out["episode_count"], 40)
        self.assertEqual(out["compliance_risk"], "medium")
        self.assertEqual(out["genre_matrix"]["audience_channel"], "female")
        self.assertEqual(out["genre_matrix"]["protagonist_structure"], "single-female")
        self.assertEqual(out["blockbuster_factors"], ["身份反转"])
        self.assertIsInstance(out["rule_params"]["reversal_density"], float)
        self.assertEqual(len(out["rule_params"]["emotion_curve"]), 8)
        self.assertEqual(len(out["rule_params"]["act_ratio"]), 6)
        self.assertNotIn("artifact_key", out)
        self.assertNotIn("sensitivity_pre_check", out)
        self.validator.validate_file(
            out, "schemas/artifacts/project_brief/1.schema.json"
        )

    def test_does_not_rewrite_blockbuster_factor_objects(self) -> None:
        raw = {
            "core_idea": "x",
            "core_conflict": "y",
            "hook_concept": "z",
            "target_audience": "a",
            "compliance_risk": "low",
            "blockbuster_factors": [
                {"factor": "身份反转", "description": "弃女实为隐藏精英"},
            ],
        }
        out = normalize_project_brief(raw, self.settings)
        self.assertNotIn("blockbuster_factors", out)

    def test_valid_fixture_stays_valid(self) -> None:
        out = normalize_project_brief(FIXTURES["project_brief"], self.settings)
        self.validator.validate_file(
            out, "schemas/artifacts/project_brief/1.schema.json"
        )


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class StoryBibleNormalizeTests(SimpleTestCase):
    def setUp(self) -> None:
        self.validator = SchemaValidator()
        self.settings = {
            "title": "玉碎宫门",
            "core_idea": "弃女入宫操盘朝局",
            "entry_type": "original_track",
        }

    def test_does_not_fill_missing_synopsis_short(self) -> None:
        raw = {
            "drama_title": "玉碎宫门",
            "logline": "弃女入宫，暗中执棋",
            "synopsis": {"full": "她被送入深宫后步步崛起，最终执掌朝局。"},
        }
        out = normalize_story_bible(raw, self.settings)
        self.assertEqual(out["synopsis"], {"full": "她被送入深宫后步步崛起，最终执掌朝局。"})
        self.assertNotIn("short", out["synopsis"])

    def test_string_synopsis_not_rewritten_to_object(self) -> None:
        raw = dict(FIXTURES["story_bible"])
        raw["synopsis"] = "她被送入深宫后步步崛起。"
        out = normalize_story_bible(raw, self.settings)
        self.assertEqual(out["synopsis"], "她被送入深宫后步步崛起。")
        with self.assertRaises(Exception):
            self.validator.validate_file(out, "schemas/artifacts/story_bible/1.schema.json")

    def test_valid_fixture_stays_valid(self) -> None:
        out = normalize_story_bible(FIXTURES["story_bible"], self.settings)
        self.validator.validate_file(out, "schemas/artifacts/story_bible/1.schema.json")

    def test_llm_loose_aliases_not_rewritten(self) -> None:
        """别名键（want/initial 等）不得改写成正式键。"""
        raw = {
            "drama_title": "玉碎宫门",
            "logline": "宫女潜入深宫复仇",
            "synopsis": {
                "short": "沈玉楼入宫复仇，却发现盟友即真凶。",
                "full": "沈玉楼以宫女身份入宫，逐步攀升并追查灭门真相。",
            },
            "characters": [
                {
                    "name": "沈玉楼",
                    "role_type": "protagonist",
                    "want": "复仇夺权",
                    "need": "保持人性底线",
                    "arc": {
                        "initial": "隐忍复仇者",
                        "midpoint": "开始不择手段",
                        "low_point": "信念崩塌",
                        "final": "成为规则制定者",
                    },
                }
            ],
            "world_rules": {
                "setting_summary": "架空古代王朝宫廷",
                "root_rules": [
                    {
                        "rule": "宫女不得擅自进入禁宫",
                        "trigger": "跨入未授权区域",
                    }
                ],
                "power_structure": {
                    "description": "皇帝为顶点，司礼监与后宫制衡。",
                },
            },
            "series_structure": {
                "conflict_escalation_chain": [
                    {
                        "stage": 1,
                        "conflict_type": "外部（宫规）",
                        "description": "身份暴露危机",
                    }
                ],
                "series_emotion_curve": {
                    "description": "希望-紧张-绝望-觉醒",
                    "key_points": [{"episode": 1, "emotion": "希望"}],
                },
            },
        }
        out = normalize_story_bible(raw, self.settings)
        char = out["characters"][0]
        self.assertIn("want", char)
        self.assertNotIn("surface_desire", char)
        self.assertIn("initial", char["arc"])
        self.assertNotIn("start", char["arc"])
        self.assertIsInstance(out["world_rules"]["root_rules"][0], dict)
        self.assertIsInstance(out["world_rules"]["power_structure"], dict)
        self.assertIsInstance(out["series_structure"]["conflict_escalation_chain"][0], dict)
        self.assertIsInstance(out["series_structure"]["series_emotion_curve"], dict)
        with self.assertRaises(Exception):
            self.validator.validate_file(out, "schemas/artifacts/story_bible/1.schema.json")

    def test_stringified_conflict_dicts_not_humanized(self) -> None:
        raw = dict(FIXTURES["story_bible"])
        raw["series_structure"] = dict(raw["series_structure"])
        raw_text = (
            "{'stage': 1, 'conflict_type': '外部（宫规）', 'description': '身份暴露危机'}"
        )
        raw["series_structure"]["conflict_escalation_chain"] = [raw_text]
        out = normalize_story_bible(raw, self.settings)
        chain = out["series_structure"]["conflict_escalation_chain"]
        self.assertEqual(chain[0], raw_text)
        self.assertIn("{", chain[0])
        self.assertNotEqual(chain[0], "第1幕 · 外部（宫规）：身份暴露危机")


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class NarrativePlanNormalizeTests(SimpleTestCase):
    def setUp(self) -> None:
        self.validator = SchemaValidator()
        self.settings = {"title": "玉碎宫门"}

    def test_does_not_invent_missing_opening_hook(self) -> None:
        raw = {
            "episode_narrative_designs": [
                {
                    "episode": 1,
                    "title": "入宫",
                    "core_event": "暗语试探",
                    "goal_conflict": "潜伏×暴露",
                    "emotion_intensity": 7,
                    "satisfaction_points": ["过关"],
                    "reversal": "陆珩知情不报",
                    "paywall_hook": "身份将露",
                    "rhythm_tag": "tight",
                    "hook_grade": "A",
                    "characters": ["沈玉楼", "陆珩"],
                }
            ]
        }
        out = normalize_narrative_plan(raw, self.settings)
        ep = out["episode_narrative_designs"][0]
        self.assertNotIn("opening_hook", ep)
        self.assertNotIn("ending_hook", ep)
        with self.assertRaises(Exception):
            self.validator.validate_file(out, "schemas/artifacts/narrative_plan/1.schema.json")

    def test_opening_hook_aliases_not_rewritten(self) -> None:
        raw = {
            "episode_narrative_designs": [
                {
                    "episode": 2,
                    "title": "锋芒",
                    "core_event": "陷害对手",
                    "open_hook": "酒宴发难",
                    "cliffhanger": "青禾被点名",
                    "emotion_intensity": 8,
                }
            ]
        }
        out = normalize_narrative_plan(raw, self.settings)
        ep = out["episode_narrative_designs"][0]
        self.assertEqual(ep.get("open_hook"), "酒宴发难")
        self.assertEqual(ep.get("cliffhanger"), "青禾被点名")
        self.assertNotIn("opening_hook", ep)
        self.assertNotIn("ending_hook", ep)

    def test_normalize_preserves_canonical_opening_hook(self) -> None:
        """已是合法键名时 normalize 不改 opening_hook。"""
        raw = {
            "episode_narrative_designs": [
                {
                    "episode": 1,
                    "title": "入宫",
                    "core_event": "暗语试探",
                    "goal_conflict": "潜伏×暴露",
                    "emotion_intensity": 7,
                    "opening_hook": "殿前暗语对上",
                    "ending_hook": "陆珩未拆穿",
                    "satisfaction_points": ["过关"],
                    "reversal": "知情不报",
                    "paywall_hook": "身份将露",
                    "rhythm_tag": "tight",
                    "foreshadowing": {"setup": [], "payoff": []},
                    "hook_grade": "A",
                    "characters": ["沈玉楼"],
                    "emotion_nodes": {
                        "EV": {"value": 7},
                        "ET": {"value": 3},
                        "TP": {"content": "暗语试探"},
                    },
                }
            ]
        }
        out = normalize_narrative_plan(raw, self.settings)
        self.assertEqual(
            out["episode_narrative_designs"][0]["opening_hook"],
            "殿前暗语对上",
        )
        self.validator.validate_file(out, "schemas/artifacts/narrative_plan/1.schema.json")

    def test_valid_fixture_stays_valid(self) -> None:
        out = normalize_narrative_plan(FIXTURES["narrative_plan"], self.settings)
        self.validator.validate_file(out, "schemas/artifacts/narrative_plan/1.schema.json")


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class QualityReportNormalizeTests(SimpleTestCase):
    def setUp(self) -> None:
        self.validator = SchemaValidator()

    def test_chinese_dimension_aliases_not_rewritten(self) -> None:
        raw = {
            "drama_title": "边关开荒",
            "overall_score": 72,
            "grade": "C",
            "needs_revision": True,
            "dimensions": [
                {
                    "name": "格式规范",
                    "score": 75,
                    "evidence": ["场景标题基本统一，对白标注规范"],
                    "deduction_reasons": ["缺少价值转变标注(-10)"],
                },
            ],
        }
        out = normalize_quality_report(raw, {"title": "边关开荒"})
        self.assertIsInstance(out["dimensions"], list)
        self.assertEqual(out["dimensions"][0]["name"], "格式规范")
        self.assertNotIn("format", out["dimensions"] if isinstance(out["dimensions"], dict) else {})

    def test_comment_not_promoted_to_evidence(self) -> None:
        raw = {
            "drama_title": "边关开荒",
            "overall_score": 82,
            "grade": "A",
            "needs_revision": False,
            "verdict": "重大返工",
            "dimensions": {
                "hooks": {"score": 82, "comment": "第1集开场冲突成立，前3秒有身份危机"},
            },
        }
        out = normalize_quality_report(raw, {})
        self.assertEqual(out["verdict"], "重大返工")
        self.assertEqual(out["dimensions"]["hooks"].get("comment"), "第1集开场冲突成立，前3秒有身份危机")
        self.assertNotIn("evidence", out["dimensions"]["hooks"])

    def test_score_only_dimensions_flagged_sparse(self) -> None:
        raw = {
            "drama_title": "边关开荒",
            "overall_score": 82,
            "dimensions": {
                key: {"score": 80}
                for key in (
                    "format",
                    "narrative",
                    "conflict",
                    "character",
                    "emotion",
                    "logic",
                    "satisfaction",
                    "hooks",
                    "paywall",
                    "genre_fit",
                )
            },
        }
        out = normalize_quality_report(raw, {})
        self.assertTrue(quality_report_evidence_too_sparse(out))

    def test_any_dimension_without_evidence_is_sparse(self) -> None:
        dims = {
            k: {"score": 80, "evidence": [f"第1集{k}有明确场景与台词支撑"], "deductions": []}
            for k in (
                "format", "narrative", "conflict", "character", "emotion",
                "logic", "satisfaction", "hooks", "paywall", "genre_fit",
            )
        }
        dims["hooks"] = {"score": 80, "evidence": [], "deductions": []}
        out = normalize_quality_report(
            {"drama_title": "t", "overall_score": 80, "dimensions": dims}, {}
        )
        self.assertTrue(quality_report_evidence_too_sparse(out))

    def test_ten_point_scores_not_rescaled(self) -> None:
        dims = {
            key: {
                "score": 8,
                "evidence": [f"第1集{key}维度有明确场景支撑示例"],
                "deductions": [],
            }
            for key in (
                "format",
                "narrative",
                "conflict",
                "character",
                "emotion",
                "logic",
                "satisfaction",
                "hooks",
                "paywall",
                "genre_fit",
            )
        }
        raw = {
            "drama_title": "边关开荒",
            "overall_score": 78,
            "needs_revision": False,
            "dimensions": dims,
        }
        out = normalize_quality_report(raw, {})
        self.assertEqual(out["dimensions"]["hooks"]["score"], 8)
        self.assertEqual(out["overall_score"], 78)

    def test_explicit_verdict_detail_preserved(self) -> None:
        detail = ("overall quality is solid with clear three-act pacing and consistent arcs. ") * 6
        dims = {
            k: {
                "score": 80,
                "evidence": [
                    f"ep1 {k} opening conflict is clear with dialogue and action setup.",
                    f"ep8 {k} payoff recovers ep1 foreshadowing with acceptable pacing.",
                    f"ep12 {k} crisis shows ability cost and consistent character motivation.",
                ],
                "deductions": [f"{k} mid-bridge slightly long, can cut half an episode."],
            }
            for k in (
                "format",
                "narrative",
                "conflict",
                "character",
                "emotion",
                "logic",
                "satisfaction",
                "hooks",
                "paywall",
                "genre_fit",
            )
        }
        out = normalize_quality_report(
            {
                "drama_title": "border farm",
                "overall_score": 86,
                "verdict": "通过",
                "verdict_detail": detail,
                "dimensions": dims,
            },
            {},
        )
        self.assertEqual(out["verdict"], "通过")
        self.assertEqual(out.get("verdict_detail"), detail)
        self.assertFalse(quality_report_evidence_too_sparse(out))

    def test_string_defects_not_rewritten_to_objects(self) -> None:
        dims = {
            k: {
                "score": 80,
                "evidence": [f"ep1 {k} has a concrete scene and dialogue beat."],
                "deductions": [],
            }
            for k in (
                "format",
                "narrative",
                "conflict",
                "character",
                "emotion",
                "logic",
                "satisfaction",
                "hooks",
                "paywall",
                "genre_fit",
            )
        }
        out = normalize_quality_report(
            {
                "drama_title": "t",
                "overall_score": 80,
                "dimensions": dims,
                "defects": ["mid episodes drag slightly"],
                "revision_priorities": ["compress ep10-12"],
            },
            {},
        )
        self.assertEqual(out["defects"], ["mid episodes drag slightly"])
        self.assertEqual(out["revision_priorities"], ["compress ep10-12"])

    def test_injects_weight_from_scoring_preset(self) -> None:
        out = normalize_quality_report(
            {
                "drama_title": "t",
                "overall_score": 80,
                "needs_revision": False,
                "dimensions": {
                    "hooks": {"score": 80, "evidence": ["ep1 hooks clear"], "deductions": []},
                },
            },
            {},
        )
        self.assertIsInstance(out["dimensions"]["hooks"]["weight"], float)
        self.assertEqual(out["scored_artifact"], "latest_script")
        self.assertEqual(out["scoring_preset"], "standard")

    def test_chinese_prose_continuity_not_rewritten(self) -> None:
        out = normalize_quality_report(
            {
                "drama_title": "t",
                "overall_score": 80,
                "continuity_summary": "整体连续性好，无重大矛盾。",
            },
            {},
        )
        self.assertEqual(out["continuity_summary"], "整体连续性好，无重大矛盾。")

    def test_short_dimension_analysis_is_sparse(self) -> None:
        dims = {
            k: {
                "score": 80,
                "evidence": [f"第1集{k}有明确场景与台词支撑示例，但篇幅仍偏短"],
                "deductions": [],
            }
            for k in (
                "format",
                "narrative",
                "conflict",
                "character",
                "emotion",
                "logic",
                "satisfaction",
                "hooks",
                "paywall",
                "genre_fit",
            )
        }
        out = normalize_quality_report(
            {
                "drama_title": "t",
                "overall_score": 80,
                "verdict_detail": "短",
                "dimensions": dims,
            },
            {},
        )
        self.assertTrue(quality_report_evidence_too_sparse(out))


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class ComplianceReportNormalizeTests(SimpleTestCase):
    def test_does_not_invent_blocking_title_from_category(self) -> None:
        raw = {
            "drama_title": "边关开荒",
            "overall_result": "不通过",
            "blocking_issues": [
                {
                    "category": "犯罪正义收束",
                    "level": "p1",
                    "description": "犯罪描写密集但正义收束不足",
                }
            ],
            "risk_items": [],
        }
        out = normalize_compliance_report(raw, {})
        self.assertNotIn("title", out["blocking_issues"][0])
        self.assertEqual(out["blocking_issues"][0]["category"], "犯罪正义收束")

    def test_compliance_report_aliases_not_rewritten(self) -> None:
        raw = {
            "drama_title": "边关开荒",
            "overall_result": "pass",
            "risk_items": [
                {"type": "P1", "issue": "暴力描写偏多", "fix": "弱化血腥细节"},
            ],
        }
        out = normalize_compliance_report(raw, {})
        self.assertEqual(out["overall_result"], "pass")
        self.assertEqual(out["risk_items"][0]["issue"], "暴力描写偏多")
        self.assertNotIn("description", out["risk_items"][0])
        with self.assertRaises(Exception):
            SchemaValidator().validate_file(
                out, "schemas/artifacts/compliance_report/1.schema.json"
            )
