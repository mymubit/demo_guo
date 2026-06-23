# -*- coding: utf-8 -*-
"""
????????

???????
- ????????????
- ?????????? HTML ??????
- ?????????? + HTML????????
"""

import re

from rest_framework import serializers

from .models import Project, ScriptWork, ShareLink


# ============================================================
# ??????
# ============================================================
class CreationSubmitSerializer(serializers.Serializer):
    """??????

    ???????????????????????????
    """

    theme = serializers.CharField(
        max_length=64,
        error_messages={
            "blank": "?????",
            "max_length": "??????",
        },
        help_text="?????? family-revenge / overbearing-ceo",
    )
    core_idea = serializers.CharField(
        max_length=1000,
        error_messages={
            "blank": "???????",
            "max_length": "?????? 1000 ?",
        },
        help_text="?????????",
    )
    episode_count = serializers.IntegerField(
        min_value=10,
        max_value=500,
        default=30,
        error_messages={
            "min_value": "???? 10 ?",
            "max_value": "???? 500 ?",
        },
        help_text="?????10-500?",
    )
    format_variant = serializers.ChoiceField(
        choices=[("A", "?? A"), ("B", "?? B"), ("C", "?? C"), ("D", "?? D")],
        default="B",
        help_text="????????? B",
    )
    audience = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        default="",
        help_text="??????????",
    )
    reference_work = serializers.CharField(
        max_length=2000,
        required=False,
        allow_blank=True,
        default="",
        help_text="????????",
    )
    outline_text = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="???????from-outline?",
    )
    novel_text = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="?????novel-adaptation?",
    )
    ip_sequel_mode = serializers.ChoiceField(
        choices=[("sequel", "??"), ("prequel", "??"), ("spin-off", "??")],
        required=False,
        allow_blank=True,
        default="sequel",
    )
    ip_keep_rules = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="IP ????????",
    )
    target_platform = serializers.CharField(
        max_length=32,
        default="douyin",
        required=False,
        help_text="????????? GET /api/creation/fusion/catalog/",
    )
    episode_duration_minutes = serializers.FloatField(
        min_value=0.5,
        max_value=30,
        default=2.0,
        required=False,
    )
    creation_entry = serializers.CharField(
        max_length=32,
        default="from-scratch",
        required=False,
    )
    budget_level = serializers.ChoiceField(
        choices=[("low", "???"), ("medium", "???"), ("high", "???")],
        default="medium",
        required=False,
    )
    global_market = serializers.ChoiceField(
        choices=[("domestic", "??"), ("global", "??")],
        default="domestic",
        required=False,
    )
    pipeline_mode = serializers.ChoiceField(
        choices=[
            ("workspace", "?????"),
            ("auto", "????"),
            ("step", "????"),
        ],
        default="workspace",
        required=False,
        help_text="workspace=??????auto=???????step=????????",
    )

    def validate_theme(self, value):
        """????????? ???????????"""
        if not re.match(r"^[a-z][a-z0-9-]{1,62}[a-z0-9]$", value):
            raise serializers.ValidationError("?????????")
        return value

    def validate_core_idea(self, value):
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError("????????")
        return value

    def validate_creation_entry(self, value):
        value = (value or "from-scratch").strip()
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        allowed = set(CreationFormOverrideService.allowed_creation_entries())
        if value not in allowed:
            raise serializers.ValidationError("?????????????")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        entry = attrs.get("creation_entry") or "from-scratch"
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        validation = CreationFormOverrideService.creation_entry_validation(entry)
        required_fields = validation.get("requiredFields") if isinstance(validation, dict) else {}
        errors = {}
        field_labels = {
            "reference_work": "??????",
            "outline_text": "????",
            "novel_text": "????",
            "ip_keep_rules": "IP ??",
        }
        for field, rule in (required_fields or {}).items():
            if not isinstance(rule, dict):
                continue
            min_length = int(rule.get("minLength") or 1)
            label = rule.get("label") or field_labels.get(field) or field
            if len((attrs.get(field) or "").strip()) < min_length:
                errors[field] = f"{label}?? {min_length} ?"
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


# ============================================================
# ?????????
# ============================================================
class CreationSubmitResultSerializer(serializers.Serializer):
    """????????

    ??? project_id ??????????????????
    """

    project_id = serializers.CharField(help_text="??ID")
    estimated_minutes = serializers.IntegerField(
        help_text="??????????"
    )
    status = serializers.CharField(help_text="????", required=False)
    workspace_url = serializers.CharField(help_text="?????", required=False)


# ============================================================
# ??????
# ============================================================
class ProjectProgressSerializer(serializers.Serializer):
    """??????

    ?????
    - ????????? HTML ??
    - ??????????????
    - ???????????? token?15 ?????
    """

    status = serializers.CharField(help_text="pending / running / awaiting / completed / failed")
    status_text = serializers.CharField(help_text="??????")
    progress_percent = serializers.IntegerField(help_text="????? 0-100")
    rendered_progress_html = serializers.CharField(
        help_text="???????? HTML ??"
    )
    rendered_result_html = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="?????????????? HTML?????",
    )
    download_token = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="????? token?15 ????",
    )
    error_message = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="??????????????",
    )
    drama_stage = serializers.CharField(required=False, allow_blank=True, default="")
    drama_stage_display = serializers.CharField(required=False, allow_blank=True, default="")
    track_mode = serializers.CharField(required=False, allow_blank=True, default="")
    delivery_status = serializers.CharField(required=False, allow_blank=True, default="")
    overall_score = serializers.FloatField(required=False, allow_null=True)
    grade = serializers.CharField(required=False, allow_blank=True, default="")
    ready_at = serializers.DateTimeField(required=False, allow_null=True)
    skill_version = serializers.CharField(required=False, allow_blank=True, default="")
    score_summary = serializers.DictField(required=False, allow_null=True)
    pipeline_mode = serializers.CharField(required=False, default="auto")
    latest_execution_run = serializers.DictField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(help_text="??????")
    updated_at = serializers.DateTimeField(help_text="??????")


# ============================================================
# ????
# ============================================================
class ProjectListSerializer(serializers.Serializer):
    """???????????

    ???????????????????????
    ?????????????
    """

    project_id = serializers.CharField(source="id", help_text="??ID")
    title = serializers.CharField(help_text="????")
    theme = serializers.CharField(help_text="??")
    episode_count = serializers.IntegerField(help_text="??")
    format_variant = serializers.CharField(help_text="??????")
    status = serializers.SerializerMethodField(help_text="????")
    status_text = serializers.SerializerMethodField(help_text="??????")
    progress_percent = serializers.IntegerField(help_text="?????")
    overall_score = serializers.FloatField(required=False, allow_null=True)
    grade = serializers.CharField(required=False, allow_blank=True, default="")
    ready_at = serializers.DateTimeField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(help_text="????")
    updated_at = serializers.DateTimeField(help_text="????")

    core_idea = serializers.SerializerMethodField(help_text="??????")
    pipeline_mode = serializers.CharField(help_text="????")
    creation_entry = serializers.CharField(
        required=False, allow_blank=True, default="", help_text="????"
    )
    drama_workspace_url = serializers.SerializerMethodField(help_text="Drama ?????")
    track_mode = serializers.CharField(required=False, allow_blank=True, default="", help_text="????")
    drama_stage = serializers.CharField(required=False, allow_blank=True, default="", help_text="????")
    drama_stage_display = serializers.CharField(required=False, allow_blank=True, default="", help_text="????")
    completion_rate = serializers.FloatField(required=False, help_text="Drama ???")
    delivery_status = serializers.CharField(required=False, allow_blank=True, default="", help_text="????")
    target_platform = serializers.CharField(required=False, allow_blank=True, default="", help_text="????")

    def get_drama_workspace_url(self, obj) -> str:
        if not obj.is_drama_workspace:
            return ""
        return f"/drama/workspace/{obj.id}"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_drama_workspace:
            rate = instance.get_completion_rate()
            data["progress_percent"] = int(min(100, max(0, rate)))
            data["completion_rate"] = rate
            data["delivery_status"] = instance.delivery_status or "pending"
            data["target_platform"] = instance.target_platform or ""
            data["track_mode"] = instance.track_mode
            data["drama_stage"] = instance.drama_stage
            data["drama_stage_display"] = instance.get_drama_stage_display()
            if instance.quality_scores:
                data["quality_scores"] = instance.quality_scores
        else:
            progress = int(data.get("progress_percent") or 0)
            data["completion_rate"] = progress
            data["delivery_status"] = ""
            data["target_platform"] = instance.target_platform or ""
            data["track_mode"] = ""
            data["drama_stage"] = ""
            data["drama_stage_display"] = ""
            data["drama_workspace_url"] = ""
        return data

    def get_status(self, obj) -> str:
        return obj.execution_status

    def get_status_text(self, obj) -> str:
        return obj.get_status_display()

    def get_core_idea(self, obj) -> str:
        text = (obj.core_idea or "").strip()
        if len(text) <= 320:
            return text
        return text[:320] + "?"


# ============================================================
# ??????
# ============================================================
class ShareCreateSerializer(serializers.Serializer):
    """????????"""

    project_id = serializers.CharField(
        required=False,
        help_text="??ID???? URL ?????",
    )
    view_limit = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=1000,
        default=100,
        help_text="????????? 100",
    )
    valid_days = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=30,
        default=7,
        help_text="?????1-30???? 7",
    )
    allow_download = serializers.BooleanField(
        required=False,
        default=False,
        help_text="??????????",
    )
    custom_title = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
        default="",
        help_text="???????????",
    )


class ShareCreateResultSerializer(serializers.Serializer):
    """????????"""

    share_id = serializers.CharField(help_text="????ID")
    share_token = serializers.CharField(help_text="?? token????? URL?")
    share_url = serializers.CharField(
        help_text="??????????? + /share/{token}?"
    )
    expires_at = serializers.DateTimeField(help_text="????")
    view_limit = serializers.IntegerField(help_text="??????")
    allow_download = serializers.BooleanField(help_text="??????")
    custom_title = serializers.CharField(
        required=False, allow_blank=True, default="",
        help_text="???????",
    )


# ============================================================
# ?????URL ??????? body ???
# ============================================================
class DownloadFormatSerializer(serializers.Serializer):
    """??????"""

    file_format = serializers.ChoiceField(
        choices=["md", "html", "zip", "pdf"],
        default="md",
        help_text="????",
    )


# ============================================================
# ?????????????????????????
# ============================================================
class ShareViewSerializer(serializers.Serializer):
    """???????"""

    title = serializers.CharField(help_text="????")
    author_nickname = serializers.CharField(help_text="?????")
    created_at = serializers.DateTimeField(help_text="??????")
    expires_at = serializers.DateTimeField(help_text="????")
    remain_views = serializers.IntegerField(help_text="???????")
    allow_download = serializers.BooleanField(help_text="??????")
    # ??????? HTML ?????????????
    rendered_share_html = serializers.CharField(
        help_text="??????? HTML ???????"
    )
