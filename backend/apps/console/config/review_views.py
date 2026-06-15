# -*- coding: utf-8 -*-
"""配置中心 — 审查评分权重。"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_ok
from apps.skill.config.portal.review_scoring import ReviewScoringService


class ReviewScoringConfigView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return api_ok(ReviewScoringService.get_admin_payload())

    def put(self, request):
        data = request.data or {}
        ReviewScoringService.save(data)
        return api_ok(ReviewScoringService.get_admin_payload(), message="审查评分配置已保存")
