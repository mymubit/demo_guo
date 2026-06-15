# -*- coding: utf-8 -*-
"""后台：剧本质量缺陷（ScriptQualityDefect）管理 API。

路由前缀：/api/admin/creation/
  GET  quality-defects/
  POST quality-defects/
"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.creation.models import ScriptQualityDefect

from apps.console.responses import api_fail, api_ok


def _serialize(obj: ScriptQualityDefect) -> dict:
    return {
        "id": obj.pk,
        "project_id": str(obj.project_id),
        "episode": obj.episode,
        "dimension": obj.dimension,
        "defect_type": obj.defect_type,
        "score": obj.score,
        "details": obj.details,
        "source": obj.source,
        "source_label": obj.get_source_display(),
        "status": obj.status,
        "status_label": obj.get_status_display(),
        "created_at": obj.created_at.isoformat(),
    }


class ScriptQualityDefectListView(APIView):
    """GET 列表（按 project_id/dimension/status 过滤）；POST 新建"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = ScriptQualityDefect.objects.all()
        project_id = request.query_params.get("project_id")
        dimension = request.query_params.get("dimension")
        status = request.query_params.get("status")

        if project_id:
            qs = qs.filter(project_id=project_id)
        if dimension:
            qs = qs.filter(dimension=dimension)
        if status:
            qs = qs.filter(status=status)

        items = [_serialize(obj) for obj in qs.order_by("-created_at")[:200]]
        return api_ok({"items": items, "total": qs.count()})

    def post(self, request):
        from apps.creation.models import Project

        data = request.data or {}
        project_id = str(data.get("project_id") or "").strip()
        try:
            project = Project.objects.get(pk=project_id)
        except (Project.DoesNotExist, Exception):
            return api_fail("project_id 无效或不存在")

        dimension = str(data.get("dimension") or "").strip()
        defect_type = str(data.get("defect_type") or "").strip()
        if not dimension or not defect_type:
            return api_fail("dimension 和 defect_type 不能为空")

        obj = ScriptQualityDefect.objects.create(
            project=project,
            episode=data.get("episode"),
            dimension=dimension,
            defect_type=defect_type,
            score=data.get("score"),
            details=data.get("details") or {},
            source=str(data.get("source") or ScriptQualityDefect.SOURCE_MANUAL),
            status=ScriptQualityDefect.STATUS_OPEN,
        )
        return api_ok(_serialize(obj), message="质量缺陷已记录")


class ScriptQualityDefectDetailView(APIView):
    """PUT 更新缺陷状态"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get_obj(self, pk):
        try:
            return ScriptQualityDefect.objects.get(pk=pk)
        except ScriptQualityDefect.DoesNotExist:
            return None

    def put(self, request, pk=None):
        obj = self._get_obj(pk)
        if not obj:
            return api_fail("质量缺陷不存在", code=404)
        data = request.data or {}
        fields = []
        if "status" in data:
            obj.status = data["status"]
            fields.append("status")
        if "score" in data:
            obj.score = data["score"]
            fields.append("score")
        if "details" in data:
            obj.details = data["details"]
            fields.append("details")
        if fields:
            obj.save(update_fields=fields)
        return api_ok(_serialize(obj), message="质量缺陷已更新")
