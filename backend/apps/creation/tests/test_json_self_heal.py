# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.models import AgentLlmRouteConfig, AgentDefinition
from apps.creation.agent_runtime.independent_service import AgentRuntimeError, extract_json_object
from apps.creation.agent_runtime.json_self_heal import parse_json_with_self_heal
from apps.creation.models import Project

User = get_user_model()


class JsonSelfHealTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.agent = AgentDefinition.objects.get(agent_id="brief")

    @patch("apps.creation.agent_runtime.json_self_heal.LlmService.chat_completion")
    def test_self_heal_repairs_invalid_json(self, mock_chat):
        mock_chat.return_value = '{"artifact_key":"project_brief","payload":{"theme":"x"}}'
        raw = "not json at all"
        parsed, attempts = parse_json_with_self_heal(
            raw,
            agent=self.agent,
            system_prompt="sys",
            user_prompt="user",
            temperature=0.1,
            max_tokens=1024,
            provider_id=None,
        )
        self.assertEqual(attempts, 1)
        self.assertIn("payload", parsed)

    def test_valid_json_skips_heal(self):
        raw = '{"artifact_key":"project_brief","payload":{"theme":"ok"}}'
        parsed, attempts = parse_json_with_self_heal(
            raw,
            agent=self.agent,
            system_prompt="sys",
            user_prompt="user",
            temperature=0.1,
            max_tokens=1024,
            provider_id=None,
        )
        self.assertEqual(attempts, 0)
        self.assertEqual(parsed["payload"]["theme"], "ok")
