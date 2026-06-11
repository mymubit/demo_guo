"""
技能配置模块 API 视图（管理员权限）

路由 /api/skill/...

接口：
  GET  /configs/          技能配置列表（管理员，脱敏）
  PUT  /configs/<key>/    更新单个技能配置（管理员）
  GET  /themes/           题材模板列表（管理员）
  POST /themes/           新增题材模板（管理员）
  PUT  /themes/<id>/      更新题材模板（管理员）
  GET  /hooks/            钩子库列表（管理员）
  POST /hooks/            新增钩子（管理员）
  GET  /themes/public/    精简题材列表（登录用户可读）
"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import PermissionDenied

from apps.skill.serializers import (
    SkillConfigUpdateSerializer,
    ThemeTemplateSerializer,
    HookLibrarySerializer,
)
from apps.skill.services import (
    SkillConfigService,
    ThemeTemplateService,
    HookLibraryService,
)
from apps.skill.models import HookLibrary

logger = logging.getLogger(__name__)


# ============================================================
# 权限辅助：仅 staff / superuser
# ============================================================
def _require_admin(user):
    if not (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)):
        raise PermissionDenied('仅管理员可操作技能配置')


# ============================================================
# 1. 技能配置
# ============================================================
class SkillConfigListView(APIView):
    """读取所有技能配置（管理员，敏感项脱敏）

    GET /api/skill/configs/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_admin(request.user)

        # mask_sensitive=True：敏感项（如 llm.api_key）返回空字符串
        items = SkillConfigService.all_configs(mask_sensitive=True)

        return Response(
            {'code': 0, 'message': 'success', 'data': items},
            status=status.HTTP_200_OK,
        )


class SkillConfigUpdateView(APIView):
    """更新单个技能配置

    PUT /api/skill/configs/<config_key>/
    Body: { "value": "...", "description": "..." }
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, config_key: str):
        _require_admin(request.user)

        # 兼容校验：构造一个符合序列化器格式的 payload
        payload = {
            'config_key': config_key,
            'config_value': request.data.get('value', ''),
            'description': request.data.get('description', ''),
        }
        serializer = SkillConfigUpdateSerializer(data=payload)
        serializer.is_valid(raise_exception=True)

        value = serializer.validated_data.get('config_value', '')
        description = serializer.validated_data.get('description', '')

        obj = SkillConfigService.set(config_key, str(value), description)
        if obj is None:
            return Response(
                {'code': 500, 'message': '配置写入失败', 'data': None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info(
            'skill_config_updated user=%s key=%s',
            getattr(request.user, 'id', '?'),
            config_key,
        )

        return Response(
            {'code': 0, 'message': 'success', 'data': {'key': config_key}},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 2. 题材模板
# ============================================================
class ThemeTemplateListView(APIView):
    """题材模板列表 / 新增

    GET  /api/skill/themes/   （管理员）
    POST /api/skill/themes/   （管理员，新增）
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_admin(request.user)
        result = ThemeTemplateService.list_themes(only_active=False)
        return Response(
            {'code': 0, 'message': 'success', 'data': result},
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        _require_admin(request.user)
        serializer = ThemeTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            obj = ThemeTemplateService.create_or_update({
                'theme_code': data['theme_code'],
                'theme_name': data.get('theme_name', data['theme_code']),
                'is_active': data.get('is_active', True),
                'sort_order': data.get('sort_order', 0),
                'params': data.get('params', {}) or {},
                'hook_templates': data.get('hook_templates', []) or [],
                'character_archetypes': data.get('character_archetypes', []) or [],
            })
        except ValueError as exc:
            return Response(
                {'code': 400, 'message': str(exc), 'data': None},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {'code': 0, 'message': 'success', 'data': {'id': str(obj.id), 'theme_code': obj.theme_code}},
            status=status.HTTP_200_OK,
        )


class ThemeTemplateUpdateView(APIView):
    """更新题材模板

    PUT /api/skill/themes/<theme_id>/
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, theme_id):
        _require_admin(request.user)

        serializer = ThemeTemplateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        obj = ThemeTemplateService.update_by_id(theme_id, serializer.validated_data)
        if obj is None:
            return Response(
                {'code': 404, 'message': '题材模板不存在', 'data': None},
                status=status.HTTP_200_OK,
            )

        return Response(
            {'code': 0, 'message': 'success', 'data': {'id': str(obj.id)}},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 3. 钩子库
# ============================================================
class HookLibraryListView(APIView):
    """钩子库

    GET  /api/skill/hooks/   （管理员，列表）
    POST /api/skill/hooks/   （管理员，新增）
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_admin(request.user)

        hook_type = request.query_params.get('hook_type')
        data = HookLibraryService.list_hooks(hook_type=hook_type, only_active=False)

        return Response(
            {'code': 0, 'message': 'success', 'data': data},
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        _require_admin(request.user)
        serializer = HookLibrarySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        hook = HookLibraryService.create(
            hook_type=data.get('hook_type', 'opening'),
            content=data['content'],
            tags=data.get('tags', ''),
            is_active=data.get('is_active', True),
        )
        return Response(
            {'code': 0, 'message': 'success', 'data': {'id': str(hook.id)}},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 4. 前端可读取的题材列表（登录用户可读取，不带敏感信息）
# ============================================================
class ThemePublicListView(APIView):
    """公共题材列表（供前端创作页下拉框）

    GET /api/skill/themes/public/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = ThemeTemplateService.list_themes(only_active=True)
        simplified = [
            {
                'id': item.get('id'),
                'theme_code': item.get('theme_code'),
                'theme_name': item.get('theme_name'),
                'description': item.get('description', ''),
            }
            for item in items
        ]
        return Response(
            {'code': 0, 'message': 'success', 'data': simplified},
            status=status.HTTP_200_OK,
        )
