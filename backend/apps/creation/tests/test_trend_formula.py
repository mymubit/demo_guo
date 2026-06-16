# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.creation.trend_formula import (
    apply_project_story_to_trend_formula,
    build_trend_formula,
    normalize_trend_formula,
    trend_formula_has_internal_refs,
)


class TrendFormulaTests(SimpleTestCase):
    def test_build_trend_formula_sweet_pet_readable(self):
        formula = build_trend_formula("sweet-pet", theme_display_name="甜宠")
        self.assertIn("甜宠", formula.get("themeDisplayName") or "")
        self.assertTrue(formula.get("coreConflictFormula"))
        self.assertTrue(formula.get("highlights"))
        self.assertEqual(formula.get("matchedTemplates"), [])
        for item in formula.get("highlights") or []:
            self.assertNotIn(".json", str(item))
            self.assertNotIn("参考钩子", str(item))

    def test_sample_hook_separate_from_highlights(self):
        formula = build_trend_formula("family-revenge", theme_display_name="家庭伦理复仇")
        self.assertTrue(formula.get("sampleHook"))
        for item in formula.get("highlights") or []:
            self.assertNotIn("参考钩子", str(item))

    def test_apply_project_story_overrides_display(self):
        formula = build_trend_formula("family-revenge")
        merged = apply_project_story_to_trend_formula(
            formula,
            idea="女主被婆家逼到绝境后亮出隐藏身份",
            opening_hooks="第1集：当众被赶出家门\n第2集：前夫跪求复合",
        )
        self.assertIn("隐藏身份", merged.get("projectIdea") or "")
        self.assertIn("赶出家门", merged.get("projectHook") or "")
        for item in merged.get("highlights") or []:
            self.assertNotIn("参考钩子", str(item))

    def test_normalize_strips_legacy_reference_hook_in_highlights(self):
        dirty = {
            "theme": "family-revenge",
            "highlights": ["参考钩子：全职人妻隐忍五年", "身份反转"],
        }
        clean = normalize_trend_formula(dirty, theme="family-revenge")
        self.assertEqual(clean.get("sampleHook"), "全职人妻隐忍五年")
        self.assertTrue(all("参考钩子" not in str(item) for item in clean.get("highlights") or []))

    def test_normalize_strips_internal_file_refs(self):
        dirty = {
            "theme": "sweet-pet",
            "themeDisplayName": "甜宠虐恋+强制爱",
            "matchedTemplates": [
                {"file": "hook-types-library.json", "excerpt": {"foo": "bar"}},
            ],
        }
        self.assertTrue(trend_formula_has_internal_refs(dirty))
        clean = normalize_trend_formula(dirty, theme="sweet-pet")
        self.assertFalse(trend_formula_has_internal_refs(clean))
        self.assertTrue(clean.get("coreConflictFormula") or clean.get("highlights"))
