# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""真实 LLM Key 冒烟：顺序跑通 9-Agent 链路。无 Key 时自动跳过。"""
from __future__ import annotations

import json
import os
import sys

import django

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, BACKEND_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

from apps.agent.definition_service import AgentDefinitionService  # noqa: E402
from apps.creation.agent_runtime.independent_service import IndependentAgentService  # noqa: E402
from apps.creation.models import Project  # noqa: E402

User = get_user_model()
CHAIN = ["adapt", "brief", "structure", "character", "outline", "script", "review", "score", "marketing"]


def _has_llm_key() -> bool:
    keys = [
        os.getenv("LLM_API_KEY"),
        os.getenv("OPENAI_API_KEY"),
        os.getenv("DASHSCOPE_API_KEY"),
    ]
    return any(k and str(k).strip() for k in keys)


def main() -> int:
    if not _has_llm_key():
        print("SKIP: 未配置 LLM_API_KEY / OPENAI_API_KEY / DASHSCOPE_API_KEY，跳过冒烟。")
        return 0

    AgentDefinitionService.ensure_defaults()
    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not user:
        print("ERROR: 无可用用户")
        return 1

    project = Project.objects.create(
        user=user,
        title="smoke-full-chain",
        theme="overbearing-ceo",
        core_idea="冒烟测试",
        episode_count=6,
        format_variant="B",
        novel_text="测试小说正文" * 30,
        creation_entry="novel-adaptation",
    )
    print(f"project={project.id}")

    for agent_id in CHAIN:
        print(f"running {agent_id}...")
        result = IndependentAgentService.enqueue_run(project, user, agent_id, {})
        run = IndependentAgentService.execute_run(result.run)
        if run.status != "completed":
            print(json.dumps({"agent": agent_id, "status": run.status, "error": run.error_message}, ensure_ascii=False))
            return 2
        project.refresh_from_db()
        print(f"  ok -> {run.status}")

    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
