# -*- coding: utf-8 -*-
"""InjectionManifest / PromptBuilder 三元组回归。"""
from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from apps.drama.services.injection_manifest import reconcile_ok
from apps.drama.services.prompt_builder import PromptBuilder
from apps.drama.tests.helpers import FIXTURE_SETTINGS, SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class InjectionManifestBuildTests(SimpleTestCase):
    def test_build_returns_manifest_with_layers_and_checksum(self) -> None:
        system, user, manifest = PromptBuilder().build(
            "drama.topic-director",
            settings=dict(FIXTURE_SETTINGS),
            workflow_state={},
            artifacts={},
        )
        self.assertEqual(manifest["version"], 1)
        self.assertEqual(manifest["agent_id"], "drama.topic-director")
        self.assertIn("layers", manifest)
        self.assertIn("modules", manifest)
        self.assertIn("knowledge", manifest)
        self.assertIn("rules", manifest)
        self.assertIn("policies", manifest)
        self.assertEqual(manifest["system_chars"], len(system))
        self.assertEqual(manifest["user_chars"], len(user))
        self.assertTrue(manifest["checksum"])
        self.assertTrue(reconcile_ok(manifest))
        included_ids = {m["id"] for m in manifest["modules"]["included"]}
        self.assertIn("concept-development", included_ids)

    def test_story_bible_skips_adapt_module_in_manifest(self) -> None:
        settings = dict(FIXTURE_SETTINGS)
        settings["entry_type"] = "original"
        _system, _user, manifest = PromptBuilder().build(
            "drama.story-bible",
            settings=settings,
            workflow_state={},
            artifacts={},
        )
        skipped_ids = {m["id"] for m in manifest["modules"]["skipped"]}
        self.assertIn("adaptation-originality", skipped_ids)
        reason = next(
            m["reason"]
            for m in manifest["modules"]["skipped"]
            if m["id"] == "adaptation-originality"
        )
        self.assertEqual(reason, "enable_when")
