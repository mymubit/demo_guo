# -*- coding: utf-8 -*-
"""V3 W2：异步编排 + confirm 同步命令（Celery eager + mock LLM）。"""
from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.drama.models import V3ArtifactVersion, V3CommandRun, V3Project
from apps.drama.orchestrator import dispatch_command
from apps.drama.skills_bridge.recipe_map import recipe_for
from apps.drama.tests.helpers import SKILLS_ROOT

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
_BRIEF_PAYLOAD = json.loads(
    (_FIXTURE_DIR / "v3_project_brief_candidate.json").read_text(encoding="utf-8")
)
_BLUEPRINT_BUNDLE = json.loads(
    (_FIXTURE_DIR / "v3_blueprint_bundle.json").read_text(encoding="utf-8")
)
_BLUEPRINT_KEYS = recipe_for("generate_blueprint")["writes"]


def _mock_llm_call(prompt: str) -> str:
    if '"command_type": "generate_blueprint"' in prompt:
        return json.dumps(_BLUEPRINT_BUNDLE, ensure_ascii=False)
    return json.dumps(_BRIEF_PAYLOAD, ensure_ascii=False)


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    V3_LLM_CALL_OVERRIDE=_mock_llm_call,
)
class V3AsyncCommandsTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="async_w2", password="pass12345"
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="异步编排项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.TOPIC,
        )

    def test_generate_topic_brief_eager_succeeds_with_candidate(self) -> None:
        run = dispatch_command(
            owner=self.user,
            command_type="generate_topic_brief",
            payload={"project_id": str(self.project.id)},
        )
        run.refresh_from_db()
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        self.assertEqual(run.project_id, self.project.id)
        artifact_ids = run.result_payload.get("artifact_ids") or []
        self.assertEqual(len(artifact_ids), 1)
        art = V3ArtifactVersion.objects.get(id=artifact_ids[0])
        self.assertEqual(art.artifact_key, "project_brief")
        self.assertEqual(art.status, V3ArtifactVersion.Status.CANDIDATE)
        self.assertEqual(art.command_run_id, run.id)

    def test_confirm_topic_brief_commits_and_advances_stage(self) -> None:
        gen = dispatch_command(
            owner=self.user,
            command_type="generate_topic_brief",
            payload={"project_id": str(self.project.id)},
        )
        self.assertEqual(gen.status, V3CommandRun.Status.SUCCEEDED)

        run = dispatch_command(
            owner=self.user,
            command_type="confirm_topic_brief",
            payload={"project_id": str(self.project.id)},
        )
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.stage, V3Project.Stage.BLUEPRINT)
        committed = V3ArtifactVersion.objects.get(
            project=self.project,
            artifact_key="project_brief",
            status=V3ArtifactVersion.Status.COMMITTED,
        )
        self.assertEqual(committed.payload["title"], _BRIEF_PAYLOAD["title"])

    def test_generate_twice_confirm_latest_supersedes_prior_candidates(self) -> None:
        """生成两次 → 确认最新 → 无残留 CANDIDATE；再确认旧 id 应失败且不复活。"""
        first = dispatch_command(
            owner=self.user,
            command_type="generate_topic_brief",
            payload={"project_id": str(self.project.id)},
        )
        self.assertEqual(first.status, V3CommandRun.Status.SUCCEEDED)
        old_id = (first.result_payload.get("artifact_ids") or [])[0]

        second = dispatch_command(
            owner=self.user,
            command_type="generate_topic_brief",
            payload={"project_id": str(self.project.id)},
        )
        self.assertEqual(second.status, V3CommandRun.Status.SUCCEEDED)
        latest_id = (second.result_payload.get("artifact_ids") or [])[0]
        self.assertNotEqual(old_id, latest_id)

        # generate 路径应已把旧 candidate 标为 superseded
        old_art = V3ArtifactVersion.objects.get(id=old_id)
        self.assertEqual(old_art.status, V3ArtifactVersion.Status.SUPERSEDED)
        self.assertEqual(
            V3ArtifactVersion.objects.filter(
                project=self.project,
                artifact_key="project_brief",
                status=V3ArtifactVersion.Status.CANDIDATE,
            ).count(),
            1,
        )

        confirm = dispatch_command(
            owner=self.user,
            command_type="confirm_topic_brief",
            payload={
                "project_id": str(self.project.id),
                "artifact_version_ids": [latest_id],
            },
        )
        self.assertEqual(confirm.status, V3CommandRun.Status.SUCCEEDED)
        self.assertEqual(
            V3ArtifactVersion.objects.filter(
                project=self.project,
                artifact_key="project_brief",
                status=V3ArtifactVersion.Status.CANDIDATE,
            ).count(),
            0,
        )
        committed = V3ArtifactVersion.objects.get(id=latest_id)
        self.assertEqual(committed.status, V3ArtifactVersion.Status.COMMITTED)

        # 旧候选不可再确认；不得复活为 candidate/committed
        retry_old = dispatch_command(
            owner=self.user,
            command_type="confirm_topic_brief",
            payload={
                "project_id": str(self.project.id),
                "artifact_version_ids": [old_id],
            },
        )
        self.assertEqual(retry_old.status, V3CommandRun.Status.FAILED)
        self.assertIn("缺少待确认候选产物", retry_old.error_message)
        old_art.refresh_from_db()
        self.assertEqual(old_art.status, V3ArtifactVersion.Status.SUPERSEDED)
        self.assertEqual(
            V3ArtifactVersion.objects.filter(
                project=self.project,
                artifact_key="project_brief",
                status=V3ArtifactVersion.Status.CANDIDATE,
            ).count(),
            0,
        )

    def test_generate_blueprint_without_brief_fails_friendly(self) -> None:
        run = dispatch_command(
            owner=self.user,
            command_type="generate_blueprint",
            payload={"project_id": str(self.project.id)},
        )
        run.refresh_from_db()
        self.assertEqual(run.status, V3CommandRun.Status.FAILED)
        self.assertTrue(run.error_message)
        self.assertNotIn("Traceback", run.error_message)
        self.assertIn("简报", run.error_message)
        self.assertFalse(
            V3ArtifactVersion.objects.filter(project=self.project).exists()
        )

    def test_generate_blueprint_with_brief_writes_five_candidates(self) -> None:
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=1,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=_BRIEF_PAYLOAD,
        )
        self.project.stage = V3Project.Stage.BLUEPRINT
        self.project.save(update_fields=["stage", "updated_at"])

        run = dispatch_command(
            owner=self.user,
            command_type="generate_blueprint",
            payload={"project_id": str(self.project.id)},
        )
        run.refresh_from_db()
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        artifact_ids = run.result_payload.get("artifact_ids") or []
        self.assertEqual(len(artifact_ids), 5)
        arts = list(
            V3ArtifactVersion.objects.filter(
                project=self.project,
                status=V3ArtifactVersion.Status.CANDIDATE,
            ).order_by("artifact_key")
        )
        self.assertEqual(len(arts), 5)
        self.assertEqual({a.artifact_key for a in arts}, set(_BLUEPRINT_KEYS))
        self.assertTrue(all(a.command_run_id == run.id for a in arts))

    def test_confirm_blueprint_advances_to_episodes(self) -> None:
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=1,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=_BRIEF_PAYLOAD,
        )
        self.project.stage = V3Project.Stage.BLUEPRINT
        self.project.save(update_fields=["stage", "updated_at"])

        gen = dispatch_command(
            owner=self.user,
            command_type="generate_blueprint",
            payload={"project_id": str(self.project.id)},
        )
        self.assertEqual(gen.status, V3CommandRun.Status.SUCCEEDED)

        run = dispatch_command(
            owner=self.user,
            command_type="confirm_blueprint",
            payload={"project_id": str(self.project.id)},
        )
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.stage, V3Project.Stage.EPISODES)
        for key in _BLUEPRINT_KEYS:
            self.assertTrue(
                V3ArtifactVersion.objects.filter(
                    project=self.project,
                    artifact_key=key,
                    status=V3ArtifactVersion.Status.COMMITTED,
                ).exists(),
                msg=f"missing committed {key}",
            )

    def test_no_v6_runtime_in_orchestrator_skills_bridge_tasks(self) -> None:
        roots = [
            Path(settings.BASE_DIR) / "apps" / "drama" / "orchestrator",
            Path(settings.BASE_DIR) / "apps" / "drama" / "skills_bridge",
            Path(settings.BASE_DIR) / "apps" / "drama" / "tasks_v3.py",
        ]
        banned = ("v6_runtime", "v6_workbench", "v6_control_plane")
        hits: list[str] = []
        for root in roots:
            if root.is_file():
                files = [root]
            elif root.is_dir():
                files = list(root.rglob("*.py"))
            else:
                continue
            for path in files:
                if "__pycache__" in path.parts:
                    continue
                text = path.read_text(encoding="utf-8")
                for token in banned:
                    if token in text:
                        hits.append(f"{path}: {token}")
        self.assertEqual(hits, [], msg="forbidden v6 imports: " + "; ".join(hits))
