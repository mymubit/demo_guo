# -*- coding: utf-8 -*-
"""InjectionManifest / PromptBuilder 三元组回归。"""
from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from apps.drama.services.injection_manifest import reconcile_ok
from apps.drama.services.prompt_builder import PromptBuilder
from apps.drama.services.skills_loader import SkillsBundleLoader, get_skills_loader
from apps.drama.tests.helpers import FIXTURE_SETTINGS, SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, SKILLS_INJECTION_POLICY_ENFORCED=True)
class InjectionManifestBuildTests(SimpleTestCase):
    def setUp(self) -> None:
        get_skills_loader.cache_clear()

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
        self.assertTrue(manifest["policies"]["evaluate_enable_when"])
        self.assertTrue(manifest["policies"]["policy_enforced"])

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

    def test_delivery_skips_storyboard_without_deliverable(self) -> None:
        settings = dict(FIXTURE_SETTINGS)
        prefs = dict(settings.get("creation_preferences") or {})
        prefs["deliverables"] = ["marketing"]
        settings["creation_preferences"] = prefs
        _system, _user, manifest = PromptBuilder().build(
            "drama.delivery-tool",
            settings=settings,
            workflow_state={},
            artifacts={},
        )
        skipped = {m["id"]: m for m in manifest["modules"]["skipped"]}
        self.assertIn("storyboard-9col", skipped)
        self.assertEqual(skipped["storyboard-9col"]["reason"], "enable_when")
        included = {m["id"] for m in manifest["modules"]["included"]}
        self.assertIn("marketing-copy", included)

    def test_story_bible_knowledge_budget_truncates_when_enforced(self) -> None:
        settings = dict(FIXTURE_SETTINGS)
        _system, _user, manifest = PromptBuilder().build(
            "drama.story-bible",
            settings=settings,
            workflow_state={},
            artifacts={},
        )
        self.assertEqual(manifest["policies"]["knowledge_max_chars"], 8000)
        knowledge_chars = manifest["layers"]["knowledge"]["chars"]
        self.assertLessEqual(knowledge_chars, 8000)

    def test_all_production_roles_evaluate_enable_when(self) -> None:
        loader = SkillsBundleLoader(root=SKILLS_ROOT)
        roles = [
            "drama.topic-director",
            "drama.story-bible",
            "drama.episode-designer",
            "drama.script-writer",
            "drama.script-scorer",
            "drama.compliance-guard",
            "drama.revision-master",
            "drama.delivery-tool",
        ]
        for agent_id in roles:
            contract = loader.get_role_contract(agent_id)
            policy = contract.get("module_policy") or {}
            self.assertTrue(
                policy.get("evaluate_enable_when"),
                msg=f"{agent_id} 未开启 evaluate_enable_when",
            )


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, SKILLS_INJECTION_POLICY_ENFORCED=False)
class InjectionPolicyEscapeTests(SimpleTestCase):
    def setUp(self) -> None:
        get_skills_loader.cache_clear()

    def test_enforced_false_ignores_knowledge_budget(self) -> None:
        settings = dict(FIXTURE_SETTINGS)
        _system, _user, manifest = PromptBuilder().build(
            "drama.story-bible",
            settings=settings,
            workflow_state={},
            artifacts={},
        )
        self.assertFalse(manifest["policies"]["policy_enforced"])
        self.assertEqual(manifest["policies"]["knowledge_max_chars"], 0)
        self.assertFalse(manifest["layers"]["knowledge"]["truncated"])
