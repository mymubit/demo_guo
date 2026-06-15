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
    updated_at = models.DateTimeField('更新时间', auto_now=True)

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
# LlmModelCatalog：大模型目录（Admin 可维护，非运行时写死）
# ============================================================
class LlmModelCatalog(models.Model):
    """平台支持的模型目录模板；LlmProvider 为实际接入实例。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preset_key = models.CharField("预设键", max_length=64, unique=True, db_index=True)
    name = models.CharField("展示名称", max_length=100)
    vendor = models.CharField("厂商标识", max_length=64, db_index=True)
    vendor_label = models.CharField("厂商名称", max_length=64, blank=True, default="")
    base_url = models.CharField("Base URL", max_length=512)
    model_name = models.CharField("模型 ID", max_length=128)
    temperature = models.FloatField("默认 Temperature", default=0.7)
    max_tokens = models.PositiveIntegerField("默认 Max Tokens", default=8192)
    context_window_input = models.PositiveIntegerField("上下文窗口-输入", null=True, blank=True)
    context_window_output = models.PositiveIntegerField("上下文窗口-输出", null=True, blank=True)
    tool_call_rounds = models.PositiveIntegerField("工具调用轮次", null=True, blank=True)
    supports_multimodal = models.BooleanField("支持多模态", default=False)
    api_key_hint = models.CharField("API Key 提示", max_length=255, blank=True, default="")
    api_key_url = models.CharField("获取 Key 链接", max_length=512, blank=True, default="")
    remark = models.CharField("备注", max_length=512, blank=True, default="")
    input_price_per_million = models.DecimalField(
        "输入单价(元/百万Token)",
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
    )
    output_price_per_million = models.DecimalField(
        "输出单价(元/百万Token)",
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
    )
    is_enabled = models.BooleanField("启用", default=True, db_index=True)
    sort_order = models.IntegerField("排序", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "skill_llm_model_catalog"
        verbose_name = "大模型目录"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "vendor", "name"]

    def __str__(self):
        return f"{self.vendor_label or self.vendor} / {self.name}"


# ============================================================
# LlmProvider：多模型配置（OpenAI 兼容）
# ============================================================
class LlmProvider(models.Model):
    """大语言模型接入配置，支持多模型并存、切换当前启用项。"""

    PROVIDER_OPENAI_COMPAT = "openai_compatible"

    PROVIDER_TYPE_CHOICES = [
        (PROVIDER_OPENAI_COMPAT, "OpenAI 兼容"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    catalog = models.ForeignKey(
        LlmModelCatalog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="providers",
        verbose_name="目录模板",
    )
    name = models.CharField("展示名称", max_length=100)
    provider_type = models.CharField(
        "接入类型",
        max_length=32,
        choices=PROVIDER_TYPE_CHOICES,
        default=PROVIDER_OPENAI_COMPAT,
    )
    api_key_encrypted = models.TextField("加密 API Key", blank=True, default="")
    base_url = models.CharField("Base URL", max_length=512, blank=True, default="")
    model_name = models.CharField("模型名称", max_length=128, default="gpt-4o-mini")
    temperature = models.FloatField("Temperature", default=0.7)
    max_tokens = models.PositiveIntegerField("Max Tokens", default=4096)
    context_window_input = models.PositiveIntegerField("上下文窗口-输入", null=True, blank=True)
    context_window_output = models.PositiveIntegerField("上下文窗口-输出", null=True, blank=True)
    tool_call_rounds = models.PositiveIntegerField("工具调用轮次", null=True, blank=True)
    supports_multimodal = models.BooleanField("支持多模态", default=False)
    is_active = models.BooleanField("当前启用", default=False, db_index=True)
    is_enabled = models.BooleanField("启用", default=True)
    sort_order = models.IntegerField("排序", default=0)
    remark = models.CharField("备注", max_length=255, blank=True, default="")
    volcano_key_type = models.CharField(
        "火山 Key 类型",
        max_length=32,
        blank=True,
        default="",
        db_index=True,
        help_text="payg=按量付费 /api/v3；coding_plan=Coding Plan /api/coding/v3",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "skill_llm_provider"
        verbose_name = "大模型配置"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.name

    def get_api_key(self) -> Optional[str]:
        return decrypt_text(self.api_key_encrypted)

    def set_api_key(self, plain_value: str) -> None:
        self.api_key_encrypted = encrypt_text("" if plain_value is None else str(plain_value))

    @property
    def api_key_set(self) -> bool:
        return bool(self.get_api_key())


# ============================================================
# LlmUsageLog：大模型 API 调用用量（Token 统计）
# ============================================================
class LlmUsageLog(models.Model):
    """单次 Chat Completions 调用的 Token 用量。"""

    SOURCE_NODE = "node"
    SOURCE_AGENT = "agent"
    SOURCE_AI_FIELD = "ai_field"
    SOURCE_TEST = "test"
    SOURCE_OTHER = "other"

    SOURCE_TYPE_CHOICES = [
        (SOURCE_NODE, "融合节点"),
        (SOURCE_AGENT, "辅助 Agent"),
        (SOURCE_AI_FIELD, "AI 字段"),
        (SOURCE_TEST, "连通测试"),
        (SOURCE_OTHER, "其他"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        LlmProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usage_logs",
        verbose_name="Provider",
    )
    provider_name = models.CharField("Provider 名称", max_length=100, blank=True, default="")
    model_name = models.CharField("模型", max_length=128, db_index=True)
    prompt_tokens = models.PositiveIntegerField("Prompt Tokens", default=0)
    completion_tokens = models.PositiveIntegerField("Completion Tokens", default=0)
    total_tokens = models.PositiveIntegerField("Total Tokens", default=0)
    source_type = models.CharField(
        "来源类型",
        max_length=32,
        choices=SOURCE_TYPE_CHOICES,
        default=SOURCE_OTHER,
        db_index=True,
    )
    source_key = models.CharField("来源标识", max_length=64, blank=True, default="", db_index=True)
    project = models.ForeignKey(
        "creation.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="llm_usage_logs",
        verbose_name="项目",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="llm_usage_logs",
        verbose_name="用户",
    )
    success = models.BooleanField("成功", default=True)
    estimated_input_cost_yuan = models.DecimalField(
        "估算输入费用(元)",
        max_digits=12,
        decimal_places=6,
        default=0,
    )
    estimated_output_cost_yuan = models.DecimalField(
        "估算输出费用(元)",
        max_digits=12,
        decimal_places=6,
        default=0,
    )
    estimated_cost_yuan = models.DecimalField(
        "估算费用(元)",
        max_digits=12,
        decimal_places=6,
        default=0,
    )
    execution_run = models.ForeignKey(
        "creation.AgentExecutionRun",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="llm_usage_logs",
        verbose_name="Agent 执行记录",
    )
    sub_skill_id = models.CharField("子技能 ID", max_length=128, blank=True, default="", db_index=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)

    class Meta:
        db_table = "skill_llm_usage_log"
        verbose_name = "大模型调用用量"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at", "model_name"]),
            models.Index(fields=["-created_at", "provider_name"]),
        ]

    def __str__(self):
        return f"{self.model_name} {self.total_tokens}t @ {self.created_at}"


# ============================================================
# ThemeTemplate：题材模板
# ============================================================
class ThemeTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    theme_code = models.CharField('题材代码', max_length=64, unique=True, db_index=True)
    theme_name = models.CharField('题材名称', max_length=64)
    is_active = models.BooleanField('是否启用', default=True)
    sort_order = models.IntegerField('排序', default=0)
    params = models.JSONField('参数配置', default=dict, blank=True)
    hook_templates = models.JSONField('钩子模板配置', default=dict, blank=True)
    character_archetypes = models.JSONField('角色原型', default=list, blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '题材模板'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return f'{self.theme_name} ({self.theme_code})'


class HookLibrary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hook_type = models.CharField(
        '钩子类型', max_length=32, choices=HOOK_TYPE_CHOICES,
        default=HOOK_TYPE_OPENING, db_index=True,
    )
    content = models.TextField('钩子内容')
    tags = models.CharField('标签', max_length=256, blank=True, default='')
    is_active = models.BooleanField('是否启用', default=True)
    use_count = models.IntegerField('使用次数', default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        verbose_name = '钩子库'
        verbose_name_plural = verbose_name
        ordering = ['-use_count', '-created_at']
        indexes = [models.Index(fields=['hook_type', 'is_active'])]

    def __str__(self):
        snippet = self.content[:20] if self.content else ''
        return f'[{self.get_hook_type_display()}] {snippet}...'


class DialogueTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emotion_type = models.CharField(
        '情绪类型', max_length=32, choices=EMOTION_CHOICES,
        default='happy', db_index=True,
    )
    template_text = models.TextField('模板文本')
    is_active = models.BooleanField('是否启用', default=True)
    use_count = models.IntegerField('使用次数', default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        verbose_name = '对话模板'
        verbose_name_plural = verbose_name
        ordering = ['-use_count', '-created_at']
        indexes = [models.Index(fields=['emotion_type', 'is_active'])]

    def __str__(self):
        snippet = self.template_text[:20] if self.template_text else ''
        return f'[{self.get_emotion_type_display()}] {snippet}...'


class CreationFormOverrideConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=32, unique=True, default="default")
    overrides = models.JSONField("表单覆盖", default=dict, blank=True)
    episode_settings = models.JSONField("集数默认值", default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "创作表单覆盖"
        verbose_name_plural = verbose_name
        db_table = "skill_creation_form_override"

    def __str__(self) -> str:
        return self.config_key


# ============================================================
class ReferenceLibraryConfig(models.Model):
    """参考库 JSON 内容（DB SSOT；磁盘 references/ 仅 import/sync）。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=32, unique=True, default="default")
    content = models.JSONField(
        "参考库内容",
        default=dict,
        blank=True,
        help_text='键为文件名（如 industry-benchmarks.json），值为解析后的 JSON 对象',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "参考库配置"
        verbose_name_plural = verbose_name
        db_table = "skill_reference_library_config"

    def __str__(self) -> str:
        count = len(self.content) if isinstance(self.content, dict) else 0
        return f"参考库 · {count} 文件"


# ============================================================
# SkillRuleConfig：技能规则库（DB-backed，替代 tier2/tier3 JSON 文件）
# ============================================================
class SkillRuleConfig(models.Model):
    """
    技能规则配置库（Tier2 品类规范 + Tier3 节点验收标准）

    设计原则：
    - DB 优先，JSON 文件作为 fallback（首次从文件导入到 DB）
    - 每条规则有版本号、状态、来源，支持调用链追踪
    - 进化审计写 draft，Admin 批准变 active，旧版自动变 archived
    - Tier1/Tier4 可通过 DB（tier=1/4, section=tier_full）覆盖 JSON 文件；无 active 记录时仍读磁盘

    scope_type + scope_key 确定规则作用范围：
      global  + ""                → 全局通用（不区分题材/节点）
      genre   + "family-revenge"  → 针对某题材（Tier2）
      node    + "node-5-script"   → 针对某节点（Tier3）
    """

    TIER_CHOICES = [
        (1, "Tier1·全局铁律"),
        (2, "Tier2·品类规范"),
        (3, "Tier3·节点流程"),
        (4, "Tier4·合规熔断"),
    ]
    SCOPE_GLOBAL = "global"
    SCOPE_GENRE  = "genre"
    SCOPE_NODE   = "node"
    SCOPE_CHOICES = [
        (SCOPE_GLOBAL, "全局"),
        (SCOPE_GENRE,  "题材"),
        (SCOPE_NODE,   "节点"),
    ]
    STATUS_ACTIVE   = "active"
    STATUS_DRAFT    = "draft"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_ACTIVE,   "已生效"),
        (STATUS_DRAFT,    "草稿（待审核）"),
        (STATUS_ARCHIVED, "已归档"),
    ]
    SOURCE_FILE   = "file_import"
    SOURCE_ADMIN  = "admin"
    SOURCE_EVOLVE = "evolve_audit"
    SOURCE_CHOICES = [
        (SOURCE_FILE,   "JSON文件导入"),
        (SOURCE_ADMIN,  "后台手动录入"),
        (SOURCE_EVOLVE, "进化审计提案"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 规则定位（tier + scope 三元组唯一定位一批规则）
    tier = models.PositiveSmallIntegerField("层级", choices=TIER_CHOICES, db_index=True)
    scope_type = models.CharField(
        "范围类型", max_length=16, choices=SCOPE_CHOICES, default=SCOPE_GLOBAL, db_index=True
    )
    scope_key = models.CharField(
        "范围键",
        max_length=128,
        blank=True,
        default="",
        db_index=True,
        help_text="题材代码（如 family-revenge）或节点 ID（如 node-5-script），全局时留空",
    )
    section = models.CharField(
        "规则分区",
        max_length=64,
        db_index=True,
        help_text="规则在 JSON 中的 section 名，如 requirements / rhythm_rules / quantitative_constraints",
    )

    # 规则内容
    content = models.JSONField(
        "规则内容",
        help_text="该 section 的完整规则数据（结构对齐 tier JSON 文件中的对应字段）",
    )

    # 版本与状态
    version_tag = models.CharField(
        "版本标签", max_length=32, default="v5.0.0", db_index=True,
        help_text="如 v5.0.0 / v5.1.0，每次批准新提案时递增"
    )
    status = models.CharField(
        "状态", max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True
    )
    source = models.CharField(
        "来源", max_length=16, choices=SOURCE_CHOICES, default=SOURCE_ADMIN, db_index=True
    )

    # 审核信息
    note = models.TextField("备注/修改说明", blank=True, default="")
    approved_by = models.CharField("审核人", max_length=128, blank=True, default="")
    approved_at = models.DateTimeField("审核时间", null=True, blank=True)

    # 进化审计关联（evolve_audit 生成的 draft 可追踪到哪些生成项目触发了此提案）
    trigger_project_ids = models.JSONField(
        "触发项目 ID 列表",
        default=list,
        blank=True,
        help_text="触发本条规则修改提案的项目 ID（来自 evolve_audit）",
    )
    trigger_score_avg = models.FloatField(
        "触发时平均分", null=True, blank=True,
        help_text="触发低分追溯时的平均得分，用于评估修改效果"
    )

    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "技能规则配置"
        verbose_name_plural = verbose_name
        db_table = "skill_rule_config"
        ordering = ["tier", "scope_type", "scope_key", "section", "-created_at"]
        indexes = [
            models.Index(
                fields=["tier", "scope_type", "scope_key", "section", "status"],
                name="skill_rule_main_idx",
            ),
            models.Index(
                fields=["status", "-updated_at"],
                name="skill_rule_status_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"[Tier{self.tier}·{self.get_scope_type_display()}]"
            f" {self.scope_key or 'global'}/{self.section}"
            f" {self.version_tag} ({self.get_status_display()})"
        )

    def approve(self, approved_by: str = "admin") -> None:
        """
        批准此条草稿规则：将其状态变为 active，
        同时将同一 (tier, scope_type, scope_key, section) 下其他 active 记录归档。
        """
        from django.db import transaction
        from django.utils import timezone as tz

        with transaction.atomic():
            SkillRuleConfig.objects.filter(
                tier=self.tier,
                scope_type=self.scope_type,
                scope_key=self.scope_key,
                section=self.section,
                status=self.STATUS_ACTIVE,
            ).update(status=self.STATUS_ARCHIVED)

            self.status = self.STATUS_ACTIVE
            self.approved_by = approved_by
            self.approved_at = tz.now()
            self.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])


# ============================================================
# AgentSkillDefinition：Agent 技能定义（DB-backed SSOT）
# ============================================================
class AgentSkillDefinition(models.Model):
    """Agent 技能定义表

    将原来散落在各 SKILL.md 文件中的技能内容迁移到数据库，
    实现统一管理入口；Cursor Agent 通过 /api/skills/<skill_id>/definition/
    获取最新版本，不再依赖本地文件。

    category 分类：
    - creator     : 创作类技能
    - quality     : 质检类技能
    - compliance  : 合规类技能
    - shared      : 通用共享技能
    """

    CATEGORY_CREATOR    = "creator"
    CATEGORY_QUALITY    = "quality"
    CATEGORY_COMPLIANCE = "compliance"
    CATEGORY_SHARED     = "shared"

    CATEGORY_CHOICES = [
        (CATEGORY_CREATOR,    "创作类"),
        (CATEGORY_QUALITY,    "质检类"),
        (CATEGORY_COMPLIANCE, "合规类"),
        (CATEGORY_SHARED,     "通用共享"),
    ]

    skill_id    = models.CharField("技能 ID", max_length=100, unique=True, db_index=True,
                                   help_text='如 drama-master-suite / drama-creator-core')
    name        = models.CharField("技能名称", max_length=200)
    version     = models.CharField("版本号", max_length=20, default="1.0.0")
    category    = models.CharField("分类", max_length=50, choices=CATEGORY_CHOICES,
                                   default=CATEGORY_CREATOR, db_index=True)
    content     = models.TextField("技能内容（Markdown）",
                                   help_text="原始 SKILL.md 的完整 Markdown 内容")
    is_active   = models.BooleanField("是否启用", default=True, db_index=True)
    source_file = models.CharField("来源文件路径", max_length=300, blank=True,
                                   help_text="迁移前的本地相对路径，如 ai-drama-skills-v2/drama-creator-core/SKILL.md")
    created_at  = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at  = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "skill_agent_definition"
        verbose_name = "Agent 技能定义"
        verbose_name_plural = verbose_name
        ordering = ["category", "skill_id"]

    def __str__(self) -> str:
        return f"[{self.get_category_display()}] {self.skill_id} v{self.version}"


# ============================================================
# SkillConfigEntry：技能配置入库（阈值/QDN/市场规则等）
# ============================================================
class SkillConfigEntry(models.Model):
    """技能配置项

    对应 skill-thresholds.json、qdn-emotion-engine.json 等配置文件，
    迁移到 DB 后通过 /api/configs/<config_key>/ 下发给 Cursor Agent。
    """

    config_key = models.CharField("配置键", max_length=100, unique=True, db_index=True,
                                   help_text='如 skill-thresholds / qdn-emotion-engine')
    edition    = models.CharField("版本/版型", max_length=20, default="unified",
                                   help_text='如 unified / demo4book / ai-drama-skills-v2')
    content    = models.JSONField("配置内容")
    version    = models.CharField("版本号", max_length=20, default="1.0.0")
    note       = models.TextField("备注", blank=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "skill_config_entry"
        verbose_name = "技能配置项"
        verbose_name_plural = verbose_name
        ordering = ["config_key"]

    def __str__(self) -> str:
        return f"{self.config_key} ({self.edition}) v{self.version}"


# ============================================================
# SkillDefect：技能缺陷追踪
# ============================================================
class SkillDefect(models.Model):
    """技能缺陷 / Bug 追踪

    记录 Agent 技能执行过程中发现的问题，与 AgentSkillDefinition 关联。
    """

    SEVERITY_P0 = "P0"
    SEVERITY_P1 = "P1"
    SEVERITY_P2 = "P2"
    SEVERITY_P3 = "P3"

    SEVERITY_CHOICES = [
        (SEVERITY_P0, "P0-阻断"),
        (SEVERITY_P1, "P1-严重"),
        (SEVERITY_P2, "P2-一般"),
        (SEVERITY_P3, "P3-改进"),
    ]

    STATUS_OPEN        = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_RESOLVED    = "resolved"
    STATUS_CLOSED      = "closed"

    STATUS_CHOICES = [
        (STATUS_OPEN,        "待处理"),
        (STATUS_IN_PROGRESS, "处理中"),
        (STATUS_RESOLVED,    "已解决"),
        (STATUS_CLOSED,      "关闭"),
    ]

    skill           = models.ForeignKey(
        AgentSkillDefinition, on_delete=models.CASCADE,
        related_name="defects", verbose_name="所属技能",
    )
    title           = models.CharField("标题", max_length=200)
    description     = models.TextField("问题描述")
    severity        = models.CharField("严重级别", max_length=5,
                                       choices=SEVERITY_CHOICES, default=SEVERITY_P2, db_index=True)
    status          = models.CharField("状态", max_length=20,
                                       choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True)
    reproduce_steps = models.TextField("复现步骤", blank=True)
    fix_notes       = models.TextField("修复说明", blank=True)
    reported_by     = models.CharField("报告人", max_length=100, blank=True)
    resolved_at     = models.DateTimeField("解决时间", null=True, blank=True)
    created_at      = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at      = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "skill_defect"
        verbose_name = "技能缺陷"
        verbose_name_plural = verbose_name
        ordering = ["severity", "-created_at"]
        indexes = [
            models.Index(fields=["skill", "status"], name="skill_defect_skill_status_idx"),
            models.Index(fields=["severity", "status"], name="skill_defect_severity_idx"),
        ]

    def __str__(self) -> str:
        return f"[{self.severity}] {self.title} ({self.get_status_display()})"
