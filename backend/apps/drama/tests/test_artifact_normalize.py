# -*- coding: utf-8 -*-
"""产物 normalize 合成补全测试（零兼容：不做别名/形状改写）。"""
from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from apps.core.schema_validator import SchemaValidator
from apps.drama.services.artifact_normalize import (
    normalize_compliance_report,
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

    def test_canonicalizes_chinese_axis_labels(self) -> None:
        """模型常输出「复仇+爽感」等中文标签，normalize 应收束为英文枚举。"""
        settings = {
            **self.settings,
            "flavor_tags": [],
            "genre_matrix": {
                "emotion": "revenge",
                "identity": "reborn",
                "conflict": "family",
                "world": "modern",
            },
        }
        raw = {
            "core_idea": "弃女翻盘",
            "core_conflict": "复仇 vs 代价",
            "hook_concept": "假死归来",
            "target_audience": "女频",
            "audience_channel": "female",
            "genre_matrix": {
                "emotion": "复仇+爽感",
                "identity": "重生",
                "conflict": "家庭伦理",
                "world": "现代都市",
            },
            "blockbuster_factors": ["身份反转"],
            "compliance_risk": "low",
            "market_opportunity": "女频复仇热",
            "differentiation_strategy": "证据链驱动",
            "first_episode_hook": "葬礼反杀",
            "paywall_direction": "真凶现身",
        }
        out = normalize_project_brief(raw, settings)
        self.assertEqual(out["genre_matrix"]["emotion"], "revenge")
        self.assertEqual(out["genre_matrix"]["identity"], "reborn")
        self.assertEqual(out["genre_matrix"]["conflict"], "family")
        self.assertEqual(out["genre_matrix"]["world"], "modern")
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

    def test_partial_synopsis_fills_missing_short(self) -> None:
        raw = {
            "drama_title": "玉碎宫门",
            "logline": "弃女入宫，暗中执棋",
            "synopsis": {"full": "她被送入深宫后步步崛起，最终执掌朝局。"},
        }
        out = normalize_story_bible(raw, self.settings)
        self.assertEqual(out["synopsis"]["full"], "她被送入深宫后步步崛起，最终执掌朝局。")
        self.assertEqual(out["synopsis"]["short"], "她被送入深宫后步步崛起，最终执掌朝局。")

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

    def test_missing_adapt_source_defaults_to_original(self) -> None:
        raw = dict(FIXTURES["story_bible"])
        raw.pop("adapt_source", None)
        out = normalize_story_bible(raw, {**self.settings, "entry_type": "original"})
        self.assertEqual(out["adapt_source"]["mode"], "original")
        self.validator.validate_file(out, "schemas/artifacts/story_bible/1.schema.json")

    def test_missing_adapt_source_defaults_to_adapt_for_adapt_entry(self) -> None:
        raw = dict(FIXTURES["story_bible"])
        raw.pop("adapt_source", None)
        out = normalize_story_bible(raw, {**self.settings, "entry_type": "adapt"})
        self.assertEqual(out["adapt_source"]["mode"], "adapt")

    def test_missing_world_rules_gets_minimal_defaults(self) -> None:
        raw = dict(FIXTURES["story_bible"])
        raw.pop("world_rules", None)
        out = normalize_story_bible(raw, self.settings)
        rules = out["world_rules"]
        self.assertIsInstance(rules, dict)
        self.assertTrue(rules["setting_summary"])
        self.assertIsInstance(rules["root_rules"], list)
        self.assertGreaterEqual(len(rules["root_rules"]), 1)
        self.assertTrue(rules["power_structure"])
        self.validator.validate_file(out, "schemas/artifacts/story_bible/1.schema.json")

    def test_partial_world_rules_fills_required_fields(self) -> None:
        raw = dict(FIXTURES["story_bible"])
        raw["world_rules"] = {"setting_summary": "现代都市"}
        out = normalize_story_bible(raw, self.settings)
        self.assertEqual(out["world_rules"]["setting_summary"], "现代都市")
        self.assertIsInstance(out["world_rules"]["root_rules"], list)
        self.assertTrue(out["world_rules"]["power_structure"])
        self.validator.validate_file(out, "schemas/artifacts/story_bible/1.schema.json")

    def test_empty_payload_normalizes_to_schema_valid(self) -> None:
        """LLM 漏掉几乎全部字段时，归一化后仍须过 schema（占位骨架）。"""
        from apps.drama.skills_bridge.validate import validate_artifact_payload

        out = normalize_story_bible({}, self.settings)
        errors = validate_artifact_payload("story_bible", out)
        self.assertEqual(errors, [], errors)

    def test_each_required_top_level_key_can_be_omitted(self) -> None:
        """逐个剥离 fixture 顶层必填键，归一化后仍须过 schema。"""
        from apps.drama.skills_bridge.validate import validate_artifact_payload

        required = [
            "drama_title",
            "logline",
            "synopsis",
            "adapt_source",
            "world_rules",
            "characters",
            "relationship_map",
            "series_structure",
        ]
        for key in required:
            raw = dict(FIXTURES["story_bible"])
            raw.pop(key, None)
            out = normalize_story_bible(raw, self.settings)
            errors = validate_artifact_payload("story_bible", out)
            self.assertEqual(errors, [], f"omit {key}: {errors}")

    def test_user_reported_missing_world_rules_only(self) -> None:
        """对齐线上报错：仅缺 world_rules 时必须能过校验，无需用户重试碰运气。"""
        from apps.drama.skills_bridge.validate import validate_artifact_payload

        raw = dict(FIXTURES["story_bible"])
        raw.pop("world_rules", None)
        out = normalize_story_bible(raw, {**self.settings, "title": "重生之逆袭人生"})
        errors = validate_artifact_payload("story_bible", out)
        self.assertEqual(errors, [], errors)
        self.assertIn("setting_summary", out["world_rules"])

    def test_character_missing_required_fields_get_filled(self) -> None:
        """对齐线上：characters 缺 ghost 等必填时补齐后过 schema。"""
        from apps.drama.skills_bridge.validate import validate_artifact_payload

        raw = dict(FIXTURES["story_bible"])
        chars = [dict(raw["characters"][0])]
        for key in ("ghost", "lie", "flaw", "voice_tag", "visual_anchor"):
            chars[0].pop(key, None)
        raw["characters"] = chars
        out = normalize_story_bible(raw, self.settings)
        errors = validate_artifact_payload("story_bible", out)
        self.assertEqual(errors, [], errors)
        self.assertEqual(out["characters"][0]["ghost"], "待细化")

    def test_each_character_required_field_can_be_omitted(self) -> None:
        from apps.drama.skills_bridge.validate import validate_artifact_payload

        required = [
            "name",
            "role_type",
            "surface_desire",
            "deep_need",
            "ghost",
            "lie",
            "flaw",
            "arc",
            "voice_tag",
            "visual_anchor",
        ]
        for key in required:
            raw = dict(FIXTURES["story_bible"])
            char = dict(raw["characters"][0])
            char.pop(key, None)
            raw["characters"] = [char]
            out = normalize_story_bible(raw, self.settings)
            errors = validate_artifact_payload("story_bible", out)
            self.assertEqual(errors, [], f"omit character.{key}: {errors}")

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

    def test_missing_resolved_script_key_defaults_for_project(self) -> None:
        from apps.drama.skills_bridge.validate import validate_artifact_payload

        raw = dict(FIXTURES["quality_report"])
        raw.pop("resolved_script_key", None)
        out = normalize_quality_report(raw, {"title": "测试短剧"})
        self.assertEqual(out["resolved_script_key"], "episode_scripts")
        self.assertEqual(validate_artifact_payload("quality_report", out), [])

    def test_missing_resolved_script_key_defaults_external(self) -> None:
        from apps.drama.skills_bridge.validate import validate_artifact_payload

        raw = dict(FIXTURES["quality_report"])
        raw.pop("resolved_script_key", None)
        out = normalize_quality_report(
            raw,
            {
                "title": "发配边关",
                "resolved_script_key": "external_script",
                "external_script_review": True,
            },
        )
        self.assertEqual(out["resolved_script_key"], "external_script")
        self.assertEqual(validate_artifact_payload("quality_report", out), [])

    def test_each_required_quality_key_can_be_omitted(self) -> None:
        from apps.drama.skills_bridge.validate import validate_artifact_payload

        required = [
            "drama_title",
            "scored_artifact",
            "resolved_script_key",
            "scoring_preset",
            "pass_threshold",
            "overall_score",
            "grade",
            "can_continue_next_batch",
            "needs_revision",
            "dimensions",
            "defects",
            "continuity_summary",
            "revision_priorities",
            "verdict",
        ]
        for key in required:
            raw = dict(FIXTURES["quality_report"])
            raw.pop(key, None)
            out = normalize_quality_report(raw, {"title": "测试短剧"})
            errors = validate_artifact_payload("quality_report", out)
            self.assertEqual(errors, [], f"omit {key}: {errors}")

    def test_empty_quality_payload_normalizes_to_schema_valid(self) -> None:
        from apps.drama.skills_bridge.validate import validate_artifact_payload

        out = normalize_quality_report({}, {"title": "发配边关"})
        self.assertEqual(validate_artifact_payload("quality_report", out), [])

    def test_strips_unexpected_top_level_keys_from_llm(self) -> None:
        """对齐线上：LLM 多吐字段导致 additionalProperties 失败。"""
        from apps.drama.services.artifact_normalize import (
            _schema_top_level_allowed_keys,
            normalize_artifact,
        )
        from apps.drama.skills_bridge.validate import validate_artifact_payload

        _schema_top_level_allowed_keys.cache_clear()
        raw = dict(FIXTURES["quality_report"])
        raw.update(
            {
                "external_review_note": "外界评审备注",
                "must_fix_issues": [{"title": "必须修"}],
                "revision_priority": "先改节奏",
                "suggested_optimizations": ["加强钩子"],
                "total_score": 88,
            }
        )
        # 故意去掉 overall_score，验证 total_score 别名收束
        raw.pop("overall_score", None)
        out = normalize_artifact("quality_report", raw, {"title": "发配边关"})
        for key in (
            "external_review_note",
            "must_fix_issues",
            "revision_priority",
            "suggested_optimizations",
            "total_score",
        ):
            self.assertNotIn(key, out)
        self.assertEqual(out["overall_score"], 88)
        self.assertEqual(validate_artifact_payload("quality_report", out), [])


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

    def test_missing_resolved_script_key_on_compliance(self) -> None:
        from apps.drama.skills_bridge.validate import validate_artifact_payload

        raw = dict(FIXTURES["compliance_report"])
        raw.pop("resolved_script_key", None)
        out = normalize_compliance_report(
            raw, {"title": "发配边关", "resolved_script_key": "external_script"}
        )
        self.assertEqual(out["resolved_script_key"], "external_script")
        self.assertEqual(validate_artifact_payload("compliance_report", out), [])

    def test_each_required_compliance_key_can_be_omitted(self) -> None:
        from apps.drama.skills_bridge.validate import validate_artifact_payload

        required = [
            "drama_title",
            "check_mode",
            "target_platform",
            "checked_artifact",
            "resolved_script_key",
            "overall_result",
            "blocking_issues",
            "risk_items",
        ]
        for key in required:
            raw = dict(FIXTURES["compliance_report"])
            raw.pop(key, None)
            out = normalize_compliance_report(raw, {"title": "测试短剧"})
            errors = validate_artifact_payload("compliance_report", out)
            self.assertEqual(errors, [], f"omit {key}: {errors}")
