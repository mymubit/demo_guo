# -*- coding: utf-8 -*-
"""Drama Skills API Serializers。"""
from __future__ import annotations

from rest_framework import serializers

from apps.drama.models import DramaProject, DramaRoleExecution


class DramaProjectSerializer(serializers.ModelSerializer):
    completion_rate = serializers.SerializerMethodField()
    track_mode_display = serializers.CharField(source="get_track_mode_display", read_only=True)
    current_stage_display = serializers.CharField(source="get_current_stage_display", read_only=True)

    class Meta:
        model = DramaProject
        fields = [
            "id", "project_id", "title", "genre_code", "total_episodes",
            "target_platform", "track_mode", "track_mode_display",
            "current_stage", "current_stage_display",
            "completed_roles", "completion_rate",
            "word_count_stats", "quality_scores", "delivery_status",
            "total_tokens_used", "total_cost_cents",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "total_tokens_used", "total_cost_cents"]

    def get_completion_rate(self, obj: DramaProject) -> float:
        return obj.get_completion_rate()


class DramaProjectCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=128)
    genre_code = serializers.CharField(max_length=32, default="family-revenge")
    total_episodes = serializers.IntegerField(default=30, min_value=5, max_value=200)
    target_platform = serializers.ChoiceField(
        choices=["douyin", "kuaishou", "weixin", "all"],
        default="douyin",
    )
    track_mode = serializers.ChoiceField(
        choices=["fast", "expert"],
        default="fast",
    )
    core_idea = serializers.CharField(required=False, allow_blank=True)


class DramaRoleExecutionSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    output_views = serializers.SerializerMethodField()

    class Meta:
        model = DramaRoleExecution
        fields = [
            "id", "agent_id", "agent_name_zh", "status", "status_display",
            "output_artifacts", "output_views",
            "prompt_tokens", "completion_tokens", "total_tokens", "cost_cents",
            "elapsed_seconds", "llm_provider", "llm_model",
            "error_message", "started_at", "finished_at", "created_at",
        ]
        read_only_fields = fields

    def get_output_views(self, obj: DramaRoleExecution) -> dict:
        from apps.drama.presentation.service import build_execution_output_views

        return build_execution_output_views(obj)


class WordCountValidateSerializer(serializers.Serializer):
    content = serializers.CharField(help_text="单集剧本内容（纯文本）")
    episode_number = serializers.IntegerField(min_value=1, help_text="集号（1=首集）")


class ModelConfigSerializer(serializers.Serializer):
    agent_id = serializers.CharField()
    provider_id = serializers.IntegerField(allow_null=True)
    model_name = serializers.CharField(allow_blank=True, default="")
    temperature = serializers.FloatField(default=0.7, min_value=0.0, max_value=2.0)
    max_completion_tokens = serializers.IntegerField(default=8000, min_value=100, max_value=128000)
