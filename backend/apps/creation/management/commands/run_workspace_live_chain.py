# -*- coding: utf-8 -*-
"""工作台五步主链 + 后处理同步联调（真实 LLM，不经 worker 队列）。"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.billing.services import BillingService
from apps.creation.artifact_service import get_artifact, save_artifact
from apps.creation.models import CreationNode, Project
from apps.creation.services import CreationService
from apps.creation.tasks import _run_skill_node_core, run_agent_post_chain
from apps.creation.workspace.workspace_service import build_workspace_payload
from apps.skill.llm.chat import LlmService

User = get_user_model()


class Command(BaseCommand):
    help = "真实 LLM 同步跑通工作台主链（默认 10 集）；输出 JSON 联调摘要"

    def add_arguments(self, parser):
        parser.add_argument("--episodes", type=int, default=10)
        parser.add_argument("--theme", default="sweet-pet")
        parser.add_argument("--phone", default="13900009999", help="联调测试用户手机号")
        parser.add_argument("--project-id", default="", help="复用已有工作台项目")
        parser.add_argument("--nodes", default="2,3,4,5", help="逗号分隔节点，默认 2–5")
        parser.add_argument("--skip-post", action="store_true", help="跳过后处理链")
        parser.add_argument("--coins", type=int, default=50000, help="为测试用户充值金币")

    def handle(self, *args, **options):
        if not LlmService.is_enabled():
            raise CommandError("LLM 未启用，请配置 FUSION_LLM_ENABLED 与 SkillConfig")

        try:
            user = User.objects.get_by_natural_key(options["phone"])
        except User.DoesNotExist:
            user = User.objects.create_user(phone=options["phone"], password="live-test-pass")
        wallet = BillingService.get_or_create_wallet(user)
        if wallet.balance < options["coins"]:
            BillingService.credit(
                user,
                options["coins"] - wallet.balance,
                action_key="admin.adjust",
                remark="工作台联调充值",
            )
        from apps.membership.models import MembershipPlan
        from apps.membership.services import MembershipService

        plan = MembershipPlan.objects.filter(is_active=True).order_by("sort_order").first()
        if plan:
            MembershipService.activate_membership(user, plan)

        project = self._resolve_project(user, options)
        nodes = [int(n.strip()) for n in options["nodes"].split(",") if n.strip()]

        report: Dict[str, Any] = {
            "project_id": str(project.id),
            "episode_count": project.episode_count,
            "steps": [],
        }
        started = time.time()

        for node in nodes:
            step = self._run_node(project, node)
            report["steps"].append(step)
            if step.get("status") != "done":
                self._emit(report, started)
                raise CommandError(f"节点 {node} 失败: {step.get('error')}")

        if 5 in nodes and not options["skip_post"]:
            post = run_agent_post_chain.call(str(project.id))
            project.refresh_from_db()
            report["post_chain"] = post
            report["project_status_after_post"] = project.status

        payload = build_workspace_payload(project)
        report["workspace"] = {
            "can_export_zip": payload.get("can_export_zip"),
            "can_share": payload.get("can_share"),
            "completed_skill_count": payload.get("completed_skill_count"),
            "post_script_status": (payload.get("post_script") or {}).get("status"),
        }
        report["artifacts"] = self._artifact_snapshot(project)

        if project.status == Project.STATUS_COMPLETED:
            try:
                share = CreationService.generate_share_link(str(project.id), user)
                report["share_ok"] = bool(share.get("share_token"))
            except Exception as exc:  # noqa: BLE001
                report["share_ok"] = False
                report["share_error"] = str(exc)

        from apps.creation.script_export import build_work_zip, project_has_exportable_content

        report["export_zip_bytes"] = len(build_work_zip(project)) if project_has_exportable_content(project) else 0

        self._emit(report, started)

    def _emit(self, report: Dict[str, Any], started: float) -> None:
        report["elapsed_seconds"] = round(time.time() - started, 1)
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))

    @transaction.atomic
    def _resolve_project(self, user, options) -> Project:
        if options["project_id"]:
            return Project.objects.select_for_update().get(id=options["project_id"], user=user)

        data = {
            "theme": options["theme"],
            "core_idea": "联调：甜宠女主逆袭，契约婚姻后真相揭开。",
            "episode_count": options["episodes"],
            "format_variant": "B",
            "audience": "18-35岁女性",
            "reference_work": "",
            "target_platform": "douyin",
            "pipeline_mode": Project.MODE_WORKSPACE,
            "creation_entry": "from-scratch",
        }
        project, _ = CreationService.submit(user, data)
        return project

    def _run_node(self, project: Project, node_index: int) -> Dict[str, Any]:
        t0 = time.time()
        if node_index == 4:
            return self._run_outline_chain(project, t0)
        if node_index == 5:
            return self._run_script_batches(project, t0)

        out = _run_skill_node_core(str(project.id), node_index)
        project.refresh_from_db()
        return self._step_result(node_index, out, t0, project)

    def _run_outline_chain(self, project: Project, t0: float) -> Dict[str, Any]:
        framework = _run_skill_node_core(str(project.id), 4, outline_mode="framework")
        project.refresh_from_db()
        if framework.get("status") != "done":
            return {
                "node_index": 4,
                "phase": "framework",
                "status": framework.get("status"),
                "error": framework.get("error"),
                "elapsed": round(time.time() - t0, 1),
            }

        from apps.creation.workspace.workspace_editor import compute_outline_fill_all_range

        o_from, o_to, _ = compute_outline_fill_all_range(project)
        fill = _run_skill_node_core(
            str(project.id),
            4,
            script_from=o_from,
            script_to=o_to,
            outline_mode="episodes",
        )
        project.refresh_from_db()
        return {
            "node_index": 4,
            "phase": "fill_all",
            "status": fill.get("status"),
            "error": fill.get("error"),
            "episode_range": [o_from, o_to],
            "elapsed": round(time.time() - t0, 1),
            "artifact_keys": list((get_artifact(project, "series_outline") or {}).keys())[:12],
        }

    def _run_script_batches(self, project: Project, t0: float) -> Dict[str, Any]:
        from apps.creation.workspace.workspace_editor import compute_script_batch_range

        batches: List[Dict[str, Any]] = []
        while True:
            project.refresh_from_db()
            script_from, script_to, _ = compute_script_batch_range(project)
            out = _run_skill_node_core(
                str(project.id),
                5,
                script_from=script_from,
                script_to=script_to,
            )
            batches.append(
                {
                    "from": script_from,
                    "to": script_to,
                    "status": out.get("status"),
                    "error": out.get("error"),
                }
            )
            if out.get("status") != "done":
                return {
                    "node_index": 5,
                    "status": out.get("status"),
                    "error": out.get("error"),
                    "batches": batches,
                    "elapsed": round(time.time() - t0, 1),
                }
            scripts = get_artifact(project, "episode_scripts") or {}
            eps = scripts.get("episodes") or []
            nums = {
                int(e.get("episodeNumber") or e.get("episode") or 0)
                for e in eps
                if isinstance(e, dict)
            }
            nums.discard(0)
            if len(nums) >= int(project.episode_count or 0):
                break
            if len(batches) > 50:
                return {
                    "node_index": 5,
                    "status": "failed",
                    "error": "批次超过上限",
                    "batches": batches,
                    "elapsed": round(time.time() - t0, 1),
                }

        return {
            "node_index": 5,
            "status": "done",
            "batches": batches,
            "episode_count": len(nums),
            "elapsed": round(time.time() - t0, 1),
        }

    def _step_result(self, node_index: int, out: dict, t0: float, project: Project) -> Dict[str, Any]:
        key_map = {
            2: "structure_plan",
            3: "character_bible",
            4: "series_outline",
            5: "episode_scripts",
        }
        art = get_artifact(project, key_map.get(node_index, "")) or {}
        checks: Dict[str, Any] = {}
        if node_index == 2:
            checks["sixStagePlan"] = len(art.get("sixStagePlan") or [])
            checks["keyReversalPoints"] = len(art.get("keyReversalPoints") or [])
        if node_index == 3:
            checks["characterCount"] = len(art.get("protagonists") or []) + len(art.get("antagonists") or [])
        return {
            "node_index": node_index,
            "status": out.get("status"),
            "error": out.get("error"),
            "elapsed": round(time.time() - t0, 1),
            "checks": checks,
        }

    def _artifact_snapshot(self, project: Project) -> Dict[str, Any]:
        brief = get_artifact(project, "project_brief") or {}
        structure = get_artifact(project, "structure_plan") or {}
        outline = get_artifact(project, "series_outline") or {}
        scripts = get_artifact(project, "episode_scripts") or {}
        return {
            "brief_has_trend": bool(brief.get("trendFormula") or brief.get("writingBrief")),
            "six_stages": len(structure.get("sixStagePlan") or []),
            "reversals": len(structure.get("keyReversalPoints") or []),
            "outline_episodes": len(outline.get("episodes") or []),
            "script_episodes": len(scripts.get("episodes") or []),
            "review_passed": (get_artifact(project, "review_report") or {}).get("passed"),
            "overall_score": (get_artifact(project, "script_score_report") or {}).get("overallScore"),
        }
