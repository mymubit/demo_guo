# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.creation.monitoring.execution_run_service import AgentExecutionRunService
from apps.creation.models import AgentExecutionRun, Project, SubSkillExecutionLog
from apps.skill.llm.usage_log import LlmUsageService, llm_usage_scope
from apps.skill.models import LlmUsageLog

User = get_user_model()


class AgentExecutionRunServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900006601", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            theme="test",
            core_idea="idea",
            episode_count=10,
        )

    def test_run_scope_finish_syncs_trace(self):
        trace = [
            {"id": "reference-injector", "type": "retrieval", "status": "executed", "message": ""},
            {"id": "structure-generator", "type": "llm", "status": "executed", "message": ""},
            {"id": "world-validator", "type": "cli", "status": "failed", "message": "rootRules 不足"},
        ]

        class _Result:
            meta = {"execution_trace": trace}

        with AgentExecutionRunService.run_scope(
            self.project,
            agent_id="world",
            node_index=2,
            input_summary={"loaded_artifacts": ["project_brief"]},
        ) as run:
            AgentExecutionRunService.record_sub_skill(
                "reference-injector",
                "executed",
                skill_type="retrieval",
                input_summary={"nodeId": "node-2-structure"},
            )
            AgentExecutionRunService.finish_run(
                run,
                AgentExecutionRun.STATUS_COMPLETED,
                agent_result=_Result(),
                output_artifact_key="structure_plan",
                output_summary={"artifactKey": "structure_plan", "totalEpisodes": 10},
            )

        run = AgentExecutionRun.objects.get(id=run.id)
        self.assertEqual(run.status, AgentExecutionRun.STATUS_COMPLETED)
        self.assertEqual(run.output_artifact_key, "structure_plan")
        logs = {log.skill_id: log for log in run.sub_skill_logs.all()}
        self.assertEqual(logs["reference-injector"].status, SubSkillExecutionLog.STATUS_EXECUTED)
        self.assertEqual(logs["world-validator"].status, SubSkillExecutionLog.STATUS_FAILED)
        self.assertIn("rootRules", logs["world-validator"].error_message)
        self.assertEqual(logs["structure-generator"].status, SubSkillExecutionLog.STATUS_EXECUTED)

    def test_llm_usage_links_execution_run_and_sub_skill(self):
        with AgentExecutionRunService.run_scope(
            self.project,
            agent_id="world",
            node_index=2,
        ) as run:
            with llm_usage_scope(
                source_type=LlmUsageLog.SOURCE_NODE,
                source_key="node-2-structure:structure-generator",
                project_id=self.project.id,
                user_id=self.user.id,
                execution_run_id=str(run.id),
                sub_skill_id="structure-generator",
            ):
                LlmUsageService.record(
                    cfg={"provider_name": "volcano", "model": "ep-test"},
                    usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                )

        usage = LlmUsageLog.objects.get(project=self.project)
        self.assertEqual(str(usage.execution_run_id), str(run.id))
        self.assertEqual(usage.sub_skill_id, "structure-generator")
        self.assertEqual(usage.source_key, "node-2-structure:structure-generator")

    def test_run_tracked_agent_persists_adapt(self):
        """新引擎：adapt 通过 SkillInvoker 路由，使用一个 mock 函数代理。"""
        def mock_adapt_runner(*args, **kwargs):
            class _Result:
                agent_id = "adapt"
                status = "skipped"
                outputs = {"reason": "from-scratch"}

            return _Result()

        result = AgentExecutionRunService.run_tracked_agent(
            self.project,
            "adapt",
            mock_adapt_runner,
            node_index=0,
            input_summary={"creation_entry": "from-scratch"},
        )
        self.assertEqual(result.status, "skipped")
        run = AgentExecutionRun.objects.filter(project=self.project, agent_id="adapt").first()
        self.assertIsNotNone(run)
        self.assertEqual(run.status, AgentExecutionRun.STATUS_COMPLETED)

    def test_run_scope_marks_failed_on_exception(self):
        with self.assertRaises(ValueError):
            with AgentExecutionRunService.run_scope(
                self.project,
                agent_id="world",
                node_index=2,
            ):
                raise ValueError("boom")

        run = (
            AgentExecutionRun.objects.filter(project=self.project, agent_id="world")
            .order_by("-started_at")
            .first()
        )
        self.assertIsNotNone(run)
        self.assertEqual(run.status, AgentExecutionRun.STATUS_FAILED)
        self.assertIn("boom", run.error_message)

    def test_dashboard_payload_and_run_detail_llm(self):
        with AgentExecutionRunService.run_scope(
            self.project,
            agent_id="world",
            node_index=2,
        ) as run:
            with llm_usage_scope(
                source_type=LlmUsageLog.SOURCE_NODE,
                source_key="node-2:structure-generator",
                project_id=self.project.id,
                user_id=self.user.id,
                execution_run_id=str(run.id),
                sub_skill_id="structure-generator",
            ):
                LlmUsageService.record(
                    cfg={"provider_name": "volcano", "model": "ep-test"},
                    usage={"prompt_tokens": 80, "completion_tokens": 20, "total_tokens": 100},
                )
            AgentExecutionRunService.finish_run(
                run,
                AgentExecutionRun.STATUS_COMPLETED,
                output_artifact_key="structure_plan",
            )

        dash = AgentExecutionRunService.dashboard_payload(days=30)
        self.assertGreaterEqual(dash["summary"]["period"]["run_count"], 1)
        self.assertEqual(len(dash["runs_7d"]), 7)

        detail = AgentExecutionRunService.get_run_detail(str(run.id))
        self.assertIsNotNone(detail)
        self.assertEqual(detail["llm_summary"]["call_count"], 1)
        self.assertEqual(detail["llm_summary"]["total_tokens"], 100)
        self.assertEqual(len(detail["llm_usage"]), 1)
        self.assertIn("rendered_prompt_preview", detail)

    def test_serialize_run_portal_strips_sensitive_fields(self):
        run = AgentExecutionRun.objects.create(
            project=self.project,
            user=self.user,
            agent_id="brief",
            status=AgentExecutionRun.STATUS_COMPLETED,
            rendered_prompt_preview="hidden prompt text",
            input_snapshot={
                "required_artifacts": ["project_brief"],
                "artifacts": {"project_brief": {"secret": True}},
                "params": {"episode_from": 2},
            },
        )
        portal = AgentExecutionRunService.serialize_run(run, include_sensitive=False)
        self.assertNotIn("rendered_prompt_preview", portal)
        self.assertNotIn("artifacts", portal.get("input_snapshot") or {})
        self.assertNotIn("sub_skills", portal)
        self.assertNotIn("execution_trace", portal)

        admin = AgentExecutionRunService.serialize_run(
            run, include_sensitive=True, include_sub_skills=True
        )
        self.assertEqual(admin.get("rendered_prompt_preview"), "hidden prompt text")
        self.assertIn("artifacts", admin.get("input_snapshot") or {})
