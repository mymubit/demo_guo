# -*- coding: utf-8 -*-
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.utils import timezone

from apps.creation.models import AgentExecutionRun, Project
from apps.creation.services import CreationService

User = get_user_model()


class WorkDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900002201", password="test-pass-123")
        self.other = User.objects.create_user(phone="13900002202", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="待删作品",
            theme="sweet-pet",
            episode_count=80,
        )

    def test_delete_user_project(self):
        pid = str(self.project.id)
        result = CreationService.delete_user_project(pid, self.user)
        self.assertTrue(result.get("deleted"))
        self.assertFalse(Project.objects.filter(id=pid).exists())

    def test_delete_running_blocked(self):
        from apps.drama.models import DramaRoleExecution

        self.project.track_mode = "fast"
        self.project.pipeline_mode = Project.MODE_WORKSPACE
        self.project.save(update_fields=["track_mode", "pipeline_mode"])
        DramaRoleExecution.objects.create(
            project=self.project,
            agent_id="drama.topic-planner",
            agent_name_zh="选题策划官",
            status=DramaRoleExecution.Status.RUNNING,
            started_at=timezone.now(),
        )
        with self.assertRaises(PermissionDenied):
            CreationService.delete_user_project(str(self.project.id), self.user)

    def test_delete_stale_drama_execution_without_started_at(self):
        from apps.drama.models import DramaRoleExecution

        self.project.track_mode = "fast"
        self.project.pipeline_mode = Project.MODE_WORKSPACE
        self.project.save(update_fields=["track_mode", "pipeline_mode"])
        exec_obj = DramaRoleExecution.objects.create(
            project=self.project,
            agent_id="drama.topic-planner",
            agent_name_zh="选题策划官",
            status=DramaRoleExecution.Status.RUNNING,
        )
        DramaRoleExecution.objects.filter(id=exec_obj.id).update(
            created_at=timezone.now() - timedelta(minutes=30),
        )
        pid = str(self.project.id)
        result = CreationService.delete_user_project(pid, self.user)
        self.assertTrue(result.get("deleted"))
        self.assertFalse(Project.objects.filter(id=pid).exists())

    def test_delete_stale_workspace_running_unlocks(self):
        from apps.creation.models import AgentExecutionRun

        self.project.pipeline_mode = Project.MODE_WORKSPACE
        run = AgentExecutionRun.objects.create(
            project=self.project,
            user=self.user,
            agent_id="drama.topic-planner",
            node_index=2,
            status=AgentExecutionRun.STATUS_RUNNING,
            started_at=timezone.now() - timedelta(minutes=20),
        )
        pid = str(self.project.id)
        result = CreationService.delete_user_project(pid, self.user)
        self.assertTrue(result.get("deleted"))
        self.assertFalse(Project.objects.filter(id=pid).exists())

    def test_delete_other_user_forbidden(self):
        with self.assertRaises(PermissionDenied):
            CreationService.delete_user_project(str(self.project.id), self.other)
