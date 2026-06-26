# -*- coding: utf-8 -*-
import threading

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection
from django.test import TransactionTestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.models import AgentLlmRouteConfig
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.artifact_service import save_artifact
from apps.creation.models import AgentExecutionRun, Project
from apps.skill.models import LlmProvider

from apps.creation.tests.test_helpers import grant_test_coins

User = get_user_model()


def _attach_test_llm_provider(agent_id: str) -> LlmProvider:
    provider = LlmProvider.objects.create(
        name=f"test-conc-{agent_id}",
        model_name="gpt-test",
        is_enabled=True,
    )
    route = AgentLlmRouteConfig.objects.get(route_key=agent_id)
    route.llm_provider = provider
    route.save(update_fields=["llm_provider"])
    return provider


class EnqueueConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        _attach_test_llm_provider("drama.topic-director")
        self.user = User.objects.create_user(phone="13900008901", password="test-pass-123")
        grant_test_coins(self.user)
        self.project = Project.objects.create(
            user=self.user,
            title="concurrency-test",
            theme="overbearing-ceo",
            core_idea="并发入队",
            episode_count=20,
            format_variant="B",
        )
        save_artifact(self.project, "project_brief", {"status": "confirmed", "coreIdea": "x"})

    def test_parallel_enqueue_only_one_running_run(self):
        if connection.vendor != "postgresql":
            self.skipTest("部分唯一约束仅 PostgreSQL 支持")

        barrier = threading.Barrier(2)
        results = []
        errors = []

        def _enqueue():
            try:
                barrier.wait(timeout=5)
                results.append(
                    IndependentAgentService.enqueue_run(self.project, self.user, "drama.topic-director", {})
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        t1 = threading.Thread(target=_enqueue)
        t2 = threading.Thread(target=_enqueue)
        t1.start()
        t2.start()
        t1.join(timeout=30)
        t2.join(timeout=30)

        running_count = AgentExecutionRun.objects.filter(
            project=self.project,
            status=AgentExecutionRun.STATUS_RUNNING,
        ).count()
        self.assertLessEqual(running_count, 1)
        created = sum(1 for r in results if r.created_new_run)
        self.assertGreaterEqual(created, 1)
        self.assertLessEqual(created, 2)
        if errors:
            self.assertTrue(
                all(isinstance(e, IntegrityError) for e in errors),
                errors,
            )
