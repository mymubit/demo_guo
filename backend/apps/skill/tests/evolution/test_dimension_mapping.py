# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.creation.models import ScriptQualityDimension
from apps.creation.quality_dimensions import (
    FALLBACK_SUGGESTION,
    quality_dimension_label,
    quality_dimension_skill_id,
    quality_dimension_suggestion,
)
from apps.skill.evolution.services import RuleEvolutionService


class QualityDimensionMappingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = RuleEvolutionService()

    def test_all_script_quality_dimensions_have_chinese_labels(self):
        for dimension in ScriptQualityDimension.values:
            label = quality_dimension_label(dimension)
            self.assertNotEqual(label, dimension)
            self.assertTrue(any("\u4e00" <= ch <= "\u9fff" for ch in label))

    def test_all_script_quality_dimensions_have_specific_suggestions(self):
        for dimension in ScriptQualityDimension.values:
            suggestion = quality_dimension_suggestion(dimension)
            self.assertNotEqual(suggestion, FALLBACK_SUGGESTION)

    def test_all_script_quality_dimensions_have_skill_ids(self):
        for dimension in ScriptQualityDimension.values:
            skill_id = quality_dimension_skill_id(dimension)
            self.assertTrue(skill_id.startswith("quality-"))

    def test_pattern_description_uses_chinese_for_hook(self):
        desc = self.service._generate_pattern_description(
            ScriptQualityDimension.HOOK,
            {"count": 5, "avg_score": 62.5},
        )
        self.assertIn("钩子", desc)
        self.assertNotIn("hook", desc)

    def test_pattern_description_uses_chinese_for_reversal(self):
        desc = self.service._generate_pattern_description(
            ScriptQualityDimension.REVERSAL,
            {"count": 4, "avg_score": 55.0},
        )
        self.assertIn("反转", desc)

    def test_pattern_description_uses_chinese_for_structure(self):
        desc = self.service._generate_pattern_description(
            ScriptQualityDimension.STRUCTURE,
            {"count": 3, "avg_score": 60.0},
        )
        self.assertIn("结构", desc)

    def test_unknown_dimension_falls_back_gracefully(self):
        label = quality_dimension_label("unknown_dim")
        self.assertEqual(label, "unknown_dim")
        suggestion = quality_dimension_suggestion("unknown_dim")
        self.assertEqual(suggestion, FALLBACK_SUGGESTION)
