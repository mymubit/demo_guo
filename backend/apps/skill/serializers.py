"""
技能引擎序列化器

提供以下序列化器：
- SkillConfigUpdateSerializer：技能配置写入（明文输入，写入时由 service 层加密）
- ThemeTemplateSerializer：题材模板读写
- HookLibrarySerializer：钩子库读写
- ScriptGenerateInputSerializer：剧本生成输入参数（用于创作模块对接校验）
"""
from rest_framework import serializers

from .models import SkillConfig, ThemeTemplate, HookLibrary


# ============================================================
# SkillConfig
# ============================================================
class SkillConfigUpdateSerializer(serializers.Serializer):
    """SkillConfig 更新/创建序列化器

    接收明文值，写入时由 SkillConfigService 调用 models 层方法自动加密。
    """

    config_key = serializers.CharField(
        max_length=128,
        help_text='配置键，例如 llm.api_key',
    )
    config_value = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        help_text='配置明文值（写入时自动加密）',
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        help_text='配置描述',
    )


# ============================================================
# ThemeTemplate
# ============================================================
class ThemeTemplateSerializer(serializers.ModelSerializer):
    """题材模板序列化器"""

    class Meta:
        model = ThemeTemplate
        fields = [
            'theme_code',
            'theme_name',
            'is_active',
            'sort_order',
            'params',
            'hook_templates',
            'character_archetypes',
        ]


# ============================================================
# HookLibrary
# ============================================================
class HookLibrarySerializer(serializers.ModelSerializer):
    """钩子库序列化器"""

    class Meta:
        model = HookLibrary
        fields = [
            'hook_type',
            'content',
            'tags',
            'is_active',
        ]


# ============================================================
# ScriptGenerateInput（创作模块参数校验用）
# ============================================================
class ScriptGenerateInputSerializer(serializers.Serializer):
    """剧本生成输入参数

    用于创作模块调用前的参数校验。
    """

    theme_code = serializers.CharField(
        required=True,
        help_text='题材代码，例如 family-revenge',
    )
    title = serializers.CharField(
        required=False,
        default='',
        allow_blank=True,
        help_text='剧本标题（可选）',
    )
    protagonist = serializers.CharField(
        required=False,
        default='主角',
        help_text='主角名称',
    )
    scene_count = serializers.IntegerField(
        required=False,
        default=8,
        min_value=3,
        max_value=30,
        help_text='场次数（3-30）',
    )
    use_llm = serializers.BooleanField(
        required=False,
        default=False,
        help_text='是否启用 LLM 生成内容',
    )
