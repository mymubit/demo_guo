# -*- coding: utf-8 -*-
"""调度中心 · 流程编排 API（统一读写蓝图、重排、后处理链）。"""
import hashlib
import json

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated

from apps.common.agent_term import attach_api_meta
from apps.common.permissions import IsAdminUser

from apps.console.base_views import AdminAPIView
from apps.console.responses import api_fail, api_ok
from apps.console.main_chain.blueprint_service import MainChainBlueprintService
from apps.console.orchestration.publish_service import OrchestrationPublishService
from apps.workflow.models import FusionPipelinePack
from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.workflow.step_admin import PipelineStepAdminService


class OrchestrationFlowBlueprintView(AdminAPIView):
    """GET /api/admin/orchestration/flow/blueprint/ — 流程编排蓝图。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        payload = MainChainBlueprintService.build_blueprint()
        return api_ok(attach_api_meta(payload))


class OrchestrationFlowStepPatchView(AdminAPIView):
    """PUT /api/admin/orchestration/flow/steps/<uuid>/ — 更新单步。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, step_id=None):
        try:
            step = MainChainBlueprintService.patch_step(str(step_id), request.data or {})
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(step, message="步骤已保存")


class OrchestrationFlowStepsReorderView(AdminAPIView):
    """PUT /api/admin/orchestration/flow/steps/reorder/ — 拖拽重排 chain_order。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request):
        ordered_ids = request.data.get("ordered_ids") or request.data.get("order") or []
        if not isinstance(ordered_ids, list) or not ordered_ids:
            return api_fail("ordered_ids 不能为空")
        try:
            steps = PipelineStepAdminService.reorder_steps(ordered_ids)
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok({"steps": steps}, message="流程顺序已更新")


class OrchestrationFlowRegistryMetaView(AdminAPIView):
    """PUT /api/admin/orchestration/flow/registry-meta/ — 后处理链与画布元数据。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request):
        try:
            meta = MainChainBlueprintService.patch_registry_meta(request.data or {})
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(meta, message="编排元数据已保存")


class OrchestrationFlowPublishView(AdminAPIView):
    """POST /api/admin/orchestration/flow/publish/ — 发布编排蓝图到 C 端。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        note = str((request.data or {}).get("note") or "").strip()
        try:
            payload = OrchestrationPublishService.publish(note=note)
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(payload, message="编排蓝图已发布")


# ────────────────────────────────────────────────
# 灰度切流 / 回滚 / 列表
# ────────────────────────────────────────────────

class OrchestrationFlowGraySwitchView(AdminAPIView):
    """POST /api/admin/orchestration/flow/gray-switch/ — 灰度切流预览 + 确认切换。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        """输入：{action: "preview"|"switch", pack_id, gray_weight, gray_traffic_salt}"""
        data = request.data or {}
        action = str(data.get("action") or "").strip()
        pack_id = str(data.get("pack_id") or "").strip()

        if action not in ("preview", "switch"):
            return api_fail("action 必须为 preview 或 switch")
        if not pack_id:
            return api_fail("pack_id 不能为空")

        try:
            pack = FusionPipelinePack.objects.get(pk=pack_id)
        except FusionPipelinePack.DoesNotExist:
            return api_fail("配置包不存在", code=404)

        gray_weight = int(data.get("gray_weight", pack.gray_weight))
        gray_traffic_salt = str(data.get("gray_traffic_salt") or "").strip()

        if not 0 <= gray_weight <= 100:
            return api_fail("gray_weight 须在 0-100 之间")

        if action == "preview":
            # 预览：按 user_id hash 的命中分布（取样 100 个测试 user_id）
            sample_user_ids = [f"preview_user_{i}" for i in range(100)]
            hits = []
            gray_count = 0
            for uid in sample_user_ids:
                hash_input = f"{gray_traffic_salt}{uid}".encode("utf-8")
                hash_val = int(hashlib.md5(hash_input).hexdigest(), 16) % 100
                will_hit = hash_val < gray_weight
                if will_hit:
                    gray_count += 1
                hits.append({"user_id": uid, "will_hit_gray": will_hit})
            return api_ok({
                "pack_id": pack_id,
                "gray_weight": gray_weight,
                "gray_traffic_salt": gray_traffic_salt,
                "sample_hits": hits,
                "estimated_gray_ratio": gray_count / 100,
            })

        # switch：执行灰度切换
        pack.pack_status = FusionPipelinePack.PACK_GRAY if gray_weight < 100 else FusionPipelinePack.PACK_ACTIVE
        pack.gray_weight = gray_weight
        pack.published_at = timezone.now()
        pack.save(update_fields=["pack_status", "gray_weight", "published_at", "updated_at"])
        return api_ok(
            FusionPipelineDbService.serialize_pack_summary(pack),
            message=f"灰度切流已完成，gray_weight={gray_weight}",
        )


class OrchestrationFlowRollbackView(AdminAPIView):
    """POST /api/admin/orchestration/flow/rollback/ — 回滚到指定历史版本。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        """输入：{pack_id, target_version（可选，默认回滚到 rollback_to 指向的版本）}"""
        data = request.data or {}
        pack_id = str(data.get("pack_id") or "").strip()
        if not pack_id:
            return api_fail("pack_id 不能为空")

        try:
            current = FusionPipelinePack.objects.get(pk=pack_id)
        except FusionPipelinePack.DoesNotExist:
            return api_fail("配置包不存在", code=404)

        # 确定目标版本
        target_version = str(data.get("target_version") or "").strip()
        if target_version:
            try:
                target = FusionPipelinePack.objects.get(version=target_version)
            except FusionPipelinePack.DoesNotExist:
                return api_fail(f"目标版本 {target_version} 不存在")
        elif current.rollback_to:
            target = current.rollback_to
        else:
            return api_fail("无可回滚的目标版本（rollback_to 未设置）")

        # 执行回滚：current.active → archived；target → active
        with timezone.now():
            current.pack_status = FusionPipelinePack.PACK_ARCHIVED
            current.save(update_fields=["pack_status", "updated_at"])

            target.pack_status = FusionPipelinePack.PACK_ACTIVE
            target.gray_weight = 100
            target.published_at = timezone.now()
            target.rollback_to = None
            target.save(update_fields=["pack_status", "gray_weight", "published_at", "rollback_to", "updated_at"])

        return api_ok(
            {
                "current_pack": FusionPipelineDbService.serialize_pack_summary(current),
                "target_pack": FusionPipelineDbService.serialize_pack_summary(target),
            },
            message=f"已回滚到版本 {target.version}",
        )


class OrchestrationFlowListView(AdminAPIView):
    """GET /api/admin/orchestration/flow/list/ — 工作流包列表（支持过滤）。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """支持 pack_status / gray_weight / is_default 过滤。"""
        qs = FusionPipelinePack.objects.all()

        pack_status = request.query_params.get("pack_status")
        is_default = request.query_params.get("is_default")
        q = request.query_params.get("q", "").strip()

        if pack_status:
            qs = qs.filter(pack_status=pack_status)
        if is_default is not None:
            qs = qs.filter(is_default_for_creation=(is_default.lower() not in ("false", "0")))
        if q:
            qs = qs.filter(version__icontains=q) | qs.filter(display_name__icontains=q)

        qs = qs.order_by("-updated_at")

        items = []
        for pack in qs:
            items.append({
                "id": str(pack.id),
                "version": pack.version,
                "name": pack.display_name or pack.version,
                "pack_status": pack.pack_status,
                "pack_status_label": pack.get_pack_status_display(),
                "gray_weight": pack.gray_weight,
                "is_default": pack.is_default_for_creation,
                "nodes_count": pack.nodes.count(),
                "published_by": pack.published_by,
                "published_at": pack.published_at.isoformat() if pack.published_at else None,
                "created_at": pack.created_at.isoformat(),
                "updated_at": pack.updated_at.isoformat(),
            })

        return api_ok({"items": items, "total": len(items)})
