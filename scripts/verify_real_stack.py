"""在真实 PostgreSQL、Redis、Celery Worker 上执行 V3 最小闭环。

验证内容：
1. Redis 读写
2. V3 orchestrator / tasks_v3 可导入（无已删 GenerationService / WorkflowService）
3. 同步 create_project（PostgreSQL）
4. 异步 generate_topic_brief 经 Celery worker 执行并落终态（LLM 未配置时允许 FAILED）
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _bootstrap_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    backend = str(ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    import django

    django.setup()


def wait_run(run_id: str, timeout_seconds: int = 45):
    from apps.drama.models import V3CommandRun

    deadline = time.monotonic() + timeout_seconds
    terminal = {
        V3CommandRun.Status.SUCCEEDED,
        V3CommandRun.Status.FAILED,
        V3CommandRun.Status.UNSUPPORTED,
    }
    while time.monotonic() < deadline:
        run = V3CommandRun.objects.get(id=run_id)
        if run.status in terminal:
            return run
        time.sleep(0.5)
    raise TimeoutError(f"V3 Celery 任务未在期限内结束: run_id={run_id}")


def verify_imports() -> None:
    """导入烟测：确认 V3 栈符号存在且无引用已删服务。"""
    from apps.drama import tasks_v3
    from apps.drama.orchestrator import dispatch_command
    from apps.drama.orchestrator.async_runner import enqueue_v3_command, run_v3_command
    from apps.drama.orchestrator.dispatcher import dispatch_command as dispatch_impl

    assert callable(dispatch_command)
    assert callable(dispatch_impl)
    assert callable(run_v3_command)
    assert callable(enqueue_v3_command)
    assert callable(tasks_v3.run_v3_command_task)
    banned = ("GenerationService", "WorkflowService", "generation_service", "workflow_service")
    for name in banned:
        if name in sys.modules:
            raise RuntimeError(f"不应加载已删模块: {name}")


def run_stack_smoke() -> None:
    from django.contrib.auth import get_user_model
    from django.core.cache import cache

    from apps.drama.models import V3CommandRun, V3Project
    from apps.drama.orchestrator import dispatch_command

    cache.set("real-stack-v3", "ok", timeout=30)
    if cache.get("real-stack-v3") != "ok":
        raise RuntimeError("Redis 读写失败")

    verify_imports()

    username = f"integration-{uuid.uuid4().hex[:8]}"
    user = get_user_model().objects.create_user(username=username, password="test-only")
    create_run = dispatch_command(
        owner=user,
        command_type="create_project",
        payload={"title": "真实基础设施测试", "entry_type": "original"},
    )
    if create_run.status != V3CommandRun.Status.SUCCEEDED:
        raise RuntimeError(f"create_project 失败: {create_run.status} {create_run.error_message}")
    project_id = create_run.result_payload.get("project_id")
    if not project_id:
        raise RuntimeError("create_project 未返回 project_id")
    project = V3Project.objects.get(id=project_id, owner=user)
    if project.stage != V3Project.Stage.TOPIC:
        raise RuntimeError(f"项目阶段异常: {project.stage}")

    async_run = dispatch_command(
        owner=user,
        command_type="generate_topic_brief",
        payload={"project_id": str(project.id)},
    )
    # Celery eager=false 时此处多为 queued；worker 拉起后进入终态
    completed = wait_run(str(async_run.id))
    if completed.status not in {
        V3CommandRun.Status.SUCCEEDED,
        V3CommandRun.Status.FAILED,
    }:
        raise RuntimeError(
            f"异步命令终态异常: {completed.status} err={completed.error_message}"
        )
    # LLM 未配置时 FAILED 仍证明 worker 已执行 run_v3_command_task
    if completed.status == V3CommandRun.Status.FAILED and not (completed.error_message or "").strip():
        raise RuntimeError("异步命令 FAILED 但缺少 error_message")

    print("REAL_STACK_OK")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify V3 real stack (Redis + PostgreSQL + Celery + orchestrator)."
    )
    parser.add_argument(
        "--imports-only",
        action="store_true",
        help="仅 django.setup + 导入烟测（不访问 Redis/Celery 闭环）",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    _bootstrap_django()
    if args.imports_only:
        verify_imports()
        print("V3_IMPORTS_OK")
        return
    run_stack_smoke()


if __name__ == "__main__":
    main()
