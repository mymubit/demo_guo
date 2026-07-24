# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.drama.services.skills_loader import SkillsBundleLoader
from apps.drama.tests.helpers import SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class FewshotPolicyTests(SimpleTestCase):
    def test_load_fewshots_respects_role_max_shots(self):
        loader = SkillsBundleLoader()
        role = "drama.topic-director"
        real = loader.get_role_contract(role)
        patched = {**real, "fewshot_policy": {"max_shots": 1}}
        with patch.object(loader, "get_role_contract", return_value=patched):
            text = loader.load_fewshots(role)
        self.assertIn("1. input=", text)
        self.assertNotIn("\n2. input=", text)

    def test_explicit_max_shots_overrides_policy(self):
        loader = SkillsBundleLoader()
        role = "drama.topic-director"
        real = loader.get_role_contract(role)
        patched = {**real, "fewshot_policy": {"max_shots": 1}}
        with patch.object(loader, "get_role_contract", return_value=patched):
            text = loader.load_fewshots(role, max_shots=2)
        self.assertIn("\n2. input=", text)
