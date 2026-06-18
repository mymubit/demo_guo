# -*- coding: utf-8 -*-
"""Fusion Pack Admin API 已随 main-chain 路由下线。"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class FusionPipelinePackAdminApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser(
            phone="13900007701",
            password="test-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_main_chain_fusion_packs_returns_404(self):
        res = self.client.get("/api/admin/main-chain/fusion/packs/")
        self.assertEqual(res.status_code, 404)
