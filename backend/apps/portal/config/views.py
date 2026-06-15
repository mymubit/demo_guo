"""前台公开技能接口（不含管理配置）"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.skill.config.portal.skill_settings import ThemeTemplateService

logger = logging.getLogger(__name__)


class ThemePublicListView(APIView):
    """公共题材列表（供创作页下拉框）"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = ThemeTemplateService.list_themes(only_active=True)
        simplified = [
            {
                "id": item.get("id"),
                "theme_code": item.get("theme_code"),
                "theme_name": item.get("theme_name"),
                "description": item.get("description", ""),
            }
            for item in items
        ]
        return Response(
            {"code": 0, "message": "success", "data": simplified},
            status=status.HTTP_200_OK,
        )
