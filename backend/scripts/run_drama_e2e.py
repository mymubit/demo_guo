# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Drama ??/???? E2E?????????????????????????????????

???
  python scripts/run_drama_e2e.py --track fast
  python scripts/run_drama_e2e.py --track expert
  python scripts/run_drama_e2e.py --track both
  python scripts/run_drama_e2e.py --track both --resume
  python scripts/run_drama_e2e.py --track both --resume --reset
  python scripts/run_drama_e2e.py --track both --resume --mock-llm
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional, Tuple
from unittest.mock import patch

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.models import AgentLlmRouteConfig
from apps.billing.models import UserWallet
from apps.billing.services import BillingService
from apps.creation.models import AgentExecutionRun, Project
from apps.drama.constants import DramaStage
from apps.drama.defaults import DRAMA_FAST_TRACK_ROLES, DRAMA_ROLE_DEFAULTS
from apps.drama.models import DramaRoleExecution
from apps.drama.services import DramaRoleRunService
from apps.skill.llm.providers import LlmProviderService
from apps.skill.llm.vendor_keys import LlmVendorCredentialService
from apps.skill.models import LlmProvider

User = get_user_model()

FAST_TITLE = "e2e-drama-fast"
EXPERT_TITLE = "e2e-drama-expert"
CORE_IDEA = (
    "???????????????????????????"
    "????????????3??????????????"
)
GENRE = "overbearing-ceo"
EPISODES = 3
MAX_RETRIES = 3

# Mock ??????? chat_completion patch ???
_MOCK_CTX: dict = {"agent_id": "", "run_params": {}}

VENDOR_PROBE_ORDER = [
    ("volcengine", "VOLCANO_ARK_API_KEY", "DeepSeek V4 Flash????"),
    ("moonshot", "MOONSHOT_API_KEY", "Kimi K2.5"),
    ("deepseek", "DEEPSEEK_API_KEY", "DeepSeek V4 Flash"),
    ("zhipu", "ZHIPU_API_KEY", "GLM-5??????"),
    ("openai", "LLM_API_KEY", "GPT-4o mini"),
]


def _log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)


def _resolve_api_key(env_name: str) -> str:
    val = (getattr(settings, env_name, "") or os.getenv(env_name, "")).strip()
    if not val or "your-api-key" in val.lower() or val.startswith("sk-your"):
        return ""
    return val


def _bind_drama_routes(provider: LlmProvider) -> int:
    LlmProviderService.set_active(provider.id)
    return AgentLlmRouteConfig.objects.filter(route_key__startswith="drama.").update(
        llm_provider=provider
    )


def ensure_llm_ready(*, mock: bool = False) -> Optional[LlmProvider]:
    """???? Key??? drama ??????????mock ??????? Provider?"""
    if mock:
        provider = (
            LlmProvider.objects.filter(is_enabled=True).exclude(base_url__icontains="example.com").first()
        )
        if provider:
            _bind_drama_routes(provider)
            _log(f"Mock ????? Provider {provider.name}")
        return provider

    LlmVendorCredentialService.sync_from_settings()
    for vendor, env_name, label in VENDOR_PROBE_ORDER:
        api_key = _resolve_api_key(env_name)
        if not api_key:
            continue
        provider = LlmProvider.objects.filter(vendor=vendor, is_enabled=True).first()
        if not provider:
            continue
        bound = _bind_drama_routes(provider)
        _log(f"??? {label} drama ?? {bound} ?")
        return provider

    _log("????? LLM Provider???? API Key ??? --mock-llm")
    return None


def ensure_admin():
    admin = User.objects.filter(is_superuser=True).order_by("id").first()
    if not admin:
        admin = User.objects.create_superuser(phone="13800000001", password="admin-pass")
        _log("??????? 13800000001")
    wallet, _ = UserWallet.objects.get_or_create(user=admin)
    if wallet.balance_cents < 100000:
        BillingService.credit_wallet(admin, 100000, reason="E2E ????")
    return admin


@contextmanager
def mock_llm_context():
    from apps.skill.llm.providers import LlmProviderService

    def _mock_chat(*args, **kwargs):
        agent_id = _MOCK_CTX.get("agent_id") or "drama.topic-director"
        return {
            "content": json.dumps({"mock": True, "agent_id": agent_id}, ensure_ascii=False),
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }

    with patch.object(LlmProviderService, "chat_completion", side_effect=_mock_chat):
        yield


def role_list_for_track(track_mode: str) -> List[str]:
    if track_mode == "fast":
        return list(DRAMA_FAST_TRACK_ROLES)
    if track_mode == "expert":
        return [r["agent_id"] for r in sorted(DRAMA_ROLE_DEFAULTS, key=lambda x: x["workspace_order"])]
    raise ValueError(f"?? track: {track_mode}")


def reset_project_state(project: Project) -> None:
    """????????????????????? LLM?"""
    from apps.creation.models import ProjectFusionArtifact

    ProjectFusionArtifact.objects.filter(project=project).delete()
    AgentExecutionRun.objects.filter(project=project).delete()
    DramaRoleExecution.objects.filter(project=project).delete()
    project.completed_roles = []
    project.drama_stage = DramaStage.STRATEGY
    project.delivery_status = "pending"
    project.quality_scores = {}
    project.total_tokens_used = 0
    project.total_cost_cents = 0
    project.save(
        update_fields=[
            "completed_roles",
            "drama_stage",
            "delivery_status",
            "quality_scores",
            "total_tokens_used",
            "total_cost_cents",
            "updated_at",
        ]
    )
    _log(f"????? [{project.track_mode}] id={project.id}???????")


def get_or_create_project(admin, *, track_mode: str, title: str) -> Project:
    existing = (
        Project.objects.filter(user=admin, title=title, track_mode=track_mode)
        .order_by("-created_at")
        .first()
    )
    if existing:
        _log(f"?????? [{track_mode}] id={existing.id} completed={len(existing.completed_roles or [])}")
        return existing

    project = Project.objects.create(
        user=admin,
        title=title,
        theme=GENRE,
        episode_count=EPISODES,
        target_platform="douyin",
        track_mode=track_mode,
        pipeline_mode=Project.MODE_WORKSPACE,
        core_idea=CORE_IDEA,
    )
    _log(f"???? [{track_mode}] id={project.id}")
    return project


def _clear_stale_runs(project: Project, agent_id: str) -> None:
    AgentExecutionRun.objects.filter(
        project=project,
        agent_id=agent_id,
        status=AgentExecutionRun.STATUS_RUNNING,
    ).update(
        status=AgentExecutionRun.STATUS_FAILED,
        error_message="E2E ????? stale running",
        finished_at=timezone.now(),
    )
    DramaRoleExecution.objects.filter(
        project=project,
        agent_id=agent_id,
        status__in=[DramaRoleExecution.Status.PENDING, DramaRoleExecution.Status.RUNNING],
    ).update(
        status=DramaRoleExecution.Status.FAILED,
        error_message="E2E ????? stale running",
        finished_at=timezone.now(),
    )


def run_one_role(project: Project, admin, agent_id: str, *, use_mock: bool) -> Tuple[bool, str]:
    params = DramaRoleRunService.build_run_params(project)
    if agent_id == "drama.script-writer":
        params["episode_from"] = 1
        params["episode_to"] = EPISODES

    _clear_stale_runs(project, agent_id)

    drama_exec = DramaRoleExecution.objects.create(
        project=project,
        agent_id=agent_id,
        agent_name_zh=agent_id,
        status=DramaRoleExecution.Status.RUNNING,
        input_artifacts={"params": params},
        started_at=timezone.now(),
    )

    _MOCK_CTX["agent_id"] = agent_id
    _MOCK_CTX["run_params"] = params

    try:
        if use_mock:
            with mock_llm_context():
                DramaRoleRunService.execute_role(str(drama_exec.id))
        else:
            DramaRoleRunService.execute_role(str(drama_exec.id))
    except Exception as exc:  # noqa: BLE001
        drama_exec.refresh_from_db()
        return False, str(exc)[:500]

    drama_exec.refresh_from_db()
    if drama_exec.status == DramaRoleExecution.Status.SUCCESS:
        return True, ""
    return False, (drama_exec.error_message or f"status={drama_exec.status}")[:500]


def run_track(admin, track_mode: str, *, resume: bool, use_mock: bool, reset: bool) -> int:
    title = FAST_TITLE if track_mode == "fast" else EXPERT_TITLE
    roles = role_list_for_track(track_mode)
    project = get_or_create_project(admin, track_mode=track_mode, title=title)
    if reset:
        reset_project_state(project)

    completed = set(project.completed_roles or [])
    _log(f"=== ?? [{track_mode}] ? {len(roles)} ?????? {len(completed)} ===")

    for idx, agent_id in enumerate(roles, start=1):
        project.refresh_from_db()
        completed = set(project.completed_roles or [])
        if agent_id in completed:
            _log(f"[{idx}/{len(roles)}] ????? {agent_id}")
            continue

        _log(f"[{idx}/{len(roles)}] ?? {agent_id} ...")
        ok = False
        err = ""
        for attempt in range(1, MAX_RETRIES + 1):
            if attempt > 1:
                _log(f"  ?? {attempt}/{MAX_RETRIES} ...")
                time.sleep(min(5 * attempt, 20))
            ok, err = run_one_role(project, admin, agent_id, use_mock=use_mock)
            if ok:
                break

        if not ok:
            _log(f"FAILED {agent_id}: {err}")
            summary = {
                "track": track_mode,
                "project_id": str(project.id),
                "failed_agent": agent_id,
                "error": err,
                "completed": list(project.completed_roles or []),
            }
            _log(json.dumps(summary, ensure_ascii=False))
            return 1

        project.refresh_from_db()
        _log(f"  OK -> completed_roles={len(project.completed_roles or [])}")

    project.refresh_from_db()
    from apps.drama.progress_service import DramaProgressService

    DramaProgressService.recompute_project_state(project)
    deliverable = DramaProgressService.is_deliverable(project)
    _log(
        f"=== [{track_mode}] ?????? project={project.id} "
        f"deliverable={deliverable} stage={project.drama_stage} "
        f"delivery={project.delivery_status} ==="
    )
    return 0 if deliverable else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Drama ??/?? E2E")
    parser.add_argument("--track", choices=["fast", "expert", "both"], default="both")
    parser.add_argument("--resume", action="store_true", help="????????????")
    parser.add_argument(
        "--mock-llm",
        action="store_true",
        help="Mock LLM ?????? API Key ????????????",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="????????????????????????",
    )
    args = parser.parse_args()

    AgentDefinitionService.ensure_defaults()
    ensure_llm_ready(mock=args.mock_llm)
    admin = ensure_admin()

    if args.mock_llm:
        _log("? ?? Mock LLM ? ????/??/??/??????????")

    tracks = ["fast", "expert"] if args.track == "both" else [args.track]
    exit_code = 0
    for track in tracks:
        code = run_track(admin, track, resume=args.resume, use_mock=args.mock_llm, reset=args.reset)
        if code != 0:
            exit_code = code
            _log(f"[{track}] ????????? --resume ??????")
            if args.track == "both":
                break
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
