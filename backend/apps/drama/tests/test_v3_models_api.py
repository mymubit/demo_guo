# -*- coding: utf-8 -*-
"""W5 Task 4：Models REST（providers + role-mappings）脱敏与 CRUD。"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.drama.api.v3.models_service import V3_ROLE_MODEL_KEYS
from apps.drama.models import DramaLlmProvider, V3RoleModelMapping
from apps.drama.services.secret_crypto import decrypt_secret, encrypt_secret

_PROVIDERS = "/api/v3/models/providers/"
_MAPPINGS = "/api/v3/models/role-mappings/"


class V3ModelsApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="models_api", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)

    def _create_via_api(self, **overrides) -> dict:
        payload = {
            "name": "test-provider",
            "base_url": "https://llm.example/v1",
            "model_name": "gpt-test",
            "api_key": "sk-secret-value-never-return",
            "temperature": 0.5,
            "max_tokens": 2048,
            "remark": "unit",
        }
        payload.update(overrides)
        resp = self.client.post(_PROVIDERS, payload, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        return body["data"]

    def test_create_and_list_never_returns_api_key(self) -> None:
        created = self._create_via_api()
        self.assertNotIn("api_key", created)
        self.assertTrue(created["api_key_set"])
        self.assertEqual(created["name"], "test-provider")

        listed = self.client.get(_PROVIDERS)
        self.assertEqual(listed.status_code, 200)
        items = listed.json()["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertNotIn("api_key", items[0])
        self.assertTrue(items[0]["api_key_set"])
        # 密文已落库且可解密
        obj = DramaLlmProvider.objects.get(pk=created["id"])
        self.assertEqual(
            decrypt_secret(obj.api_key_encrypted),
            "sk-secret-value-never-return",
        )

    def test_patch_empty_api_key_does_not_overwrite(self) -> None:
        created = self._create_via_api()
        provider_id = created["id"]
        before = DramaLlmProvider.objects.get(pk=provider_id).api_key_encrypted

        resp = self.client.patch(
            f"{_PROVIDERS}{provider_id}/",
            {"name": "renamed", "api_key": ""},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["name"], "renamed")
        self.assertNotIn("api_key", data)
        self.assertTrue(data["api_key_set"])
        after = DramaLlmProvider.objects.get(pk=provider_id)
        self.assertEqual(after.api_key_encrypted, before)
        self.assertEqual(after.name, "renamed")

    def test_activate_makes_unique_active(self) -> None:
        a = self._create_via_api(name="a", api_key="sk-a")
        b = self._create_via_api(name="b", api_key="sk-b")
        resp = self.client.post(f"{_PROVIDERS}{a['id']}/activate/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["data"]["is_active"])

        resp2 = self.client.post(f"{_PROVIDERS}{b['id']}/activate/")
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(resp2.json()["data"]["is_active"])

        a_obj = DramaLlmProvider.objects.get(pk=a["id"])
        b_obj = DramaLlmProvider.objects.get(pk=b["id"])
        self.assertFalse(a_obj.is_active)
        self.assertTrue(b_obj.is_active)
        self.assertEqual(
            DramaLlmProvider.objects.filter(is_active=True).count(), 1
        )

    def test_delete_provider(self) -> None:
        created = self._create_via_api()
        provider_id = created["id"]
        resp = self.client.delete(f"{_PROVIDERS}{provider_id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["code"], 0)
        self.assertFalse(
            DramaLlmProvider.objects.filter(pk=provider_id).exists()
        )

    def test_role_mappings_put_get_and_defaults_to_active(self) -> None:
        created = self._create_via_api(name="active-one")
        provider_id = created["id"]
        self.client.post(f"{_PROVIDERS}{provider_id}/activate/")

        # 未写映射时 GET 应缺省指向 active
        got = self.client.get(_MAPPINGS)
        self.assertEqual(got.status_code, 200)
        items = got.json()["data"]["items"]
        self.assertEqual(len(items), len(V3_ROLE_MODEL_KEYS))
        for item in items:
            self.assertEqual(item["provider_id"], provider_id)
            self.assertIn(item["role_key"], V3_ROLE_MODEL_KEYS)

        # PUT 两条映射
        other = DramaLlmProvider.objects.create(
            name="other",
            base_url="https://other.example/v1",
            model_name="m2",
            api_key_encrypted=encrypt_secret("sk-other"),
        )
        put_resp = self.client.put(
            _MAPPINGS,
            {
                "items": [
                    {
                        "role_key": "drama-topic-director",
                        "provider_id": str(other.id),
                        "temperature": 0.2,
                    },
                    {
                        "role_key": "drama-script-writer",
                        "provider_id": provider_id,
                        "max_tokens": 1024,
                    },
                ]
            },
            format="json",
        )
        self.assertEqual(put_resp.status_code, 200)
        put_items = {
            i["role_key"]: i for i in put_resp.json()["data"]["items"]
        }
        self.assertEqual(
            put_items["drama-topic-director"]["provider_id"], str(other.id)
        )
        self.assertEqual(put_items["drama-topic-director"]["temperature"], 0.2)
        self.assertEqual(
            put_items["drama-script-writer"]["provider_id"], provider_id
        )
        self.assertEqual(put_items["drama-script-writer"]["max_tokens"], 1024)
        self.assertEqual(V3RoleModelMapping.objects.count(), 2)

        # 非法 role_key
        bad = self.client.put(
            _MAPPINGS,
            {
                "items": [
                    {
                        "role_key": "not-a-role",
                        "provider_id": provider_id,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(bad.status_code, 400)

    def test_unauthenticated_rejected(self) -> None:
        self.client.force_authenticate(user=None)
        resp = self.client.get(_PROVIDERS)
        self.assertIn(resp.status_code, (401, 403))

    def test_role_mappings_backup_provider_ids_put_get(self) -> None:
        primary = self._create_via_api(name="primary")
        b1 = self._create_via_api(name="backup-1", api_key="sk-b1")
        b2 = self._create_via_api(name="backup-2", api_key="sk-b2")
        role_key = "drama-topic-director"
        backup_ids = [b2["id"], b1["id"], b2["id"]]

        put_resp = self.client.put(
            _MAPPINGS,
            {
                "items": [
                    {
                        "role_key": role_key,
                        "provider_id": primary["id"],
                        "backup_provider_ids": backup_ids,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(put_resp.status_code, 200, put_resp.content)
        put_item = {
            i["role_key"]: i for i in put_resp.json()["data"]["items"]
        }[role_key]
        self.assertEqual(
            put_item["backup_provider_ids"], [b2["id"], b1["id"]]
        )

        got = self.client.get(_MAPPINGS)
        self.assertEqual(got.status_code, 200)
        got_item = {
            i["role_key"]: i for i in got.json()["data"]["items"]
        }[role_key]
        self.assertEqual(
            got_item["backup_provider_ids"], [b2["id"], b1["id"]]
        )

        mapping = V3RoleModelMapping.objects.get(role_key=role_key)
        self.assertEqual(mapping.backup_provider_ids, [b2["id"], b1["id"]])

    def test_role_mappings_primary_in_backup_rejected(self) -> None:
        primary = self._create_via_api(name="primary")
        backup = self._create_via_api(name="backup", api_key="sk-backup")
        resp = self.client.put(
            _MAPPINGS,
            {
                "items": [
                    {
                        "role_key": "drama-topic-director",
                        "provider_id": primary["id"],
                        "backup_provider_ids": [backup["id"], primary["id"]],
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_role_mappings_backup_provider_ids_validation(self) -> None:
        primary = self._create_via_api(name="primary")
        backups = [
            self._create_via_api(name=f"backup-{i}", api_key=f"sk-{i}")
            for i in range(6)
        ]
        too_many = self.client.put(
            _MAPPINGS,
            {
                "items": [
                    {
                        "role_key": "drama-topic-director",
                        "provider_id": primary["id"],
                        "backup_provider_ids": [b["id"] for b in backups],
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(too_many.status_code, 400)

        missing_id = "00000000-0000-0000-0000-000000000099"
        missing = self.client.put(
            _MAPPINGS,
            {
                "items": [
                    {
                        "role_key": "drama-topic-director",
                        "provider_id": primary["id"],
                        "backup_provider_ids": [missing_id],
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(missing.status_code, 400)

    def test_role_mappings_default_includes_empty_backup_provider_ids(self) -> None:
        created = self._create_via_api(name="active-one")
        self.client.post(f"{_PROVIDERS}{created['id']}/activate/")
        got = self.client.get(_MAPPINGS)
        self.assertEqual(got.status_code, 200)
        for item in got.json()["data"]["items"]:
            self.assertEqual(item["backup_provider_ids"], [])
