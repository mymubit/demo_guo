# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

User = get_user_model()


class PortalBillingCatalogApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone="13900008902", password="test-pass-123")
        self.client.force_authenticate(user=self.user)

    @override_settings(ALLOW_MOCK_PAYMENT=False, DEBUG=True)
    def test_catalog_returns_payment_method_when_mock_payment_disabled(self):
        resp = self.client.get("/api/billing/catalog/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.assertIn("payment_method", resp.data["data"])
        self.assertEqual(resp.data["data"]["payment_method"], "mock")
