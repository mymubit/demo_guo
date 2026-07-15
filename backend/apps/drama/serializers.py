# -*- coding: utf-8 -*-
"""Drama API 序列化。"""
from __future__ import annotations

from rest_framework import serializers

from apps.drama.models import DramaProject


class DramaProjectSerializer(serializers.ModelSerializer):
    settings_revision = serializers.IntegerField(read_only=True)
    entry_type = serializers.SerializerMethodField()
    episode_count = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = DramaProject
        fields = (
            "id",
            "title",
            "entry_type",
            "episode_count",
            "status",
            "settings_revision",
            "skills_version",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_entry_type(self, obj: DramaProject) -> str:
        return (obj.settings or {}).get("entry_type", "original_track")

    def get_episode_count(self, obj: DramaProject) -> int | None:
        return (obj.settings or {}).get("episode_count")

    def get_status(self, obj: DramaProject) -> str | None:
        wf = getattr(obj, "workflow_state", None)
        if wf is None:
            return None
        return wf.state.get("status")


class DramaProjectCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    entry_type = serializers.ChoiceField(
        choices=["original_track", "story_adapt"],
        default="original_track",
    )
    episode_count = serializers.IntegerField(min_value=1, required=False)
    core_idea = serializers.CharField(required=False, allow_blank=True)
    external_story = serializers.CharField(required=False, allow_blank=True)


class WorkflowCommandSerializer(serializers.Serializer):
    command_id = serializers.CharField(max_length=128)
    event = serializers.CharField(max_length=64)
    expected_version = serializers.IntegerField(min_value=0)
    payload = serializers.JSONField(required=False, default=dict)


class StoryBibleApprovalSerializer(serializers.Serializer):
    command_id = serializers.CharField(max_length=128)
    decision = serializers.ChoiceField(choices=["approve", "reject"])
    expected_version = serializers.IntegerField(min_value=0)


class GenerationStartSerializer(serializers.Serializer):
    command_id = serializers.CharField(max_length=128)
    expected_version = serializers.IntegerField(min_value=0)
    role = serializers.CharField(max_length=64, default="drama.topic-director")
    input = serializers.JSONField(required=False, default=dict)


class ExternalReviewSerializer(serializers.Serializer):
    command_id = serializers.CharField(max_length=128)
    scoring_preset = serializers.CharField(max_length=64)
    check_mode = serializers.ChoiceField(
        choices=["standard", "values-risk", "full"],
    )
    script_content = serializers.CharField(required=False, allow_blank=True)
    project_id = serializers.UUIDField(required=False)


class ConfigRollbackSerializer(serializers.Serializer):
    target_revision = serializers.IntegerField(min_value=1)
    change_reason = serializers.CharField(max_length=500)
