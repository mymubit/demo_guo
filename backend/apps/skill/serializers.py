"""
技能引擎序列化器

提供配置、题材模板、钩子库、对话模板的序列化器。

注意：
- 敏感字段（如 API Key）不会在普通列表/详情接口中以明文返回。
- 更新接口支持写入敏感值。
"""
from rest_framework import serializers

from .models import SkillConfig, ThemeTemplate, HookLibrary, DialogueTemplate


class SkillConfigListSerializer(serializers.ModelSerializer):
    """SkillConfig 列表/详情序列化器

    安全策略：配置值以 *** 展示，不会返回明文。
    """

    config_value_masked = serializers.SerializerMethodField()
    has_value = serializers.SerializerMethodField()

    class Meta:
        model = SkillConfig
        fields = [
            'id',
            'config_key',
            'config_value_masked',
            'has_value',
            'description',
            'updated_at',
        ]

    def get_config_value_masked(self, obj) -> str:
        """脱敏展示配置值：若存在则显示 ******"""
        plain = obj.get_decrypted_value()
        if not plain:
            return ''
        if len(plain) <= 8:
            return '*' * len(plain)
        # 展示前 4 位 + 8 个星号
        return f'{plain[:4]}********'

    def get_has_value(self, obj) -> bool:
        return bool(obj.config_value_encrypted)


class SkillConfigUpdateSerializer(serializers.ModelSerializer):
    """SkillConfig 更新/创建序列化器

    接收明文值，写入时自动加密。
    """

    config_value = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='配置明文值（写入时自动加密）',
    )

    class Meta:
        model = SkillConfig
        fields = [
            'id',
            'config_key',
            'config_value',
            'description',
        ]

    def create(self, validated_data):
        plain_value = validated_data.pop('config_value', '')
        obj = super().create(validated_data)
        obj.set_encrypted_value(plain_value)
        obj.save()
        return obj

    def update(self, instance, validated_data):
        plain_value = validated_data.pop('config_value', None)
        instance.config_key = validated_data.get('config_key', instance.config_key)
        instance.description = validated_data.get('description', instance.description)
        if plain_value is not None:
            instance.set_encrypted_value(plain_value)
        instance.save()
        return instance


class SkillConfigDetailSerializer(serializers.ModelSerializer):
    """SkillConfig 详情（管理端使用）

    仅超级管理员在需要明文配置
    """

    config_value = serializers.SerializerMethodField()

    class Meta:
        model = SkillConfig
        fields = [
            'id',
            'config_key',
            'config_value',
            'description',
            'updated_at',
        ]

    def get_config_value(self, obj) -> str:
        return obj.get_decrypted_value() or ''


class ThemeTemplateSerializer(serializers.ModelSerializer):
    """题材模板序列化器"""

    class Meta:
        model = ThemeTemplate
        fields = [
            'id',
            'theme_code',
            'theme_name',
            'is_active',
            'sort_order',
            'params',
            'hook_templates',
            'character_archetypes',
            'created_at',
            'updated_at',
        ]


class ThemeTemplateSummarySerializer(serializers.ModelSerializer):
    """题材模板摘要（供前端选择使用）"""

    class Meta:
        model = ThemeTemplate
        fields = [
            'id',
            'theme_code',
            'theme_name',
            'is_active',
            'sort_order',
            'params',
            'hook_templates',
            'character_archetypes',
        ]


class HookLibrarySerializer(serializers.ModelSerializer):
    """钩子库序列化器"""

    hook_type_label = serializers.SerializerMethodField()
    tag_list = serializers.SerializerMethodField()

    class Meta:
        model = HookLibrary
        fields = [
            'id',
            'hook_type',
            'hook_type_label',
            'content',
            'tags',
            'tag_list',
            'is_active',
            'use_count',
            'created_at',
        ]

    def get_hook_type_label(self, obj) -> str:
        return obj.get_hook_type_display()

    def get_tag_list(self, obj):
        return obj.get_tag_list()


class DialogueTemplateSerializer(serializers.ModelSerializer):
    """对话模板序列化器"""

    emotion_type_label = serializers.SerializerMethodField()

    class Meta:
        model = DialogueTemplate
        fields = [
            'id',
            'emotion_type',
            'emotion_type_label',
            'template_text',
            'is_active',
            'use_count',
            'created_at',
        ]

    def get_emotion_type_label(self, obj) -> str:
        return obj.get_emotion_type_display()


class ScriptGenerateInputSerializer(serializers.Serializer):
    """剧本生成输入参数"""

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
        help_text='是否使用 LLM 生成（默认 False，使用模板生成）',
    )


class ScriptSceneSerializer(serializers.Serializer):
    """剧本场次序列化器"""

    scene_index = serializers.IntegerField()
    scene_title = serializers.CharField()
    location = serializers.CharField()
    hook = serializers.CharField(required=False, default='')
    dialogue = serializers.ListField(child=serializers.CharField())
    narration = serializers.CharField(required=False, default='')


class ScriptGenerateResultSerializer(serializers.Serializer):
    """剧本生成结果"""

    title = serializers.CharField()
    theme_code = serializers.CharField()
    protagonist = serializers.CharField()
    scenes = ScriptSceneSerializer(many=True)
    golden_sentences = serializers.ListField(child=serializers.CharField(), required=False)
    generated_by = serializers.CharField(required=False, default='template')
