# -*- coding: utf-8 -*-
from django.test import SimpleTestCase, override_settings

from apps.drama.services.condition_eval import evaluate_condition, module_enable_context
from apps.drama.services.skills_loader import SkillsBundleLoader
from apps.drama.tests.helpers import SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class ConditionEvalTests(SimpleTestCase):
    def test_equals_and_contains(self):
        ctx = {"entry_type": "story_adapt", "deliverables": ["storyboard", "budget"]}
        self.assertTrue(evaluate_condition("entry_type == 'story_adapt'", ctx))
        self.assertFalse(evaluate_condition("entry_type == 'original_track'", ctx))
        self.assertTrue(evaluate_condition("deliverables contains 'budget'", ctx))

    def test_module_context(self):
        settings = {
            "entry_type": "original_track",
            "creation_preferences": {"delivery_items": ["marketing"]},
        }
        ctx = module_enable_context(settings)
        self.assertEqual(ctx["entry_type"], "original_track")
        self.assertEqual(ctx["deliverables"], ["marketing"])


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class SkillsProgressiveLoadTests(SimpleTestCase):
    def test_anti_examples_and_knowledge(self):
        loader = SkillsBundleLoader()
        anti = loader.load_anti_examples("drama.topic-director")
        self.assertIn("禁止字段", anti)
        knowledge = loader.load_knowledge_for_role(
            "drama.topic-director",
            {"target_platform": "douyin", "entry_type": "original_track"},
        )
        self.assertTrue(knowledge)
        few = loader.load_fewshots("drama.topic-director")
        self.assertIn("few-shot", few.lower())
