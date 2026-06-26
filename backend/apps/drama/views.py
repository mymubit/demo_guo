# -*- coding: utf-8 -*-
"""Drama Skills API Views"""
from __future__ import annotations

import logging

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.creation.models import Project
from apps.drama.constants import DramaTrackMode
from apps.drama.models import DramaEpisodeArtifact, DramaEpisodeQuality, DramaRoleExecution
from apps.drama.serializers import (
    DramaWorkspaceCreateSerializer,
    DramaWorkspaceSerializer,
    DramaRoleExecutionSerializer,
    ModelConfigSerializer,
    WordCountValidateSerializer,
)
from apps.drama.services import DramaQualityService, DramaRoleService, DramaWordCountService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 角色列表
# ---------------------------------------------------------------------------

class DramaRoleListView(APIView):
    """获取 drama 所有角色分组列表（12个可见角色）"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.drama.defaults import DRAMA_VISIBLE_ROLES

        data = DramaRoleService.get_all_roles_grouped()
        total = sum(len(d["roles"]) for d in data)
        composite_count = sum(
            1 for dept in data for role in dept["roles"] if role.get("is_composite")
        )
        return Response({
            "code": 0,
            "message": "success",
            "data": {
                "departments": data,
                "total_roles": total,
                "visible_roles": len(DRAMA_VISIBLE_ROLES),
                "fast_track_count": 8,
                "composite_count": composite_count,
            },
        })


class ThemeMatrixView(APIView):
    """题材四轴矩阵与预设组合（SSOT: drama-skills/foundation/theme-matrix.yaml）"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.drama.theme_matrix_service import build_theme_matrix_ui_config

        config = build_theme_matrix_ui_config()
        if not config:
            return Response(
                {
                    "code": 50001,
                    "message": "题材矩阵配置不可用，请检查 drama-skills 同步状态",
                    "data": None,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"code": 0, "message": "success", "data": config})


# ---------------------------------------------------------------------------
# 工作区
# ---------------------------------------------------------------------------

class DramaWorkspaceViewSet(ModelViewSet):
    """Drama Project CRUD + 进度查询"""
    permission_classes = [IsAuthenticated]
    serializer_class = DramaWorkspaceSerializer

    def get_queryset(self):
        return Project.objects.filter(
            user=self.request.user,
            track_mode__in=[DramaTrackMode.FAST, DramaTrackMode.EXPERT],
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        """兼容 /api/works/?scope=drama 的列表接口，返回 Project + Drama 数据"""
        from apps.creation.services.works import build_user_work_list_page

        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = min(100, max(1, int(request.query_params.get("page_size", 100))))
        except (TypeError, ValueError):
            page_size = 100

        payload = build_user_work_list_page(
            request.user,
            page=page,
            page_size=page_size,
            scope="drama",
            ordering="newest",
        )
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": payload["items"],
                "pagination": payload["pagination"],
            }
        )

    def create(self, request):
        ser = DramaWorkspaceCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        with transaction.atomic():
            shared_id = d.get("project_id") or __import__("uuid").uuid4()
            project = Project.objects.create(
                id=shared_id,
                user=request.user,
                title=d["title"],
                theme=d["theme"],
                episode_count=d["episode_count"],
                target_platform=d["target_platform"],
                track_mode=d["track_mode"],
                drama_stage="strategy",
                pipeline_mode=Project.MODE_WORKSPACE,
                creation_entry="from-scratch",
                core_idea=(d.get("core_idea") or d["title"]).strip(),
            )

        return Response(
            {"code": 0, "message": "success", "data": DramaWorkspaceSerializer(project).data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="progress")
    def progress(self, request, pk=None):
        """获取项目进度，包括角色执行状态和剧集完成情况"""
        project = self.get_object()
        from apps.drama.defaults import DRAMA_FAST_TRACK_ROLES, DRAMA_ROLE_DEFAULTS, DRAMA_VISIBLE_ROLES
        from apps.drama.progress_service import DramaProgressService
        from apps.drama.services import DramaRoleRunService

        DramaRoleRunService.fail_stale_active_executions(project)
        DramaProgressService.recompute_project_state(project)
        project.refresh_from_db()

        if project.track_mode == "fast":
            all_role_ids = list(DRAMA_VISIBLE_ROLES)
        else:
            all_role_ids = [r["agent_id"] for r in DRAMA_ROLE_DEFAULTS]

        # tier层级映射
        tier_map = {r["agent_id"]: r.get("tier", 3) for r in DRAMA_ROLE_DEFAULTS}

        completed = set(project.completed_roles or [])
        role_progress = [
            {
                "agent_id": r,
                "is_completed": r in completed,
                "tier": tier_map.get(r, 1 if r in DRAMA_FAST_TRACK_ROLES else 3),
                "execution": None,
            }
            for r in all_role_ids
        ]

        executions = {}
        for exec_obj in DramaRoleExecution.objects.filter(
            project=project
        ).select_related("project").order_by("-created_at"):
            if exec_obj.agent_id not in executions:
                executions[exec_obj.agent_id] = exec_obj
        for item in role_progress:
            exec_obj = executions.get(item["agent_id"])
            if exec_obj:
                item["execution"] = DramaRoleExecutionSerializer(exec_obj).data

        from apps.drama.outline_progress import summarize_series_outline_progress
        from apps.drama.episode_artifact_store import (
            EPISODE_SCRIPTS_CONFIG,
            NARRATIVE_PLAN_CONFIG,
            POLISHED_SCRIPT_CONFIG,
            summarize_episode_blob_progress,
        )

        payload = DramaProgressService.build_progress_payload(project)
        payload["roles"] = role_progress
        payload["outline_progress"] = summarize_series_outline_progress(project)
        payload["script_progress"] = summarize_episode_blob_progress(
            project, EPISODE_SCRIPTS_CONFIG, batch_size=5
        )
        payload["polish_progress"] = summarize_episode_blob_progress(
            project, POLISHED_SCRIPT_CONFIG, batch_size=5
        )
        payload["narrative_progress"] = summarize_episode_blob_progress(
            project, NARRATIVE_PLAN_CONFIG, batch_size=5
        )
        script_prog = payload["script_progress"]
        payload["episode_progress"] = {
            "total": script_prog["expected"],
            "completed": script_prog["generated"],
            "rate": script_prog["completion_rate"],
        }

        return Response({
            "code": 0,
            "message": "success",
            "data": payload,
        })

    @action(detail=True, methods=["post"], url_path=r"run/(?P<role_id>[^/]+)")
    def run_role(self, request, pk=None, role_id=None):
        """
        执行指定角色任务

        支持的参数：
        - episode_range: str  例如 "1-5"，指定集数范围（script-writer / plot-architect 支持）
        - episode_count: int  总集数，给 plot-architect 使用
        - outline_mode: str  plot-architect 专用：full | episodes_only | structure_only
        - blob_mode: str  叙事/剧本/润色等分批角色：full | episodes_only | structure_only
        - artifact_mode: str  outline_mode / blob_mode 通用别名
        - custom_params: dict  自定义参数
        - priority: str  "normal" | "high"
        """
        project = self.get_object()

        from apps.agent.models import AgentDefinition
        from apps.drama.services import DramaRoleRunService

        DramaRoleRunService.fail_stale_active_executions(project)

        agent = AgentDefinition.objects.filter(
            agent_id=role_id, category="drama_skills", is_enabled=True
        ).first()
        if not agent:
            return Response(
                {"code": 404, "message": f"角色 {role_id} 不存在或未启用"},
                status=status.HTTP_404_NOT_FOUND,
            )

        episode_range = request.data.get("episode_range", "")
        episode_count = request.data.get("episode_count", project.episode_count)
        outline_mode = request.data.get("outline_mode", "")
        blob_mode = request.data.get("blob_mode", "") or request.data.get("artifact_mode", "")
        custom_params = request.data.get("custom_params") or {}

        ep_start, ep_end = None, None
        if episode_range and "-" in str(episode_range):
            try:
                parts = str(episode_range).split("-")
                ep_start = int(parts[0])
                ep_end = int(parts[1])
                if ep_start < 1 or ep_end > project.episode_count or ep_start > ep_end:
                    return Response(
                        {"code": 4001, "message": f"集数范围 {episode_range} 无效，总集数为{project.episode_count}集"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except (ValueError, IndexError):
                return Response(
                    {"code": 4001, "message": "episode_range格式错误，请使用'开始-结束'格式，如'1-5'"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        run_params = DramaRoleRunService.build_run_params(project)
        if ep_start and ep_end:
            run_params["episode_range"] = str(episode_range)
            run_params["episode_start"] = ep_start
            run_params["episode_end"] = ep_end
            run_params["episode_from"] = ep_start
            run_params["episode_to"] = ep_end
        if episode_count:
            run_params["episode_count"] = int(episode_count)
        if outline_mode:
            run_params["outline_mode"] = str(outline_mode).strip()
        if blob_mode:
            run_params["blob_mode"] = str(blob_mode).strip()
        if isinstance(custom_params, dict):
            run_params.update(custom_params)

        is_structure_run = (
            run_params.get("outline_mode") == "structure_only"
            or run_params.get("blob_mode") == "structure_only"
        )

        try:
            exec_record, is_new = DramaRoleRunService.enqueue_role_run(
                project,
                role_id,
                request.user,
                params=run_params,
            )
        except ValueError as exc:
            return Response(
                {"code": 4002, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[DramaRun] enqueue failed project=%s role=%s", project.id, role_id)
            return Response(
                {"code": 5001, "message": f"任务提交失败：{exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if is_structure_run:
            scope_desc = "全剧结构（六阶段 / 伏笔等）"
        elif ep_start and ep_end:
            scope_desc = f"第{ep_start}-{ep_end}集（共{ep_end - ep_start + 1}集）"
        elif role_id == "drama.plot-architect":
            scope_desc = f"共{episode_count}集大纲"
        else:
            scope_desc = "整体执行"

        from apps.drama.models import DramaEpisodePlan
        if ep_start and ep_end:
            DramaEpisodePlan.objects.filter(
                project=project,
                episode_number__gte=ep_start,
                episode_number__lte=ep_end,
                status__in=["pending", "fail"],
            ).update(status=DramaEpisodePlan.EpisodeStatus.QUEUED)

        message = (
            f"{agent.name_zh} 已提交执行 · {scope_desc}"
            if is_new
            else f"{agent.name_zh} 仍在执行中"
        )

        return Response({
            "code": 0,
            "message": message,
            "data": {
                "project_id": str(project.id),
                "role_id": role_id,
                "role_name": agent.name_zh,
                "execution_id": str(exec_record.id),
                "status": exec_record.status,
                "scope": scope_desc,
                "episode_range": episode_range or None,
                "is_new": is_new,
            },
        })


# ---------------------------------------------------------------------------
# 字数校验
# ---------------------------------------------------------------------------

class WordCountValidateView(APIView):
    """剧本字数校验"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = WordCountValidateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        result = DramaWordCountService.validate_episode(
            content=ser.validated_data["content"],
            episode_number=ser.validated_data["episode_number"],
        )

        return Response({"code": 0, "message": "success", "data": result})


# ---------------------------------------------------------------------------
# Token/统计
# ---------------------------------------------------------------------------

class TokenStatsView(APIView):
    """Token 消耗统计"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            days = int(request.query_params.get("days", 30))
            if days < 1 or days > 365:
                days = 30
        except (TypeError, ValueError):
            days = 30

        user_only = request.query_params.get("user_only", "true").lower() == "true"

        try:
            if user_only:
                user_id = request.user.id
            else:
                user_id = None
            data = DramaRoleService.get_token_stats(user_id=user_id, days=days)
            return Response({"code": 0, "message": "success", "data": data})
        except Exception as e:
            logger.exception("Error fetching token stats user=%s", request.user.id)
            return Response({"code": 500, "message": "获取统计数据失败，请稍后重试"}, status=500)


# ---------------------------------------------------------------------------
# 模型配置管理
# ---------------------------------------------------------------------------

class ModelConfigView(APIView):
    """配置各角色LLM模型参数"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            from apps.agent.models import AgentLlmRouteConfig
            from apps.skill.models import LlmProvider

            routes = AgentLlmRouteConfig.objects.filter(
                route_key__startswith="drama."
            ).select_related("llm_provider")

            providers = LlmProvider.objects.filter(is_active=True).values("id", "name", "provider_type")

            config_data = []
            for route in routes.order_by("sort_order"):
                config_data.append({
                    "agent_id": route.route_key,
                    "display_name": route.display_name,
                    "provider_id": route.llm_provider_id,
                    "provider_name": route.llm_provider.name if route.llm_provider else None,
                    "model_name": getattr(route, "model_name", ""),
                    "temperature": route.temperature,
                    "max_completion_tokens": route.max_completion_tokens,
                    "is_active": route.is_active,
                })

            return Response({
                "code": 0,
                "message": "success",
                "data": {
                    "configs": config_data,
                    "available_providers": list(providers),
                },
            })
        except Exception as e:
            logger.exception("Error fetching model configs")
            return Response({"code": 500, "message": "获取模型配置失败，请稍后重试"}, status=500)

    def put(self, request):
        try:
            ser = ModelConfigSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            d = ser.validated_data

            from apps.agent.models import AgentLlmRouteConfig

            try:
                route = AgentLlmRouteConfig.objects.get(route_key=d["agent_id"])
            except AgentLlmRouteConfig.DoesNotExist:
                return Response(
                    {"code": 404, "message": f"角色 {d['agent_id']} 不存在"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if d.get("provider_id"):
                from apps.skill.models import LlmProvider
                try:
                    provider = LlmProvider.objects.get(id=d["provider_id"])
                    route.llm_provider = provider
                except LlmProvider.DoesNotExist:
                    return Response(
                        {"code": 404, "message": f"Provider {d['provider_id']} 不存在"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                route.llm_provider = None

            route.model_name = d.get("model_name", "")
            route.temperature = d.get("temperature", 0.7)
            route.max_completion_tokens = d.get("max_completion_tokens", 8000)
            route.is_active = d.get("is_active", True)
            route.save(update_fields=["llm_provider", "model_name", "temperature", "max_completion_tokens", "is_active", "updated_at"])

            return Response({"code": 0, "message": "配置已更新"})
        except Exception as e:
            logger.exception("Error updating model config")
            return Response({"code": 500, "message": "更新配置失败，请稍后重试"}, status=500)


# ---------------------------------------------------------------------------
# 质量评估
# ---------------------------------------------------------------------------

class QualityRadarView(APIView):
    """获取8维度质量雷达图，支持单集和全剧汇总"""
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(
                id=project_id,
                user=request.user,
                track_mode__in=[DramaTrackMode.FAST, DramaTrackMode.EXPERT],
            )
        except Project.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        episode_number = request.query_params.get("episode")
        episode_num_int = None

        if episode_number:
            try:
                episode_num_int = int(episode_number)
            except (TypeError, ValueError):
                return Response(
                    {"code": 400, "message": "参数错误：episode必须是有效数字"},
                    status=400,
                )

            if episode_num_int < 1 or episode_num_int > project.episode_count:
                return Response(
                    {"code": 400, "message": f"集数范围无效：必须在1-{project.episode_count}之间"},
                    status=400,
                )

        try:
            if episode_num_int:
                try:
                    eq = DramaEpisodeQuality.objects.get(
                        project=project,
                        episode_number=episode_num_int,
                    )
                    scores = eq.scores
                    word_count_result = eq.word_count_result
                except DramaEpisodeQuality.DoesNotExist:
                    scores = {}
                    word_count_result = None
            else:
                scores = project.quality_scores or {}
                word_count_result = None

            detailed = DramaQualityService.build_detailed_quality_report(
                scores=scores,
                episode_number=episode_num_int,
                word_count_result=word_count_result,
            )

            radar_data = [
                {
                    "dimension": d["name"],
                    "key": d["key"],
                    "score": scores.get(d["key"], 0),
                    "weight": d["weight"],
                }
                for d in DramaQualityService.DIMENSIONS
            ]

            episode_qualities = list(
                DramaEpisodeQuality.objects.filter(project=project)
                .values("episode_number", "scores")
                .order_by("episode_number")
            )
            series_summary = DramaQualityService.build_series_quality_summary(episode_qualities)

            return Response({
                "code": 0,
                "message": "success",
                "data": {
                    "project_id": str(project.id),
                    "overall_score": detailed["overall_score"],
                    "grade": detailed["grade"],
                    "grade_desc": detailed["grade_desc"],
                    "radar": radar_data,
                    "dimensions": detailed["dimensions"],
                    "all_issues": detailed["all_issues"],
                    "error_count": detailed["error_count"],
                    "warning_count": detailed["warning_count"],
                    "top_suggestions": detailed["top_suggestions"],
                    "series_summary": series_summary,
                },
            })
        except Exception as e:
            logger.exception("Error fetching quality radar project=%s episode=%s", project_id, episode_number)
            return Response({"code": 500, "message": "获取质量报告失败，请稍后重试"}, status=500)


class EpisodeQualityView(APIView):
    """单集质量报告提交/查询接口"""
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """获取所有单集质量列表"""
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        qualities = DramaEpisodeQuality.objects.filter(project=project).order_by("episode_number")
        results = []
        for eq in qualities:
            results.append({
                "episode_number": eq.episode_number,
                "overall_score": eq.get_overall_score(),
                "grade": eq.get_grade(),
                "issue_count": len(eq.issues or []),
                "error_count": sum(1 for i in (eq.issues or []) if i.get("severity") == "error"),
                "word_count": eq.word_count_result.get("word_count", {}).get("total", 0) if eq.word_count_result else 0,
                "has_suggestions": bool(eq.issues),
                "summary": eq.summary,
                "updated_at": eq.updated_at.isoformat(),
            })

        return Response({
            "code": 0,
            "message": "success",
            "data": {
                "project_id": str(project.id),
                "total_episodes": project.episode_count,
                "evaluated_count": len(results),
                "episodes": results,
            },
        })

    def post(self, request, project_id):
        """
        提交单集质量评估结果（由 quality-reporter 角色调用）

        会根据问题维度自动推荐修复角色：
        - 格式/对白/结构/角色问题 → drama.polish-master（润色大师）
        - 情绪/钩子/节奏问题 → drama.narrative-engineer（叙事工程师）
        返回 pending_suggestions 供前端展示一键修复建议
        """
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        episode_number = request.data.get("episode_number")
        scores = request.data.get("scores", {})
        issues = request.data.get("issues", [])
        summary = request.data.get("summary", "")
        word_count_result = request.data.get("word_count_result", {})
        auto_trigger_fixes = request.data.get("auto_trigger_fixes", True)

        if not episode_number:
            return Response({"code": 4001, "message": "episode_number 不能为空"}, status=400)

        # 如果没有传issues，自动从分数检测生成
        detailed_report = DramaQualityService.build_detailed_quality_report(
            scores=scores,
            episode_number=int(episode_number),
            word_count_result=word_count_result,
        )
        # 补充issues内容
        if not issues and detailed_report.get("all_issues"):
            issues = detailed_report["all_issues"]

        with transaction.atomic():
            eq, created = DramaEpisodeQuality.objects.update_or_create(
                project=project,
                episode_number=int(episode_number),
                defaults={
                    "scores": scores,
                    "issues": issues,
                    "summary": summary,
                    "word_count_result": word_count_result,
                    "evaluated_by_agent": request.data.get("agent_id", "drama.quality-reporter"),
                },
            )

        # 生成一键修复建议
        pending_suggestions = []
        if auto_trigger_fixes and issues:
            # 根据问题维度映射到对应修复角色
            FIX_ROLE_MAP = {
                # 格式/对白/结构/角色问题交给润色大师，优先级1-2
                "format":     {"role": "drama.polish-master", "role_name": "润色大师", "priority": 1},
                "dialogue":   {"role": "drama.polish-master", "role_name": "润色大师", "priority": 1},
                "structure":  {"role": "drama.polish-master", "role_name": "润色大师", "priority": 2},
                "emotion":    {"role": "drama.narrative-engineer", "role_name": "叙事工程师", "priority": 2},
                "character":  {"role": "drama.polish-master", "role_name": "润色大师", "priority": 2},
                "hooks":      {"role": "drama.narrative-engineer", "role_name": "叙事工程师", "priority": 3},
            }

            triggered_roles = set()
            for issue in issues:
                # 根据维度名称查找 key
                dim_name = issue.get("dimension", "")
                dim_key = next(
                    (d["key"] for d in DramaQualityService.DIMENSIONS if d["name"] == dim_name),
                    None
                )
                if dim_key and dim_key in FIX_ROLE_MAP:
                    fix_info = FIX_ROLE_MAP[dim_key]
                    role_id = fix_info["role"]
                    if role_id not in triggered_roles:
                        triggered_roles.add(role_id)
                        pending_suggestions.append({
                            "trigger_role": role_id,
                            "trigger_role_name": fix_info["role_name"],
                            "priority": fix_info["priority"],
                            "reason": f"检测到{dim_name}维度问题，建议由{fix_info['role_name']}修复",
                            "issues": [i for i in issues if i.get("dimension") == dim_name],
                            "episode_number": int(episode_number),
                            "status": "pending",  # pending → confirmed → applied
                        })

            # 按优先级排序
            pending_suggestions.sort(key=lambda x: x["priority"])

        return Response({
            "code": 0,
            "message": "质量报告已保存",
            "data": {
                "episode_number": eq.episode_number,
                "overall_score": eq.get_overall_score(),
                "grade": eq.get_grade(),
                "created": created,
                "detailed_report": detailed_report,
                # 一键修复建议列表
                "pending_fix_suggestions": pending_suggestions,
                "fix_suggestion_count": len(pending_suggestions),
            },
        })


class EpisodeArtifactView(APIView):
    """单集剧本内容获取与修改建议应用"""
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """获取单集剧本或剧集列表"""
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        episode_number = request.query_params.get("episode")
        artifact_key = request.query_params.get("key", "episode_script")

        if not episode_number:
            # 返回所有剧集的版本列表
            episodes = (
                DramaEpisodeArtifact.objects.filter(
                    project=project,
                    artifact_key=artifact_key,
                )
                .order_by("episode_number", "-version")
                .values("episode_number", "version", "word_count", "quality_score", "updated_at")
                .distinct()
            )
            return Response({
                "code": 0,
                "message": "success",
                "data": {
                    "artifact_key": artifact_key,
                    "episodes": list(episodes),
                    "total_episodes": project.episode_count,
                    "completed_episodes": DramaEpisodeArtifact.objects.filter(
                        project=project, artifact_key=artifact_key,
                    ).values("episode_number").distinct().count(),
                },
            })

        # 获取指定单集内容
        try:
            artifact = DramaEpisodeArtifact.objects.filter(
                project=project,
                episode_number=int(episode_number),
                artifact_key=artifact_key,
            ).order_by("-version").first()

            if not artifact:
                return Response({"code": 404, "message": f"第{episode_number}集剧本不存在"}, status=404)

            return Response({
                "code": 0,
                "message": "success",
                "data": {
                    "episode_number": artifact.episode_number,
                    "artifact_key": artifact.artifact_key,
                    "version": artifact.version,
                    "content": artifact.content,
                    "word_count": artifact.word_count,
                    "quality_score": artifact.quality_score,
                    "diff_summary": artifact.diff_summary,
                    "produced_by_agent": artifact.produced_by_agent,
                    "updated_at": artifact.updated_at.isoformat(),
                },
            })
        except DramaEpisodeArtifact.DoesNotExist:
            return Response({"code": 404, "message": f"第{episode_number}集剧本不存在"}, status=404)
        except (TypeError, ValueError) as e:
            logger.warning("Invalid episode_number parameter: %s", e)
            return Response({"code": 400, "message": "参数错误：episode_number必须是有效数字"}, status=400)
        except Exception as e:
            logger.exception("Error fetching episode artifact project=%s episode=%s", project_id, episode_number)
            return Response({"code": 500, "message": "获取剧本内容失败，请稍后重试"}, status=500)

    def post(self, request, project_id):
        """应用修改建议，创建新版本剧本"""
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        episode_number = request.data.get("episode_number")
        artifact_key = request.data.get("artifact_key", "episode_script")
        suggestions = request.data.get("suggestions", [])
        agent_id = request.data.get("agent_id", "drama.polish-master")

        if not episode_number:
            return Response({"code": 4001, "message": "episode_number 不能为空"}, status=400)

        # 获取当前版本
        current = DramaEpisodeArtifact.objects.filter(
            project=project,
            episode_number=int(episode_number),
            artifact_key=artifact_key,
        ).order_by("-version").first()

        current_content = current.content if current else {}
        current_version = current.version if current else 0

        # 应用建议
        result = DramaQualityService.apply_suggestions_to_episode(
            current_content=str(current_content),
            suggestions=suggestions,
            agent_id=agent_id,
        )

        with transaction.atomic():
            new_artifact = DramaEpisodeArtifact.objects.create(
                project=project,
                episode_number=int(episode_number),
                artifact_key=artifact_key,
                version=current_version + 1,
                content=current_content,
                diff_summary=result["diff_summary"],
                produced_by_agent=agent_id,
                word_count=current.word_count if current else 0,
            )

        return Response({
            "code": 0,
            "message": "修改建议功能开发中，当前为占位实现，暂未实际修改剧本内容",
            "data": {
                "episode_number": new_artifact.episode_number,
                "new_version": new_artifact.version,
                "diff_summary": result["diff_summary"],
                "applied_count": result["applied_count"],
                "skipped_count": result["skipped_count"],
                "feature_status": "placeholder",
                "note": "剧本自动修改功能待接入LLM后开放，当前仅记录修改建议",
            },
        })


# ---------------------------------------------------------------------------
# 批量生成计划（100集模式，含token成本预估）
# ---------------------------------------------------------------------------

class GenerationPlanView(APIView):
    """
    批量生成计划

    功能包括：
    - 100集批量生成执行计划、token成本估算 + 进度追踪
    - 批量执行建议（每批5集，质量门禁自动触发重写）
    - 质量门禁（默认75分以下重写，连续失败2次熔断）
    - 批量执行进度、剩余时间、预估成本实时展示
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """获取当前生成计划和执行进度"""
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        from apps.drama.models import DramaEpisodePlan, DramaGenerationPlan

        # 获取当前计划
        plan = DramaGenerationPlan.objects.filter(project=project).first()
        episode_plans = list(
            DramaEpisodePlan.objects.filter(project=project)
            .values("episode_number", "status", "quality_score",
                    "quality_gate_passed", "batch_number", "rewrite_count", "actual_tokens")
            .order_by("episode_number")
        )

        # 计算批次信息
        total_ep = project.episode_count
        batch_size = plan.batch_size if plan else 5
        total_batches = -(-total_ep // batch_size)  # 向上取整

        # 统计各状态数量
        status_counts = {}
        for ep in episode_plans:
            s = ep["status"]
            status_counts[s] = status_counts.get(s, 0) + 1

        done_count = status_counts.get("done", 0) + status_counts.get("pass", 0)

        # Token成本预估
        avg_tokens = (
            sum(ep["actual_tokens"] for ep in episode_plans if ep["actual_tokens"] > 0)
            // max(1, sum(1 for ep in episode_plans if ep["actual_tokens"] > 0))
        ) or 12000  # 默认12000 tokens/集

        remaining = total_ep - done_count
        estimated_minutes = round(remaining * avg_tokens / 800 / 60, 1)

        return Response({
            "code": 0,
            "message": "success",
            "data": {
                "project_id": str(project.id),
                "total_episodes": total_ep,
                "batch_size": batch_size,
                "total_batches": total_batches,
                "plan_status": plan.get_status_display() if plan else "未创建",
                "quality_gate": {
                    "enabled": plan.quality_gate_enabled if plan else True,
                    "threshold": plan.quality_gate_score if plan else 75.0,
                },
                "progress": {
                    "done": done_count,
                    "total": total_ep,
                    "pct": round(done_count / total_ep * 100, 1) if total_ep > 0 else 0,
                    "status_counts": status_counts,
                },
                "cost_estimate": {
                    "remaining_episodes": remaining,
                    "avg_tokens_per_episode": avg_tokens,
                    "estimated_remaining_tokens": remaining * avg_tokens,
                    "estimated_remaining_minutes": estimated_minutes,
                    "tip": f"预计还需{int(estimated_minutes)}分钟完成，建议每次执行{batch_size}集",
                },
                "episode_plans": episode_plans,
                "batch_suggestions": GenerationPlanView._get_batch_suggestions(
                    total_ep, batch_size, done_count, status_counts
                ),
            },
        })

    @staticmethod
    def _get_batch_suggestions(total_ep, batch_size, done_count, status_counts):
        """根据执行进度给出批量执行建议"""
        remaining = total_ep - done_count
        if remaining <= 0:
            return []

        suggestions = []
        if total_ep > 50:
            suggestions.append({
                "type": "strategy",
                "title": f"建议分{-(-remaining//batch_size)}批执行，剩余{remaining}集",
                "desc": f"每批{batch_size}集，避免一次执行过多导致超时或质量下降",
            })
        if status_counts.get("fail", 0) > 0:
            suggestions.append({
                "type": "warning",
                "title": f"检测到{status_counts['fail']}个失败剧集",
                "desc": "建议先查看失败原因，修复后再继续批量执行",
            })
        fail_count = status_counts.get("fail", 0) + status_counts.get("rewrite", 0)
        if fail_count > total_ep * 0.3:
            suggestions.append({
                "type": "quality",
                "title": "失败率较高",
                "desc": "建议降低temperature参数或检查prompt配置，提升生成质量",
            })
        return suggestions

    def post(self, request, project_id):
        """创建或更新批量生成计划"""
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        from apps.drama.models import DramaEpisodePlan, DramaGenerationPlan

        batch_size = int(request.data.get("batch_size", 5))
        quality_gate_score = float(request.data.get("quality_gate_score", 75.0))
        auto_proceed = bool(request.data.get("auto_proceed", False))

        if batch_size < 1 or batch_size > 20:
            return Response({"code": 4001, "message": "批次大小请设置1-20"}, status=400)

        with transaction.atomic():
            plan, _ = DramaGenerationPlan.objects.update_or_create(
                project=project,
                defaults={
                    "batch_size": batch_size,
                    "total_batches": -(-project.episode_count // batch_size),
                    "quality_gate_enabled": True,
                    "quality_gate_score": quality_gate_score,
                    "auto_proceed_on_pass": auto_proceed,
                    "status": DramaGenerationPlan.PlanStatus.ACTIVE,
                },
            )

            # 为不存在的剧集创建计划
            existing = set(
                DramaEpisodePlan.objects.filter(project=project)
                .values_list("episode_number", flat=True)
            )
            new_plans = [
                DramaEpisodePlan(
                    project=project,
                    episode_number=ep_num,
                    batch_number=((ep_num - 1) // batch_size) + 1,
                    quality_gate_threshold=quality_gate_score,
                )
                for ep_num in range(1, project.episode_count + 1)
                if ep_num not in existing
            ]
            if new_plans:
                DramaEpisodePlan.objects.bulk_create(new_plans)

        return Response({
            "code": 0,
            "message": "生成计划已创建",
            "data": {
                "total_episodes": project.episode_count,
                "batch_size": batch_size,
                "total_batches": plan.total_batches,
                "quality_gate_score": quality_gate_score,
                "estimated_cost": plan.estimate_remaining_cost(),
                "batch_schedule": [
                    {
                        "batch": i + 1,
                        "episodes": f"{i*batch_size+1}-{min((i+1)*batch_size, project.episode_count)}",
                        "count": min(batch_size, project.episode_count - i * batch_size),
                    }
                    for i in range(plan.total_batches)
                ],
            },
        })
