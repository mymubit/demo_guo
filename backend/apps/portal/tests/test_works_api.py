# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.creation.artifact_service import save_artifact
from apps.creation.models import AgentExecutionRun, Project

User = get_user_model()


class PortalWorksApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone="13900008902", password="test-pass-123")
        self.other = User.objects.create_user(phone="13900008903", password="test-pass-123")
        self.client.force_authenticate(user=self.user)
        self.completed = Project.objects.create(
            user=self.user,
            title="completed-work",
            theme="sweet-pet",
            episode_count=10,
        )
        save_artifact(
            self.completed,
            "episode_scripts",
            {"episodes": [{"episodeNumber": 1, "title": "ep1", "full_script_text": "done"}]},
        )
        self.running = Project.objects.create(
            user=self.user,
            title="running-work",
            theme="overbearing-ceo",
            episode_count=20,
        )
        AgentExecutionRun.objects.create(
            project=self.running,
            user=self.user,
            agent_id="drama.topic-planner",
            status=AgentExecutionRun.STATUS_RUNNING,
            run_params={},
        )
        Project.objects.create(
            user=self.other,
            title="other-user-work",
            theme="sweet-pet",
            episode_count=5,
        )

    def test_works_list_paginated_with_data_and_pagination(self):
        resp = self.client.get("/api/works/?page=1&page_size=10")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.assertIn("pagination", resp.data)
        self.assertEqual(resp.data["pagination"]["total"], 2)
        self.assertIsInstance(resp.data["data"], list)
        self.assertTrue(all("project_id" in item for item in resp.data["data"]))

    def test_works_list_status_filter(self):
        resp = self.client.get("/api/works/?status=completed")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        statuses = {item["status"] for item in resp.data["data"]}
        self.assertEqual(statuses, {Project.STATUS_COMPLETED})
        project_ids = {item["project_id"] for item in resp.data["data"]}
        self.assertIn(str(self.completed.id), project_ids)

    def test_works_list_empty_for_other_user_scope(self):
        resp = self.client.get("/api/works/")
        project_ids = {item["project_id"] for item in resp.data["data"]}
        self.assertNotIn(str(Project.objects.filter(user=self.other).first().id), project_ids)

    def test_works_list_requires_auth(self):
        client = APIClient()
        resp = client.get("/api/works/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 401)

    def test_works_scope_drama_matches_drama_project_list(self):
        pid = "66666666-6666-6666-6666-666666666666"
        Project.objects.create(
            id=pid,
            user=self.user,
            title="drama-linked",
            theme="sweet-pet",
            episode_count=12,
            track_mode="fast",
            pipeline_mode=Project.MODE_WORKSPACE,
            creation_entry="from-scratch",
            core_idea="drama test",
        )

        works_resp = self.client.get("/api/works/?scope=drama&page_size=50")
        drama_resp = self.client.get("/api/drama/projects/")

        self.assertEqual(works_resp.status_code, 200)
        self.assertEqual(drama_resp.status_code, 200)
        works_ids = {item["project_id"] for item in works_resp.data["data"]}
        drama_ids = {item["project_id"] for item in drama_resp.data["data"]}
        self.assertIn(pid, works_ids)
        self.assertEqual(works_ids, drama_ids)
        works_item = next(item for item in works_resp.data["data"] if item["project_id"] == pid)
        drama_item = next(item for item in drama_resp.data["data"] if item["project_id"] == pid)
        self.assertEqual(works_item["completion_rate"], drama_item["completion_rate"])
        self.assertEqual(works_item["progress_percent"], drama_item["progress_percent"])
