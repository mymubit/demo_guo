# -*- coding: utf-8 -*-
"""
技能配置模块 - 技能引擎与配置管理

核心组件：
- SkillConfigService: 技能配置的读取与更新（AES-256加密）
- ThemeTemplateService: 题材模板管理
- HookLibraryService: 钩子库服务
- ScriptGenerator: 剧本生成器（基于模板）

安全设计：
- 所有敏感配置值使用 AES-256-CBC 加密存储
- LLM API Key 等核心密钥仅在内存解密使用
- 仅超级管理员可访问配置管理
"""
import json
import os
import random
import hashlib
from typing import Dict, Any, List, Optional

from django.conf import settings
from django.core.cache import cache
from django.db.models import F
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

from apps.skill.models import SkillConfig, ThemeTemplate, HookLibrary, DialogueTemplate


# ============================================================
# 加密工具
# ============================================================

def _aes_encrypt(plain_text: str, key_str: str = None) -> str:
    """AES-256-CBC 加密，返回 'ENC:' + base64(iv+ciphertext)"""
    key_str = key_str or getattr(settings, 'SKILL_ENCRYPT_KEY', 'default-key-change-me-32bytes!')
    key = hashlib.sha256(key_str.encode('utf-8')).digest()  # 32字节
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct_bytes = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))
    return 'ENC:' + base64.b64encode(iv + ct_bytes).decode('utf-8')


def _aes_decrypt(value: str, key_str: str = None) -> str:
    """解密 'ENC:' 前缀的值"""
    if not value.startswith('ENC:'):
        return value  # 明文直接返回（兼容老数据）
    key_str = key_str or getattr(settings, 'SKILL_ENCRYPT_KEY', 'default-key-change-me-32bytes!')
    key = hashlib.sha256(key_str.encode('utf-8')).digest()
    try:
        raw = base64.b64decode(value[4:].encode('utf-8'))
        iv = raw[:16]
        ct = raw[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), AES.block_size).decode('utf-8')
    except Exception:
        return ''


# ============================================================
# 技能配置服务
# ============================================================

class SkillConfigService:
    """技能配置读取与更新服务（带缓存）"""

    CACHE_KEY_PREFIX = 'skill:config:'
    CACHE_TTL = 3600  # 1小时

    DEFAULT_CONFIGS = {
        # LLM 配置
        'llm.api_endpoint': '',
        'llm.api_key': '',
        'llm.temperature': '0.7',
        'llm.max_tokens': '4096',
        'llm.model': 'gpt-4o-mini',
        'llm.enabled': 'false',
        # 技能版本
        'skill.version': '3.5.0',
        'skill.active_nodes': '[1,2,3,4,5,6,7]',
        # 质量审查规则
        'review.format_score_weight': '20',
        'review.rhythm_score_weight': '40',
        'review.content_score_weight': '20',
        'review.production_score_weight': '20',
        'review.pass_threshold': '70',
        # 输出格式
        'export.default_format': 'B',
        'export.enable_watermark': 'true',
        # 合规
        'compliance.sensitive_words': '["色情","暴力","政治敏感","赌博","毒品"]',
    }

    @classmethod
    def get(cls, key: str, default: Any = None) -> str:
        """读取单个配置项"""
        cache_key = cls.CACHE_KEY_PREFIX + key
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            obj = SkillConfig.objects.filter(config_key=key).first()
            val = _aes_decrypt(obj.config_value_encrypted) if obj else None
            if val is None:
                val = cls.DEFAULT_CONFIGS.get(key, default if default is not None else '')
        except Exception:
            val = cls.DEFAULT_CONFIGS.get(key, default if default is not None else '')

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
            return default or {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return default or {}

    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        return cls.get(key, str(default)).lower() in ('true', '1', 'yes', 'on')

    @classmethod
    def set(cls, key: str, value: str, description: str = '') -> SkillConfig:
        """设置单个配置项（自动加密存储）"""
        encrypted = _aes_encrypt(str(value))
        obj, created = SkillConfig.objects.update_or_create(
            config_key=key,
            defaults={'config_value_encrypted': encrypted, 'description': description or key},
        )
        cache.delete(cls.CACHE_KEY_PREFIX + key)
        return obj

    @classmethod
    def all_configs(cls) -> List[Dict[str, Any]]:
        """返回所有配置（含默认值）"""
        db_items = {}
        for sc in SkillConfig.objects.all():
            db_items[sc.config_key] = _aes_decrypt(sc.config_value_encrypted)

        result = []
        seen = set()
        all_keys = set(db_items.keys()) | set(cls.DEFAULT_CONFIGS.keys())

        for key in sorted(all_keys):
            if key in seen:
                continue
            seen.add(key)

            desc_obj = SkillConfig.objects.filter(config_key=key).first()
            desc = desc_obj.description if desc_obj else ''

            is_sensitive = any(k in key.lower() for k in ['api_key', 'secret', 'password', 'token', 'key'])

            result.append({
                'key': key,
                'value': db_items.get(key, cls.DEFAULT_CONFIGS.get(key, '')),
                'description': desc,
                'encrypted': is_sensitive,
                'is_default': key not in db_items,
            })

        return result

    @classmethod
    def init_default_configs(cls):
        """初始化默认配置（首次部署时调用）"""
        for key, default_val in cls.DEFAULT_CONFIGS.items():
            if not SkillConfig.objects.filter(config_key=key).exists():
                cls.set(key, default_val)


# ============================================================
# 题材模板服务
# ============================================================

class ThemeTemplateService:
    """题材模板服务"""

    # 内置默认题材配置
    BUILTIN_THEMES = [
        {
            'theme_code': 'family-revenge',
            'theme_name': '家庭伦理复仇',
            'description': '隐忍女主被家庭/婆家欺压，觉醒后反击夺回一切',
            'params': {
                'act_ratio': [0.10, 0.18, 0.22, 0.22, 0.18, 0.10],
                'reversal_density': 0.35,
                'emotion_curve': [3, 2, 1, 4, 7, 8, 9, 10],
                'hook_types': ['隐忍爆发', '身份反转', '真相揭露', '情感打脸'],
            },
        },
        {
            'theme_code': 'overbearing-ceo',
            'theme_name': '豪门霸总',
            'description': '隐藏身份继承人在势利反派中崛起，收割真爱与商业帝国',
            'params': {
                'act_ratio': [0.10, 0.20, 0.25, 0.20, 0.15, 0.10],
                'reversal_density': 0.40,
                'emotion_curve': [4, 3, 5, 6, 8, 7, 9, 10],
                'hook_types': ['隐藏身份', '商战反转', '英雄救美', '豪门对峙'],
            },
        },
        {
            'theme_code': 'sweet-pet',
            'theme_name': '甜宠虐恋',
            'description': '傲娇男主+元气女主，甜虐交替，感情升温',
            'params': {
                'act_ratio': [0.15, 0.25, 0.25, 0.15, 0.10, 0.10],
                'reversal_density': 0.25,
                'emotion_curve': [5, 4, 6, 5, 7, 8, 9, 10],
                'hook_types': ['误会解开', '吃醋反转', '告白时刻', '甜蜜暴击'],
            },
        },
        {
            'theme_code': 'time-travel',
            'theme_name': '穿越重生',
            'description': '重生者利用未来信息反击，改写命运',
            'params': {
                'act_ratio': [0.10, 0.15, 0.25, 0.25, 0.15, 0.10],
                'reversal_density': 0.45,
                'emotion_curve': [3, 5, 4, 7, 8, 6, 9, 10],
                'hook_types': ['先知先觉', '改变历史', '时空悖论', '命运重逢'],
            },
        },
        {
            'theme_code': 'urban-rebirth',
            'theme_name': '都市逆袭',
            'description': '小人物在压力下崛起，职场与人生双丰收',
            'params': {
                'act_ratio': [0.10, 0.20, 0.25, 0.20, 0.15, 0.10],
                'reversal_density': 0.30,
                'emotion_curve': [2, 3, 4, 6, 7, 8, 9, 10],
                'hook_types': ['职场反转', '贵人相助', '技能觉醒', '对手溃败'],
            },
        },
        {
            'theme_code': 'ancient-costume',
            'theme_name': '古装权谋',
            'description': '权力斗争中的成长与反击，江山与美人兼得',
            'params': {
                'act_ratio': [0.10, 0.15, 0.25, 0.20, 0.20, 0.10],
                'reversal_density': 0.50,
                'emotion_curve': [3, 2, 5, 4, 7, 6, 9, 10],
                'hook_types': ['宫廷政变', '身份揭秘', '权谋反转', '帝王之心'],
            },
        },
        {
            'theme_code': 'suspense-reversal',
            'theme_name': '悬疑反转',
            'description': '隐藏真相层层揭露，多重反转挑战认知',
            'params': {
                'act_ratio': [0.10, 0.20, 0.20, 0.25, 0.15, 0.10],
                'reversal_density': 0.60,
                'emotion_curve': [5, 6, 5, 7, 6, 8, 9, 10],
                'hook_types': ['真相揭露', '凶手反转', '时间错位', '双重人格'],
            },
        },
        {
            'theme_code': 'mixed-theme',
            'theme_name': '混合题材定制',
            'description': '自定义混合题材，根据创意灵活调整',
            'params': {
                'act_ratio': [0.10, 0.20, 0.20, 0.20, 0.15, 0.15],
                'reversal_density': 0.35,
                'emotion_curve': [4, 4, 5, 6, 7, 8, 9, 10],
                'hook_types': ['定制钩子1', '定制钩子2', '定制钩子3'],
            },
        },
    ]

    @classmethod
    def get_theme(cls, theme_code: str) -> Dict[str, Any]:
        """获取单个题材"""
        from_db = ThemeTemplate.objects.filter(theme_code=theme_code, is_active=True).first()
        if from_db:
            return {
                'theme_code': from_db.theme_code,
                'theme_name': from_db.theme_name,
                'description': from_db.description or '',
                'params': from_db.params or {},
                'hook_templates': from_db.hook_templates or [],
                'character_archetypes': from_db.character_archetypes or [],
            }
        for t in cls.BUILTIN_THEMES:
            if t['theme_code'] == theme_code:
                return t
        return cls.BUILTIN_THEMES[-1]

    @classmethod
    def list_themes(cls) -> List[Dict[str, Any]]:
        db_themes = {t.theme_code: t for t in ThemeTemplate.objects.filter(is_active=True)}
        result = []
        for builtin in cls.BUILTIN_THEMES:
            t = db_themes.get(builtin['theme_code'])
            if t:
                result.append({
                    'theme_code': t.theme_code,
                    'theme_name': t.theme_name,
                    'description': t.description or builtin.get('description', ''),
                    'params': t.params or builtin.get('params', {}),
                })
            else:
                result.append(builtin)
        return result

    @classmethod
    def init_default_themes(cls):
        """初始化默认题材模板"""
        for theme_data in cls.BUILTIN_THEMES:
            ThemeTemplate.objects.get_or_create(
                theme_code=theme_data['theme_code'],
                defaults={
                    'theme_name': theme_data['theme_name'],
                    'description': theme_data['description'],
                    'params': theme_data['params'],
                    'is_active': True,
                }
            )


# ============================================================
# 钩子库服务
# ============================================================

class HookLibraryService:
    """钩子库服务"""

    BUILTIN_HOOKS = [
        # 开场钩子
        ('opening', '她隐忍三年，今天终于拿到了丈夫出轨的铁证。'),
        ('opening', '电梯里，他与未来老总的女儿相撞，却不知道这将改变他的一生。'),
        ('opening', '婚礼当天，新娘在化妆间发现了未婚夫手机里的惊天秘密。'),
        ('opening', '当她醒来，发现自己重生在了十年前。'),
        ('opening', '他被陷害入狱三年，出来后却发现世界已经变了。'),
        # 反转钩子
        ('reversal', '原来一直欺压她的婆婆，竟是她失散多年的亲生母亲。'),
        ('reversal', '公司新来的实习生，竟然是隐藏身份的集团继承人。'),
        ('reversal', '他以为自己赢了一切，却发现这都是对手设计的陷阱。'),
        ('reversal', '原来她一直深爱的人，竟是害死她全家的凶手。'),
        ('reversal', '当他揭露真相时，所有人都震惊了。'),
        # 悬念钩子
        ('suspense', '她收到一封没有寄件人的信，里面写着她明天会做的三件事。'),
        ('suspense', '午夜十二点，电梯突然停在从未有过的第十三层。'),
        ('suspense', '他打开家门，发现另一个自己正坐在客厅等他。'),
        ('suspense', '这封信，到底是谁寄来的？'),
        ('suspense', '她总觉得有人在暗中跟踪她...'),
        # 金句
        ('金句', '"你以为的岁月静好，不过是有人替你负重前行。"'),
        ('金句', '"有些真相，不如永远不知道。"'),
        ('金句', '"命运赠送的礼物，早已在暗中标好了价格。"'),
        ('金句', '"我不是变了，而是终于认清了你。"'),
        ('金句', '"有些路，只能一个人走。"'),
    ]

    @classmethod
    def get_random_hook(cls, hook_type: str = None, count: int = 1) -> List[str]:
        """随机获取钩子"""
        db_hooks = list(HookLibrary.objects.filter(is_active=True))
        hooks = []

        if hook_type:
            typed = [h.content for h in db_hooks if h.hook_type == hook_type]
            if typed:
                hooks.extend(typed)
            else:
                hooks.extend([c for t, c in cls.BUILTIN_HOOKS if t == hook_type])

        if not hooks:
            hooks.extend([h.content for h in db_hooks])
            hooks.extend([c for t, c in cls.BUILTIN_HOOKS])

        if not hooks:
            return []
        random.shuffle(hooks)
        return hooks[:count]

    @classmethod
    def count(cls) -> int:
        return HookLibrary.objects.filter(is_active=True).count() + len(cls.BUILTIN_HOOKS)

    @classmethod
    def init_default_hooks(cls):
        """初始化默认钩子库"""
        for hook_type, content in cls.BUILTIN_HOOKS:
            HookLibrary.objects.get_or_create(
                hook_type=hook_type,
                content=content,
                defaults={'is_active': True}
            )


# ============================================================
# 剧本生成器（对接 creation.engine.pipeline）
# ============================================================

class ScriptGenerator:
    """
    剧本生成器

    工作原理：
    1. 调用 creation.engine.pipeline.ScriptPipeline 执行完整7节点流水线
    2. 返回生成结果（含预渲染HTML、安全的摘要等）
    3. 不返回原始剧本数据结构，只返回前端需要的信息
    """

    @classmethod
    def generate(cls, user_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行剧本生成

        参数:
            user_inputs: 用户创作参数
                - theme: str 题材代码
                - core_idea: str 一句话创意
                - episode_count: int 集数
                - format_variant: str 格式变体 A/B/C/D
                - user_id: str 用户ID
                - project_id: str 项目ID

        返回:
            生成结果（安全的，不暴露原始剧本结构）
        """
        from apps.creation.engine.pipeline import run_full_pipeline

        try:
            # 执行流水线
            result = run_full_pipeline(user_inputs)

            # 提取安全的结果（不包含原始剧本结构）
            safe_result = {
                'status': result.get('status', 'unknown'),
                'project_brief': result.get('project_brief'),
                'structure': {
                    'acts': result.get('structure', {}).get('acts', [])[:6],
                    'reversal_points': result.get('structure', {}).get('reversal_points', [])[:4],
                    'theme_code': result.get('structure', {}).get('theme_code', ''),
                },
                'characters_summary': {
                    'protagonist': result.get('characters', {}).get('protagonist', {}).get('name', ''),
                    'antagonist': result.get('characters', {}).get('antagonist', {}).get('name', ''),
                    'character_count': result.get('characters', {}).get('character_count', 0),
                },
                'scripts_summary': {
                    'total_episodes': result.get('scripts', {}).get('total_episodes', 0),
                    'total_words': result.get('scripts', {}).get('total_words', 0),
                    'format_variant': result.get('scripts', {}).get('format_variant', ''),
                },
                'review': result.get('review'),
                'export': {
                    'total_files': result.get('export', {}).get('total_files', 0),
                    'preview_html': result.get('export', {}).get('preview_html', ''),
                },
                'total_time_seconds': result.get('total_time_seconds', 0),
                'errors': result.get('errors', []),
                'warnings': result.get('warnings', []),
            }

            return safe_result

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'errors': [str(e)],
            }


# ============================================================
# 初始化函数（首次部署时调用）
# ============================================================

def init_skill_data():
    """初始化技能数据（默认题材、钩子、配置）"""
    SkillConfigService.init_default_configs()
    ThemeTemplateService.init_default_themes()
    HookLibraryService.init_default_hooks()
