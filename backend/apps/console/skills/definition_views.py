# -*- coding: utf-8 -*-
"""后台：Agent 技能定义 / 技能配置项 / 技能缺陷 管理 API。

路由前缀：/api/admin/skills/
  GET/POST  definitions/
  GET/PUT/DELETE  definitions/<pk>/
  GET/POST  configs/
  GET/PUT   configs/<config_key>/
  GET/POST  defects/
  GET/PUT   defects/<pk>/
"""
from __future__ import annotations

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.skill.models import AgentSkillDefinition, SkillConfigEntry, SkillDefect

from apps.console.responses import api_fail, api_ok


# ────────────────────────────────────────────────
# 序列化辅助
# ────────────────────────────────────────────────

def _serialize_definition(obj: AgentSkillDefinition) -> dict:
    return {
        "id": obj.pk,
        "skill_id": obj.skill_id,
        "name": obj.name,
        "version": obj.version,
        "category": obj.category,
        "category_label": obj.get_category_display(),
        "is_active": obj.is_active,
        "source_file": obj.source_file,
        "content": obj.content,
        "created_at": obj.created_at.isoformat(),
        "updated_at": obj.updated_at.isoformat(),
    }


def _serialize_config(obj: SkillConfigEntry) -> dict:
    return {
        "config_key": obj.config_key,
        "edition": obj.edition,
        "version": obj.version,
        "note": obj.note,
        "content": obj.content,
        "updated_at": obj.updated_at.isoformat(),
    }


def _serialize_defect(obj: SkillDefect) -> dict:
    return {
        "id": obj.pk,
        "skill_id": obj.skill.skill_id if obj.skill_id else None,
        "title": obj.title,
        "description": obj.description,
        "severity": obj.severity,
        "severity_label": obj.get_severity_display(),
        "status": obj.status,
        "status_label": obj.get_status_display(),
        "reproduce_steps": obj.reproduce_steps,
        "fix_notes": obj.fix_notes,
        "reported_by": obj.reported_by,
        "resolved_at": obj.resolved_at.isoformat() if obj.resolved_at else None,
        "created_at": obj.created_at.isoformat(),
        "updated_at": obj.updated_at.isoformat(),
    }


# ────────────────────────────────────────────────
# AgentSkillDefinition 视图
# ────────────────────────────────────────────────

class SkillDefinitionListView(APIView):
    """GET 列表（支持 category/is_active/q 过滤）；POST 新建"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = AgentSkillDefinition.objects.all()
        category = request.query_params.get("category")
        is_active = request.query_params.get("is_active")
        q = request.query_params.get("q", "").strip()

        if category:
            qs = qs.filter(category=category)
        if is_active is not None:
            qs = qs.filter(is_active=(is_active.lower() not in ("false", "0")))
        if q:
            qs = qs.filter(skill_id__icontains=q) | qs.filter(name__icontains=q)

        items = [_serialize_definition(obj) for obj in qs.order_by("category", "skill_id")]
        return api_ok({"items": items, "total": len(items)})

    def post(self, request):
        data = request.data or {}
        skill_id = str(data.get("skill_id") or "").strip()
        if not skill_id:
            return api_fail("skill_id 不能为空")
        if AgentSkillDefinition.objects.filter(skill_id=skill_id).exists():
            return api_fail(f"skill_id={skill_id!r} 已存在，请使用 PUT 更新")

        obj = AgentSkillDefinition.objects.create(
            skill_id=skill_id,
            name=str(data.get("name") or skill_id),
            version=str(data.get("version") or "1.0.0"),
            category=str(data.get("category") or AgentSkillDefinition.CATEGORY_CREATOR),
            content=str(data.get("content") or ""),
            is_active=data.get("is_active", True),
            source_file=str(data.get("source_file") or ""),
        )
        return api_ok(_serialize_definition(obj), message="技能定义已创建")


class SkillDefinitionDetailView(APIView):
    """GET 详情；PUT 更新；DELETE 软删除（is_active=False）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get_obj(self, pk):
        try:
            return AgentSkillDefinition.objects.get(pk=pk)
        except AgentSkillDefinition.DoesNotExist:
            return None

    def get(self, request, pk=None):
        obj = self._get_obj(pk)
        if not obj:
            return api_fail("技能定义不存在", code=404)
        return api_ok(_serialize_definition(obj))

    def put(self, request, pk=None):
        obj = self._get_obj(pk)
        if not obj:
            return api_fail("技能定义不存在", code=404)
        data = request.data or {}
        fields = []
        for field in ("name", "version", "category", "content", "source_file"):
            if field in data:
                setattr(obj, field, data[field])
                fields.append(field)
        if "is_active" in data:
            obj.is_active = bool(data["is_active"])
            fields.append("is_active")
        if fields:
            obj.save(update_fields=fields + ["updated_at"])
        return api_ok(_serialize_definition(obj), message="技能定义已更新")

    def delete(self, request, pk=None):
        obj = self._get_obj(pk)
        if not obj:
            return api_fail("技能定义不存在", code=404)
        obj.is_active = False
        obj.save(update_fields=["is_active", "updated_at"])
        return api_ok(None, message=f"技能 {obj.skill_id} 已停用（软删除）")


# ────────────────────────────────────────────────
# SkillConfigEntry 视图
# ────────────────────────────────────────────────

class SkillConfigEntryListView(APIView):
    """GET 配置列表；POST 新建配置项"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        items = [_serialize_config(obj) for obj in SkillConfigEntry.objects.all()]
        return api_ok({"items": items, "total": len(items)})

    def post(self, request):
        data = request.data or {}
        config_key = str(data.get("config_key") or "").strip()
        if not config_key:
            return api_fail("config_key 不能为空")
        if SkillConfigEntry.objects.filter(config_key=config_key).exists():
            return api_fail(f"config_key={config_key!r} 已存在，请使用 PUT 更新")

        obj = SkillConfigEntry.objects.create(
            config_key=config_key,
            edition=str(data.get("edition") or "unified"),
            version=str(data.get("version") or "1.0.0"),
            content=data.get("content") or {},
            note=str(data.get("note") or ""),
        )
        return api_ok(_serialize_config(obj), message="配置项已创建")


class SkillConfigEntryDetailView(APIView):
    """GET 单项详情；PUT 更新内容"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get_obj(self, config_key: str):
        try:
            return SkillConfigEntry.objects.get(config_key=config_key)
        except SkillConfigEntry.DoesNotExist:
            return None

    def get(self, request, config_key: str = ""):
        obj = self._get_obj(config_key)
        if not obj:
            return api_fail("配置项不存在", code=404)
        return api_ok(_serialize_config(obj))

    def put(self, request, config_key: str = ""):
        obj = self._get_obj(config_key)
        if not obj:
            return api_fail("配置项不存在", code=404)
        data = request.data or {}
        fields = []
        for field in ("edition", "version", "note"):
            if field in data:
                setattr(obj, field, data[field])
                fields.append(field)
        if "content" in data:
            obj.content = data["content"]
            fields.append("content")
        if fields:
            obj.save(update_fields=fields + ["updated_at"])
        return api_ok(_serialize_config(obj), message="配置项已更新")


# ────────────────────────────────────────────────
# SkillDefect 视图
# ────────────────────────────────────────────────

class SkillDefectListView(APIView):
    """GET 缺陷列表（按 skill_id/severity/status 过滤）；POST 新建缺陷"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = SkillDefect.objects.select_related("skill").all()
        skill_id = request.query_params.get("skill_id")
        severity = request.query_params.get("severity")
        status = request.query_params.get("status")

        if skill_id:
            qs = qs.filter(skill__skill_id=skill_id)
        if severity:
            qs = qs.filter(severity=severity)
        if status:
            qs = qs.filter(status=status)

        items = [_serialize_defect(obj) for obj in qs.order_by("severity", "-created_at")]
        return api_ok({"items": items, "total": len(items)})

    def post(self, request):
        data = request.data or {}
        skill_id = str(data.get("skill_id") or "").strip()
        try:
            skill = AgentSkillDefinition.objects.get(skill_id=skill_id)
        except AgentSkillDefinition.DoesNotExist:
            return api_fail(f"技能 skill_id={skill_id!r} 不存在")

        title = str(data.get("title") or "").strip()
        if not title:
            return api_fail("title 不能为空")

        obj = SkillDefect.objects.create(
            skill=skill,
            title=title,
            description=str(data.get("description") or ""),
            severity=str(data.get("severity") or SkillDefect.SEVERITY_P2),
            status=SkillDefect.STATUS_OPEN,
            reproduce_steps=str(data.get("reproduce_steps") or ""),
            fix_notes=str(data.get("fix_notes") or ""),
            reported_by=str(data.get("reported_by") or getattr(request.user, "username", "")),
        )
        return api_ok(_serialize_defect(obj), message="技能缺陷已创建")


class SkillDefectDetailView(APIView):
    """GET 详情；PUT 更新（含状态流转，resolved 时记录 resolved_at）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get_obj(self, pk):
        try:
            return SkillDefect.objects.select_related("skill").get(pk=pk)
        except SkillDefect.DoesNotExist:
            return None

    def get(self, request, pk=None):
        obj = self._get_obj(pk)
        if not obj:
            return api_fail("技能缺陷不存在", code=404)
        return api_ok(_serialize_defect(obj))

    def put(self, request, pk=None):
        obj = self._get_obj(pk)
        if not obj:
            return api_fail("技能缺陷不存在", code=404)
        data = request.data or {}
        fields = []
        for field in ("title", "description", "severity", "reproduce_steps", "fix_notes", "reported_by"):
            if field in data:
                setattr(obj, field, data[field])
                fields.append(field)
        if "status" in data:
            new_status = data["status"]
            if new_status == SkillDefect.STATUS_RESOLVED and obj.status != SkillDefect.STATUS_RESOLVED:
                obj.resolved_at = timezone.now()
                fields.append("resolved_at")
            obj.status = new_status
            fields.append("status")
        if fields:
            obj.save(update_fields=fields + ["updated_at"])
        return api_ok(_serialize_defect(obj), message="技能缺陷已更新")
