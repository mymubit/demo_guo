# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.creation.trend_formula import (
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
