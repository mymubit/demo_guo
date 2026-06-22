# -*- coding: utf-8 -*-
"""Drama Skills 核心服务层。"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class DramaWordCountService:
    """字数治理服务 — 行业字数硬标准执行。"""

    # 行业标准参数（来自 dramaskilltrae skill-thresholds.json）
    FIRST_EPISODE_MIN = 900
    FIRST_EPISODE_MAX = 1100
    OTHER_EPISODE_MIN = 700
    OTHER_EPISODE_MAX = 900
    DIALOGUE_RATIO_MIN = 0.28
    MAX_SCENES = 3

    # 非剧本内容的过滤模式（AI绘图提示词块等）
    NON_SCRIPT_PATTERNS = [
        r"```.*?```",          # 代码块（AI提示词通常在此）
        r"<!--.*?-->",         # HTML注释
        r"\[AI提示词\].*?\[/AI提示词\]",  # 自定义AI提示词块
        r"【付费卡点】.*?【/付费卡点】",
        r"【悬念钩子】.*?【/悬念钩子】",
        r"## 润色报告.*?---",  # 润色报告块
    ]

    # 台词格式：角色（情绪）：台词内容
    DIALOGUE_PATTERN = re.compile(r'^[^\n]+（[^）]+）：(.+)$', re.MULTILINE)

    # 场景头格式：数字-数字 时间 内外 地点
    SCENE_HEAD_PATTERN = re.compile(r'^\d+-\d+\s+[日夜晨昏]\s+[内外]\s+.+$', re.MULTILINE)

    @classmethod
    def clean_non_script(cls, content: str) -> str:
        """清除非剧本内容，获取纯剧本文本。"""
        cleaned = content
        for pattern in cls.NON_SCRIPT_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    @classmethod
    def count_cjk(cls, text: str) -> int:
        """统计CJK字符数量（中日韩字符）。"""
        return sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3400' <= c <= '\u4dbf')

    @classmethod
    def count_dialogue_cjk(cls, text: str) -> int:
        """统计台词部分的CJK字符数量。"""
        dialogues = cls.DIALOGUE_PATTERN.findall(text)
        return sum(cls.count_cjk(d) for d in dialogues)

    @classmethod
    def count_scenes(cls, text: str) -> int:
        """统计场景数量。"""
        return len(cls.SCENE_HEAD_PATTERN.findall(text))

    @classmethod
    def validate_episode(cls, content: str, episode_number: int) -> Dict[str, Any]:
        """
        验证单集字数是否达标。

        返回格式：
        {
            "episode": 1,
            "word_count": {"total": 1050, "target_range": [900, 1100], "status": "✅达标"},
            "dialogue_ratio": {"count": 320, "ratio": "30.5%", "target": "≥28%", "status": "✅达标"},
            "scene_count": {"count": 2, "target": "1-3", "status": "✅达标"},
            "overall": "通过",
            "recommendations": []
        }
        """
        cleaned = cls.clean_non_script(content)

        total_cjk = cls.count_cjk(cleaned)
        dialogue_cjk = cls.count_dialogue_cjk(cleaned)
        scene_count = cls.count_scenes(cleaned)

        # 字数范围
        if episode_number == 1:
            min_words, max_words = cls.FIRST_EPISODE_MIN, cls.FIRST_EPISODE_MAX
        else:
            min_words, max_words = cls.OTHER_EPISODE_MIN, cls.OTHER_EPISODE_MAX

        # 台词占比
        dialogue_ratio = dialogue_cjk / total_cjk if total_cjk > 0 else 0

        # 判定
        word_ok = min_words <= total_cjk <= max_words
        dialogue_ok = dialogue_ratio >= cls.DIALOGUE_RATIO_MIN
        scene_ok = 1 <= scene_count <= cls.MAX_SCENES

        word_status = "✅达标" if word_ok else ("❌偏短" if total_cjk < min_words else "⚠️偏长")
        dialogue_status = "✅达标" if dialogue_ok else "❌台词不足"
        scene_status = "✅达标" if scene_ok else ("⚠️场景过多" if scene_count > cls.MAX_SCENES else "⚠️无场景")

        recommendations = []
        if not word_ok:
            if total_cjk < min_words:
                deficit = min_words - total_cjk
                recommendations.append(
                    f"字数偏短（缺{deficit}字）：建议延伸情绪高点场景、增加对峙来回台词、增加环境/道具细节描写"
                )
            else:
                surplus = total_cjk - max_words
                recommendations.append(
                    f"字数偏长（多{surplus}字）：建议删除重复△动作行、压缩过渡场景、删除无功能过渡台词"
                )

        if not dialogue_ok:
            actual_pct = f"{dialogue_ratio:.1%}"
            recommendations.append(
                f"台词占比不足（{actual_pct}<28%）：建议将部分△动作改为台词传达、增加角色间的简短交锋"
            )

        if scene_count > cls.MAX_SCENES:
            recommendations.append(
                f"场景数量过多（{scene_count}>3）：建议合并功能相近的相邻小场景"
            )

        overall = "通过" if (word_ok and dialogue_ok and scene_ok) else "不通过"

        return {
            "episode": episode_number,
            "word_count": {
                "total": total_cjk,
                "target_range": [min_words, max_words],
                "deviation": total_cjk - min_words if total_cjk < min_words else (
                    total_cjk - max_words if total_cjk > max_words else 0
                ),
                "status": word_status,
            },
            "dialogue_ratio": {
                "dialogue_count": dialogue_cjk,
                "ratio": f"{dialogue_ratio:.1%}",
                "target": f"≥{cls.DIALOGUE_RATIO_MIN:.0%}",
                "status": dialogue_status,
            },
            "scene_count": {
                "count": scene_count,
                "target": f"1-{cls.MAX_SCENES}",
                "status": scene_status,
            },
            "overall": overall,
            "recommendations": recommendations,
        }

    @classmethod
    def validate_all_episodes(cls, episodes: Dict[int, str]) -> Dict[str, Any]:
        """
        批量验证所有集的字数。

        参数：
        - episodes: {episode_number: content}

        返回：
        {
            "summary": {"total": 30, "pass": 28, "fail": 2, "avg_words": 835},
            "episodes": [每集报告],
            "issues": [不达标集数列表]
        }
        """
        reports = []
        total_words = 0
        pass_count = 0
        issues = []

        for ep_num, content in sorted(episodes.items()):
            report = cls.validate_episode(content, ep_num)
            reports.append(report)
            total_words += report["word_count"]["total"]
            if report["overall"] == "通过":
                pass_count += 1
            else:
                issues.append({"episode": ep_num, "issues": report["recommendations"]})

        total = len(episodes)
        avg_words = total_words // total if total > 0 else 0

        return {
            "summary": {
                "total_episodes": total,
                "pass_count": pass_count,
                "fail_count": total - pass_count,
                "pass_rate": f"{pass_count / total:.1%}" if total > 0 else "N/A",
                "avg_words": avg_words,
                "total_words": total_words,
            },
            "episodes": reports,
            "issues": issues,
        }


class DramaRoleService:
    """Drama Skills 角色管理服务。"""

    @staticmethod
    def get_all_roles_grouped() -> List[Dict[str, Any]]:
        """
        获取36个角色，按部门分组，包含模型配置信息。

        返回格式：
        [
            {
                "dept_code": "strategy",
                "dept_name": "战略选题部",
                "dept_order": 1,
                "roles": [
                    {
                        "agent_id": "drama.market-radar",
                        "name_zh": "市场雷达",
                        "description": "...",
                        "is_fast_track": False,
                        "is_enabled": True,
                        "current_model": "GPT-4o",
                    }
                ]
            }
        ]
        """
        from apps.agent.models import AgentDefinition, AgentLlmRouteConfig
        from apps.drama.defaults import (
            DRAMA_DEPARTMENTS,
            DRAMA_FAST_TRACK_ROLES,
            DRAMA_ROLE_DEFAULTS,
        )

        defaults_by_id = {role["agent_id"]: role for role in DRAMA_ROLE_DEFAULTS}

        agents = list(
            AgentDefinition.objects.filter(
                agent_id__startswith="drama.",
                is_enabled=True,
            ).order_by("workspace_order", "agent_id")
        )

        routes = {
            r.route_key: r
            for r in AgentLlmRouteConfig.objects.filter(
                route_key__startswith="drama."
            ).select_related("llm_provider")
        }

        def resolve_dept_code(agent: AgentDefinition) -> str | None:
            ui_schema = agent.ui_schema if isinstance(agent.ui_schema, dict) else {}
            dept_code = ui_schema.get("dept")
            if dept_code:
                return dept_code
            meta = defaults_by_id.get(agent.agent_id)
            return meta.get("dept") if meta else None

        result = []
        for dept in sorted(DRAMA_DEPARTMENTS, key=lambda d: d["order"]):
            dept_roles = []
            for agent in agents:
                if resolve_dept_code(agent) != dept["code"]:
                    continue

                agent_id = agent.agent_id
                route = routes.get(agent_id)
                model_name = "未配置"
                if route and route.llm_provider:
                    model_name = route.llm_provider.name
                elif route and route.display_name:
                    model_name = route.display_name

                dept_roles.append({
                    "agent_id": agent_id,
                    "name": agent.name,
                    "name_zh": agent.name_zh,
                    "description": agent.description,
                    "workspace_order": agent.workspace_order,
                    "is_fast_track": agent_id in DRAMA_FAST_TRACK_ROLES,
                    "is_enabled": agent.is_enabled,
                    "current_model": model_name,
                    "input_contract": agent.input_contract,
                    "output_contract": agent.output_contract,
                    "runtime_policy": agent.runtime_policy,
                })

            if dept_roles:
                result.append({
                    "dept_code": dept["code"],
                    "dept_name": dept["name_zh"],
                    "dept_order": dept["order"],
                    "roles": sorted(dept_roles, key=lambda r: r["workspace_order"]),
                })

        return result

    @staticmethod
    def get_token_stats(user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """
        获取Token用量统计。

        返回按角色/时间/项目维度的统计数据。
        """
        from datetime import timedelta

        from django.db.models import Avg, Count, Sum
        from django.utils import timezone

        from apps.drama.models import DramaRoleExecution

        cutoff = timezone.now() - timedelta(days=days)
        qs = DramaRoleExecution.objects.filter(
            created_at__gte=cutoff,
            status=DramaRoleExecution.Status.SUCCESS,
        )

        if user_id:
            qs = qs.filter(drama_project__user_id=user_id)

        # 按角色聚合（注意：先values再annotate，避免聚合嵌套问题）
        from django.db.models import FloatField, ExpressionWrapper
        by_role = list(
            qs.values("agent_id", "agent_name_zh")
            .annotate(
                total_calls=Count("id"),
                total_tokens=Sum("total_tokens"),
                total_cost_cents=Sum("cost_cents"),
            )
            .order_by("-total_tokens")
        )
        # 手动计算avg_tokens
        for item in by_role:
            item["avg_tokens"] = (item["total_tokens"] or 0) / max(item["total_calls"], 1)

        # 按天聚合（最近30天）
        from django.db.models.functions import TruncDate

        by_day = list(
            qs.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                total_tokens=Sum("total_tokens"),
                total_cost_cents=Sum("cost_cents"),
                call_count=Count("id"),
            )
            .order_by("date")
        )

        # 总计
        totals = qs.aggregate(
            total_tokens=Sum("total_tokens"),
            total_cost_cents=Sum("cost_cents"),
            total_calls=Count("id"),
        )

        return {
            "period_days": days,
            "totals": {
                "total_tokens": totals["total_tokens"] or 0,
                "total_cost_cents": totals["total_cost_cents"] or 0,
                "total_calls": totals["total_calls"] or 0,
                "total_cost_yuan": round((totals["total_cost_cents"] or 0) / 100, 2),
            },
            "by_role": by_role[:20],
            "by_day": [
                {
                    "date": str(item["date"]),
                    "total_tokens": item["total_tokens"] or 0,
                    "total_cost_yuan": round((item["total_cost_cents"] or 0) / 100, 2),
                    "call_count": item["call_count"],
                }
                for item in by_day
            ],
        }


class DramaRoleRunService:
    """Drama 角色执行 — 桥接 creation.Project 与 IndependentAgentService。"""

    ACTIVE_STATUSES = (
        "pending",
        "running",
    )

    @staticmethod
    def ensure_creation_project(drama_project, core_idea: str = ""):
        """确保存在关联的 creation.Project（id = drama_project.project_id）。"""
        from apps.creation.models import Project

        defaults = {
            "user": drama_project.user,
            "theme": drama_project.genre_code,
            "core_idea": (core_idea or drama_project.title).strip() or drama_project.title,
            "episode_count": drama_project.total_episodes,
            "target_platform": drama_project.target_platform,
            "title": drama_project.title,
            "pipeline_mode": Project.MODE_WORKSPACE,
            "creation_entry": "from-scratch",
        }
        project, created = Project.objects.get_or_create(
            id=drama_project.project_id,
            defaults=defaults,
        )
        if not created:
            updates = {}
            if core_idea and not (project.core_idea or "").strip():
                updates["core_idea"] = core_idea.strip()
            if drama_project.title and not (project.title or "").strip():
                updates["title"] = drama_project.title
            if updates:
                for field, value in updates.items():
                    setattr(project, field, value)
                project.save(update_fields=list(updates.keys()) + ["updated_at"])
        return project

    @staticmethod
    def build_run_params(drama_project, creation_project) -> Dict[str, Any]:
        """从 Drama 项目字段构造 Agent 运行参数。"""
        return {
            "core_idea": (creation_project.core_idea or drama_project.title).strip(),
            "genre": drama_project.genre_code,
            "genre_hint": drama_project.genre_code,
            "episode_count": drama_project.total_episodes,
            "target_platform": drama_project.target_platform,
            "platform": drama_project.target_platform,
        }

    @classmethod
    def get_active_execution(cls, drama_project, agent_id: str):
        from apps.drama.models import DramaRoleExecution

        return (
            DramaRoleExecution.objects.filter(
                drama_project=drama_project,
                agent_id=agent_id,
                status__in=[
                    DramaRoleExecution.Status.PENDING,
                    DramaRoleExecution.Status.RUNNING,
                ],
            )
            .order_by("-created_at")
            .first()
        )

    @classmethod
    def enqueue_role_run(cls, drama_project, agent_id: str, user, params: Optional[Dict[str, Any]] = None):
        """创建执行记录并入队异步任务。"""
        from apps.agent.definition_service import AgentDefinitionService
        from apps.drama.models import DramaRoleExecution
        from apps.drama.tasks import run_drama_role
        from dj_queue.api import enqueue_on_commit

        agent = AgentDefinitionService.get_runnable(agent_id)

        existing = cls.get_active_execution(drama_project, agent_id)
        if existing:
            return existing, False

        creation_project = cls.ensure_creation_project(drama_project)
        run_params = dict(params or cls.build_run_params(drama_project, creation_project))

        with transaction.atomic():
            drama_exec = DramaRoleExecution.objects.create(
                drama_project=drama_project,
                agent_id=agent_id,
                agent_name_zh=agent.name_zh or agent.name,
                status=DramaRoleExecution.Status.RUNNING,
                input_artifacts={"params": run_params},
                started_at=timezone.now(),
            )
            enqueue_on_commit(run_drama_role, str(drama_exec.id))

        return drama_exec, True

    @classmethod
    def execute_role(cls, drama_execution_id: str, agent_run_id: str = "") -> Dict[str, Any]:
        """后台任务：调用 IndependentAgentService 并回写 DramaRoleExecution。"""
        from apps.agent.definition_service import AgentDefinitionService
        from apps.creation.agent_runtime.independent_service import IndependentAgentService
        from apps.creation.models import AgentExecutionRun
        from apps.drama.models import DramaRoleExecution

        drama_exec = DramaRoleExecution.objects.select_related(
            "drama_project", "drama_project__user"
        ).get(id=drama_execution_id)
        drama_project = drama_exec.drama_project
        user = drama_project.user
        agent_id = drama_exec.agent_id
        run_params = (drama_exec.input_artifacts or {}).get("params") or {}

        creation_project = cls.ensure_creation_project(drama_project)

        try:
            if agent_run_id:
                run = AgentExecutionRun.objects.select_related("project").get(id=agent_run_id)
            else:
                result = IndependentAgentService.enqueue_run(
                    creation_project, user, agent_id, run_params
                )
                run = result.run
                if result.should_enqueue:
                    IndependentAgentService.execute_run(run)
                else:
                    run.refresh_from_db()

            cls.sync_from_agent_run(drama_exec, run, creation_project)
            drama_exec.refresh_from_db()
            return {
                "execution_id": str(drama_exec.id),
                "agent_id": agent_id,
                "status": drama_exec.status,
                "run_id": str(run.id),
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception("[DramaRoleRun] 执行失败 execution=%s agent=%s", drama_execution_id, agent_id)
            cls._mark_failed(drama_exec, str(exc))
            raise

    @classmethod
    def sync_from_agent_run(cls, drama_exec, agent_run, creation_project) -> None:
        """将 AgentExecutionRun 结果同步到 DramaRoleExecution。"""
        from apps.agent.definition_service import AgentDefinitionService
        from apps.creation.artifact_service import get_artifact
        from apps.creation.models import AgentExecutionRun
        from apps.drama.models import DramaRoleExecution

        agent = AgentDefinitionService.get_runnable(drama_exec.agent_id)
        output_keys = [str(k) for k in (agent.output_contract or {}).get("artifacts") or []]
        output_artifacts = {}
        for key in output_keys:
            payload = get_artifact(creation_project, key)
            if payload is not None:
                output_artifacts[key] = payload

        now = timezone.now()
        elapsed = None
        if drama_exec.started_at:
            elapsed = (now - drama_exec.started_at).total_seconds()

        if agent_run.status == AgentExecutionRun.STATUS_COMPLETED:
            drama_status = DramaRoleExecution.Status.SUCCESS
        elif agent_run.status == AgentExecutionRun.STATUS_FAILED:
            drama_status = DramaRoleExecution.Status.FAILED
        elif agent_run.status == AgentExecutionRun.STATUS_RUNNING:
            drama_status = DramaRoleExecution.Status.RUNNING
        else:
            drama_status = DramaRoleExecution.Status.FAILED

        drama_exec.status = drama_status
        drama_exec.output_artifacts = output_artifacts
        drama_exec.prompt_tokens = agent_run.prompt_tokens or 0
        drama_exec.completion_tokens = agent_run.completion_tokens or 0
        drama_exec.total_tokens = agent_run.total_tokens or 0
        run_params = (drama_exec.input_artifacts or {}).get("params") or {}
        try:
            from apps.creation.agent_runtime.agent_billing import resolve_coin_cost

            drama_exec.cost_cents = resolve_coin_cost(drama_exec.agent_id, run_params)
        except Exception:  # noqa: BLE001
            drama_exec.cost_cents = 0
        input_meta = dict(drama_exec.input_artifacts or {})
        input_meta["agent_run_id"] = str(agent_run.id)
        drama_exec.input_artifacts = input_meta
        drama_exec.llm_provider = agent_run.provider_name or ""
        drama_exec.llm_model = agent_run.model_name or ""
        drama_exec.error_message = (agent_run.error_message or "")[:2000]
        drama_exec.elapsed_seconds = elapsed
        drama_exec.finished_at = now if drama_status != DramaRoleExecution.Status.RUNNING else None
        drama_exec.save(
            update_fields=[
                "status",
                "output_artifacts",
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "cost_cents",
                "input_artifacts",
                "llm_provider",
                "llm_model",
                "error_message",
                "elapsed_seconds",
                "finished_at",
            ]
        )

        if drama_status == DramaRoleExecution.Status.SUCCESS:
            cls._mark_project_role_completed(drama_exec)

    @classmethod
    def _mark_project_role_completed(cls, drama_exec) -> None:
        from apps.drama.progress_service import DramaProjectProgressService

        drama_project = drama_exec.drama_project
        completed = list(drama_project.completed_roles or [])
        if drama_exec.agent_id not in completed:
            completed.append(drama_exec.agent_id)
        drama_project.completed_roles = completed
        drama_project.total_tokens_used = (drama_project.total_tokens_used or 0) + (drama_exec.total_tokens or 0)
        drama_project.total_cost_cents = (drama_project.total_cost_cents or 0) + (drama_exec.cost_cents or 0)
        drama_project.save(
            update_fields=[
                "completed_roles",
                "total_tokens_used",
                "total_cost_cents",
                "updated_at",
            ]
        )
        DramaProjectProgressService.recompute_project_state(drama_project)

    @staticmethod
    def _mark_failed(drama_exec, message: str) -> None:
        from apps.drama.models import DramaRoleExecution

        drama_exec.status = DramaRoleExecution.Status.FAILED
        drama_exec.error_message = (message or "执行失败")[:2000]
        drama_exec.finished_at = timezone.now()
        if drama_exec.started_at:
            drama_exec.elapsed_seconds = (drama_exec.finished_at - drama_exec.started_at).total_seconds()
        drama_exec.save(
            update_fields=["status", "error_message", "finished_at", "elapsed_seconds"]
        )
