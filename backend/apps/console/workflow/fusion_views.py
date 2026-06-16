# -*- coding: utf-8 -*-
"""Admin Fusion Pipeline Pack — 多流水线模板。"""
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

    def post(self, request):
        """复制已有 Pack 或从 source_pack_id 创建副本。"""
        data = request.data or {}
        source_id = (data.get("source_pack_id") or "").strip()
        display_name = (data.get("display_name") or "").strip()
        slug = (data.get("slug") or "").strip()
        activate = bool(data.get("activate", False))
        if not source_id:
            return api_fail("请指定 source_pack_id")
        if not display_name:
            return api_fail("请填写 display_name")
        try:
            pack = FusionPipelineDbService.duplicate_pack(
                source_id,
                display_name=display_name,
                slug=slug,
                activate=activate,
            )
            return api_ok(
                FusionPipelineDbService.serialize_pack_summary(pack),
                message="流水线已复制",
            )
        except FusionPipelinePack.DoesNotExist:
            return api_fail("源配置包不存在")
        except Exception as exc:  # noqa: BLE001
            return api_fail(str(exc))


class FusionPipelinePackDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pack_id=None):
        try:
            pack = FusionPipelineDbService.update_pack_meta(pack_id, request.data or {})
            return api_ok(
                FusionPipelineDbService.serialize_pack_summary(pack),
                message="流水线已更新",
            )
        except FusionPipelinePack.DoesNotExist:
            return api_fail("配置包不存在")
        except Exception as exc:  # noqa: BLE001
            return api_fail(str(exc))


class FusionPipelinePackActivateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pack_id=None):
        try:
            FusionPipelineDbService.activate_pack(pack_id)
            return api_ok(FusionPipelineDbService.meta_payload(), message="已切换为当前编辑流水线")
        except FusionPipelinePack.DoesNotExist:
            return api_fail("配置包不存在")


class FusionPipelinePackSetDefaultView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pack_id=None):
        try:
            FusionPipelineDbService.set_default_for_creation(pack_id)
            pack = FusionPipelinePack.objects.get(pk=pack_id)
            return api_ok(
                FusionPipelineDbService.serialize_pack_summary(pack),
                message="已设为创作默认流水线",
            )
        except FusionPipelinePack.DoesNotExist:
            return api_fail("配置包不存在")


class FusionPipelinePackPublishView(APIView):
    """切换创作入口可见；可选同时发布编排蓝图。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pack_id=None):
        data = request.data or {}
        published = bool(data.get("published", True))
        try:
            pack = FusionPipelineDbService.update_pack_meta(
                pack_id,
                {"is_published_to_portal": published},
            )
            note = (data.get("note") or "").strip()
            if published and data.get("publish_blueprint", False):
                active = FusionPipelineDbService.get_active_pack()
                if active and str(active.id) != str(pack.id):
                    FusionPipelineDbService.activate_pack(pack.id)
                from apps.console.orchestration.publish_service import OrchestrationPublishService

                OrchestrationPublishService.publish(note=note or "流水线发布到创作入口")
            return api_ok(
                FusionPipelineDbService.serialize_pack_summary(pack),
                message="已发布到创作入口" if published else "已从创作入口下架",
            )
        except FusionPipelinePack.DoesNotExist:
            return api_fail("配置包不存在")
        except Exception as exc:  # noqa: BLE001
            return api_fail(str(exc))
