"""
技能引擎数据模型

核心模型：
- SkillConfig：技能引擎加密配置（LLM API Key、模型参数等敏感信息）
- ThemeTemplate：短剧题材模板（8大热门题材）
- HookLibrary：钩子库（开场/反转/悬念/金句）
- DialogueTemplate：常见对话模板

加密方案：
- 使用 pycryptodome 的 AES-256-CBC
- 密钥从 settings.SKILL_ENCRYPT_KEY 读取（32 字节）
- IV 使用随机 16 字节
- 密文存储格式：base64(iv + ciphertext)
"""
import base64
import hashlib
import logging
import random
import uuid
from typing import Optional

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

from django.conf import settings
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)

# ============================================================
# AES-256-CBC 加密辅助函数
# ============================================================


def _get_encrypt_key() -> bytes:
    """获取加密密钥（32 字节 / 256 位）

    优先使用 settings.SKILL_ENCRYPT_KEY（若为 32 字节字符串直接使用）
    否则对设置字符串进行 SHA256 摘要，确保产生 32 字节密钥。
    """
    raw = str(settings.SKILL_ENCRYPT_KEY or '')
    if len(raw) == 32:
        return raw.encode('utf-8')
    # 对任意长度输入做 SHA256，稳定得到 32 字节
    return hashlib.sha256(raw.encode('utf-8')).digest()


def encrypt_text(plain_text: str) -> str:
    """使用 AES-256-CBC 加密文本，返回 base64(iv + ciphertext)"""
    if plain_text is None:
        return ''
    key = _get_encrypt_key()
    iv = get_random_bytes(16)  # IV 必须 16 字节
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(plain_text.encode('utf-8'), AES.block_size)
    ciphertext = cipher.encrypt(padded)
    return base64.b64encode(iv + ciphertext).decode('utf-8')


def decrypt_text(cipher_text: str) -> Optional[str]:
    """解密 AES-256-CBC 加密文本"""
    if not cipher_text:
        return None
    try:
        key = _get_encrypt_key()
        raw = base64.b64decode(cipher_text.encode('utf-8'))
        iv = raw[:16]
        ciphertext = raw[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded = cipher.decrypt(ciphertext)
        plain = unpad(padded, AES.block_size)
        return plain.decode('utf-8')
    except Exception as e:  # noqa: BLE001
        logger.warning('解密失败: %s', e)
        return None


# ============================================================
# 钩子类型常量
# ============================================================
HOOK_TYPE_OPENING = 'opening'       # 开场钩子
HOOK_TYPE_REVERSAL = 'reversal'     # 反转钩子
HOOK_TYPE_SUSPENSE = 'suspense'     # 悬念钩子
HOOK_TYPE_GOLDEN = 'golden'         # 金句钩子
HOOK_TYPE_CLIMAX = 'climax'         # 高潮钩子
HOOK_TYPE_ENDING = 'ending'         # 结尾钩子

HOOK_TYPE_CHOICES = [
    (HOOK_TYPE_OPENING, '开场钩子'),
    (HOOK_TYPE_REVERSAL, '反转钩子'),
    (HOOK_TYPE_SUSPENSE, '悬念钩子'),
    (HOOK_TYPE_GOLDEN, '金句钩子'),
    (HOOK_TYPE_CLIMAX, '高潮钩子'),
    (HOOK_TYPE_ENDING, '结尾钩子'),
]

# ============================================================
# 情绪类型常量
# ============================================================
EMOTION_CHOICES = [
    ('happy', '开心'),
    ('sad', '悲伤'),
    ('angry', '愤怒'),
    ('anxious', '焦虑'),
    ('surprised', '惊讶'),
    ('fear', '恐惧'),
    ('romantic', '浪漫'),
    ('cold', '冷漠'),
    ('sarcastic', '讽刺'),
    ('gentle', '温柔'),
    ('domineering', '霸道'),
    ('mocking', '嘲讽'),
    ('firm', '坚定'),
    ('desperate', '绝望'),
    ('envy', '嫉妒'),
]


# ============================================================
# SkillConfig：加密配置
# ============================================================
class SkillConfig(models.Model):
    """技能引擎加密配置

    存储 LLM API Key、模型名称、温度、提示词模板等敏感信息。
    所有配置值均使用 AES-256-CBC 加密后存储。

    常见 config_key 示例：
    - llm.api_key        : 大语言模型 API Key
    - llm.base_url       : 大语言模型 Base URL
    - llm.model_name     : 使用的模型名称（如 gpt-4 / deepseek-chat）
    - llm.temperature    : 温度参数（默认 0.7）
    - llm.max_tokens     : 最大 token 数
    - llm.system_prompt  : 系统提示词模板
    - script.max_length  : 剧本最大长度
    - script.min_scenes  : 最少场次数
    - hook.daily_limit   : 每日钩子调用上限
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField(
        '配置键',
        max_length=128,
        unique=True,
        db_index=True,
        help_text='唯一配置键名（例如 llm.api_key）',
    )
    config_value_encrypted = models.TextField(
        '加密后的配置值',
        blank=True,
        default='',
        help_text='AES-256-CBC 加密后的 base64 文本',
    )
    description = models.CharField(
        '配置描述',
        max_length=512,
        blank=True,
        default='',
    )
    updated_at = models.DateTimeField('更新时间', default=timezone.now, auto_now=True)

    class Meta:
        verbose_name = '技能引擎配置'
        verbose_name_plural = verbose_name
        ordering = ['config_key']

    def __str__(self):
        return f'{self.config_key}'

    # ---------- 加密/解密辅助方法 ----------

    def get_decrypted_value(self) -> Optional[str]:
        """获取解密后的配置值"""
        return decrypt_text(self.config_value_encrypted)

    def set_encrypted_value(self, plain_value: str) -> None:
        """设置配置值（自动加密）"""
        if plain_value is None:
            plain_value = ''
        self.config_value_encrypted = encrypt_text(str(plain_value))

    def save(self, *args, **kwargs):
        # 确保 updated_at 被更新
        if not self.updated_at:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)


# ============================================================
# ThemeTemplate：题材模板
# ============================================================
class ThemeTemplate(models.Model):
    """短剧题材模板

    包含 8 大热门题材：
    - family-revenge   家庭复仇
    - domineering-ceo  豪门霸总
    - sweet-pet        甜宠虐恋
    - time-travel      穿越重生
    - urban-counterattack 都市逆袭
    - ancient-power    古装权谋
    - mystery-reversal 悬疑反转
    - hybrid           混合题材
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    theme_code = models.CharField(
        '题材代码',
        max_length=64,
        unique=True,
        db_index=True,
        help_text='英文唯一标识，例如 family-revenge',
    )
    theme_name = models.CharField('题材名称', max_length=64, help_text='例如 家庭复仇')
    is_active = models.BooleanField('是否启用', default=True)
    sort_order = models.IntegerField('排序', default=0, help_text='数值越小越靠前')

    # 结构化参数：包括剧本结构模板、反转密度、情绪曲线系数等
    params = models.JSONField(
        '参数配置',
        default=dict,
        blank=True,
        help_text='包含 structure(结构)、reversal_density(反转密度)、emotion_curve(情绪曲线) 等',
    )

    # 钩子模板：按剧情阶段（开场/发展/高潮/结尾）的推荐钩子组合
    hook_templates = models.JSONField(
        '钩子模板配置',
        default=dict,
        blank=True,
        help_text='按剧情阶段分类的钩子推荐配置',
    )

    # 角色原型：主角/配角/反派的典型人设模板
    character_archetypes = models.JSONField(
        '角色原型',
        default=list,
        blank=True,
        help_text='角色原型列表，包含名称、描述、标签等',
    )

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', default=timezone.now, auto_now=True)

    class Meta:
        verbose_name = '题材模板'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return f'{self.theme_name} ({self.theme_code})'


# ============================================================
# HookLibrary：钩子库
# ============================================================
class HookLibrary(models.Model):
    """钩子库

    存储可复用的短剧钩子文本，按类型（开场/反转/悬念/金句/高潮/结尾）组织。
    use_count 记录被引用次数，用于统计和排序。
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hook_type = models.CharField(
        '钩子类型',
        max_length=32,
        choices=HOOK_TYPE_CHOICES,
        default=HOOK_TYPE_OPENING,
        db_index=True,
    )
    content = models.TextField(
        '钩子内容',
        help_text='钩子文本，可包含 {role} {name} 等占位符',
    )
    tags = models.CharField(
        '标签',
        max_length=256,
        blank=True,
        default='',
        help_text='逗号分隔的标签，例如 豪门,误会,身份反转',
    )
    is_active = models.BooleanField('是否启用', default=True)
    use_count = models.IntegerField('使用次数', default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        verbose_name = '钩子库'
        verbose_name_plural = verbose_name
        ordering = ['-use_count', '-created_at']
        indexes = [
            models.Index(fields=['hook_type', 'is_active']),
        ]

    def __str__(self):
        snippet = self.content[:20] if self.content else ''
        return f'[{self.get_hook_type_display()}] {snippet}...'

    def increment_use_count(self) -> None:
        """使用次数 +1"""
        self.use_count = models.F('use_count') + 1
        self.save(update_fields=['use_count'])

    def get_tag_list(self):
        """将 tags 字段拆分为列表"""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]


# ============================================================
# DialogueTemplate：对话模板
# ============================================================
class DialogueTemplate(models.Model):
    """对话模板

    按情绪类型组织的常见对话句式，用于剧本生成时填充对话。
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emotion_type = models.CharField(
        '情绪类型',
        max_length=32,
        choices=EMOTION_CHOICES,
        default='happy',
        db_index=True,
    )
    template_text = models.TextField(
        '模板文本',
        help_text='对话文本，可包含 {speaker} {listener} {topic} 等占位符',
    )
    is_active = models.BooleanField('是否启用', default=True)
    use_count = models.IntegerField('使用次数', default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        verbose_name = '对话模板'
        verbose_name_plural = verbose_name
        ordering = ['-use_count', '-created_at']
        indexes = [
            models.Index(fields=['emotion_type', 'is_active']),
        ]

    def __str__(self):
        snippet = self.template_text[:20] if self.template_text else ''
        return f'[{self.get_emotion_type_display()}] {snippet}...'

    def increment_use_count(self) -> None:
        """使用次数 +1"""
        self.use_count = models.F('use_count') + 1
        self.save(update_fields=['use_count'])
