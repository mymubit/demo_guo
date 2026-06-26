# -*- coding: utf-8 -*-
"""theme_matrix_service 单元测试。"""
from django.test import SimpleTestCase

from apps.drama.theme_matrix_service import build_matrix_theme_code, build_theme_matrix_ui_config


class ThemeMatrixServiceTests(SimpleTestCase):
    def test_build_matrix_theme_code_without_tags(self):
        code = build_matrix_theme_code(
            {"emotion": "revenge", "identity": "underdog", "conflict": "family", "world": "modern"}
        )
        self.assertEqual(code, "revenge-underdog-family-modern")

    def test_build_matrix_theme_code_with_sorted_tags(self):
        code = build_matrix_theme_code(
            {"emotion": "revenge", "identity": "underdog", "conflict": "family", "world": "modern"},
            flavor_tags=["ceo-domineering", "sweet-heavy", "female-lead"],
        )
        self.assertEqual(code, "revenge-underdog-family-modern|ceo-domineering+female-lead+sweet-heavy")

    def test_ui_config_includes_flavor_groups(self):
        config = build_theme_matrix_ui_config()
        self.assertTrue(config)
        flavor = config["flavor_tags"]
        self.assertGreaterEqual(len(flavor["options"]), 60)
        self.assertGreaterEqual(len(flavor["groups"]), 10)
        first_group = flavor["groups"][0]
        self.assertTrue(first_group["id"])
        self.assertTrue(first_group["label"])
        self.assertTrue(first_group["options"])
