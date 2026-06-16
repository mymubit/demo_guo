# -*- coding: utf-8 -*-
"""
AI 规则进化 API（Admin 视角）。

提供提案的列表、详情、审批和应用等管理接口。
所有接口均需 Admin 权限。
"""
from __future__ import annotations

import uuid

from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok
from apps.skill.evolution.models import RuleEvolutionProposal
from apps.skill.evolution.services import RuleEvolutionService


class EvolutionProposalListView(APIView):
    """提案列表 — GET /api/admin/skills/evolution/"""

    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        获取提案列表。
        支持按 status 筛选和分页。
        """
        status_filter = request.query_params.get("status")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        qs = RuleEvolutionProposal.objects.all()

        if status_filter:
            qs = qs.filter(status=status_filter)

        total = qs.count()
        offset = (page - 1) * page_size
        proposals = qs[offset : offset + page_size]

        items = []
        for p in proposals:
            items.append({
                "id": str(p.id),
                "trigger_project_id": str(p.trigger_project_id) if p.trigger_project_id else None,
                "trigger_reason": p.trigger_reason,
                "target_skill_id": p.target_skill_id,
                "target_tier": p.target_tier,
                "target_scope_key": p.target_scope_key,
                "current_value": p.current_value,
                "proposed_value": p.proposed_value,
                "change_reason": p.change_reason,
                "status": p.status,
                "status_label": p.get_status_display(),
                "proposed_by": p.proposed_by,
                "approved_by": str(p.approved_by_id) if p.approved_by_id else None,
                "approved_at": p.approved_at.isoformat() if p.approved_at else None,
                "approval_comment": p.approval_comment,
                "applied_at": p.applied_at.isoformat() if p.applied_at else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })

        return api_ok({
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        })


class EvolutionAnalyzeView(APIView):
    """触发分析 — POST /api/admin/skills/evolution/analyze/"""

    permission_classes = [IsAdminUser]

    def post(self, request):
        """
        触发低评分项目分析和提案生成。

        入参：{days: 7}  // 可选，默认 7 天
        执行 batch_analyze_and_propose。
        """
        days = int(request.data.get("days", 7))
        if days < 1 or days > 90:
            return api_fail("分析天数必须在 1-90 之间", code=400)

        service = RuleEvolutionService()
        proposals = service.batch_analyze_and_propose(days=days)

        return api_ok({
            "proposals_created": len(proposals),
            "proposal_ids": [str(p.id) for p in proposals],
        }, message=f"分析完成，生成 {len(proposals)} 个提案")


class EvolutionProposalDetailView(APIView):
    """提案详情 — GET /api/admin/skills/evolution/<id>/"""

    permission_classes = [IsAdminUser]

    def get(self, request, proposal_id: str):
        """获取提案详情。"""
        try:
            proposal = RuleEvolutionProposal.objects.get(pk=proposal_id)
        except RuleEvolutionProposal.DoesNotExist:
            return api_fail("提案不存在", code=404)
        except ValueError:
            return api_fail("无效的提案 ID", code=400)

        return api_ok({
            "id": str(proposal.id),
            "trigger_project_id": str(proposal.trigger_project_id) if proposal.trigger_project_id else None,
            "trigger_reason": proposal.trigger_reason,
            "target_skill_id": proposal.target_skill_id,
            "target_tier": proposal.target_tier,
            "target_scope_key": proposal.target_scope_key,
            "current_value": proposal.current_value,
            "proposed_value": proposal.proposed_value,
            "change_reason": proposal.change_reason,
            "status": proposal.status,
            "status_label": proposal.get_status_display(),
            "proposed_by": proposal.proposed_by,
            "approved_by": str(proposal.approved_by_id) if proposal.approved_by_id else None,
            "approved_at": proposal.approved_at.isoformat() if proposal.approved_at else None,
            "approval_comment": proposal.approval_comment,
            "applied_at": proposal.applied_at.isoformat() if proposal.applied_at else None,
            "created_at": proposal.created_at.isoformat() if proposal.created_at else None,
            "updated_at": proposal.updated_at.isoformat() if proposal.updated_at else None,
        })


class EvolutionApproveView(APIView):
    """审批通过 — POST /api/admin/skills/evolution/<id>/approve/"""

    permission_classes = [IsAdminUser]

    def post(self, request, proposal_id: str):
        """
        审批通过提案。

        入参：{comment: "审批意见"}  // 可选
        """
        try:
            proposal_uuid = uuid.UUID(proposal_id)
        except ValueError:
            return api_fail("无效的提案 ID", code=400)

        comment = request.data.get("comment", "")
        approver = request.user

        service = RuleEvolutionService()
        try:
            service.approve_proposal(proposal_uuid, approver, comment)
        except ValueError as exc:
            return api_fail(str(exc), code=400)

        return api_ok(message="审批通过")


class EvolutionRejectView(APIView):
    """审批拒绝 — POST /api/admin/skills/evolution/<id>/reject/"""

    permission_classes = [IsAdminUser]

    def post(self, request, proposal_id: str):
        """
        拒绝提案。

        入参：{comment: "拒绝原因"}  // 可选
        """
        try:
            proposal_uuid = uuid.UUID(proposal_id)
        except ValueError:
            return api_fail("无效的提案 ID", code=400)

        comment = request.data.get("comment", "")
        rejector = request.user

        service = RuleEvolutionService()
        try:
            service.reject_proposal(proposal_uuid, rejector, comment)
        except ValueError as exc:
            return api_fail(str(exc), code=400)

        return api_ok(message="提案已拒绝")


class EvolutionApplyView(APIView):
    """应用提案 — POST /api/admin/skills/evolution/<id>/apply/"""

    permission_classes = [IsAdminUser]

    def post(self, request, proposal_id: str):
        """
        应用已审批的提案。

        将提案值写入 SkillRuleConfig 表。
        """
        try:
            proposal_uuid = uuid.UUID(proposal_id)
        except ValueError:
            return api_fail("无效的提案 ID", code=400)

        service = RuleEvolutionService()
        try:
            service.apply_proposal(proposal_uuid)
        except ValueError as exc:
            return api_fail(str(exc), code=400)

        return api_ok(message="提案已应用")
