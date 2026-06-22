# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.creation.agent_runtime.agent_notes_utils import merge_agent_notes_patch, normalize_agent_notes
from apps.creation.agent_runtime.entry_plan import get_entry_plan
from apps.skill.models import AgentSkillDefinition
from apps.skill.skills.router import pick_skill_version

User = get_user_model()


class AgentNotesUtilsTests(TestCase):
    def test_merge_truncates_rejects(self):
        existing = {"rejects": [f"r{i}" for i in range(25)]}
        merged = merge_agent_notes_patch(existing, {"rejects": ["新拒绝"]})
        self.assertLessEqual(len(merged["rejects"]), 20)
        self.assertEqual(merged["rejects"][-1], "新拒绝")
        self.assertIn("last_feedback_at", merged)


class EntryPlanValidationTests(TestCase):
    @patch("apps.creation.agent_runtime.entry_plan.logger")
    def test_unknown_agent_logs_warning(self, mock_logger):
        from apps.skill.models import SkillConfigEntry

        SkillConfigEntry.objects.update_or_create(
            config_key="creation-entry-plans",
            defaults={
                "edition": "unified",
                "content": {
                    "from-scratch": {
                        "recommended_agents": ["not-a-real-agent"],
                        "hidden_agents": [],
                    }
                },
                "version": "1.0.0",
            },
        )
        get_entry_plan("from-scratch")
        mock_logger.warning.assert_called()


class PickSkillVersionTests(TestCase):
    def test_pick_active_skill(self):
        AgentSkillDefinition.objects.create(
            skill_id="test.skill.pick",
            name="Active",
            lifecycle_status=AgentSkillDefinition.LIFECYCLE_ACTIVE,
            version="1.0.0",
            content="# active",
        )
        picked = pick_skill_version("test.skill.pick", user_id=42)
        self.assertIsNotNone(picked)
        self.assertEqual(picked.lifecycle_status, AgentSkillDefinition.LIFECYCLE_ACTIVE)
