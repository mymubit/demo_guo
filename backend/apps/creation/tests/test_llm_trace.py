# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.creation.monitoring.execution_run_service import AgentExecutionRunService
from apps.creation.monitoring.llm_trace import (
    begin_llm_trace,
    finish_llm_trace_success,
    merge_request_into_usage_record,
)
from apps.creation.models import AgentExecutionRun, Project, SubSkillExecutionLog
from apps.skill.llm.usage_log import LlmUsageService, llm_usage_scope
from apps.skill.models import LlmUsageLog

User = get_user_model()


@override_settings(CREATION_LLM_TRACE_FULL=True, CREATION_LLM_TRACE_MAX_CHARS=65536)
class LlmTraceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900006602", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            theme="trace-test",
            core_idea="idea",
            episode_count=10,
        )

    def test_full_io_persisted_on_sub_skill_and_usage_log(self):
        upstream = {"nodeId": "node-2-structure", "theme": "trace-test", "episodeCount": 10}
        system_prompt = "你是结构策划师"
        user_prompt = "请生成世界观结构"
        parsed = {"rootRules": ["规则1"], "totalEpisodes": 10}

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
                begin_llm_trace(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    provider_id="volcano",
                    upstream=upstream,
                )
                LlmUsageService.record(
                    cfg={"provider_name": "volcano", "model": "ep-test"},
                    usage={"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200},
                )
                merge_request_into_usage_record()
                finish_llm_trace_success(raw_content='{"rootRules":["规则1"]}', parsed_output=parsed)

            AgentExecutionRunService.finish_run(run, AgentExecutionRun.STATUS_COMPLETED)

        usage = LlmUsageLog.objects.get(project=self.project)
        self.assertIn("system_prompt", usage.request_payload)
        self.assertEqual(usage.request_payload["system_prompt"]["text"], system_prompt)
        self.assertEqual(usage.request_payload["user_prompt"]["text"], user_prompt)
        self.assertIn("upstream", usage.request_payload)
        self.assertEqual(usage.request_payload["upstream_mode"], "summary")
        self.assertEqual(usage.request_payload["upstream"]["theme"], "trace-test")
        self.assertIn("upstreamKeys", usage.request_payload["upstream"])
        self.assertTrue(usage.response_payload.get("success"))
        self.assertIn("raw_content", usage.response_payload)
        self.assertEqual(usage.response_payload["parsed"]["rootRules"], ["规则1"])

        log = SubSkillExecutionLog.objects.get(run=run, skill_id="structure-generator")
        self.assertEqual(log.input_payload["theme"], "trace-test")
        self.assertIn("upstreamKeys", log.input_payload)
        self.assertEqual(log.output_payload["totalEpisodes"], 10)
        self.assertEqual(log.llm_io["request"]["system_prompt"]["text"], system_prompt)
        self.assertEqual(log.llm_io["response"]["parsed"]["rootRules"], ["规则1"])

        detail = AgentExecutionRunService.get_run_detail(str(run.id))
        self.assertEqual(len(detail["llm_usage"]), 1)
        self.assertEqual(
            detail["llm_usage"][0]["request_payload"]["system_prompt"]["text"],
            system_prompt,
        )
        sub = next(s for s in detail["sub_skills"] if s["skill_id"] == "structure-generator")
        self.assertEqual(sub["llm_io"]["request"]["user_prompt"]["text"], user_prompt)

    def test_record_sub_skill_accepts_full_payload(self):
        with AgentExecutionRunService.run_scope(
            self.project,
            agent_id="world",
            node_index=2,
        ) as run:
            AgentExecutionRunService.record_sub_skill(
                "reference-injector",
                "executed",
                skill_type="retrieval",
                input_payload={"query": "短剧结构", "topK": 5},
                output_payload={"hits": [{"id": "ref-1", "score": 0.9}]},
            )
            AgentExecutionRunService.finish_run(run, AgentExecutionRun.STATUS_COMPLETED)

        log = SubSkillExecutionLog.objects.get(run=run, skill_id="reference-injector")
        self.assertEqual(log.input_payload["query"], "短剧结构")
        self.assertEqual(log.output_payload["hits"][0]["id"], "ref-1")
