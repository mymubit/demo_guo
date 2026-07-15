"""在真实 PostgreSQL、Redis、Celery Worker 上执行最小闭环。"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.core.cache import cache  # noqa: E402

from apps.drama.models import DramaGenerationJob  # noqa: E402
from apps.drama.services.artifact_service import ArtifactService  # noqa: E402
from apps.drama.services.generation_service import GenerationService  # noqa: E402
from apps.drama.services.project_settings import ProjectSettingsService  # noqa: E402
from apps.drama.services.workflow_service import WorkflowService  # noqa: E402


def wait_job(job_id: str, timeout_seconds: int = 30) -> DramaGenerationJob:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        job = DramaGenerationJob.objects.get(id=job_id)
        if job.status in {
            DramaGenerationJob.Status.COMPLETED,
            DramaGenerationJob.Status.FAILED,
            DramaGenerationJob.Status.DISABLED,
        }:
            return job
        time.sleep(0.5)
    raise TimeoutError("Celery 任务未在期限内结束")


def main() -> None:
    cache.set("real-stack", "ok", timeout=30)
    if cache.get("real-stack") != "ok":
        raise RuntimeError("Redis 读写失败")

    username = f"integration-{uuid.uuid4().hex[:8]}"
    user = get_user_model().objects.create_user(username=username, password="test-only")
    project = ProjectSettingsService().create_project(
        user,
        "真实基础设施测试",
        entry_type="original_track",
    )

    skills_root = Path(os.environ.get("DRAMA_SKILLS_ROOT", ROOT / "drama-skills"))
    fixture_path = skills_root / "build/fixtures/artifacts/valid-artifacts.json"
    fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
    ArtifactService().save_artifact(
        project,
        "project_brief",
        fixtures["project_brief"],
    )
    stored = ArtifactService().get_artifact(project, "project_brief")
    if stored["version"] != 1:
        raise RuntimeError("PostgreSQL 产物版本写入失败")
    WorkflowService().apply_command(
        project,
        command_id="verify-project-brief",
        event="project_brief_completed",
        expected_version=project.workflow_state.version,
        actor=username,
    )
    project.workflow_state.refresh_from_db()

    job = GenerationService().start_generation(
        project,
        command_id="verify-stack-1",
        expected_version=project.workflow_state.version,
        role="drama.story-bible",
        input_payload={"project_brief": stored["payload"]},
        actor=username,
    )
    completed = wait_job(str(job.id))
    if completed.status != DramaGenerationJob.Status.DISABLED:
        raise RuntimeError(f"LLM禁用任务状态异常: {completed.status}")

    print("REAL_STACK_OK")


if __name__ == "__main__":
    main()
