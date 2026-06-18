# -*- coding: utf-8 -*-
import os
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.creation.library.models import ReferenceMaterial


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class LibraryMaterialApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            phone="13900008801",
            password="admin-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.base_url = "/api/admin/creation/library/materials"

    def _create_material(self, name="测试素材"):
        fd, file_path = tempfile.mkstemp(suffix=".txt")
        os.write(fd, b"sample content")
        os.close(fd)
        return ReferenceMaterial.objects.create(
            user=self.admin,
            name=name,
            material_type=ReferenceMaterial.TYPE_OTHER,
            file_path=file_path,
            file_size=14,
            parse_status=ReferenceMaterial.STATUS_READY,
        )

    def test_get_material_detail(self):
        material = self._create_material()
        response = self.client.get(f"{self.base_url}/{material.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 0)
        self.assertEqual(response.data["data"]["id"], str(material.id))
        self.assertEqual(response.data["data"]["name"], "测试素材")

    def test_delete_material_removes_record_and_file(self):
        material = self._create_material(name="待删除素材")
        file_path = material.file_path
        self.assertTrue(os.path.exists(file_path))

        response = self.client.delete(f"{self.base_url}/{material.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 0)
        self.assertFalse(ReferenceMaterial.objects.filter(pk=material.id).exists())
        self.assertFalse(os.path.exists(file_path))

    def test_delete_nonexistent_material_returns_error(self):
        import uuid

        response = self.client.delete(f"{self.base_url}/{uuid.uuid4()}/")
        self.assertNotEqual(response.data.get("code"), 0)
        self.assertIn("不存在", response.data.get("message", ""))

    def test_delete_route_not_405(self):
        """回归：DELETE 不应命中仅支持 GET 的视图返回 405。"""
        material = self._create_material(name="405回归")
        response = self.client.delete(f"{self.base_url}/{material.id}/")
        self.assertNotEqual(response.status_code, 405)
