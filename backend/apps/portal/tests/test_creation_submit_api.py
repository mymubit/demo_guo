# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.billing.services import InsufficientCoins
from apps.creation.models import Project

User = get_user_model()


class PortalCreationSubmitApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone="13900008901", password="test-pass-123")
        self.client.force_authenticate(user=self.user)

    def _payload(self, **overrides):
        data = {
            "theme": "overbearing-ceo",
            "core_idea": "一个被误解的女主重回豪门，在权力与情感夹缝中反击。",
            "episode_count": 20,
            "format_variant": "B",
            "target_platform": "douyin",
            "budget_level": "medium",
            "pipeline_mode": Project.MODE_WORKSPACE,
        }
        data.update(overrides)
        return data

    def test_submit_invalid_payload_returns_validation_error(self):
        resp = self.client.post("/api/creation/submit/", {"theme": "x"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 4001)

    def test_submit_unauthenticated_returns_401(self):
        client = APIClient()
        resp = client.post("/api/creation/submit/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 401)

    @patch("apps.creation.workspace.workspace_service.finalize_workspace_brief")
    @patch("apps.creation.services.submission.get_skill_invoker")
    @patch("apps.creation.services.submission.MembershipService.get_current_membership", return_value=None)
    @patch("apps.billing.services.BillingService.charge")
    @patch("apps.billing.services.BillingService.ensure_can_create")
    def test_submit_success_returns_project_id(
        self,
        _mock_can_create,
        _mock_charge,
        _mock_membership,
        mock_invoker_factory,
        _mock_finalize,
    ):
        # 新引擎：SkillInvoker 成功即可通过 adapt 校验
        mock_invoker = mock_invoker_factory.return_value
        skill_result = MagicMock()
        skill_result.success = True
        skill_result.data = {"adapted": True}
        skill_result.error = {}
        skill_result.skill_id = "creation.adapt"
        skill_result.trace_id = "trace-1"
        mock_invoker.invoke.return_value = skill_result

        resp = self.client.post("/api/creation/submit/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.assertIn("project_id", resp.data["data"])
        self.assertIn("estimated_minutes", resp.data["data"])

    @patch("apps.creation.workspace.workspace_service.finalize_workspace_brief")
    @patch("apps.creation.services.submission.get_skill_invoker")
    @patch("apps.creation.services.submission.MembershipService.get_current_membership", return_value=None)
    @patch("apps.billing.services.BillingService.charge")
    @patch("apps.billing.services.BillingService.ensure_can_create")
    def test_submit_insufficient_coins_returns_forbidden(
        self,
        _mock_can_create,
        mock_charge,
        _mock_membership,
        mock_invoker_factory,
        _mock_finalize,
    ):
        mock_invoker = mock_invoker_factory.return_value
        skill_result = MagicMock()
        skill_result.success = True
        skill_result.data = {"adapted": True}
        skill_result.error = {}
        skill_result.skill_id = "creation.adapt"
        skill_result.trace_id = "trace-2"
        mock_invoker.invoke.return_value = skill_result

        mock_charge.side_effect = InsufficientCoins("创作币不足")
        resp = self.client.post("/api/creation/submit/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 403)
