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
        "skill_layer": obj.skill_layer,
        "skill_layer_label": obj.get_skill_layer_display() if obj.skill_layer else "",
        "sub_category": obj.sub_category,
        "lifecycle_status": obj.lifecycle_status,
        "lifecycle_status_label": obj.get_lifecycle_status_display(),
        "gray_weight": obj.gray_weight,
        "is_active": obj.is_active,
        "source_file": obj.source_file,
        "content": obj.content,
        "system_hint": obj.system_hint,
        "input_schema": obj.input_schema,
        "output_schema": obj.output_schema,
        "timeout_seconds": obj.timeout_seconds,
        "quota_cost": str(obj.quota_cost),
        "retry_policy": obj.retry_policy,
        "fallback_skill_id": obj.fallback_skill_id,
        "published_at": obj.published_at.isoformat() if obj.published_at else None,
        "deprecated_at": obj.deprecated_at.isoformat() if obj.deprecated_at else None,
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
    """GET 列表（支持 category/skill_layer/lifecycle_status/q 过滤）；POST 新建"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = AgentSkillDefinition.objects.all()
        category         = request.query_params.get("category")
        skill_layer      = request.query_params.get("skill_layer")
        lifecycle_status = request.query_params.get("lifecycle_status")
        is_active        = request.query_params.get("is_active")
        q                = request.query_params.get("q", "").strip()

        if category:
            qs = qs.filter(category=category)
        if skill_layer:
            qs = qs.filter(skill_layer=skill_layer)
        if lifecycle_status:
            qs = qs.filter(lifecycle_status=lifecycle_status)
        if is_active is not None:
            qs = qs.filter(is_active=(is_active.lower() not in ("false", "0")))
        if q:
            qs = qs.filter(skill_id__icontains=q) | qs.filter(name__icontains=q)

        items = [_serialize_definition(obj) for obj in qs.order_by("skill_layer", "category", "skill_id")]
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
            skill_layer=str(data.get("skill_layer") or ""),
            sub_category=str(data.get("sub_category") or ""),
            lifecycle_status=str(data.get("lifecycle_status") or AgentSkillDefinition.LIFECYCLE_DRAFT),
            content=str(data.get("content") or ""),
            system_hint=str(data.get("system_hint") or ""),
            input_schema=data.get("input_schema") or {},
            output_schema=data.get("output_schema") or {},
            timeout_seconds=int(data.get("timeout_seconds") or 60),
            quota_cost=float(data.get("quota_cost") or 0),
            retry_policy=data.get("retry_policy") or {},
            fallback_skill_id=str(data.get("fallback_skill_id") or ""),
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
        for f in (
            "name", "version", "category", "content", "source_file",
            "skill_layer", "sub_category", "system_hint",
            "timeout_seconds", "fallback_skill_id",
        ):
            if f in data:
                setattr(obj, f, data[f])
                fields.append(f)
        for json_field in ("input_schema", "output_schema", "retry_policy"):
            if json_field in data:
                setattr(obj, json_field, data[json_field] or {})
                fields.append(json_field)
        if "quota_cost" in data:
            obj.quota_cost = float(data["quota_cost"])
            fields.append("quota_cost")
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
        obj.deprecate()
        return api_ok(None, message=f"技能 {obj.skill_id} 已废弃")


class SkillDefinitionPublishView(APIView):
    """POST：发布技能（draft/gray → active 或 gray）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk=None):
        try:
            obj = AgentSkillDefinition.objects.get(pk=pk)
        except AgentSkillDefinition.DoesNotExist:
            return api_fail("技能定义不存在", code=404)

        gray_weight = int(request.data.get("gray_weight", 100))
        if not 0 <= gray_weight <= 100:
            return api_fail("gray_weight 须在 0-100 之间")

        obj.publish(gray_weight=gray_weight)
        return api_ok(_serialize_definition(obj), message=f"技能 {obj.skill_id} 已{'灰度' if gray_weight < 100 else '全量'}发布")


class SkillDefinitionDeprecateView(APIView):
    """POST：废弃技能"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk=None):
        try:
            obj = AgentSkillDefinition.objects.get(pk=pk)
        except AgentSkillDefinition.DoesNotExist:
            return api_fail("技能定义不存在", code=404)

        obj.deprecate()
        return api_ok(_serialize_definition(obj), message=f"技能 {obj.skill_id} 已废弃")


class SkillDefinitionRollbackView(APIView):
    """POST：回滚技能到上一个 active 版本"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk=None):
        try:
            current = AgentSkillDefinition.objects.get(pk=pk)
        except AgentSkillDefinition.DoesNotExist:
            return api_fail("技能定义不存在", code=404)

        # 找上一个非当前的 active 记录（按 skill_id 家族）
        prev = (
            AgentSkillDefinition.objects.filter(
                skill_id=current.skill_id,
                lifecycle_status=AgentSkillDefinition.LIFECYCLE_ACTIVE,
            )
            .exclude(pk=pk)
            .order_by("-published_at", "-created_at")
            .first()
        )
        if not prev:
            return api_fail("无可回滚的上一个 active 版本")

        # 废弃当前版本，激活上一版本
        current.deprecate()
        prev.publish(gray_weight=100)
        return api_ok(_serialize_definition(prev), message=f"已回滚到版本 {prev.version}")


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


# ────────────────────────────────────────────────
# 技能统计与灰度预览
# ────────────────────────────────────────────────

class SkillDefinitionStatsView(APIView):
    """GET：技能调用统计（成功率 / 平均耗时 / 调用量）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """查询 SkillDefect 按 skill 聚合数量，查询 LlmUsageLog 按 source_key=skill_id 聚合。"""
        from django.db.models import Count, Avg, Q
        from django.utils import timezone
        from datetime import timedelta

        # 统计 open 状态的缺陷数量（按 skill_id 聚合）
        open_defects_map = {}
        for row in (
            SkillDefect.objects.filter(status=SkillDefect.STATUS_OPEN)
            .values("skill__skill_id")
            .annotate(count=Count("id"))
        ):
            open_defects_map[row["skill__skill_id"]] = row["count"]

        # 解析时间范围过滤（默认 7 天）
        days = int(request.query_params.get("days", 7))
        days = max(1, min(days, 90))
        since = timezone.now() - timedelta(days=days)

        # 按 source_key（即 skill_id）聚合 LlmUsageLog
        from apps.skill.models import LlmUsageLog

        stats_map = {}
        for row in (
            LlmUsageLog.objects.filter(created_at__gte=since)
            .values("source_key")
            .annotate(
                total_calls=Count("id"),
                success_count=Count("id", filter=Q(success=True)),
            )
        ):
            key = row["source_key"] or ""
            if key:
                stats_map[key] = {
                    "total_calls": row["total_calls"],
                    "success_count": row["success_count"],
                    "success_rate": round(row["success_count"] / row["total_calls"], 4) if row["total_calls"] else 0.0,
                    "open_defects": open_defects_map.get(key, 0),
                }

        # 合并所有技能的统计数据
        items = []
        for skill in AgentSkillDefinition.objects.filter(is_active=True).order_by("skill_id"):
            key = skill.skill_id
            stats = stats_map.get(key, {"total_calls": 0, "success_count": 0, "success_rate": 0.0, "open_defects": 0})
            items.append({
                "skill_id": key,
                "name": skill.name,
                "total_calls": stats["total_calls"],
                "success_rate": stats["success_rate"],
                "open_defects": stats["open_defects"],
            })

        return api_ok({
            "items": items,
            "total": len(items),
            "days": days,
            "since": since.isoformat(),
        })


class SkillDefinitionGrayPreviewView(APIView):
    """GET：预览灰度分流效果（给定 user_id 列表，返回每个命中哪个版本）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """根据 gray_traffic_salt + user_id % 100 < gray_weight 计算每个 user_id 命中灰度还是正式版本。"""
        skill_id = request.query_params.get("skill_id", "").strip()
        if not skill_id:
            return api_fail("skill_id 不能为空")

        try:
            skill = AgentSkillDefinition.objects.get(skill_id=skill_id)
        except AgentSkillDefinition.DoesNotExist:
            return api_fail(f"技能 {skill_id} 不存在", code=404)

        # 获取 user_id 列表（逗号分隔或 JSON 数组）
        raw_user_ids = request.query_params.get("user_ids", "").strip()
        if not raw_user_ids:
            return api_fail("user_ids 不能为空")

        import json
        try:
            user_ids = json.loads(raw_user_ids)
        except (json.JSONDecodeError, TypeError):
            user_ids = [uid.strip() for uid in raw_user_ids.split(",") if uid.strip()]

        if not user_ids:
            return api_fail("user_ids 解析为空")

        gray_weight = skill.gray_weight
        salt = skill.gray_traffic_salt or ""

        previews = []
        for uid in user_ids[:1000]:  # 限制最多 1000 个
            # 稳定的灰度分流计算：hash(salt + str(uid)) % 100 < gray_weight
            import hashlib
            hash_input = f"{salt}{uid}".encode("utf-8")
            hash_val = int(hashlib.md5(hash_input).hexdigest(), 16) % 100
            will_hit_gray = hash_val < gray_weight
            previews.append({
                "user_id": str(uid),
                "will_hit_gray": will_hit_gray,
                "gray_weight": gray_weight,
            })

        return api_ok({
            "skill_id": skill_id,
            "gray_weight": gray_weight,
            "gray_traffic_salt": salt,
            "previews": previews,
            "total": len(previews),
        })
