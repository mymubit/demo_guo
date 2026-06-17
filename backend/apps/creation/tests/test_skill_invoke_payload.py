# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.creation.models import Project
from apps.creation.skill_invoke_payload import build_creation_skill_invoke_payload


class SkillInvokePayloadTests(TestCase):
    def test_structure_payload_includes_brief_and_episode_count(self):
        project = MagicMock(spec=Project)
        project.id = "proj-1"
        project.theme = "family-revenge"
        project.core_idea = "复仇故事"
        project.audience = "女性18-35"
        project.reference_work = ""
        project.episode_count = 30
        project.target_platform = "douyin"
        project.user_id = 1

        brief = {
            "projectId": "proj-1",
            "theme": "family-revenge",
            "episodeCount": 30,
            "targetPlatform": "douyin",
            "coreHook": "复仇故事",
        }

        with patch("apps.creation.skill_invoke_payload.get_artifact", return_value=brief):
            with patch(
                "apps.creation.workspace.workspace_content.ensure_brief_seed_enriched",
                return_value=brief,
            ):
                payload = build_creation_skill_invoke_payload(project, "creation.structure")

        self.assertIn("brief", payload)
        self.assertEqual(payload["brief"]["theme"], "family-revenge")
        self.assertEqual(payload["episode_count"], 30)
        self.assertEqual(payload["target_platform"], "douyin")
        self.assertTrue(payload["skip_skill_quota"])

    def test_outline_payload_includes_upstream_artifacts(self):
        project = MagicMock(spec=Project)
        project.id = "proj-2"
        project.theme = "overbearing-ceo"
        project.core_idea = "霸总"
        project.audience = ""
        project.reference_work = ""
        project.episode_count = 80
        project.user_id = 1

        brief = {"projectId": "proj-2", "episodeCount": 80, "coreHook": "霸总"}
        structure = {"totalEpisodes": 80, "nodeId": "node-2-structure"}
        characters = {"characters": [{"name": "林晚", "roleType": "protagonist"}]}

        def fake_get_artifact(_project, key):
            return {
                "project_brief": brief,
                "structure_plan": structure,
                "character_bible": characters,
            }.get(key)

        with patch("apps.creation.skill_invoke_payload.get_artifact", side_effect=fake_get_artifact):
            with patch(
                "apps.creation.workspace.workspace_content.ensure_brief_seed_enriched",
                return_value=brief,
            ):
                payload = build_creation_skill_invoke_payload(
                    project,
                    "creation.outline",
                    script_from=1,
                    script_to=5,
                )

        self.assertEqual(payload["brief"], brief)
        self.assertEqual(payload["structure"], structure)
        self.assertEqual(len(payload["characters"]), 1)
        self.assertEqual(payload["episode_from"], 1)
        self.assertEqual(payload["episode_to"], 5)
