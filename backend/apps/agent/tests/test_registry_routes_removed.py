# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class AgentRegistryLegacyRoutesRemovedTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            phone="13900007702",
            password="admin-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_registry_import_route_removed(self):
        resp = self.client.post("/api/admin/agent/registry/import/", {}, format="json")
        self.assertEqual(resp.status_code, 404)

    def test_registry_migrate_route_removed(self):
        resp = self.client.post("/api/admin/agent/registry/migrate/")
        self.assertEqual(resp.status_code, 404)

    def test_registry_get_still_available(self):
        resp = self.client.get("/api/admin/agent/registry/")
        self.assertEqual(resp.status_code, 200)
