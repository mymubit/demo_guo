# -*- coding: utf-8 -*-
from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from apps.drama.services.injection_manifest import (
    CANONICAL_LAYER_NAMES,
    canonical_layer_name,
    normalize_layers,
)
from apps.drama.services.skills_loader import resolve_seed_path
from apps.drama.tests.helpers import SKILLS_ROOT


class ManifestLayerCanonicalTests(SimpleTestCase):
    def test_aliases(self) -> None:
        self.assertEqual(canonical_layer_name("scoring"), "scoring_inline")
        self.assertEqual(canonical_layer_name("anti_examples"), "anti")
        self.assertIn("scoring_inline", CANONICAL_LAYER_NAMES)

    def test_normalize_merges_aliases(self) -> None:
        layers = normalize_layers(
            {
                "scoring": {"chars": 10, "truncated": False},
                "scoring_inline": {"chars": 20, "truncated": True},
            }
        )
        self.assertEqual(set(layers), {"scoring_inline"})
        self.assertEqual(layers["scoring_inline"]["chars"], 20)


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class SeedPathAliasTests(SimpleTestCase):
    def test_constraints_presets_alias_to_presets_dir(self) -> None:
        self.assertEqual(
            resolve_seed_path("foundation/constraints/scoring-presets.yaml"),
            "foundation/presets/scoring-presets.yaml",
        )
        self.assertEqual(
            resolve_seed_path("foundation/presets/scoring-presets.yaml"),
            "foundation/presets/scoring-presets.yaml",
        )
