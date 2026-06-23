# -*- coding: utf-8 -*-
"""Drama Skills API Views。"""
from __future__ import annotations

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.drama.models import DramaEpisodeArtifact, DramaEpisodeQuality, DramaProject, DramaRoleExecution
from apps.drama.serializers import (
    DramaProjectCreateSerializer,
    DramaProjectSerializer,
    DramaRoleExecutionSerializer,
    ModelConfigSerializer,
    WordCountValidateSerializer,
)
from apps.drama.services import DramaQualityService, DramaRoleService, DramaWordCountService


# ---------------------------------------------------------------------------
# 角色列表
# ---------------------------------------------------------------------------

class DramaRoleListView(APIView):
    """获取36个角色列表，按部门分组。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = DramaRoleService.get_all_roles_grouped()
        return Response({
            "code": 0,
            "message": "success",
            "data": {
                "departments": data,
                "total_roles": sum(len(d["roles"]) for d in data),
                "fast_track_count": 8,
            },
        })


# ---------------------------------------------------------------------------
# 项目管理
# ---------------------------------------------------------------------------

class DramaProjectViewSet(ModelViewSet):
    """Drama Project CRUD + 进度查询。"""
    permission_classes = [IsAuthenticated]
    serializer_class = DramaProjectSerializer

    def get_queryset(self):
        return DramaProject.objects.filter(user=self.request.user).order_by("-created_at")

    def create(self, request):
        ser = DramaProjectCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        with transaction.atomic():
            shared_id = d.get("project_id") or __import__("uuid").uuid4()
            project = DramaProject.objects.create(
                id=shared_id,
                user=request.user,
                project_id=shared_id,
                title=d["title"],
                genre_code=d["genre_code"],
                total_episodes=d["total_episodes"],
                target_platform=d["target_platform"],
                track_mode=d["track_mode"],
            )
            from apps.drama.services import DramaRoleRunService

            DramaRoleRunService.ensure_creation_project(
                project,
                core_idea=d.get("core_idea") or "",
            )

        return Response(
            {"code": 0, "message": "success", "data": DramaProjectSerializer(project).data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="progress")
    def progress(self, request, pk=None):
        """获取项目进度（哪些角色已完成，含三层分级信息）。"""
        project = self.get_object()
        from apps.drama.defaults import DRAMA_FAST_TRACK_ROLES, DRAMA_ROLE_DEFAULTS

        if project.track_mode == "fast":
            all_role_ids = DRAMA_FAST_TRACK_ROLES
        else:
            all_role_ids = [r["agent_id"] for r in DRAMA_ROLE_DEFAULTS]

        # tier信息映射
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
            drama_project=project
        ).order_by("-created_at"):
            if exec_obj.agent_id not in executions:
                executions[exec_obj.agent_id] = exec_obj
        for item in role_progress:
            exec_obj = executions.get(item["agent_id"])
            if exec_obj:
                item["execution"] = DramaRoleExecutionSerializer(exec_obj).data

        episode_artifacts_count = DramaEpisodeArtifact.objects.filter(
            drama_project=project,
            artifact_key=DramaEpisodeArtifact.ArtifactKey.EPISODE_SCRIPT,
        ).values("episode_number").distinct().count()
        from apps.drama.progress_service import DramaProjectProgressService

        payload = DramaProjectProgressService.build_progress_payload(project)
        payload["roles"] = role_progress
        payload["episode_progress"] = {
            "total": project.total_episodes,
            "completed": episode_artifacts_count,
            "rate": round(episode_artifacts_count / project.total_episodes * 100, 1)
            if project.total_episodes > 0 else 0,
        }

        return Response({
            "code": 0,
            "message": "success",
            "data": payload,
        })

    @action(detail=True, methods=["post"], url_path=r"run/(?P<role_id>[^/]+)")
    def run_role(self, request, pk=None, role_id=None):
        """
        触发某个角色执行。

        请求体参数（可选）：
        - episode_range: str  如 "1-5"，指定生成集数范围（script-writer / plot-architect 使用）
        - episode_count: int  总集数（用于 plot-architect）
        - custom_params: dict  角色特定参数
        - priority: str  "normal" | "high"
        """
        project = self.get_object()

        from apps.agent.models import AgentDefinition
        agent = AgentDefinition.objects.filter(
            agent_id=role_id, category="drama_skills", is_enabled=True
        ).first()
        if not agent:
            return Response(
                {"code": 404, "message": f"角色 {role_id} 不存在或未启用"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 读取执行参数
        episode_range = request.data.get("episode_range", "")
        episode_count = request.data.get("episode_count", project.total_episodes)
        custom_params = request.data.get("custom_params", {})

        # 解析 episode_range
        ep_start, ep_end = None, None
        if episode_range and "-" in str(episode_range):
            try:
                parts = str(episode_range).split("-")
                ep_start = int(parts[0])
                ep_end = int(parts[1])
                # 校验范围合法性
                if ep_start < 1 or ep_end > project.total_episodes or ep_start > ep_end:
                    return Response(
                        {"code": 4001, "message": f"集数范围 {episode_range} 不合法（项目共{project.total_episodes}集）"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except (ValueError, IndexError):
                return Response(
                    {"code": 4001, "message": f"集数范围格式错误，应为 '开始集-结束集'，如 '1-5'"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 创建执行记录
        with transaction.atomic():
            exec_record = DramaRoleExecution.objects.create(
                drama_project=project,
                agent_id=role_id,
                agent_name_zh=agent.name_zh,
                status=DramaRoleExecution.Status.PENDING,
                input_artifacts={
                    "episode_range": episode_range or None,
                    "episode_start": ep_start,
                    "episode_end": ep_end,
                    "episode_count": episode_count,
                    "custom_params": custom_params,
                },
            )

        # 构建用户可读的执行说明
        if ep_start and ep_end:
            scope_desc = f"第{ep_start}-{ep_end}集（共{ep_end - ep_start + 1}集）"
        elif role_id == "drama.plot-architect":
            scope_desc = f"全部{episode_count}集大纲"
        else:
            scope_desc = "整体执行"

        # 分集计划同步更新
        from apps.drama.models import DramaEpisodePlan
        if ep_start and ep_end:
            DramaEpisodePlan.objects.filter(
                drama_project=project,
                episode_number__gte=ep_start,
                episode_number__lte=ep_end,
                status__in=["pending", "fail"],
            ).update(status=DramaEpisodePlan.EpisodeStatus.QUEUED)

        return Response({
            "code": 0,
            "message": f"「{agent.name_zh}」已加入执行队列 — {scope_desc}",
            "data": {
                "project_id": str(project.id),
                "role_id": role_id,
                "role_name": agent.name_zh,
                "execution_id": str(exec_record.id),
                "status": "queued",
                "scope": scope_desc,
                "episode_range": episode_range or None,
                "tip": "实际LLM执行需配置模型后生效，当前记录已建立可追踪" if not episode_range else None,
            },
        })


# ---------------------------------------------------------------------------
# 字数验证
# ---------------------------------------------------------------------------

class WordCountValidateView(APIView):
    """字数验证接口。"""
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
# Token/计费统计
# ---------------------------------------------------------------------------

class TokenStatsView(APIView):
    """Token 用量统计。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        user_only = request.query_params.get("user_only", "true").lower() == "true"

        user_id = request.user.id if user_only else None
        data = DramaRoleService.get_token_stats(user_id=user_id, days=days)

        return Response({"code": 0, "message": "success", "data": data})


# ---------------------------------------------------------------------------
# 模型配置（仅管理员）
# ---------------------------------------------------------------------------

class ModelConfigView(APIView):
    """每个角色的LLM模型配置。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取所有角色的当前模型配置。"""
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

    def put(self, request):
        """更新某个角色的模型配置。"""
        if not request.user.is_staff:
            return Response(
                {"code": 403, "message": "需要管理员权限"},
                status=status.HTTP_403_FORBIDDEN,
            )

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
        route.save(update_fields=["llm_provider", "temperature", "max_completion_tokens"])

        return Response({"code": 0, "message": "配置已更新"})


# ---------------------------------------------------------------------------
# 评分雷达数据
# ---------------------------------------------------------------------------

class QualityRadarView(APIView):
    """获取项目8维度评分雷达数据（含扣分点和改进建议）。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = DramaProject.objects.get(id=project_id, user=request.user)
        except DramaProject.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        episode_number = request.query_params.get("episode")

        if episode_number:
            # 分集质量评估
            try:
                eq = DramaEpisodeQuality.objects.get(
                    drama_project=project,
                    episode_number=int(episode_number),
                )
                scores = eq.scores
                word_count_result = eq.word_count_result
            except DramaEpisodeQuality.DoesNotExist:
                scores = {}
                word_count_result = None
        else:
            # 整剧整体评估
            scores = project.quality_scores or {}
            word_count_result = None

        # 构建详细报告（含扣分点）
        detailed = DramaQualityService.build_detailed_quality_report(
            scores=scores,
            episode_number=int(episode_number) if episode_number else None,
            word_count_result=word_count_result,
        )

        # 雷达图数据（维度分数）
        radar_data = [
            {
                "dimension": d["name"],
                "key": d["key"],
                "score": scores.get(d["key"], 0),
                "weight": d["weight"],
            }
            for d in DramaQualityService.DIMENSIONS
        ]

        # 分集概况（如果有多集评估数据）
        episode_qualities = list(
            DramaEpisodeQuality.objects.filter(drama_project=project)
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
                # 新增：详细维度报告（含扣分点和建议）
                "dimensions": detailed["dimensions"],
                "all_issues": detailed["all_issues"],
                "error_count": detailed["error_count"],
                "warning_count": detailed["warning_count"],
                "top_suggestions": detailed["top_suggestions"],
                # 分集概况
                "series_summary": series_summary,
            },
        })


class EpisodeQualityView(APIView):
    """分集质量评估接口（提交/查询单集评估结果）。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """获取所有集的质量评估概况列表。"""
        try:
            project = DramaProject.objects.get(id=project_id, user=request.user)
        except DramaProject.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        qualities = DramaEpisodeQuality.objects.filter(drama_project=project).order_by("episode_number")
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
                "total_episodes": project.total_episodes,
                "evaluated_count": len(results),
                "episodes": results,
            },
        })

    def post(self, request, project_id):
        """
        提交单集质量评估结果（由质量报告官角色执行后调用）。

        质量审查完成后，自动触发关联修复角色：
        - 格式/台词/结构问题 → drama.polish-master（精修大师）
        - 情绪/节奏/钩子问题 → drama.narrative-engineer（叙事工程师）
        这些建议作为 pending_suggestions 返回，由用户确认后应用。
        """
        try:
            project = DramaProject.objects.get(id=project_id, user=request.user)
        except DramaProject.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        episode_number = request.data.get("episode_number")
        scores = request.data.get("scores", {})
        issues = request.data.get("issues", [])
        summary = request.data.get("summary", "")
        word_count_result = request.data.get("word_count_result", {})
        auto_trigger_fixes = request.data.get("auto_trigger_fixes", True)

        if not episode_number:
            return Response({"code": 4001, "message": "episode_number 不能为空"}, status=400)

        # 构建详细质量报告（含扣分点）
        detailed_report = DramaQualityService.build_detailed_quality_report(
            scores=scores,
            episode_number=int(episode_number),
            word_count_result=word_count_result,
        )
        # 将详细issues合并到存储
        if not issues and detailed_report.get("all_issues"):
            issues = detailed_report["all_issues"]

        with transaction.atomic():
            eq, created = DramaEpisodeQuality.objects.update_or_create(
                drama_project=project,
                episode_number=int(episode_number),
                defaults={
                    "scores": scores,
                    "issues": issues,
                    "summary": summary,
                    "word_count_result": word_count_result,
                    "evaluated_by_agent": request.data.get("agent_id", "drama.quality-reporter"),
                },
            )

        # 自动触发关联修复建议
        pending_suggestions = []
        if auto_trigger_fixes and issues:
            # 按问题类型路由到对应修复角色
            FIX_ROLE_MAP = {
                # 所有格式/台词/结构/节奏问题统一路由到精修大师（整合了原7个修复角色）
                "format":     {"role": "drama.polish-master", "role_name": "精修大师", "priority": 1},
                "dialogue":   {"role": "drama.polish-master", "role_name": "精修大师", "priority": 1},
                "structure":  {"role": "drama.polish-master", "role_name": "精修大师", "priority": 2},
                "emotion":    {"role": "drama.narrative-engineer", "role_name": "叙事工程师", "priority": 2},
                "character":  {"role": "drama.polish-master", "role_name": "精修大师", "priority": 2},
                "hooks":      {"role": "drama.narrative-engineer", "role_name": "叙事工程师", "priority": 3},
            }

            triggered_roles = set()
            for issue in issues:
                dim_key = next(
                    (k for k, d in DramaQualityService.DIMENSIONS.__class__.__mro__[0]
                     if False), None  # placeholder
                ) if False else None

                # 通过维度名称推断 key
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
                            "reason": f"检测到{dim_name}问题，建议执行{fix_info['role_name']}",
                            "issues": [i for i in issues if i.get("dimension") == dim_name],
                            "episode_number": int(episode_number),
                            "status": "pending",  # pending → confirmed → applied
                        })

            # 按优先级排序
            pending_suggestions.sort(key=lambda x: x["priority"])

        return Response({
            "code": 0,
            "message": "质量评估已保存",
            "data": {
                "episode_number": eq.episode_number,
                "overall_score": eq.get_overall_score(),
                "grade": eq.get_grade(),
                "created": created,
                "detailed_report": detailed_report,
                # 自动触发的修复角色建议
                "pending_fix_suggestions": pending_suggestions,
                "fix_suggestion_count": len(pending_suggestions),
            },
        })


class EpisodeArtifactView(APIView):
    """分集产物接口（剧本内容读写 + 建议应用）。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """获取指定集、指定产物类型的最新内容。"""
        try:
            project = DramaProject.objects.get(id=project_id, user=request.user)
        except DramaProject.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        episode_number = request.query_params.get("episode")
        artifact_key = request.query_params.get("key", "episode_script")

        if not episode_number:
            # 返回所有集的摘要列表
            episodes = (
                DramaEpisodeArtifact.objects.filter(
                    drama_project=project,
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
                    "total_episodes": project.total_episodes,
                    "completed_episodes": DramaEpisodeArtifact.objects.filter(
                        drama_project=project, artifact_key=artifact_key,
                    ).values("episode_number").distinct().count(),
                },
            })

        # 返回具体集的内容
        try:
            artifact = DramaEpisodeArtifact.objects.filter(
                drama_project=project,
                episode_number=int(episode_number),
                artifact_key=artifact_key,
            ).order_by("-version").first()

            if not artifact:
                return Response({"code": 404, "message": f"第{episode_number}集暂无内容"}, status=404)

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
        except Exception as e:
            return Response({"code": 500, "message": str(e)}, status=500)

    def post(self, request, project_id):
        """应用修改建议到某集剧本（生成新版本）。"""
        try:
            project = DramaProject.objects.get(id=project_id, user=request.user)
        except DramaProject.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        episode_number = request.data.get("episode_number")
        artifact_key = request.data.get("artifact_key", "episode_script")
        suggestions = request.data.get("suggestions", [])
        agent_id = request.data.get("agent_id", "drama.polish-master")

        if not episode_number:
            return Response({"code": 4001, "message": "episode_number 不能为空"}, status=400)

        # 获取当前版本
        current = DramaEpisodeArtifact.objects.filter(
            drama_project=project,
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
                drama_project=project,
                episode_number=int(episode_number),
                artifact_key=artifact_key,
                version=current_version + 1,
                content=current_content,  # TODO: 替换为LLM修改后的内容
                diff_summary=result["diff_summary"],
                produced_by_agent=agent_id,
                word_count=current.word_count if current else 0,
            )

        return Response({
            "code": 0,
            "message": "建议已应用，新版本已保存",
            "data": {
                "episode_number": new_artifact.episode_number,
                "new_version": new_artifact.version,
                "diff_summary": result["diff_summary"],
                "applied_count": result["applied_count"],
                "skipped_count": result["skipped_count"],
                "note": result.get("note", ""),
            },
        })


# ---------------------------------------------------------------------------
# 分集生成计划（解决100集token爆炸问题）
# ---------------------------------------------------------------------------

class GenerationPlanView(APIView):
    """
    全局生成计划管理。

    核心设计思路：
    - 100集剧本不能一次性生成（token爆炸 + 质量无法控制）
    - 分批生成（默认5集/批），每批完成后立即质检
    - 质量gate（默认75分），不通过则触发重写（最多2次）
    - 支持断点续写（任何时候中断，下次从最后成功集继续）
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """获取当前生成计划和进度。"""
        try:
            project = DramaProject.objects.get(id=project_id, user=request.user)
        except DramaProject.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        from apps.drama.models import DramaEpisodePlan, DramaGenerationPlan

        # 获取或估算生成计划
        plan = DramaGenerationPlan.objects.filter(drama_project=project).first()
        episode_plans = list(
            DramaEpisodePlan.objects.filter(drama_project=project)
            .values("episode_number", "status", "quality_score",
                    "quality_gate_passed", "batch_number", "rewrite_count", "actual_tokens")
            .order_by("episode_number")
        )

        # 计算批次进度
        total_ep = project.total_episodes
        batch_size = plan.batch_size if plan else 5
        total_batches = -(-total_ep // batch_size)  # 向上取整

        # 各状态统计
        status_counts = {}
        for ep in episode_plans:
            s = ep["status"]
            status_counts[s] = status_counts.get(s, 0) + 1

        done_count = status_counts.get("done", 0) + status_counts.get("pass", 0)

        # Token和时间估算
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
                    "tip": f"约{int(estimated_minutes)}分钟，建议按批次执行（每批{batch_size}集）",
                },
                "episode_plans": episode_plans,
                # 分批建议
                "batch_suggestions": GenerationPlanView._get_batch_suggestions(
                    total_ep, batch_size, done_count, status_counts
                ),
            },
        })

    @staticmethod
    def _get_batch_suggestions(total_ep, batch_size, done_count, status_counts):
        """生成分批执行建议。"""
        remaining = total_ep - done_count
        if remaining <= 0:
            return []

        suggestions = []
        if total_ep > 50:
            suggestions.append({
                "type": "strategy",
                "title": f"建议分{-(-remaining//batch_size)}批生成剩余{remaining}集",
                "desc": f"每批{batch_size}集，完成后立即质检，低于75分自动触发重写",
            })
        if status_counts.get("fail", 0) > 0:
            suggestions.append({
                "type": "warning",
                "title": f"有{status_counts['fail']}集质检不通过",
                "desc": "建议先处理不通过的集数，再继续生成新集",
            })
        fail_count = status_counts.get("fail", 0) + status_counts.get("rewrite", 0)
        if fail_count > total_ep * 0.3:
            suggestions.append({
                "type": "quality",
                "title": "质检通过率偏低",
                "desc": "建议提高生成参数（temperature调低）或检查角色prompt配置",
            })
        return suggestions

    def post(self, request, project_id):
        """创建或更新生成计划，并初始化分集计划。"""
        try:
            project = DramaProject.objects.get(id=project_id, user=request.user)
        except DramaProject.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        from apps.drama.models import DramaEpisodePlan, DramaGenerationPlan

        batch_size = int(request.data.get("batch_size", 5))
        quality_gate_score = float(request.data.get("quality_gate_score", 75.0))
        auto_proceed = bool(request.data.get("auto_proceed", False))

        if batch_size < 1 or batch_size > 20:
            return Response({"code": 4001, "message": "每批集数应为1-20"}, status=400)

        with transaction.atomic():
            plan, _ = DramaGenerationPlan.objects.update_or_create(
                drama_project=project,
                defaults={
                    "batch_size": batch_size,
                    "total_batches": -(-project.total_episodes // batch_size),
                    "quality_gate_enabled": True,
                    "quality_gate_score": quality_gate_score,
                    "auto_proceed_on_pass": auto_proceed,
                    "status": DramaGenerationPlan.PlanStatus.ACTIVE,
                },
            )

            # 初始化所有集的计划（只创建尚未存在的）
            existing = set(
                DramaEpisodePlan.objects.filter(drama_project=project)
                .values_list("episode_number", flat=True)
            )
            new_plans = [
                DramaEpisodePlan(
                    drama_project=project,
                    episode_number=ep_num,
                    batch_number=((ep_num - 1) // batch_size) + 1,
                    quality_gate_threshold=quality_gate_score,
                )
                for ep_num in range(1, project.total_episodes + 1)
                if ep_num not in existing
            ]
            if new_plans:
                DramaEpisodePlan.objects.bulk_create(new_plans)

        return Response({
            "code": 0,
            "message": "生成计划已创建",
            "data": {
                "total_episodes": project.total_episodes,
                "batch_size": batch_size,
                "total_batches": plan.total_batches,
                "quality_gate_score": quality_gate_score,
                "estimated_cost": plan.estimate_remaining_cost(),
                "batch_schedule": [
                    {
                        "batch": i + 1,
                        "episodes": f"{i*batch_size+1}-{min((i+1)*batch_size, project.total_episodes)}",
                        "count": min(batch_size, project.total_episodes - i * batch_size),
                    }
                    for i in range(plan.total_batches)
                ],
            },
        })
