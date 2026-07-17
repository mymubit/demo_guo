# -*- coding: utf-8 -*-
"""任务级 LLM 日志：服务层隔离与外部评测任务访问权限。"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, override_settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.drama.services.llm_call_log_service import LlmCallLogService
from apps.drama.views import GenerationJobLlmCallLogListView, _assert_job_access


def _external_job(*, owner_id: int, owner_username: str = "owner") -> MagicMock:
    job = MagicMock()
    job.id = uuid.uuid4()
    job.project_id = None
    job.owner_id = owner_id
    job.request_payload = {"actor": owner_username}
    return job


@override_settings(DRAMA_SKILLS_ROOT="/tmp/drama-skills", LLM_ENABLED=False)
class JobLlmLogServiceTests(SimpleTestCase):
    @patch("apps.drama.services.llm_call_log_service.DramaLlmCallLog.objects")
    def test_list_for_job_returns_only_that_job_logs(self, mock_objects: MagicMock) -> None:
        job_a = _external_job(owner_id=1)
        job_b = _external_job(owner_id=1)
        log_a = MagicMock(generation_job_id=job_a.id)
        log_b = MagicMock(generation_job_id=job_b.id)

        chain = mock_objects.select_related.return_value
        filtered = chain.filter.return_value
        filtered.order_by.return_value.__getitem__.side_effect = (
            lambda key: [log_a] if filtered.filter.call_args is None else [log_b]
        )

        def filter_side_effect(**kwargs):
            if kwargs.get("generation_job") is job_a:
                qs = MagicMock()
                qs.order_by.return_value.__getitem__ = MagicMock(return_value=[log_a])
                qs.filter.return_value = qs
                return qs
            qs = MagicMock()
            qs.order_by.return_value.__getitem__ = MagicMock(return_value=[log_b])
            qs.filter.return_value = qs
            return qs

        chain.filter.side_effect = filter_side_effect

        items_a = list(LlmCallLogService.list_for_job(job_a))
        items_b = list(LlmCallLogService.list_for_job(job_b))

        chain.filter.assert_any_call(generation_job=job_a)
        chain.filter.assert_any_call(generation_job=job_b)
        self.assertEqual([log_a], items_a)
        self.assertEqual([log_b], items_b)
        self.assertTrue(all(log.generation_job_id == job_a.id for log in items_a))
        self.assertTrue(all(log.generation_job_id == job_b.id for log in items_b))


@override_settings(DRAMA_SKILLS_ROOT="/tmp/drama-skills", LLM_ENABLED=False)
class AssertJobAccessTests(SimpleTestCase):
    def test_owner_can_access_external_job(self) -> None:
        request = MagicMock()
        request.user = MagicMock(id=7, username="owner")
        job = _external_job(owner_id=7, owner_username="owner")
        _assert_job_access(request, job)

    def test_actor_username_can_access_external_job(self) -> None:
        request = MagicMock()
        request.user = MagicMock(id=99, username="actor-user")
        job = _external_job(owner_id=7, owner_username="actor-user")
        _assert_job_access(request, job)

    def test_other_user_cannot_access_external_job(self) -> None:
        request = MagicMock()
        request.user = MagicMock(id=2, username="intruder")
        job = _external_job(owner_id=1, owner_username="owner")
        with self.assertRaises(PermissionDenied):
            _assert_job_access(request, job)


@override_settings(DRAMA_SKILLS_ROOT="/tmp/drama-skills", LLM_ENABLED=False)
class JobLlmLogAccessApiTests(SimpleTestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.owner = User(id=1, username="review-owner")
        self.other = User(id=2, username="review-other")

    @patch("apps.drama.views.LlmCallLogService.serialize_detail")
    @patch("apps.drama.views.LlmCallLogService.list_for_job")
    @patch("apps.drama.views.get_object_or_404")
    def test_owner_can_list_external_job_logs(
        self,
        mock_get_job: MagicMock,
        mock_list_for_job: MagicMock,
        mock_serialize: MagicMock,
    ) -> None:
        job = _external_job(owner_id=self.owner.id, owner_username=self.owner.username)
        mock_get_job.return_value = job
        log = MagicMock()
        mock_list_for_job.return_value = [log]
        mock_serialize.return_value = {
            "id": str(uuid.uuid4()),
            "user_prompt": "prompt-1",
            "response_text": "response-1",
        }

        request = self.factory.get(f"/api/v1/drama/jobs/{job.id}/llm-logs/?detail=1")
        force_authenticate(request, user=self.owner)
        response = GenerationJobLlmCallLogListView.as_view()(request, job_id=str(job.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 0)
        items = response.data["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["user_prompt"], "prompt-1")
        self.assertEqual(items[0]["response_text"], "response-1")
        mock_list_for_job.assert_called_once()

    @patch("apps.drama.views.get_object_or_404")
    def test_other_user_cannot_list_external_job_logs(self, mock_get_job: MagicMock) -> None:
        job = _external_job(owner_id=self.owner.id, owner_username=self.owner.username)
        mock_get_job.return_value = job

        request = self.factory.get(f"/api/v1/drama/jobs/{job.id}/llm-logs/")
        force_authenticate(request, user=self.other)
        response = GenerationJobLlmCallLogListView.as_view()(request, job_id=str(job.id))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], 403)
