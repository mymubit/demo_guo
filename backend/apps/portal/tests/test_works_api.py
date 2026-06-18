# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.creation.models import Project

User = get_user_model()


class PortalWorksApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone="13900008902", password="test-pass-123")
        self.other = User.objects.create_user(phone="13900008903", password="test-pass-123")
        self.client.force_authenticate(user=self.user)
        self.completed = Project.objects.create(
            user=self.user,
            title="已完成作品",
            theme="sweet-pet",
            episode_count=10,
            fusion_status=Project.FUSION_READY,
        )
        Project.objects.create(
            user=self.user,
            title="进行中作品",
            theme="overbearing-ceo",
            episode_count=20,
            fusion_status=Project.FUSION_WRITING,
        )
        Project.objects.create(
            user=self.other,
            title="他人作品",
            theme="sweet-pet",
            episode_count=5,
            fusion_status=Project.FUSION_READY,
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

    def test_works_list_empty_for_other_user_scope(self):
        resp = self.client.get("/api/works/")
        project_ids = {item["project_id"] for item in resp.data["data"]}
        self.assertNotIn(str(Project.objects.filter(user=self.other).first().id), project_ids)

    def test_works_list_requires_auth(self):
        client = APIClient()
        resp = client.get("/api/works/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 401)
