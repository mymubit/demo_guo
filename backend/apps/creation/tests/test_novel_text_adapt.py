# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.models import Project
from apps.creation.services.submission import submit

User = get_user_model()

NOVEL_BODY = "第一章 女主重生回到豪门。" * 20


class NovelTextAdaptInputTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.user = User.objects.create_user(phone="13900008911", password="test-pass-123")

    @patch("apps.billing.services.BillingService.charge")
    @patch("apps.billing.services.BillingService.ensure_can_create")
    @patch("apps.creation.services.submission.MembershipService.get_current_membership", return_value=None)
    def test_submit_persists_novel_text_on_project(
        self,
        _mock_membership,
        _mock_can_create,
        _mock_charge,
    ):
        project, _ = submit(
            self.user,
            {
                "theme": "overbearing-ceo",
                "core_idea": NOVEL_BODY[:200],
                "episode_count": 20,
                "format_variant": "B",
                "creation_entry": "novel-adaptation",
                "novel_text": NOVEL_BODY,
                "target_platform": "douyin",
            },
        )
        project.refresh_from_db()
        self.assertEqual(project.novel_text, NOVEL_BODY)
        self.assertEqual(project.creation_entry, "novel-adaptation")

    def test_build_agent_input_includes_novel_text_for_adapt(self):
        project = Project.objects.create(
            user=self.user,
            title="adapt-input",
            theme="overbearing-ceo",
            core_idea="改编测试",
            episode_count=20,
            format_variant="B",
            novel_text=NOVEL_BODY,
            creation_entry="novel-adaptation",
            status=Project.STATUS_PENDING,
        )
        agent = AgentDefinitionService.get_runnable("adapt")
        payload = IndependentAgentService.build_agent_input(project, agent, {})
        self.assertEqual(payload["project"]["novel_text"], NOVEL_BODY)
