# -*- coding: utf-8 -*-
"""V3 产品 API serializers。"""
from __future__ import annotations

from rest_framework import serializers

from apps.drama.models import V3ArtifactVersion, V3CommandRun, V3Project, V3QualityFinding


class CreateProjectSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, min_length=1)
    entry_type = serializers.ChoiceField(choices=["original", "adapt"])
    template_id = serializers.UUIDField(required=False, allow_null=True)
    theme_code = serializers.CharField(
        max_length=64, required=False, allow_blank=True, default=""
    )

    def validate(self, attrs: dict) -> dict:
        template_id = attrs.get("template_id")
        theme_code = (attrs.get("theme_code") or "").strip()
        if template_id and theme_code:
            raise serializers.ValidationError(
                "template_id 与 theme_code 不能同时提供"
            )
        attrs["theme_code"] = theme_code
        if template_id is not None:
            attrs["template_id"] = str(template_id)
        return attrs


class CustomTemplateWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, min_length=1)
    theme_code = serializers.CharField(max_length=64, min_length=1)
    label_zh = serializers.CharField(max_length=200, min_length=1)
    dims = serializers.DictField(required=False, default=dict)
    description = serializers.CharField(
        required=False, allow_blank=True, default=""
    )


class CustomTemplatePatchSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, min_length=1, required=False)
    theme_code = serializers.CharField(max_length=64, min_length=1, required=False)
    label_zh = serializers.CharField(max_length=200, min_length=1, required=False)
    dims = serializers.DictField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class ProjectSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = V3Project
        fields = (
            "id",
            "title",
            "entry_type",
            "stage",
            "progress_percent",
            "archived_at",
            "updated_at",
        )
        read_only_fields = fields


class DispatchCommandSerializer(serializers.Serializer):
    command_type = serializers.CharField(max_length=64)
    payload = serializers.DictField(required=False, default=dict)
    idempotency_key = serializers.CharField(
        max_length=64, required=False, allow_blank=True, default=""
    )


class CommandRunSerializer(serializers.ModelSerializer):
    project_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = V3CommandRun
        fields = (
            "id",
            "command_type",
            "status",
            "project_id",
            "error_message",
            "result_payload",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ArtifactVersionSerializer(serializers.ModelSerializer):
    """产物版本（选题/蓝图预览用）。"""

    class Meta:
        model = V3ArtifactVersion
        fields = (
            "id",
            "artifact_key",
            "version",
            "schema_version",
            "status",
            "payload",
            "created_at",
        )
        read_only_fields = fields


class ArtifactRollbackSerializer(serializers.Serializer):
    artifact_key = serializers.CharField(max_length=64, allow_blank=False)
    source_version = serializers.IntegerField(min_value=1)


class TopicDraftPutSerializer(serializers.Serializer):
    payload = serializers.DictField(allow_empty=False)


class TopicConfirmSerializer(serializers.Serializer):
    use_draft = serializers.BooleanField(required=False, default=False)


class BlueprintConfirmSerializer(serializers.Serializer):
    use_draft = serializers.BooleanField(required=False, default=False)


class EpisodeGenerateSerializer(serializers.Serializer):
    episode_count = serializers.IntegerField(required=False, min_value=1)
    duration_target = serializers.CharField(required=False, allow_blank=False)
    planning_requests = serializers.DictField(required=False)


class EpisodeReviseSerializer(serializers.Serializer):
    episode_numbers = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )
    revision_requests = serializers.DictField(required=False)


class ScriptDraftPutSerializer(serializers.Serializer):
    payload = serializers.DictField(allow_empty=False)


class ScriptGenerateSerializer(serializers.Serializer):
    start = serializers.IntegerField(min_value=1)
    end = serializers.IntegerField(min_value=1)
    writing_requests = serializers.DictField(required=False)

    def validate(self, attrs: dict) -> dict:
        if attrs["end"] < attrs["start"]:
            raise serializers.ValidationError("end 不能小于 start")
        return attrs


class ScriptConfirmSerializer(serializers.Serializer):
    use_drafts = serializers.BooleanField(required=False, default=False)


class QualityFindingSerializer(serializers.ModelSerializer):
    report_artifact_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = V3QualityFinding
        fields = (
            "id",
            "source",
            "finding_key",
            "title",
            "severity",
            "status",
            "report_artifact_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class QualityAcceptFindingItemSerializer(serializers.Serializer):
    source = serializers.ChoiceField(
        choices=[
            V3QualityFinding.Source.QUALITY,
            V3QualityFinding.Source.COMPLIANCE,
        ]
    )
    finding_key = serializers.CharField(max_length=128, allow_blank=False)
    title = serializers.CharField(max_length=256, required=False, allow_blank=True)
    severity = serializers.CharField(max_length=32, required=False, allow_blank=True)


class QualityAcceptSerializer(serializers.Serializer):
    findings = QualityAcceptFindingItemSerializer(many=True, allow_empty=False)


class QualityReviseSerializer(serializers.Serializer):
    finding_keys = serializers.ListField(
        child=serializers.CharField(max_length=128, allow_blank=False),
        required=False,
        allow_empty=False,
    )
    episode_range = serializers.DictField(required=False)

    def validate_episode_range(self, value: dict) -> dict:
        start = value.get("start")
        end = value.get("end")
        if not isinstance(start, int) or not isinstance(end, int):
            raise serializers.ValidationError("episode_range 需包含整数 start/end")
        if start < 1 or end < 1:
            raise serializers.ValidationError("start/end 必须 ≥ 1")
        if end < start:
            raise serializers.ValidationError("end 不能小于 start")
        return {"start": start, "end": end}


class SystemConfigPutSerializer(serializers.Serializer):
    overlay = serializers.DictField(allow_empty=True)
    change_reason = serializers.CharField(
        max_length=500, required=False, allow_blank=True, default=""
    )


class ModelProviderWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    base_url = serializers.CharField(
        max_length=512, required=False, allow_blank=True, default=""
    )
    model_name = serializers.CharField(
        max_length=128, required=False, default="gpt-4o-mini"
    )
    api_key = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )
    temperature = serializers.FloatField(
        required=False, min_value=0, max_value=2, default=0.7
    )
    max_tokens = serializers.IntegerField(
        required=False, min_value=1, max_value=128000, default=4096
    )
    is_enabled = serializers.BooleanField(required=False, default=True)
    is_active = serializers.BooleanField(required=False, default=False)
    remark = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )


class ModelProviderPatchSerializer(serializers.Serializer):
    """部分更新：无 default，避免未提交字段被默认值覆盖。"""

    name = serializers.CharField(max_length=100, required=False)
    base_url = serializers.CharField(
        max_length=512, required=False, allow_blank=True
    )
    model_name = serializers.CharField(max_length=128, required=False)
    api_key = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )
    temperature = serializers.FloatField(
        required=False, min_value=0, max_value=2
    )
    max_tokens = serializers.IntegerField(
        required=False, min_value=1, max_value=128000
    )
    is_enabled = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    remark = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )


class ProviderKeyWriteSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=100)
    api_key = serializers.CharField(write_only=True)
    sort_order = serializers.IntegerField(required=False, min_value=0, default=0)
    is_enabled = serializers.BooleanField(required=False, default=True)


class ProviderKeyPatchSerializer(serializers.Serializer):
    """部分更新：空 api_key 不覆盖密文。"""

    label = serializers.CharField(max_length=100, required=False)
    api_key = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )
    sort_order = serializers.IntegerField(required=False, min_value=0)
    is_enabled = serializers.BooleanField(required=False)


class RoleModelMappingItemSerializer(serializers.Serializer):
    role_key = serializers.CharField(max_length=64)
    provider_id = serializers.UUIDField()
    backup_provider_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    temperature = serializers.FloatField(
        required=False, allow_null=True, min_value=0, max_value=2
    )
    max_tokens = serializers.IntegerField(
        required=False, allow_null=True, min_value=1, max_value=128000
    )


class RoleModelMappingTableSerializer(serializers.Serializer):
    items = RoleModelMappingItemSerializer(many=True, allow_empty=False)


class ModelPriceItemWriteSerializer(serializers.Serializer):
    provider_id = serializers.UUIDField()
    model_name = serializers.CharField(max_length=128)
    price_in_per_1k = serializers.DecimalField(
        max_digits=16, decimal_places=6, min_value=0
    )
    price_out_per_1k = serializers.DecimalField(
        max_digits=16, decimal_places=6, min_value=0
    )
    price_cache_in_per_1k = serializers.DecimalField(
        max_digits=16,
        decimal_places=6,
        min_value=0,
        required=False,
        allow_null=True,
    )
    currency = serializers.CharField(
        max_length=8, required=False, default="CNY"
    )


class ModelPriceTableSerializer(serializers.Serializer):
    items = ModelPriceItemWriteSerializer(many=True, allow_empty=False)


class ScriptReviewCreateSerializer(serializers.Serializer):
    script_text = serializers.CharField(allow_blank=False, trim_whitespace=True)
    title = serializers.CharField(
        required=False, allow_blank=True, max_length=200, default=""
    )
    project_id = serializers.UUIDField(required=False, allow_null=True)


class ScriptReviewUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(
        required=False, allow_blank=True, max_length=200, default=""
    )
    project_id = serializers.UUIDField(required=False, allow_null=True)


class ScriptReviewCompareQuerySerializer(serializers.Serializer):
    a = serializers.UUIDField()
    b = serializers.UUIDField()

    def validate(self, attrs):
        if attrs["a"] == attrs["b"]:
            raise serializers.ValidationError("对比记录不能相同")
        return attrs

