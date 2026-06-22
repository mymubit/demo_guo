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

from apps.drama.models import DramaProject, DramaRoleExecution
from apps.drama.serializers import (
    DramaProjectCreateSerializer,
    DramaProjectSerializer,
    DramaRoleExecutionSerializer,
    ModelConfigSerializer,
    WordCountValidateSerializer,
)
from apps.drama.services import DramaRoleService, DramaWordCountService


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
            project = DramaProject.objects.create(
                user=request.user,
                project_id=d.get("project_id") or __import__("uuid").uuid4(),
                title=d["title"],
                genre_code=d["genre_code"],
                total_episodes=d["total_episodes"],
                target_platform=d["target_platform"],
                track_mode=d["track_mode"],
            )

        return Response(
            {"code": 0, "message": "success", "data": DramaProjectSerializer(project).data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="progress")
    def progress(self, request, pk=None):
        """获取项目进度（哪些角色已完成）。"""
        project = self.get_object()
        from apps.drama.defaults import DRAMA_FAST_TRACK_ROLES, DRAMA_ROLE_DEFAULTS

        if project.track_mode == "fast":
            all_roles = DRAMA_FAST_TRACK_ROLES
        else:
            all_roles = [r["agent_id"] for r in DRAMA_ROLE_DEFAULTS]

        completed = set(project.completed_roles or [])
        role_progress = [
            {
                "agent_id": r,
                "completed": r in completed,
                "execution": None,
            }
            for r in all_roles
        ]

        # 加载最新执行记录
        executions = {
            e.agent_id: e
            for e in DramaRoleExecution.objects.filter(
                drama_project=project
            ).order_by("-created_at")
        }
        for item in role_progress:
            exec_obj = executions.get(item["agent_id"])
            if exec_obj:
                item["execution"] = DramaRoleExecutionSerializer(exec_obj).data

        return Response({
            "code": 0,
            "message": "success",
            "data": {
                "project_id": str(project.id),
                "title": project.title,
                "completion_rate": project.get_completion_rate(),
                "current_stage": project.current_stage,
                "roles": role_progress,
            },
        })

    @action(detail=True, methods=["post"], url_path="run/(?P<role_id>[^/.]+)")
    def run_role(self, request, pk=None, role_id=None):
        """触发某个角色执行（异步）。"""
        project = self.get_object()
        # TODO: 集成 IndependentAgentService 执行
        # 此处先返回占位响应，实际实现需接入 Celery 任务队列
        return Response({
            "code": 0,
            "message": f"角色 {role_id} 已加入执行队列",
            "data": {"project_id": str(project.id), "role_id": role_id, "status": "queued"},
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
        ).select_related("provider")

        providers = LlmProvider.objects.filter(is_active=True).values("id", "name", "vendor")

        config_data = []
        for route in routes.order_by("sort_order"):
            config_data.append({
                "agent_id": route.route_key,
                "display_name": route.display_name,
                "provider_id": route.provider_id,
                "provider_name": route.provider.name if route.provider else None,
                "model_name": route.model_name or "",
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
                route.provider = provider
            except LlmProvider.DoesNotExist:
                return Response(
                    {"code": 404, "message": f"Provider {d['provider_id']} 不存在"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            route.provider = None

        route.model_name = d.get("model_name", "")
        route.temperature = d.get("temperature", 0.7)
        route.max_completion_tokens = d.get("max_completion_tokens", 8000)
        route.save(update_fields=["provider", "model_name", "temperature", "max_completion_tokens"])

        return Response({"code": 0, "message": "配置已更新"})


# ---------------------------------------------------------------------------
# 评分雷达数据
# ---------------------------------------------------------------------------

class QualityRadarView(APIView):
    """获取项目8维度评分雷达数据。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = DramaProject.objects.get(id=project_id, user=request.user)
        except DramaProject.DoesNotExist:
            return Response({"code": 404, "message": "项目不存在"}, status=404)

        scores = project.quality_scores or {}

        # 8维度评分数据（供雷达图渲染）
        radar_data = [
            {"dimension": "格式规范", "key": "format",     "score": scores.get("format", 0),     "weight": 0.15},
            {"dimension": "结构完整", "key": "structure",  "score": scores.get("structure", 0),  "weight": 0.20},
            {"dimension": "人物塑造", "key": "character",  "score": scores.get("character", 0),  "weight": 0.15},
            {"dimension": "情绪曲线", "key": "emotion",    "score": scores.get("emotion", 0),    "weight": 0.15},
            {"dimension": "对白质量", "key": "dialogue",   "score": scores.get("dialogue", 0),   "weight": 0.15},
            {"dimension": "钩子效果", "key": "hooks",      "score": scores.get("hooks", 0),      "weight": 0.10},
            {"dimension": "梦境指标", "key": "dream",      "score": scores.get("dream", 0),      "weight": 0.05},
            {"dimension": "商业可行", "key": "commercial", "score": scores.get("commercial", 0), "weight": 0.05},
        ]

        overall = scores.get("overall", 0)
        grade = "S" if overall >= 90 else "A" if overall >= 80 else "B" if overall >= 75 else "C" if overall >= 60 else "D"

        return Response({
            "code": 0,
            "message": "success",
            "data": {
                "project_id": str(project.id),
                "overall_score": overall,
                "grade": grade,
                "radar": radar_data,
            },
        })
