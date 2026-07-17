# -*- coding: utf-8 -*-
"""project_brief 契约对齐测试。"""
from __future__ import annotations

from django.test import SimpleTestCase, TestCase, override_settings

from apps.core.schema_validator import SchemaValidator
from apps.drama.services.artifact_normalize import (
    normalize_narrative_plan,
    normalize_project_brief,
    normalize_story_bible,
)
from apps.drama.tests.helpers import FIXTURES, SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class ProjectBriefNormalizeTests(TestCase):
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
            "one_line_theme": "弃女入宫，暗中执棋",
            "synopsis": "她被送入深宫后步步崛起。",
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
            "blockbuster_factors": [
                {"factor": "身份反转", "description": "弃女实为隐藏精英"},
            ],
            "sensitivity_pre_check": [{"risk": "历史虚无", "level": "medium"}],
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

    def test_valid_fixture_stays_valid(self) -> None:
        out = normalize_project_brief(FIXTURES["project_brief"], self.settings)
        self.validator.validate_file(
            out, "schemas/artifacts/project_brief/1.schema.json"
        )


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class StoryBibleNormalizeTests(TestCase):
    def setUp(self) -> None:
        self.validator = SchemaValidator()
        self.settings = {
            "title": "玉碎宫门",
            "core_idea": "弃女入宫操盘朝局",
            "entry_type": "original_track",
        }

    def test_fills_missing_synopsis_short(self) -> None:
        raw = {
            "drama_title": "玉碎宫门",
            "logline": "弃女入宫，暗中执棋",
            "synopsis": {"full": "她被送入深宫后步步崛起，最终执掌朝局。"},
            "adapt_source": {"mode": "original"},
            "world_rules": {
                "setting_summary": "大周朝堂",
                "root_rules": ["后宫不得干政"],
                "power_structure": "帝后外戚博弈",
            },
            "characters": [
                {
                    "name": "沈玉碎",
                    "role_type": "protagonist",
                    "surface_desire": "活下去",
                    "deep_need": "被看见",
                    "ghost": "被弃之痛",
                    "lie": "示弱才能活",
                    "flaw": "过度隐忍",
                    "arc": {
                        "start": "棋子",
                        "turning_point_1": "第一次反杀",
                        "turning_point_2": "身份暴露",
                        "end": "执棋者",
                    },
                    "voice_tag": "冷而克制",
                    "visual_anchor": "一枚玉碎簪",
                }
            ],
            "relationship_map": [],
            "series_structure": {
                "main_storyline": "弃女崛起",
                "six_stage_structure": [
                    {"stage": 1},
                    {"stage": 2},
                    {"stage": 3},
                    {"stage": 4},
                    {"stage": 5},
                    {"stage": 6},
                ],
                "conflict_escalation_chain": ["入宫", "夺权"],
                "major_reversal_positions": [],
                "paywall_distribution": [],
                "foreshadowing_table": [],
                "series_emotion_curve": [],
            },
        }
        out = normalize_story_bible(raw, self.settings)
        self.assertIn("short", out["synopsis"])
        self.assertTrue(out["synopsis"]["short"])
        self.assertEqual(out["synopsis"]["full"], raw["synopsis"]["full"])
        self.validator.validate_file(out, "schemas/artifacts/story_bible/1.schema.json")

    def test_string_synopsis_becomes_object(self) -> None:
        raw = dict(FIXTURES["story_bible"])
        raw["synopsis"] = "她被送入深宫后步步崛起。"
        out = normalize_story_bible(raw, self.settings)
        self.assertIsInstance(out["synopsis"], dict)
        self.assertIn("short", out["synopsis"])
        self.assertIn("full", out["synopsis"])
        self.validator.validate_file(out, "schemas/artifacts/story_bible/1.schema.json")

    def test_valid_fixture_stays_valid(self) -> None:
        out = normalize_story_bible(FIXTURES["story_bible"], self.settings)
        self.validator.validate_file(out, "schemas/artifacts/story_bible/1.schema.json")

    def test_llm_loose_aliases_preserve_content(self) -> None:
        """模型常用 want/initial/规则对象/情绪曲线对象，归一化后不得变成「待补充」。"""
        raw = {
            "drama_title": "玉碎宫门",
            "logline": "宫女潜入深宫复仇",
            "synopsis": {
                "short": "沈玉楼入宫复仇，却发现盟友即真凶。",
                "full": "沈玉楼以宫女身份入宫，逐步攀升并追查灭门真相。",
            },
            "adapt_source": {"mode": "original"},
            "world_rules": {
                "setting_summary": "架空古代王朝宫廷",
                "root_rules": [
                    {
                        "rule": "宫女不得擅自进入禁宫",
                        "trigger": "跨入未授权区域",
                        "applicable_to": "所有宫女",
                        "violation_cost": "杖责或处死",
                        "visible_manifestation": "令牌通行",
                    }
                ],
                "power_structure": {
                    "description": "皇帝为顶点，司礼监与后宫制衡。",
                    "key_actors": [
                        {
                            "name": "陆珩",
                            "position": "司礼监掌印",
                            "resources": "暗探网络",
                            "motivation": "掩盖灭门案",
                        }
                    ],
                },
            },
            "characters": [
                {
                    "name": "沈玉楼",
                    "role_type": "protagonist",
                    "background": "沈家灭门唯一幸存者",
                    "want": "复仇夺权",
                    "need": "保持人性底线",
                    "ghost": "灭门夜记忆",
                    "lie": "复仇即正义",
                    "flaw": "过度自信",
                    "arc": {
                        "initial": "隐忍复仇者",
                        "midpoint": "开始不择手段",
                        "low_point": "信念崩塌",
                        "final": "成为规则制定者",
                    },
                    "voice_tag": "冷静锋利",
                    "visual_anchor": "腕上碎玉红绳",
                }
            ],
            "relationship_map": [
                {
                    "from": "沈玉楼",
                    "to": "陆珩",
                    "type": "同盟与猜忌",
                    "description": "先合作后决裂再联手",
                }
            ],
            "series_structure": {
                "main_storyline": "入宫复仇至权力之巅",
                "six_stage_structure": [
                    {
                        "stage": 1,
                        "name": "入宫与潜伏",
                        "episode_range": "1-6",
                        "target": "建立动机",
                        "irreversible_turn": "与陆珩结盟",
                    },
                    {"stage": 2, "name": "初露锋芒"},
                    {"stage": 3, "name": "信任危机"},
                    {"stage": 4, "name": "决裂"},
                    {"stage": 5, "name": "低谷"},
                    {"stage": 6, "name": "终局"},
                ],
                "conflict_escalation_chain": [
                    {
                        "stage": 1,
                        "conflict_type": "外部（宫规）",
                        "description": "身份暴露危机",
                    }
                ],
                "major_reversal_positions": [
                    {"episode": 22, "type": "S级", "description": "发现陆珩在场"}
                ],
                "paywall_distribution": [],
                "foreshadowing_table": [
                    {
                        "id": "f1",
                        "description": "碎玉与扳指同源",
                        "setup_episodes": [1, 5],
                        "payoff_episode": 22,
                        "status": "setup",
                    }
                ],
                "series_emotion_curve": {
                    "description": "希望-紧张-绝望-觉醒",
                    "key_points": [
                        {"episode": 1, "emotion": "希望", "event": "入宫"},
                        {"episode": 22, "emotion": "震惊", "event": "发现真凶"},
                    ],
                },
            },
        }
        out = normalize_story_bible(raw, self.settings)
        self.validator.validate_file(out, "schemas/artifacts/story_bible/1.schema.json")

        char = out["characters"][0]
        self.assertEqual(char["surface_desire"], "复仇夺权")
        self.assertEqual(char["deep_need"], "保持人性底线")
        self.assertEqual(char["arc"]["start"], "隐忍复仇者")
        self.assertEqual(char["arc"]["turning_point_1"], "开始不择手段")
        self.assertEqual(char["arc"]["turning_point_2"], "信念崩塌")
        self.assertEqual(char["arc"]["end"], "成为规则制定者")
        self.assertEqual(char["audience_identification"], "沈家灭门唯一幸存者")
        self.assertNotIn("待补充", char["surface_desire"])

        rules = out["world_rules"]["root_rules"]
        self.assertEqual(len(rules), 1)
        self.assertIn("宫女不得擅自进入禁宫", rules[0])
        self.assertIn("触发：", rules[0])
        self.assertIn("司礼监掌印", out["world_rules"]["power_structure"])
        self.assertIn("陆珩", out["world_rules"]["power_structure"])

        chain = out["series_structure"]["conflict_escalation_chain"]
        self.assertEqual(len(chain), 1)
        self.assertIn("身份暴露危机", chain[0])
        curve = out["series_structure"]["series_emotion_curve"]
        self.assertEqual(len(curve), 2)
        self.assertEqual(curve[0]["episode"], 1)
        self.assertEqual(curve[0].get("curve_summary"), "希望-紧张-绝望-觉醒")

    def test_stringified_conflict_dicts_are_humanized(self) -> None:
        raw = dict(FIXTURES["story_bible"])
        raw["series_structure"] = dict(raw["series_structure"])
        raw["series_structure"]["conflict_escalation_chain"] = [
            "{'stage': 1, 'conflict_type': '外部（宫规）', 'description': '身份暴露危机'}",
            {
                "stage": 2,
                "conflict_type": "人际",
                "description": "卷入后妃争斗",
            },
        ]
        out = normalize_story_bible(raw, self.settings)
        chain = out["series_structure"]["conflict_escalation_chain"]
        self.assertEqual(chain[0], "第1幕 · 外部（宫规）：身份暴露危机")
        self.assertEqual(chain[1], "第2幕 · 人际：卷入后妃争斗")
        self.assertNotIn("{", chain[0])
        self.validator.validate_file(out, "schemas/artifacts/story_bible/1.schema.json")


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class NarrativePlanNormalizeTests(TestCase):
    def setUp(self) -> None:
        self.validator = SchemaValidator()
        self.settings = {"title": "玉碎宫门"}

    def test_fills_missing_opening_hook(self) -> None:
        raw = {
            "episode_narrative_designs": [
                {
                    "episode": 1,
                    "title": "入宫",
                    "core_event": "暗语试探",
                    "goal_conflict": "潜伏×暴露",
                    "emotion_intensity": 7,
                    # 故意缺少 opening_hook / ending_hook
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
        self.assertIn("opening_hook", ep)
        self.assertTrue(ep["opening_hook"])
        self.assertIn("ending_hook", ep)
        self.assertTrue(ep["ending_hook"])
        self.assertEqual(ep["foreshadowing"], {"setup": [], "payoff": []})
        self.assertIn("EV", ep["emotion_nodes"])
        self.validator.validate_file(out, "schemas/artifacts/narrative_plan/1.schema.json")

    def test_opening_hook_aliases(self) -> None:
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
        self.assertEqual(ep["opening_hook"], "酒宴发难")
        self.assertEqual(ep["ending_hook"], "青禾被点名")
        self.validator.validate_file(out, "schemas/artifacts/narrative_plan/1.schema.json")

    def test_normalize_preserves_canonical_opening_hook(self) -> None:
        """已是合法键名时 normalize 不改 opening_hook，防止回归。"""
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

    def test_dimensions_array_converted_to_object(self) -> None:
        from apps.drama.services.artifact_normalize import normalize_quality_report

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
                {
                    "name": "叙事效率",
                    "score": 73,
                    "evidence": ["三幕式完整但中段节奏偏慢"],
                    "deduction_reasons": ["情节重复(-8)"],
                },
            ],
        }
        out = normalize_quality_report(raw, {"title": "边关开荒"})
        self.assertIsInstance(out["dimensions"], dict)
        self.assertIn("format", out["dimensions"])
        self.assertEqual(out["dimensions"]["format"]["score"], 75)
        self.assertEqual(
            out["dimensions"]["format"]["deductions"],
            ["缺少价值转变标注(-10)"],
        )
        self.assertIn("genre_fit", out["dimensions"])
        self.assertEqual(out["verdict"], "需要修改")
        # 未给出的维度会被补齐为空 evidence，不能通过现行 score_dimension 契约
        self.assertEqual(out["dimensions"]["genre_fit"]["evidence"], [])

    def test_promotes_comment_and_reconciles_verdict(self) -> None:
        from apps.drama.services.artifact_normalize import normalize_quality_report

        raw = {
            "drama_title": "边关开荒",
            "overall_score": 82,
            "grade": "A",
            "needs_revision": False,
            "verdict": "重大返工",
            "dimensions": {
                "hooks": {"score": 82, "comment": "第1集开场冲突成立，前3秒有身份危机"},
                "logic": {"score": 75, "evidence": "因果链基本自洽，动机交代清楚"},
            },
        }
        out = normalize_quality_report(raw, {})
        self.assertEqual(out["verdict"], "通过")
        self.assertFalse(out["needs_revision"])
        self.assertIn("第1集开场冲突成立", out["dimensions"]["hooks"]["evidence"][0])
        self.assertEqual(
            out["dimensions"]["logic"]["evidence"],
            ["因果链基本自洽，动机交代清楚"],
        )

    def test_score_only_dimensions_flagged_sparse(self) -> None:
        from apps.drama.services.artifact_normalize import (
            normalize_quality_report,
            quality_report_evidence_too_sparse,
        )

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
        from apps.drama.services.artifact_normalize import (
            normalize_quality_report,
            quality_report_evidence_too_sparse,
        )

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

    def test_ten_point_dimension_scores_scaled_when_overall_is_percent(self) -> None:
        from apps.drama.services.artifact_normalize import normalize_quality_report

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
        self.assertEqual(out["dimensions"]["hooks"]["score"], 80.0)
        self.assertFalse(
            __import__(
                "apps.drama.services.artifact_normalize",
                fromlist=["quality_report_evidence_too_sparse"],
            ).quality_report_evidence_too_sparse(out)
        )

    def test_compliance_blocking_gets_title(self) -> None:
        from apps.drama.services.artifact_normalize import normalize_compliance_report

        raw = {
            "title": "边关开荒",
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
        self.assertEqual(out["blocking_issues"][0]["title"], "犯罪正义收束")

    def test_compliance_report_aliases(self) -> None:
        from apps.drama.services.artifact_normalize import normalize_compliance_report

        raw = {
            "title": "边关开荒",
            "overall_result": "pass",
            "risk_items": [
                {"type": "P1", "issue": "暴力描写偏多", "fix": "弱化血腥细节"},
            ],
        }
        out = normalize_compliance_report(raw, {})
        self.assertEqual(out["overall_result"], "通过")
        self.assertEqual(out["risk_items"][0]["type"], "p1")
        self.assertEqual(out["risk_items"][0]["description"], "暴力描写偏多")
        self.validator.validate_file(
            out, "schemas/artifacts/compliance_report/1.schema.json"
        )