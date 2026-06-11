# -*- coding: utf-8 -*-
"""
技能配置模块 - 技能引擎与配置管理

核心组件：
- SkillConfigService: 技能配置的读取与更新（统一 AES-256-CBC，通过 models 层方法）
- ThemeTemplateService: 题材模板管理（纯数据库读写）
- HookLibraryService: 钩子库服务（纯数据库读写）

安全设计：
- 所有敏感配置值统一使用 models.encrypt_text / decrypt_text (AES-256-CBC)
- 通过 SkillConfig 对象的 set_encrypted_value / get_decrypted_value 读写
- 仅超级管理员可访问配置管理
- 配置首次访问时自动写入数据库（含默认值）
"""
import json
import logging
import random
from typing import Dict, Any, List, Optional

from django.conf import settings
from django.core.cache import cache

from apps.skill.models import SkillConfig, ThemeTemplate, HookLibrary

logger = logging.getLogger(__name__)


# ============================================================
# 技能配置服务
# ============================================================

class SkillConfigService:
    """技能配置读取与更新服务（带缓存）

    加密方式：统一通过 SkillConfig 对象的 set_encrypted_value / get_decrypted_value
    （底层为 apps.skill.models.encrypt_text / decrypt_text，AES-256-CBC）
    """

    CACHE_KEY_PREFIX = 'skill:config:'
    CACHE_TTL = 3600  # 1小时

    # 默认配置（首次部署 / 首次访问时写入数据库）
    # 所有值以字符串形式存储（写入时自动加密，读取时自动解密）
    DEFAULT_CONFIGS: Dict[str, Dict[str, str]] = {
        # --- LLM 大模型 ---
        'llm.api_key': {
            'value': '',
            'description': '大语言模型 API Key（加密存储）',
        },
        'llm.base_url': {
            'value': '',
            'description': '大语言模型 API Base URL',
        },
        'llm.model_name': {
            'value': 'gpt-4o-mini',
            'description': '大语言模型名称',
        },
        'llm.temperature': {
            'value': '0.7',
            'description': '采样温度 (0-2)',
        },
        'llm.max_tokens': {
            'value': '4096',
            'description': '单次生成最大 token 数',
        },
        'llm.enabled': {
            'value': 'false',
            'description': '是否启用大语言模型（true/false）',
        },
        # --- 技能版本 ---
        'skill.version': {
            'value': '3.5.0',
            'description': '技能引擎版本号',
        },
        # --- 导出 ---
        'export.default_format': {
            'value': 'B',
            'description': '默认导出格式（A/B/C/D）',
        },
        'export.enable_watermark': {
            'value': 'true',
            'description': '是否启用水印（true/false）',
        },
        # --- 质量审查 ---
        'review.pass_threshold': {
            'value': '70',
            'description': '剧本审查通过分数阈值（0-100）',
        },
    }

    # 判断敏感配置的关键字（列表接口脱敏使用）
    SENSITIVE_KEY_HINTS = ['api_key', 'secret', 'password', 'token']

    # --------------------------------------------------------
    # 私有工具
    # --------------------------------------------------------
    @classmethod
    def _cache_key(cls, key: str) -> str:
        return cls.CACHE_KEY_PREFIX + key

    @classmethod
    def _get_default_value(cls, key: str, default: Any = None) -> str:
        entry = cls.DEFAULT_CONFIGS.get(key)
        if entry is not None:
            return entry.get('value', '')
        return default if default is not None else ''

    @classmethod
    def _get_default_description(cls, key: str) -> str:
        entry = cls.DEFAULT_CONFIGS.get(key)
        return entry.get('description', key) if entry else key

    @classmethod
    def _is_sensitive(cls, key: str) -> bool:
        k = key.lower()
        return any(h in k for h in cls.SENSITIVE_KEY_HINTS)

    @classmethod
    def _ensure_in_db(cls, key: str) -> Optional[SkillConfig]:
        """确保配置在数据库中存在。如不存在，使用默认值写入。

        返回 SkillConfig 对象（若 key 不在 DEFAULT_CONFIGS 也无 DB 记录则返回 None）
        """
        obj = SkillConfig.objects.filter(config_key=key).first()
        if obj is not None:
            return obj
        if key not in cls.DEFAULT_CONFIGS:
            return None
        default_val = cls._get_default_value(key)
        description = cls._get_default_description(key)
        obj = SkillConfig(config_key=key, description=description)
        obj.set_encrypted_value(default_val)
        try:
            obj.save()
        except Exception:
            # 并发情况下可能已存在，尝试再次读取
            obj = SkillConfig.objects.filter(config_key=key).first()
        return obj

    # --------------------------------------------------------
    # 公共读取 API
    # --------------------------------------------------------
    @classmethod
    def get(cls, key: str, default: Any = None) -> str:
        """读取单个配置项（字符串形式）"""
        cache_key = cls._cache_key(key)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        obj = cls._ensure_in_db(key)
        if obj is None:
            val = default if default is not None else ''
        else:
            try:
                val = obj.get_decrypted_value()
            except Exception as exc:  # noqa: BLE001
                logger.warning('配置 %s 解密失败，使用默认值: %s', key, exc)
                val = cls._get_default_value(key, default)

        if val is None:
            val = ''

        cache.set(cache_key, val, cls.CACHE_TTL)
        return val

    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        try:
            return int(cls.get(key, str(default)))
        except (ValueError, TypeError):
            return default

    @classmethod
    def get_float(cls, key: str, default: float = 0.0) -> float:
        try:
            return float(cls.get(key, str(default)))
        except (ValueError, TypeError):
            return default

    @classmethod
    def get_json(cls, key: str, default: Any = None) -> Any:
        raw = cls.get(key, '')
        if not raw:
            return default if default is not None else {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return default if default is not None else {}

    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        return cls.get(key, str(default)).lower() in ('true', '1', 'yes', 'on')

    # --------------------------------------------------------
    # 公共写入 API
    # --------------------------------------------------------
    @classmethod
    def set(cls, key: str, value: str, description: str = '') -> Optional[SkillConfig]:
        """设置单个配置项（自动加密存储）"""
        value_str = '' if value is None else str(value)
        desc = description or cls._get_default_description(key)

        try:
            obj, _created = SkillConfig.objects.update_or_create(
                config_key=key,
                defaults={'description': desc},
            )
        except Exception as exc:  # noqa: BLE001
            logger.error('写入配置失败 key=%s: %s', key, exc)
            return None

        obj.set_encrypted_value(value_str)
        obj.save()

        cache.delete(cls._cache_key(key))
        return obj

    # --------------------------------------------------------
    # 列表/初始化
    # --------------------------------------------------------
    @classmethod
    def all_configs(cls, mask_sensitive: bool = True) -> List[Dict[str, Any]]:
        """返回所有配置（含默认值）

        返回结构：
            [
                {
                    'key': 'llm.api_key',
                    'value': '...（若 mask_sensitive=True 且为敏感项则为空字符串）',
                    'description': '...',
                    'encrypted': True,  # 是否敏感
                    'is_default': False,  # 是否仍使用默认值（未被用户覆盖）
                },
                ...
            ]
        """
        # 1) 先把所有已知 key 的默认记录补齐
        for k in cls.DEFAULT_CONFIGS:
            cls._ensure_in_db(k)

        db_items: Dict[str, SkillConfig] = {sc.config_key: sc for sc in SkillConfig.objects.all()}

        result = []
        all_keys = set(db_items.keys()) | set(cls.DEFAULT_CONFIGS.keys())
        for key in sorted(all_keys):
            obj = db_items.get(key)
            plain = obj.get_decrypted_value() if obj is not None else None
            default_val = cls._get_default_value(key)

            if obj is None or plain is None or plain == '':
                used_value = default_val
                is_default = True
            else:
                used_value = plain
                # 与默认值相同视为仍为默认
                is_default = used_value == default_val

            description = obj.description if (obj and obj.description) else cls._get_default_description(key)
            is_sensitive = cls._is_sensitive(key)

            result.append({
                'key': key,
                'value': '' if (mask_sensitive and is_sensitive) else used_value,
                'description': description,
                'encrypted': is_sensitive,
                'is_default': is_default,
            })

        return result

    @classmethod
    def init_default_configs(cls) -> None:
        """初始化默认配置（首次部署时调用）

        仅当 key 在数据库中不存在时写入默认值。
        """
        for key, entry in cls.DEFAULT_CONFIGS.items():
            if SkillConfig.objects.filter(config_key=key).exists():
                continue
            try:
                obj = SkillConfig(
                    config_key=key,
                    description=entry.get('description', key),
                )
                obj.set_encrypted_value(entry.get('value', ''))
                obj.save()
            except Exception as exc:  # noqa: BLE001
                logger.warning('初始化配置 %s 失败: %s', key, exc)


# ============================================================
# 题材模板服务
# ============================================================

class ThemeTemplateService:
    """题材模板服务（纯数据库读写）

    内置 8 大题材默认数据，通过 management/commands/init_skill_data.py
    在首次启动时写入 ThemeTemplate 表。
    """

    BUILTIN_THEMES: List[Dict[str, Any]] = [
        {
            'theme_code': 'family-revenge',
            'theme_name': '家庭伦理复仇',
            'is_active': True,
            'sort_order': 10,
            'params': {
                'description': '隐忍女主被家庭/婆家欺压，觉醒后反击夺回一切',
                'act_ratio': [0.10, 0.18, 0.22, 0.22, 0.18, 0.10],
                'reversal_density': 0.35,
                'emotion_curve': [3, 2, 1, 4, 7, 8, 9, 10],
                'hook_types': ['隐忍爆发', '身份反转', '真相揭露', '情感打脸'],
            },
            'hook_templates': [],
            'character_archetypes': [],
        },
        {
            'theme_code': 'domineering-ceo',
            'theme_name': '豪门霸总',
            'is_active': True,
            'sort_order': 20,
            'params': {
                'description': '隐藏身份继承人在势利反派中崛起，收割真爱与商业帝国',
                'act_ratio': [0.10, 0.20, 0.25, 0.20, 0.15, 0.10],
                'reversal_density': 0.40,
                'emotion_curve': [4, 3, 5, 6, 8, 7, 9, 10],
                'hook_types': ['隐藏身份', '商战反转', '英雄救美', '豪门对峙'],
            },
            'hook_templates': [],
            'character_archetypes': [],
        },
        {
            'theme_code': 'sweet-pet',
            'theme_name': '甜宠虐恋',
            'is_active': True,
            'sort_order': 30,
            'params': {
                'description': '傲娇男主+元气女主，甜虐交替，感情升温',
                'act_ratio': [0.15, 0.25, 0.25, 0.15, 0.10, 0.10],
                'reversal_density': 0.25,
                'emotion_curve': [5, 4, 6, 5, 7, 8, 9, 10],
                'hook_types': ['误会解开', '吃醋反转', '告白时刻', '甜蜜暴击'],
            },
            'hook_templates': [],
            'character_archetypes': [],
        },
        {
            'theme_code': 'time-travel',
            'theme_name': '穿越重生',
            'is_active': True,
            'sort_order': 40,
            'params': {
                'description': '重生者利用未来信息反击，改写命运',
                'act_ratio': [0.10, 0.15, 0.25, 0.25, 0.15, 0.10],
                'reversal_density': 0.45,
                'emotion_curve': [3, 5, 4, 7, 8, 6, 9, 10],
                'hook_types': ['先知先觉', '改变历史', '时空悖论', '命运重逢'],
            },
            'hook_templates': [],
            'character_archetypes': [],
        },
        {
            'theme_code': 'urban-counterattack',
            'theme_name': '都市逆袭',
            'is_active': True,
            'sort_order': 50,
            'params': {
                'description': '小人物在压力下崛起，职场与人生双丰收',
                'act_ratio': [0.10, 0.20, 0.25, 0.20, 0.15, 0.10],
                'reversal_density': 0.30,
                'emotion_curve': [2, 3, 4, 6, 7, 8, 9, 10],
                'hook_types': ['职场反转', '贵人相助', '技能觉醒', '对手溃败'],
            },
            'hook_templates': [],
            'character_archetypes': [],
        },
        {
            'theme_code': 'ancient-power',
            'theme_name': '古装权谋',
            'is_active': True,
            'sort_order': 60,
            'params': {
                'description': '权力斗争中的成长与反击，江山与美人兼得',
                'act_ratio': [0.10, 0.15, 0.25, 0.20, 0.20, 0.10],
                'reversal_density': 0.50,
                'emotion_curve': [3, 2, 5, 4, 7, 6, 9, 10],
                'hook_types': ['宫廷政变', '身份揭秘', '权谋反转', '帝王之心'],
            },
            'hook_templates': [],
            'character_archetypes': [],
        },
        {
            'theme_code': 'mystery-reversal',
            'theme_name': '悬疑反转',
            'is_active': True,
            'sort_order': 70,
            'params': {
                'description': '隐藏真相层层揭露，多重反转挑战认知',
                'act_ratio': [0.10, 0.20, 0.20, 0.25, 0.15, 0.10],
                'reversal_density': 0.60,
                'emotion_curve': [5, 6, 5, 7, 6, 8, 9, 10],
                'hook_types': ['真相揭露', '凶手反转', '时间错位', '双重人格'],
            },
            'hook_templates': [],
            'character_archetypes': [],
        },
        {
            'theme_code': 'hybrid',
            'theme_name': '混合题材定制',
            'is_active': True,
            'sort_order': 80,
            'params': {
                'description': '自定义混合题材，根据创意灵活调整',
                'act_ratio': [0.10, 0.20, 0.20, 0.20, 0.15, 0.15],
                'reversal_density': 0.35,
                'emotion_curve': [4, 4, 5, 6, 7, 8, 9, 10],
                'hook_types': ['定制钩子1', '定制钩子2', '定制钩子3'],
            },
            'hook_templates': [],
            'character_archetypes': [],
        },
    ]

    # --------------------------------------------------------
    # 查询
    # --------------------------------------------------------
    @classmethod
    def get_theme(cls, theme_code: str) -> Optional[Dict[str, Any]]:
        """按 theme_code 获取题材（包含完整结构）"""
        obj = ThemeTemplate.objects.filter(theme_code=theme_code, is_active=True).first()
        if obj is None:
            return None
        return cls._to_dict(obj)

    @classmethod
    def list_themes(cls, only_active: bool = True) -> List[Dict[str, Any]]:
        """列出题材（按 sort_order 排序，is_active=True 在前）"""
        qs = ThemeTemplate.objects.all()
        if only_active:
            qs = qs.filter(is_active=True)
        qs = qs.order_by('sort_order', '-created_at')
        return [cls._to_dict(obj) for obj in qs]

    # --------------------------------------------------------
    # 写入
    # --------------------------------------------------------
    @classmethod
    def create_or_update(cls, theme_data: Dict[str, Any]) -> ThemeTemplate:
        """创建或更新题材（以 theme_code 为唯一键）

        可接受字段：theme_code, theme_name, is_active, sort_order,
                     params, hook_templates, character_archetypes
        """
        code = theme_data.get('theme_code')
        if not code:
            raise ValueError('theme_code 是必填项')

        obj, _created = ThemeTemplate.objects.update_or_create(
            theme_code=code,
            defaults={
                'theme_name': theme_data.get('theme_name', code),
                'is_active': bool(theme_data.get('is_active', True)),
                'sort_order': int(theme_data.get('sort_order', 0)),
                'params': theme_data.get('params', {}) or {},
                'hook_templates': theme_data.get('hook_templates', []) or [],
                'character_archetypes': theme_data.get('character_archetypes', []) or [],
            },
        )
        return obj

    @classmethod
    def update_by_id(cls, theme_id, update_data: Dict[str, Any]) -> Optional[ThemeTemplate]:
        """按主键 ID 更新题材"""
        try:
            obj = ThemeTemplate.objects.get(pk=theme_id)
        except ThemeTemplate.DoesNotExist:
            return None
        for field in ('theme_code', 'theme_name', 'is_active', 'sort_order',
                      'params', 'hook_templates', 'character_archetypes'):
            if field in update_data and update_data[field] is not None:
                setattr(obj, field, update_data[field])
        obj.save()
        return obj

    # --------------------------------------------------------
    # 初始化
    # --------------------------------------------------------
    @classmethod
    def init_default_themes(cls) -> None:
        """将 BUILTIN_THEMES 写入数据库（仅当 theme_code 不存在时）"""
        for theme_data in cls.BUILTIN_THEMES:
            if ThemeTemplate.objects.filter(theme_code=theme_data['theme_code']).exists():
                continue
            try:
                ThemeTemplate.objects.create(
                    theme_code=theme_data['theme_code'],
                    theme_name=theme_data['theme_name'],
                    is_active=theme_data.get('is_active', True),
                    sort_order=theme_data.get('sort_order', 0),
                    params=theme_data.get('params', {}) or {},
                    hook_templates=theme_data.get('hook_templates', []) or [],
                    character_archetypes=theme_data.get('character_archetypes', []) or [],
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning('初始化题材 %s 失败: %s', theme_data['theme_code'], exc)

    # --------------------------------------------------------
    # 工具
    # --------------------------------------------------------
    @classmethod
    def _to_dict(cls, obj: ThemeTemplate) -> Dict[str, Any]:
        params = obj.params or {}
        # params 内的 description 作为题材的整体描述
        description = params.get('description', '') if isinstance(params, dict) else ''
        return {
            'id': str(obj.id),
            'theme_code': obj.theme_code,
            'theme_name': obj.theme_name,
            'description': description,
            'is_active': obj.is_active,
            'sort_order': obj.sort_order,
            'params': params,
            'hook_templates': obj.hook_templates or [],
            'character_archetypes': obj.character_archetypes or [],
            'created_at': obj.created_at.isoformat() if obj.created_at else None,
            'updated_at': obj.updated_at.isoformat() if obj.updated_at else None,
        }


# ============================================================
# 钩子库服务
# ============================================================

class HookLibraryService:
    """钩子库服务（纯数据库读写）

    内置钩子数据通过 init_default_hooks() 在首次启动时写入。
    """

    BUILTIN_HOOKS: List[Dict[str, Any]] = [
        # 开场钩子
        {'hook_type': 'opening', 'content': '她隐忍三年，今天终于拿到了丈夫出轨的铁证。', 'tags': '家庭,复仇'},
        {'hook_type': 'opening', 'content': '电梯里，他与未来老总的女儿相撞，却不知道这将改变他的一生。', 'tags': '豪门,命运'},
        {'hook_type': 'opening', 'content': '婚礼当天，新娘在化妆间发现了未婚夫手机里的惊天秘密。', 'tags': '婚礼,反转'},
        {'hook_type': 'opening', 'content': '当她醒来，发现自己重生在了十年前。', 'tags': '重生,穿越'},
        {'hook_type': 'opening', 'content': '他被陷害入狱三年，出来后却发现世界已经变了。', 'tags': '逆袭,复仇'},

        # 反转钩子
        {'hook_type': 'reversal', 'content': '原来一直欺压她的婆婆，竟是她失散多年的亲生母亲。', 'tags': '身份,反转'},
        {'hook_type': 'reversal', 'content': '公司新来的实习生，竟然是隐藏身份的集团继承人。', 'tags': '隐藏身份,商战'},
        {'hook_type': 'reversal', 'content': '他以为自己赢了一切，却发现这都是对手设计的陷阱。', 'tags': '阴谋,反转'},
        {'hook_type': 'reversal', 'content': '原来她一直深爱的人，竟是害死她全家的凶手。', 'tags': '情感,复仇'},
        {'hook_type': 'reversal', 'content': '当他揭露真相时，所有人都震惊了。', 'tags': '真相,揭露'},

        # 悬念钩子
        {'hook_type': 'suspense', 'content': '她收到一封没有寄件人的信，里面写着她明天会做的三件事。', 'tags': '预言,悬疑'},
        {'hook_type': 'suspense', 'content': '午夜十二点，电梯突然停在从未有过的第十三层。', 'tags': '悬疑,惊悚'},
        {'hook_type': 'suspense', 'content': '他打开家门，发现另一个自己正坐在客厅等他。', 'tags': '双重人格,悬疑'},
        {'hook_type': 'suspense', 'content': '这封信，到底是谁寄来的？', 'tags': '悬念,未知'},
        {'hook_type': 'suspense', 'content': '她总觉得有人在暗中跟踪她...', 'tags': '跟踪,悬疑'},

        # 金句钩子
        {'hook_type': 'golden', 'content': '你以为的岁月静好，不过是有人替你负重前行。', 'tags': '金句,感悟'},
        {'hook_type': 'golden', 'content': '有些真相，不如永远不知道。', 'tags': '金句,真相'},
        {'hook_type': 'golden', 'content': '命运赠送的礼物，早已在暗中标好了价格。', 'tags': '金句,命运'},
        {'hook_type': 'golden', 'content': '我不是变了，而是终于认清了你。', 'tags': '金句,情感'},
        {'hook_type': 'golden', 'content': '有些路，只能一个人走。', 'tags': '金句,成长'},
    ]

    # --------------------------------------------------------
    # 查询
    # --------------------------------------------------------
    @classmethod
    def list_hooks(cls, hook_type: Optional[str] = None, only_active: bool = True) -> List[Dict[str, Any]]:
        qs = HookLibrary.objects.all()
        if only_active:
            qs = qs.filter(is_active=True)
        if hook_type:
            qs = qs.filter(hook_type=hook_type)
        qs = qs.order_by('-use_count', '-created_at')
        return [cls._to_dict(obj) for obj in qs]

    @classmethod
    def get_random_hook(cls, hook_type: Optional[str] = None, count: int = 1) -> List[str]:
        """随机获取钩子内容"""
        qs = HookLibrary.objects.filter(is_active=True)
        if hook_type:
            qs = qs.filter(hook_type=hook_type)
        hooks = list(qs.values_list('content', flat=True))
        if not hooks:
            return []
        random.shuffle(hooks)
        return hooks[:count]

    @classmethod
    def count(cls, only_active: bool = True) -> int:
        qs = HookLibrary.objects.all()
        if only_active:
            qs = qs.filter(is_active=True)
        return qs.count()

    # --------------------------------------------------------
    # 写入
    # --------------------------------------------------------
    @classmethod
    def create(cls, hook_type: str, content: str, tags: str = '', is_active: bool = True) -> HookLibrary:
        return HookLibrary.objects.create(
            hook_type=hook_type,
            content=content,
            tags=tags,
            is_active=is_active,
        )

    @classmethod
    def increment_use_count(cls, hook_id) -> None:
        HookLibrary.objects.filter(pk=hook_id).update(use_count=models_F() + 1)

    # --------------------------------------------------------
    # 初始化
    # --------------------------------------------------------
    @classmethod
    def init_default_hooks(cls) -> None:
        """将 BUILTIN_HOOKS 写入数据库（去重依据 hook_type + content）"""
        for item in cls.BUILTIN_HOOKS:
            if HookLibrary.objects.filter(
                hook_type=item['hook_type'],
                content=item['content'],
            ).exists():
                continue
            try:
                HookLibrary.objects.create(
                    hook_type=item['hook_type'],
                    content=item['content'],
                    tags=item.get('tags', ''),
                    is_active=item.get('is_active', True),
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning('初始化钩子失败: %s', exc)

    # --------------------------------------------------------
    # 工具
    # --------------------------------------------------------
    @classmethod
    def _to_dict(cls, obj: HookLibrary) -> Dict[str, Any]:
        return {
            'id': str(obj.id),
            'hook_type': obj.hook_type,
            'hook_type_label': obj.get_hook_type_display(),
            'content': obj.content,
            'tags': obj.tags or '',
            'tag_list': obj.get_tag_list(),
            'is_active': obj.is_active,
            'use_count': obj.use_count,
            'created_at': obj.created_at.isoformat() if obj.created_at else None,
        }


# 延迟导入避免循环依赖（仅在 increment_use_count 中使用）
from django.db.models import F as models_F  # noqa: E402


# ============================================================
# 初始化函数（首次部署 / 命令调用）
# ============================================================

def init_skill_data():
    """初始化技能数据（默认配置、题材模板、钩子库）"""
    SkillConfigService.init_default_configs()
    ThemeTemplateService.init_default_themes()
    HookLibraryService.init_default_hooks()
    logger.info('技能数据初始化完成')
