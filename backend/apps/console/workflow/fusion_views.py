# -*- coding: utf-8 -*-
"""Admin Fusion Pipeline Pack（Phase C）。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok
from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.workflow.models import FusionPipelinePack


class FusionPipelineMetaView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return api_ok(FusionPipelineDbService.meta_payload())


class FusionPipelineImportView(APIView):
    """POST — 从技能包磁盘导入主链 + Schema 到 DB 并激活。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        data = request.data or {}
        root = (data.get("root") or "").strip() or None
        activate = data.get("activate", True)
        try:
            pack_id = FusionPipelineDbService.import_from_disk(
                activate=bool(activate),
                root=root,
            )
            meta = FusionPipelineDbService.meta_payload()
            return api_ok(
                {"pack_id": pack_id, **meta},
                message="主链与 Schema 已导入数据库",
            )
        except Exception as exc:  # noqa: BLE001
            return api_fail(str(exc))


class FusionPipelinePackListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        items = [
            FusionPipelineDbService.serialize_pack_summary(p)
            for p in FusionPipelinePack.objects.all().order_by("-updated_at")
        ]
        return api_ok({"items": items, "meta": FusionPipelineDbService.meta_payload()})


class FusionPipelinePackActivateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pack_id=None):
        try:
            FusionPipelineDbService.activate_pack(pack_id)
            return api_ok(FusionPipelineDbService.meta_payload(), message="已切换为当前配置包")
        except FusionPipelinePack.DoesNotExist:
            return api_fail("配置包不存在")
