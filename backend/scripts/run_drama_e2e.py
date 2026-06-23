#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Drama 快速/专家通道 E2E：各创建一个项目，按角色顺序跑通；失败则从该角色重试，不新建项目。

用法：
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
from apps.creation.models import AgentExecutionRun
from apps.drama.defaults import DRAMA_FAST_TRACK_ROLES, DRAMA_ROLE_DEFAULTS
from apps.drama.models import DramaProject, DramaRoleExecution
from apps.drama.services import DramaRoleRunService
from apps.skill.llm.providers import LlmProviderService
from apps.skill.llm.vendor_keys import LlmVendorCredentialService
from apps.skill.models import LlmProvider

User = get_user_model()

FAST_TITLE = "e2e-drama-fast"
EXPERT_TITLE = "e2e-drama-expert"
CORE_IDEA = (
    "现代都市甜宠逆袭：女主被豪门退婚，携隐藏身份重返商界，"
    "与冷面霸总从对立到联手，3集内完成身份反转与情感落地。"
)
GENRE = "overbearing-ceo"
EPISODES = 3
MAX_RETRIES = 3

# Mock 执行上下文（供 chat_completion patch 读取）
_MOCK_CTX: dict = {"agent_id": "", "run_params": {}}

VENDOR_PROBE_ORDER = [
    ("volcengine", "VOLCANO_ARK_API_KEY", "DeepSeek V4 Flash（火山）"),
    ("moonshot", "MOONSHOT_API_KEY", "Kimi K2.5"),
    ("deepseek", "DEEPSEEK_API_KEY", "DeepSeek V4 Flash"),
    ("zhipu", "ZHIPU_API_KEY", "GLM-5（智谱原生）"),
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
    """同步厂商 Key、绑定 drama 路由并做连通性测试；mock 模式仅绑定可用 Provider。"""
    if mock:
        provider = (
            LlmProvider.objects.filter(is_enabled=True).exclude(base_url__icontains="example.com").first()
            or LlmProvider.objects.filter(is_enabled=True).first()
        )
        if provider is None:
            raise RuntimeError("无可用 LlmProvider，请先 init_skill_data / seed_drama_skills")
        updated = _bind_drama_routes(provider)
        _log(f"Mock LLM 模式：已绑定 {updated} 条 drama 路由 -> {provider.name}")
        return provider

    from apps.skill.llm.chat import LlmService

    # 优先使用后台已配置的全局默认 Provider（如 Doubao Seed 2.0 Lite）
    active = LlmProviderService.get_active()
    if active and active.is_enabled and "example.com" not in (active.base_url or ""):
        has_key = bool(active.api_key_set or LlmProviderService.provider_has_api_key(active))
        if has_key:
            updated = _bind_drama_routes(active)
            _log(f"使用全局默认 Provider：{active.name}（已绑定 {updated} 条 drama 路由）")
            try:
                LlmService.test_connectivity(provider_id=str(active.id))
                _log(f"LLM 连通性测试通过：{active.name} / {active.model_name}")
                return active
            except Exception as exc:  # noqa: BLE001
                _log(f"全局默认 Provider 连通失败，尝试 env 探测：{str(exc)[:200]}")

    last_err = ""
    for vendor, env_name, provider_name in VENDOR_PROBE_ORDER:
        api_key = _resolve_api_key(env_name)
        if not api_key:
            continue
        LlmVendorCredentialService.set_vendor_credential(vendor, api_key=api_key, sync_providers=True)
        provider = LlmProvider.objects.filter(name=provider_name, is_enabled=True).first()
        if provider is None:
            provider = LlmProvider.objects.filter(is_enabled=True).exclude(
                base_url__icontains="example.com"
            ).first()
        if provider is None:
            continue
        updated = _bind_drama_routes(provider)
        _log(f"尝试 LLM 厂商 {vendor} -> {provider.name}（已更新 {updated} 条路由）")
        try:
            LlmService.test_connectivity(provider_id=str(provider.id))
            _log(f"LLM 连通性测试通过：{provider.name}")
            return provider
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)[:300]
            _log(f"  连通失败：{last_err}")

    hint = (
        "未找到可用的 LLM API Key / 连通性测试失败。"
        f"{' 最后错误: ' + last_err if last_err else ''} "
        "请在后台配置全局默认 Provider 或 .env 中设置 VOLCANO_ARK_API_KEY，或使用 --mock-llm。"
    )
    raise RuntimeError(hint)


@contextmanager
def mock_llm_context():
    from e2e_mock_responses import mock_llm_json

    def _fake_chat(**kwargs):  # noqa: ARG001
        return mock_llm_json(_MOCK_CTX["agent_id"], _MOCK_CTX["run_params"])

    with patch(
        "apps.creation.agent_runtime.independent_service.LlmService.chat_completion",
        side_effect=_fake_chat,
    ):
        yield


def ensure_admin() -> "User":
    admin = User.objects.filter(is_superuser=True).order_by("created_at").first()
    if admin is None:
        raise RuntimeError("无超级管理员账号，请先 createsuperuser")
    wallet = BillingService.get_or_create_wallet(admin)
    if wallet.balance < 3000:
        UserWallet.objects.filter(pk=wallet.pk).update(balance=5000)
        _log(f"管理员 {admin.phone} 钱包已充值至 5000 Coin")
    return admin


def role_list_for_track(track_mode: str) -> List[str]:
    if track_mode == "fast":
        return list(DRAMA_FAST_TRACK_ROLES)
    if track_mode == "expert":
        return [r["agent_id"] for r in sorted(DRAMA_ROLE_DEFAULTS, key=lambda x: x["workspace_order"])]
    raise ValueError(f"未知 track: {track_mode}")


def reset_project_state(drama_project: DramaProject) -> None:
    """清空产物与执行记录，在同一项目上重新跑真实 LLM。"""
    from apps.creation.models import AgentExecutionRun, ProjectFusionArtifact

    creation = DramaRoleRunService.ensure_creation_project(drama_project)
    ProjectFusionArtifact.objects.filter(project=creation).delete()
    AgentExecutionRun.objects.filter(project=creation).delete()
    DramaRoleExecution.objects.filter(drama_project=drama_project).delete()
    drama_project.completed_roles = []
    drama_project.current_stage = DramaProject.Stage.STRATEGY
    drama_project.delivery_status = "pending"
    drama_project.quality_scores = {}
    drama_project.total_tokens_used = 0
    drama_project.total_cost_cents = 0
    drama_project.save(
        update_fields=[
            "completed_roles",
            "current_stage",
            "delivery_status",
            "quality_scores",
            "total_tokens_used",
            "total_cost_cents",
            "updated_at",
        ]
    )
    _log(f"已重置项目 [{drama_project.track_mode}] id={drama_project.id}，准备重新执行")


def get_or_create_project(admin, *, track_mode: str, title: str) -> DramaProject:
    existing = DramaProject.objects.filter(user=admin, title=title).order_by("-created_at").first()
    if existing:
        _log(f"复用已有项目 [{track_mode}] id={existing.id} completed={len(existing.completed_roles or [])}")
        return existing

    pid = uuid.uuid4()
    project = DramaProject.objects.create(
        id=pid,
        project_id=pid,
        user=admin,
        title=title,
        genre_code=GENRE,
        total_episodes=EPISODES,
        target_platform="douyin",
        track_mode=track_mode,
    )
    DramaRoleRunService.ensure_creation_project(project, core_idea=CORE_IDEA)
    _log(f"新建项目 [{track_mode}] id={project.id}")
    return project


def _clear_stale_runs(drama_project: DramaProject, agent_id: str) -> None:
    AgentExecutionRun.objects.filter(
        project_id=drama_project.project_id,
        agent_id=agent_id,
        status=AgentExecutionRun.STATUS_RUNNING,
    ).update(
        status=AgentExecutionRun.STATUS_FAILED,
        error_message="E2E 重试前清理 stale running",
        finished_at=timezone.now(),
    )
    DramaRoleExecution.objects.filter(
        drama_project=drama_project,
        agent_id=agent_id,
        status__in=[DramaRoleExecution.Status.PENDING, DramaRoleExecution.Status.RUNNING],
    ).update(
        status=DramaRoleExecution.Status.FAILED,
        error_message="E2E 重试前清理 stale running",
        finished_at=timezone.now(),
    )


def run_one_role(drama_project: DramaProject, admin, agent_id: str, *, use_mock: bool) -> Tuple[bool, str]:
    creation = DramaRoleRunService.ensure_creation_project(drama_project)
    params = DramaRoleRunService.build_run_params(drama_project, creation)
    if agent_id == "drama.script-writer":
        params["episode_from"] = 1
        params["episode_to"] = EPISODES

    _clear_stale_runs(drama_project, agent_id)

    drama_exec = DramaRoleExecution.objects.create(
        drama_project=drama_project,
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
    _log(f"=== 开始 [{track_mode}] 共 {len(roles)} 角色，已完成 {len(completed)} ===")

    for idx, agent_id in enumerate(roles, start=1):
        project.refresh_from_db()
        completed = set(project.completed_roles or [])
        if agent_id in completed:
            _log(f"[{idx}/{len(roles)}] 跳过已完成 {agent_id}")
            continue

        _log(f"[{idx}/{len(roles)}] 执行 {agent_id} ...")
        ok = False
        err = ""
        for attempt in range(1, MAX_RETRIES + 1):
            if attempt > 1:
                _log(f"  重试 {attempt}/{MAX_RETRIES} ...")
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
    from apps.drama.progress_service import DramaProjectProgressService

    DramaProjectProgressService.recompute_project_state(project)
    creation = DramaRoleRunService.ensure_creation_project(project)
    deliverable = DramaProjectProgressService.is_deliverable(creation)
    _log(
        f"=== [{track_mode}] 全部角色完成 project={project.id} "
        f"deliverable={deliverable} stage={project.current_stage} "
        f"delivery={project.delivery_status} ==="
    )
    return 0 if deliverable else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Drama 快速/专家 E2E")
    parser.add_argument("--track", choices=["fast", "expert", "both"], default="both")
    parser.add_argument("--resume", action="store_true", help="复用同名项目并从断点继续")
    parser.add_argument(
        "--mock-llm",
        action="store_true",
        help="Mock LLM 响应（无真实 API Key 时用于验证整条业务链路）",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="清空同名项目的产物与执行记录，在同一项目上重新跑",
    )
    args = parser.parse_args()

    AgentDefinitionService.ensure_defaults()
    ensure_llm_ready(mock=args.mock_llm)
    admin = ensure_admin()

    if args.mock_llm:
        _log("⚠ 使用 Mock LLM — 验证编排/产物/进度/交付，非真实模型输出")

    tracks = ["fast", "expert"] if args.track == "both" else [args.track]
    exit_code = 0
    for track in tracks:
        code = run_track(admin, track, resume=args.resume, use_mock=args.mock_llm, reset=args.reset)
        if code != 0:
            exit_code = code
            _log(f"[{track}] 未完成，请修复后加 --resume 继续同一项目")
            if args.track == "both":
                break
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
