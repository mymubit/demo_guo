# -*- coding: utf-8 -*-
"""工作流命令幂等与门禁测试。"""
from django.test import TestCase, override_settings

from apps.core.exceptions import IDEMPOTENCY_CONFLICT, WORKFLOW_GATE_BLOCKED
from apps.drama.services.workflow_service import WorkflowService
from apps.drama.tests.helpers import SKILLS_ROOT, create_project, create_user


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
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

    def _advance_to_writing_with_passed_batch(self):
        """推进到 writing 且第 1 批已通过质检。"""
        events = [
            ("project_brief_completed", None),
            ("story_bible_completed", None),
            ("story_bible_approved", None),
            ("narrative_plan_completed", None),
            ("episode_batch_completed", None),
            ("quality_score_completed", {"overall_score": 82}),
            ("compliance_completed", {"blocking_issues": []}),
            ("quality_passed", None),
        ]
        version = 0
        state = None
        for index, (event, payload) in enumerate(events):
            state = self.svc.apply_command(
                self.project,
                command_id=f"adv-{index}",
                event=event,
                expected_version=version,
                payload=payload,
                actor=self.user.username,
            )
            version = state["version"]
        return state

    def test_all_batches_guard_blocks_unchecked_batch(self):
        """未通过末批质检禁止进入 delivery（total_batches=2 但只过了 1 批）。"""
        from apps.core.exceptions import BusinessException

        state = self._advance_to_writing_with_passed_batch()
        self.assertEqual(state["last_quality_passed_batch"], 1)
        with self.assertRaises(BusinessException) as ctx:
            self.svc.apply_command(
                self.project,
                command_id="cmd-early-delivery",
                event="all_batches_completed",
                expected_version=state["version"],
                payload={"total_batches": 2},
                actor=self.user.username,
            )
        self.assertEqual(ctx.exception.code, WORKFLOW_GATE_BLOCKED)

    def test_all_batches_guard_requires_total_batches(self):
        from apps.core.exceptions import BusinessException

        state = self._advance_to_writing_with_passed_batch()
        with self.assertRaises(BusinessException) as ctx:
            self.svc.apply_command(
                self.project,
                command_id="cmd-no-total",
                event="all_batches_completed",
                expected_version=state["version"],
                actor=self.user.username,
            )
        self.assertEqual(ctx.exception.code, WORKFLOW_GATE_BLOCKED)

    def test_delivery_auto_skipped_when_disabled(self):
        """enable_delivery=false 时进入 delivery 自动跳过并完成。"""
        state = self._advance_to_writing_with_passed_batch()
        prefs = dict(self.project.settings.get("creation_preferences") or {})
        self.assertFalse(prefs.get("enable_delivery"))
        final = self.svc.apply_command(
            self.project,
            command_id="cmd-finish",
            event="all_batches_completed",
            expected_version=state["version"],
            payload={"total_batches": 1},
            actor=self.user.username,
        )
        self.assertEqual(final["current_phase"], "completed")
        self.assertEqual(final["status"], "completed")

    def test_settings_invalidate_without_bible_stays_executable(self):
        """尚无蓝图时题材变更不得跳进 waiting_approval。"""
        state = self.svc.invalidate_downstream(self.project, actor=self.user.username)
        self.assertEqual(state["current_phase"], "strategy")
        self.assertEqual(state["status"], "active")
        self.assertNotEqual(state["status"], "waiting_approval")

    def test_project_brief_rework_invalidates_all(self):
        """选题重定调回流 strategy 并清空蓝图与下游。"""
        state = self._advance_to_writing_with_passed_batch()
        final = self.svc.apply_command(
            self.project,
            command_id="cmd-rework",
            event="project_brief_changed",
            expected_version=state["version"],
            actor=self.user.username,
        )
        self.assertEqual(final["current_phase"], "strategy")
        self.assertFalse(final["approvals"].get("story_bible_approved"))
        self.assertEqual(final["batch_cursor"], 1)
        self.assertEqual(final["last_quality_passed_batch"], 0)
