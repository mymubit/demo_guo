# -*- coding: utf-8 -*-
"""工作流命令幂等与门禁测试。"""
from django.test import TestCase, override_settings

from apps.core.exceptions import IDEMPOTENCY_CONFLICT, WORKFLOW_GATE_BLOCKED
from apps.drama.services.workflow_service import WorkflowService
from apps.drama.tests.helpers import create_project, create_user


@override_settings(DRAMA_SKILLS_ROOT="/workspace", LLM_ENABLED=False)
class WorkflowServiceTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.project = create_project(self.user)
        self.svc = WorkflowService()

    def test_apply_project_brief_completed(self):
        state = self.svc.apply_command(
            self.project,
            command_id="cmd-1",
            event="project_brief_completed",
            expected_version=0,
            actor=self.user.username,
        )
        self.assertEqual(state["current_phase"], "blueprint")

    def test_idempotent_command(self):
        first = self.svc.apply_command(
            self.project,
            command_id="cmd-idem",
            event="project_brief_completed",
            expected_version=0,
            actor=self.user.username,
        )
        second = self.svc.apply_command(
            self.project,
            command_id="cmd-idem",
            event="project_brief_completed",
            expected_version=0,
            actor=self.user.username,
        )
        self.assertEqual(first["version"], second["version"])

    def test_idempotency_conflict(self):
        from apps.core.exceptions import BusinessException

        self.svc.apply_command(
            self.project,
            command_id="cmd-conflict",
            event="project_brief_completed",
            expected_version=0,
            actor=self.user.username,
        )
        with self.assertRaises(BusinessException) as ctx:
            self.svc.apply_command(
                self.project,
                command_id="cmd-conflict",
                event="story_bible_completed",
                expected_version=1,
                actor=self.user.username,
            )
        self.assertEqual(ctx.exception.code, IDEMPOTENCY_CONFLICT)

    def test_workflow_gate_blocked(self):
        from apps.core.exceptions import BusinessException

        with self.assertRaises(BusinessException) as ctx:
            self.svc.apply_command(
                self.project,
                command_id="cmd-bad",
                event="quality_passed",
                expected_version=0,
                actor=self.user.username,
            )
        self.assertEqual(ctx.exception.code, WORKFLOW_GATE_BLOCKED)

    def test_user_decision_accept_current(self):
        wf = self.project.workflow_state
        state = dict(wf.state)
        state["status"] = "waiting_user"
        state["current_phase"] = "quality"
        state["pending_user_options"] = [
            "accept_current",
            "manual_revision",
            "abandon_batch",
        ]
        wf.state = state
        wf.save(update_fields=["state"])

        next_state = self.svc.apply_command(
            self.project,
            command_id="cmd-user-accept",
            event="accept_current",
            expected_version=wf.version,
            actor=self.user.username,
        )
        self.assertEqual(next_state["current_phase"], "writing")
        self.assertEqual(next_state["status"], "active")
