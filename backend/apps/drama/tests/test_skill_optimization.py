# -*- coding: utf-8 -*-
from django.test import SimpleTestCase, override_settings

from apps.drama.services.condition_eval import evaluate_condition, module_enable_context
from apps.drama.services.skills_loader import SkillsBundleLoader, _resolve_theme_code
from apps.drama.tests.helpers import SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class ConditionEvalTests(SimpleTestCase):
    def test_equals_and_contains(self):
        ctx = {"entry_type": "story_adapt", "deliverables": ["storyboard", "budget"]}
        self.assertTrue(evaluate_condition("entry_type == 'story_adapt'", ctx))
        self.assertFalse(evaluate_condition("entry_type == 'original_track'", ctx))
        self.assertTrue(evaluate_condition("deliverables contains 'budget'", ctx))

    def test_module_context_ignores_legacy_delivery_items(self):
        settings = {
            "entry_type": "original_track",
            "creation_preferences": {"delivery_items": ["marketing"]},
        }
        ctx = module_enable_context(settings)
        self.assertEqual(ctx["entry_type"], "original_track")
        self.assertEqual(ctx["deliverables"], [])
        self.assertFalse(
            evaluate_condition("deliverables contains 'marketing'", ctx)
        )

    def test_module_context_reads_deliverables(self):
        settings = {
            "entry_type": "original_track",
            "creation_preferences": {"deliverables": ["marketing"]},
        }
        ctx = module_enable_context(settings)
        self.assertEqual(ctx["deliverables"], ["marketing"])
        self.assertTrue(
            evaluate_condition("deliverables contains 'marketing'", ctx)
        )


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class SkillsProgressiveLoadTests(SimpleTestCase):
    def test_anti_examples_and_knowledge(self):
        loader = SkillsBundleLoader()
        anti = loader.load_anti_examples("drama.topic-director")
        self.assertIn("禁止字段", anti)
        knowledge = loader.load_knowledge_for_role(
            "drama.topic-director",
            {
                "target_platform": "douyin",
                "entry_type": "original_track",
                "audience_channel": "female",
                "genre_matrix": {
                    "emotion": "revenge",
                    "identity": "hidden-elite",
                    "conflict": "family",
                    "world": "modern",
                },
            },
        )
        self.assertTrue(knowledge)
        self.assertIn("隐藏身份", knowledge)
        few = loader.load_fewshots("drama.topic-director")
        self.assertIn("few-shot", few.lower())

    def test_douyin_formulas_skipped_when_platform_not_douyin(self):
        loader = SkillsBundleLoader()
        knowledge = loader.load_knowledge_for_role(
            "drama.topic-director",
            {
                "target_platform": "generic",
                "entry_type": "original_track",
                "genre_matrix": {
                    "emotion": "revenge",
                    "identity": "hidden-elite",
                    "conflict": "family",
                    "world": "modern",
                },
            },
        )
        self.assertNotIn("隐藏身份", knowledge)
        self.assertNotIn("_shared", knowledge)

    def test_douyin_formulas_injected_only_for_douyin_platform(self):
        loader = SkillsBundleLoader()
        settings_base = {
            "entry_type": "original_track",
            "genre_matrix": {
                "emotion": "revenge",
                "identity": "hidden-elite",
                "conflict": "family",
                "world": "modern",
            },
        }
        for platform, should_include in (
            ("douyin", True),
            ("kuaishou", False),
            ("generic", False),
        ):
            text = loader.load_knowledge_for_role(
                "drama.topic-director",
                {**settings_base, "target_platform": platform},
            )
            if should_include:
                self.assertIn("隐藏身份", text, platform)
            else:
                self.assertNotIn("隐藏身份", text, platform)

    def test_douyin_formulas_require_genre_match(self):
        loader = SkillsBundleLoader()
        # 平台对但题材不匹配任何公式 → 整包不注入
        unmatched = loader.load_knowledge_for_role(
            "drama.topic-director",
            {
                "target_platform": "douyin",
                "entry_type": "original_track",
                "audience_channel": "general",
                "genre_matrix": {
                    "emotion": "nostalgia",
                    "identity": "student",
                    "conflict": "survival",
                    "world": "campus",
                },
            },
        )
        self.assertNotIn("隐藏身份", unmatched)
        self.assertNotIn("古风美学", unmatched)
        self.assertNotIn("标签三级体系", unmatched)

        # 古装 → 命中 ancient-aesthetic
        ancient = loader.load_knowledge_for_role(
            "drama.topic-director",
            {
                "target_platform": "douyin",
                "entry_type": "original_track",
                "genre_matrix": {
                    "emotion": "love",
                    "identity": "underdog",
                    "conflict": "power",
                    "world": "ancient",
                },
            },
        )
        self.assertIn("古风美学", ancient)
        self.assertIn("标签三级体系", ancient)

    def test_resolve_theme_code_hard_fails_without_theme(self):
        loader = SkillsBundleLoader()
        with self.assertRaises(ValueError) as ctx:
            _resolve_theme_code({}, root=loader.root)
        message = str(ctx.exception)
        self.assertIn("genre_matrix", message)
        self.assertIn("preset_theme_code", message)

    def test_resolve_theme_code_rejects_unknown_preset(self):
        loader = SkillsBundleLoader()
        with self.assertRaises(ValueError) as ctx:
            _resolve_theme_code(
                {"preset_theme_code": "not-a-real-preset"},
                root=loader.root,
            )
        self.assertIn("not-a-real-preset", str(ctx.exception))

    def test_resolve_theme_code_accepts_valid_preset_via_matrix_rules(self):
        loader = SkillsBundleLoader()
        theme_code = _resolve_theme_code(
            {"preset_theme_code": "family-revenge"},
            root=loader.root,
        )
        self.assertEqual(theme_code, "matrix")
