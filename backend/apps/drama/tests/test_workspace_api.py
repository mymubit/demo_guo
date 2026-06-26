# -*- coding: utf-8 -*-
"""Drama 工作区 API 单元测试 - 角色列表 / 创建项目 / 进度查询"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.models import AgentDefinition
from apps.creation.models import Project
from apps.drama.defaults import DRAMA_FAST_TRACK_ROLES, DRAMA_VISIBLE_ROLES
from apps.drama.services import DramaRoleRunService, DramaRoleService

User = get_user_model()


def _create_drama_project(user, **kwargs):
    pid = kwargs.pop("id", None) or kwargs.pop("project_id", None)
    defaults = {
        "user": user,
        "title": "test-project",
        "theme": "family-revenge",
        "episode_count": 30,
        "track_mode": "fast",
        "pipeline_mode": Project.MODE_WORKSPACE,
        "creation_entry": "from-scratch",
        "core_idea": "test",
    }
    defaults.update(kwargs)
    if pid:
        defaults["id"] = pid
    return Project.objects.create(**defaults)


class DramaWorkspaceApiTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.user = User.objects.create_user(phone="13900008801", password="test-pass-123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_roles_api_returns_reorganized_visible_roles(self):
        resp = self.client.get("/api/drama/roles/")
        self.assertEqual(resp.status_code, 200)
        body = resp.data
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertEqual(data["total_roles"], 9)
        self.assertEqual(data["visible_roles"], 9)
        self.assertEqual(data["fast_track_count"], 8)
        self.assertEqual(data["composite_count"], 1)

        role_ids = {
            role["agent_id"]
            for dept in data["departments"]
            for role in dept["roles"]
        }
        self.assertEqual(role_ids, set(DRAMA_VISIBLE_ROLES))

        tier2 = [
            role for dept in data["departments"] for role in dept["roles"] if role.get("tier") == 2
        ]
        self.assertEqual(len(tier2), 1)
        self.assertTrue(all(role.get("is_composite") for role in tier2))

    def test_theme_matrix_api_returns_ssot_config(self):
        resp = self.client.get("/api/drama/theme-matrix/")
        self.assertEqual(resp.status_code, 200)
        body = resp.data
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertEqual(len(data["dim_order"]), 4)
        self.assertEqual(len(data["axes"]["emotion"]["options"]), 9)
        self.assertGreaterEqual(len(data["preset_templates"]), 8)
        self.assertGreaterEqual(len(data["featured_combos"]), 32)
        preset_codes = {item["code"] for item in data["preset_templates"]}
        self.assertIn("family-revenge", preset_codes)
        combo = data["featured_combos"][0]
        self.assertTrue(combo["code"])
        self.assertTrue(combo["label"])
        self.assertIn("emotion", combo["dims"])
        flavor = data["flavor_tags"]
        self.assertGreaterEqual(len(flavor["options"]), 60)
        self.assertGreaterEqual(len(flavor["groups"]), 10)
        self.assertEqual(flavor["max_select"], 5)

    def test_theme_matrix_api_requires_auth(self):
        client = APIClient()
        resp = client.get("/api/drama/theme-matrix/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 401)

    def test_create_project_accepts_matrix_theme(self):
        theme = "healing-ordinary-workplace-modern"
        resp = self.client.post(
            "/api/drama/projects/",
            {
                "title": "workspace-test",
                "theme": theme,
                "episode_count": 40,
                "target_platform": "douyin",
                "track_mode": "fast",
                "core_idea": "职场治愈测试创意",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["code"], 0)
        project_id = resp.data["data"]["id"]
        project = Project.objects.get(id=project_id)
        self.assertEqual(project.theme, theme)

    def test_progress_includes_optional_tool_role(self):
        pid = "33333333-3333-3333-3333-333333333333"
        project = _create_drama_project(
            self.user,
            id=pid,
            title="progress-test",
            theme="custom",
            episode_count=10,
            track_mode="fast",
        )
        resp = self.client.get(f"/api/drama/projects/{project.id}/progress/")
        self.assertEqual(resp.status_code, 200)
        roles = resp.data["data"]["roles"]
        role_ids = {item["agent_id"] for item in roles}
        self.assertEqual(role_ids, set(DRAMA_VISIBLE_ROLES))
        optional_tools = [r for r in roles if r["tier"] == 2]
        self.assertEqual(len(optional_tools), 1)

    def test_ensure_visible_roles_creates_missing_optional_agent(self):
        AgentDefinition.objects.filter(
            agent_id__in=[
                "drama.delivery-tool",
            ]
        ).delete()
        self.assertEqual(
            AgentDefinition.objects.filter(agent_id__in=DRAMA_VISIBLE_ROLES).count(),
            8,
        )
        DramaRoleService.ensure_visible_roles()
        self.assertEqual(
            AgentDefinition.objects.filter(agent_id__in=DRAMA_VISIBLE_ROLES).count(),
            9,
        )

    def test_run_role_enqueues_execution(self):
        from unittest.mock import patch

        pid = "44444444-4444-4444-4444-444444444444"
        project = _create_drama_project(
            self.user,
            id=pid,
            title="run-test",
            theme="custom",
            episode_count=10,
            track_mode="fast",
        )
        with patch(
            "apps.drama.services.DramaRoleRunService.enqueue_role_run",
            wraps=DramaRoleRunService.enqueue_role_run,
        ) as mock_enqueue:
            with patch(
                "apps.drama.services.DramaRoleRunService.execute_role",
                return_value={"status": "success"},
            ):
                with self.settings(DRAMA_ROLE_RUN_SYNC=True):
                    resp = self.client.post(
                        f"/api/drama/projects/{project.id}/run/drama.topic-director/",
                        {},
                        format="json",
                    )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        payload = resp.data["data"]
        self.assertEqual(payload["role_id"], "drama.topic-director")
        self.assertTrue(payload.get("execution_id"))
        self.assertEqual(payload.get("scope"), "\u6574\u4f53\u6267\u884c")
        mock_enqueue.assert_called_once()

    def test_fast_track_core_roles_count(self):
        grouped = DramaRoleService.get_all_roles_grouped()
        fast_track = [
            role
            for dept in grouped
            for role in dept["roles"]
            if role["agent_id"] in DRAMA_FAST_TRACK_ROLES
        ]
        self.assertEqual(len(fast_track), 8)

    def test_completion_rate_ignores_legacy_roles_and_caps_at_100(self):
        pid = "55555555-5555-5555-5555-555555555555"
        legacy_roles = [f"drama.legacy-role-{i}" for i in range(30)]
        project = _create_drama_project(
            self.user,
            id=pid,
            title="rate-test",
            theme="custom",
            episode_count=10,
            track_mode="expert",
            completed_roles=legacy_roles + list(DRAMA_FAST_TRACK_ROLES),
        )
        rate = project.get_completion_rate()
        self.assertLessEqual(rate, 100.0)
        self.assertGreater(rate, 0.0)

        from apps.drama.progress_service import DramaProgressService

        DramaProgressService.recompute_project_state(project)
        project.refresh_from_db()
        self.assertLessEqual(len(project.completed_roles), len(DRAMA_VISIBLE_ROLES))
