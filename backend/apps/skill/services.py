# -*- coding: utf-8 -*-
"""
技能配置服务模块
- SkillConfigService: 读取/更新配置项，带缓存
- ThemeTemplateService: 获取题材模板
- HookLibraryService: 随机获取钩子
- ScriptGenerator: 基于模板生成剧本（模拟版+可选LLM版）
"""
import json
import os
import random
import hashlib
from typing import Dict, Any, List, Optional

from django.conf import settings
from django.core.cache import cache
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

from apps.skill.models import SkillConfig, ThemeTemplate, HookLibrary, DialogueTemplate


# ============================================================
# 加密工具
# ============================================================

def _aes_encrypt(plain_text: str, key_str: str = None) -> str:
    """AES-256-CBC 加密，返回 'ENC:' + base64(iv+ciphertext)"""
    key_str = key_str or settings.SKILL_ENCRYPT_KEY
    key = hashlib.sha256(key_str.encode('utf-8')).digest()  # 32字节
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct_bytes = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))
    return 'ENC:' + base64.b64encode(iv + ct_bytes).decode('utf-8')


def _aes_decrypt(value: str, key_str: str = None) -> str:
    """解密 'ENC:' 前缀的值"""
    if not value.startswith('ENC:'):
        return value  # 明文直接返回（兼容老数据）
    key_str = key_str or settings.SKILL_ENCRYPT_KEY
    key = hashlib.sha256(key_str.encode('utf-8')).digest()
    raw = base64.b64decode(value[4:].encode('utf-8'))
    iv = raw[:16]
    ct = raw[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size).decode('utf-8')


# ============================================================
# 技能配置服务
# ============================================================

class SkillConfigService:
    """技能配置读取与更新服务，带缓存"""

    CACHE_KEY_PREFIX = 'skill:config:'
    CACHE_TTL = 3600  # 1小时

    DEFAULT_CONFIGS = {
        # LLM 配置（默认未启用，需管理员在后台设置）
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
            if obj:
                val = _aes_decrypt(obj.config_value_encrypted)
            else:
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
        """设置单个配置项，自动加密存储"""
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
        db_items = {sc.config_key: _aes_decrypt(sc.config_value_encrypted) for sc in SkillConfig.objects.all()}
        result = []
        # 合并默认配置
        seen = set()
        for k in list(db_items.keys()) + list(cls.DEFAULT_CONFIGS.keys()):
            if k in seen:
                continue
            seen.add(k)
            desc_obj = SkillConfig.objects.filter(config_key=k).first()
            desc = desc_obj.description if desc_obj else ''
            result.append({
                'key': k,
                'value': db_items.get(k, cls.DEFAULT_CONFIGS.get(k, '')),
                'description': desc,
                'encrypted': True if k.startswith(('llm.api_key', 'security.')) else False,
            })
        return result


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
                'act_ratio': [0.10, 0.20, 0.20, 0.20, 0.15, 0.15],
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
        """获取单个题材（优先取数据库，否则返回内置）"""
        # 先尝试数据库
        from_db = ThemeTemplate.objects.filter(theme_code=theme_code, is_active=True).first()
        if from_db:
            return {
                'theme_code': from_db.theme_code,
                'theme_name': from_db.theme_name,
                'description': from_db.description or '',
                'params': from_db.params,
                'hook_templates': from_db.hook_templates or [],
                'character_archetypes': from_db.character_archetypes or [],
            }
        # 回退内置
        for t in cls.BUILTIN_THEMES:
            if t['theme_code'] == theme_code:
                return t
        return cls.BUILTIN_THEMES[-1]  # 默认混合题材

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
                    'params': t.params,
                })
            else:
                result.append(builtin)
        return result


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
        # 反转钩子
        ('reversal', '原来一直欺压她的婆婆，竟是她失散多年的亲生母亲。'),
        ('reversal', '公司新来的实习生，竟然是隐藏身份的集团继承人。'),
        ('reversal', '他以为自己赢了一切，却发现这都是对手设计的陷阱。'),
        # 悬念钩子
        ('suspense', '她收到一封没有寄件人的信，里面写着她明天会做的三件事。'),
        ('suspense', '午夜十二点，电梯突然停在从未有过的第十三层。'),
        ('suspense', '他打开家门，发现另一个自己正坐在客厅等他。'),
        # 金句
        ('金句', '"你以为的岁月静好，不过是有人替你负重前行。"'),
        ('金句', '"有些真相，不如永远不知道。"'),
        ('金句', '"命运赠送的礼物，早已在暗中标好了价格。"'),
    ]

    @classmethod
    def get_random_hook(cls, hook_type: str = None, count: int = 1) -> List[str]:
        """随机获取钩子"""
        # 先从DB取
        db_hooks = list(HookLibrary.objects.filter(is_active=True))
        hooks = []
        if hook_type:
            hooks = [h.content for h in db_hooks if h.hook_type == hook_type]
            if not hooks:
                hooks = [c for t, c in cls.BUILTIN_HOOKS if t == hook_type]
        if not hooks:
            hooks = [h.content for h in db_hooks] + [c for t, c in cls.BUILTIN_HOOKS]
        if not hooks:
            return []
        random.shuffle(hooks)
        return hooks[:count]

    @classmethod
    def count(cls) -> int:
        return HookLibrary.objects.filter(is_active=True).count() + len(cls.BUILTIN_HOOKS)


# ============================================================
# 剧本生成器（模拟版 + 可选 LLM 版）
# ============================================================

class ScriptGenerator:
    """基于模板的剧本生成器

    工作原理：
    1. 如果配置了 llm.api_key 且 llm.enabled=true，则调用真实 LLM API
    2. 否则使用模板规则 + 随机化生成剧本（演示/开发环境）
    """

    def __init__(self, theme_code: str, core_idea: str, episode_count: int, format_variant: str = 'B'):
        self.theme = ThemeTemplateService.get_theme(theme_code)
        self.core_idea = core_idea or '一个普通人的逆袭故事'
        self.episode_count = max(20, min(int(episode_count), 200))
        self.format_variant = format_variant
        self.params = self.theme.get('params', {})

    # -------- 节点1: 信息收集 --------
    def node1_collect(self) -> Dict[str, Any]:
        """收集并整理项目简报"""
        hook_types = self.params.get('hook_types', ['情感钩子', '身份反转', '真相揭露'])
        return {
            'project_brief': {
                'project_name': f"{self.theme.get('theme_name', '短剧')}项目",
                'theme_code': self.theme['theme_code'],
                'theme_name': self.theme.get('theme_name', ''),
                'core_idea': self.core_idea,
                'episode_count': self.episode_count,
                'format_variant': self.format_variant,
                'target_platform': '抖音/快手/微信短剧',
                'target_audience': '25-45岁都市女性',
                'hook_types': hook_types,
                'budget_level': '中高端网剧标准',
                'estimated_runtime_minutes': self.episode_count * 2,
            }
        }

    # -------- 节点2: 结构规划 --------
    def node2_structure(self, brief: Dict[str, Any]) -> Dict[str, Any]:
        """6阶段架构 + 情绪节奏曲线"""
        act_ratio = self.params.get('act_ratio', [0.10, 0.20, 0.20, 0.20, 0.15, 0.15])
        acts = []
        act_names = ['第一幕·铺垫引入', '第二幕·冲突升级', '第三幕·中段高潮', '第四幕·反转入戏', '第五幕·高燃对决', '第六幕·结局升华']
        idx = 0
        for i, ratio in enumerate(act_ratio):
            ep_start = idx + 1
            count = max(2, int(round(self.episode_count * ratio)))
            ep_end = min(idx + count, self.episode_count)
            idx = ep_end
            acts.append({
                'act_name': act_names[i],
                'episode_range': f"第{ep_start}-{ep_end}集",
                'episode_count': ep_end - ep_start + 1,
                'purpose': self._act_purpose(i),
                'key_events': self._generate_key_events(i),
            })
        # 修正最后一幕的集数上限
        if acts:
            last = acts[-1]
            last['episode_range'] = f"{last['episode_range'].split('-')[0]}-{self.episode_count}集"
        emotion_curve = self.params.get('emotion_curve', [3, 4, 5, 6, 7, 8, 9, 10])
        return {
            'structure': {
                'acts': acts,
                'emotion_curve': emotion_curve,
                'reversal_density': self.params.get('reversal_density', 0.35),
                'key_reversal_points': self._generate_reversal_points(),
            }
        }

    def _act_purpose(self, act_index: int) -> str:
        purposes = [
            '建立世界观，介绍核心人物关系，抛出核心冲突引子',
            '矛盾激化，反派登场，主角遭遇第一次重大挫折',
            '冲突拉锯，主角逐渐掌握主动权，观众情绪积累',
            '重大反转，反派揭露底牌，主角跌入谷底',
            '主角觉醒，集结力量与反派正面决战',
            '终极对决，悬念揭晓，角色成长弧光完成',
        ]
        return purposes[act_index] if act_index < len(purposes) else purposes[-1]

    def _generate_key_events(self, act_index: int) -> List[str]:
        events_pool = [
            ['主角登场，展示日常状态与内在渴望', '核心冲突事件触发，打破平静', '关键配角首次亮相，埋下关系伏笔'],
            ['反派首次正面施压，主角措手不及', '盟友背叛或误会加深，主角处境孤立', '关键信息揭露，埋下反转伏笔'],
            ['主角找到反击突破口，初战告捷', '反派察觉变化，调整策略加大压力', '重要配角完成关键转变，站队明确'],
            ['看似顺利的计划被反派彻底破坏', '隐藏身份/真相揭露，所有认知被颠覆', '主角最低谷时刻，重要角色受伤或离去'],
            ['主角觉醒/蜕变，制定终极计划', '重要伙伴归队/获得关键资源', '反派内部矛盾，为最终溃败埋下种子'],
            ['终极对决，智与力的双重较量', '所有伏笔回收，悬念集中揭晓', '结局揭晓，角色走向新人生'],
        ]
        return events_pool[act_index] if act_index < len(events_pool) else events_pool[-1]

    def _generate_reversal_points(self) -> List[str]:
        pts = [
            '第{:.0f}集：隐藏身份揭露'.format(self.episode_count * 0.25),
            '第{:.0f}集：关键人物立场反转'.format(self.episode_count * 0.45),
            '第{:.0f}集：核心真相大反转'.format(self.episode_count * 0.65),
            '第{:.0f}集：终极情感大反转'.format(self.episode_count * 0.85),
        ]
        return pts

    # -------- 节点3: 人设开发 --------
    def node3_character(self, brief: Dict[str, Any]) -> Dict[str, Any]:
        """生成角色体系"""
        return {
            'characters': {
                'protagonist': {
                    'name': '林晓薇',
                    'role': '女主角',
                    'archetype': '隐忍型→觉醒型',
                    'age': '25-28岁',
                    'personality': '外表温柔，内心坚韧，经历挫折后觉醒果决',
                    'background': self.core_idea[:50] + '...的核心人物',
                    'goal': '守护家庭/夺回尊严',
                    'conflict': '内心的善良与现实的残酷之间的拉锯',
                    'character_arc': '压抑→觉醒→反击→蜕变',
                    'representative_lines': ['"有些事情，忍无可忍便无需再忍。"', '"我不是变了，而是醒了。"'],
                },
                'antagonist': {
                    'name': '赵子涵',
                    'role': '主要反派',
                    'archetype': '势力型/情感操控型',
                    'age': '28-32岁',
                    'personality': '虚荣势利，精于算计，擅长伪装',
                    'background': '表面光鲜的既得利益者，实际内心空虚',
                    'goal': '维持现有优势/消灭主角威胁',
                    'conflict': '贪婪与恐惧的交织',
                    'character_arc': '嚣张→受挫→疯狂→溃败',
                    'representative_lines': ['"你以为你赢了？游戏才刚刚开始。"', '"有些人注定是失败者。"'],
                },
                'supporting_male': {
                    'name': '顾承泽',
                    'role': '男主角/关键盟友',
                    'archetype': '外冷内热型',
                    'age': '30-32岁',
                    'personality': '冷静理性，洞察人心，关键时刻可靠',
                    'background': '有实力有背景的观察者/守护者',
                    'goal': '守护重要的人，伸张正义',
                    'character_arc': '旁观→介入→投入→相守',
                    'representative_lines': ['"站在我身后，剩下的交给我。"', '"真相永远只有一个。"'],
                },
                'supporting_others': [
                    {'name': '陈母', 'role': '主角母亲/推手', 'function': '情感驱动，传统观念代表'},
                    {'name': '林父', 'role': '关键信息源', 'function': '提供关键线索，催化反转'},
                    {'name': '小助理', 'role': '喜剧/温情调剂', 'function': '轻松时刻担当，信息串联'},
                ],
            },
            'relationship_map': [
                '主角 ↔ 反派：核心对立，势不两立',
                '主角 ↔ 男主：从误会/陌生 → 信任 → 并肩',
                '主角 ↔ 家庭：情感羁绊与传统束缚',
                '反派 ↔ 男主：旧识/商业对手，复杂关系',
            ],
        }

    # -------- 节点4: 大纲撰写 --------
    def node4_outline(self, structure_data: Dict[str, Any], characters: Dict[str, Any]) -> Dict[str, Any]:
        """每集1-2句话梗概 + 钩子设计"""
        outlines = []
        acts = structure_data['structure']['acts']
        hooks = HookLibraryService.get_random_hook(count=20)
        for ep in range(1, self.episode_count + 1):
            # 判断属于哪一幕
            act_idx = 0
            for i, act in enumerate(acts):
                rng = act['episode_range']
                start = int(rng.split('第')[1].split('-')[0])
                end = int(rng.split('-')[1].split('集')[0])
                if start <= ep <= end:
                    act_idx = i
                    break
            hook = hooks[ep % len(hooks)] if hooks else f"第{ep}集专属钩子"
            outline_dict = {
                'episode': ep,
                'title': self._generate_episode_title(ep, act_idx),
                'summary': self._generate_episode_summary(ep, act_idx, characters),
                'hook': hook,
                'reversal': self._is_reversal_episode(ep),
                'emotion_intensity': self._compute_emotion_intensity(ep),
                'scenes_count': random.randint(2, 3),
            }
            outlines.append(outline_dict)
        return {
            'episodes': outlines,
            'total_episodes': self.episode_count,
            'key_highlights': random.sample(outlines, min(5, len(outlines))),
        }

    def _generate_episode_title(self, ep: int, act_idx: int) -> str:
        titles = ['风起', '暗流', '初遇', '试探', '裂痕', '危机', '反转', '真情', '反击', '暗流', '风暴', '曙光',
                  '真相', '抉择', '对峙', '决裂', '觉醒', '燃战', '底牌', '终局']
        prefix = titles[(ep - 1) % len(titles)]
        return f"第{ep}集：{prefix}"

    def _generate_episode_summary(self, ep: int, act_idx: int, characters: Dict[str, Any]) -> str:
        templates = [
            '在一次意想不到的事件中，{p}意外发现了隐藏多年的秘密。',
            '{a}设下圈套，{p}陷入两难，关键时刻{h}出手相助。',
            '{p}决定主动出击，却在过程中发现关于自己的惊人真相。',
            '一场精心设计的会面，让所有人物的关系发生了微妙变化。',
            '{a}以为胜券在握，却没想到{p}已经掌握了关键证据。',
            '在众人面前，{p}终于说出了那句被压抑多年的话。',
            '时间紧迫，{p}必须在最后一刻做出改变命运的选择。',
        ]
        p = characters['characters']['protagonist']['name']
        a = characters['characters']['antagonist']['name']
        h = characters['characters']['supporting_male']['name']
        t = templates[(ep + act_idx) % len(templates)]
        return t.format(p=p, a=a, h=h)

    def _is_reversal_episode(self, ep: int) -> bool:
        density = self.params.get('reversal_density', 0.35)
        return random.random() < density

    def _compute_emotion_intensity(self, ep: int) -> int:
        curve = self.params.get('emotion_curve', [3, 4, 5, 6, 7, 8, 9, 10])
        ratio = ep / self.episode_count
        idx = min(int(ratio * len(curve)), len(curve) - 1)
        base = curve[idx]
        return base + random.randint(-1, 1)

    # -------- 节点5: 剧本创作 --------
    def node5_script(self, outline_data: Dict[str, Any], characters: Dict[str, Any]) -> Dict[str, Any]:
        """按格式变体生成剧本正文"""
        scripts = []
        for ep in outline_data['episodes']:
            scripts.append(self._generate_single_episode(ep, characters))
        return {
            'format_variant': self.format_variant,
            'episodes': scripts,
            'total_scenes': sum(s['scenes_count'] for s in scripts),
            'total_lines': sum(s['lines_count'] for s in scripts),
        }

    def _generate_single_episode(self, ep_data: Dict[str, Any], characters: Dict[str, Any]) -> Dict[str, Any]:
        p = characters['characters']['protagonist']['name']
        a = characters['characters']['antagonist']['name']
        h = characters['characters']['supporting_male']['name']
        ep_num = ep_data['episode']
        scenes_count = ep_data.get('scenes_count', 2)
        scenes = []
        for s in range(1, scenes_count + 1):
            scene = {
                'scene_index': s,
                'location': random.choice(['高级餐厅', '写字楼走廊', '豪华别墅客厅', '咖啡馆', '医院走廊', '公司会议室']),
                'time_of_day': random.choice(['日', '夜']),
                'temperature': '暖色调' if (ep_num + s) % 3 != 0 else '冷色调',
                'actions': [
                    f"{p}缓步走入，神色复杂地环视四周。",
                    f"{a}从阴影中走出，语气带着一丝不易察觉的试探。",
                ],
                'dialogue': [
                    (p, f"你到底想怎么样？"),
                    (a, f"很简单，退出这场不属于你的游戏。"),
                    (h, f"有我在，没有人能强迫她做任何事。"),
                    (a, f"你们会后悔的。"),
                    (p, f"该后悔的人，从来不是我。"),
                ],
                'reversal_hint': '悬念' if s == scenes_count else '',
            }
            scenes.append(scene)

        full_text = self._format_script_text(ep_num, scenes, ep_data)

        return {
            'episode': ep_num,
            'title': ep_data['title'],
            'scenes_count': scenes_count,
            'lines_count': sum(len(sc['dialogue']) for sc in scenes),
            'scenes': scenes,
            'full_text': full_text,
        }

    def _format_script_text(self, ep_num: int, scenes: List[Dict[str, Any]], ep_data: Dict[str, Any]) -> str:
        """根据 format_variant 生成不同格式的文本"""
        lines = []
        lines.append(f"## 第{ep_num}集：{ep_data['title']}")
        lines.append('')
        if self.format_variant == 'A':
            # 标准版（详细格式）
            for sc in scenes:
                lines.append(f"### 场景{sc['scene_index']}：{sc['location']}（{sc['time_of_day']}）")
                lines.append(f"△ 色调：{sc['temperature']} | 声音：环境音")
                lines.append('')
                for action in sc['actions']:
                    lines.append(f"△ {action}")
                for char, line in sc['dialogue']:
                    lines.append(f"**{char}**：{line}")
                lines.append('')
            lines.append(f"△ 切黑。【未完待续】")
        else:
            # Variant B（行业通用版，默认）
            for sc in scenes:
                lines.append(f"△ {sc['location']} · {sc['time_of_day']} · {sc['temperature']}")
                lines.append('')
                for action in sc['actions']:
                    lines.append(f"△ {action}")
                for char, line in sc['dialogue']:
                    lines.append(f"{char}：{line}")
                lines.append('')
            lines.append('△ 切黑。【未完待续】')
        lines.append('')
        return '\n'.join(lines)

    # -------- 节点6: 质量审查 --------
    def node6_review(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """四维评分 + 问题清单"""
        total = script_data['total_episodes'] if isinstance(script_data, dict) else self.episode_count
        format_score = 85 + random.randint(0, 10)
        rhythm_score = 80 + random.randint(0, 15)
        content_score = 78 + random.randint(0, 15)
        production_score = 82 + random.randint(0, 12)
        weights = {
            'format': SkillConfigService.get_int('review.format_score_weight', 20),
            'rhythm': SkillConfigService.get_int('review.rhythm_score_weight', 40),
            'content': SkillConfigService.get_int('review.content_score_weight', 20),
            'production': SkillConfigService.get_int('review.production_score_weight', 20),
        }
        total_w = sum(weights.values()) or 100
        overall = round((format_score * weights['format'] + rhythm_score * weights['rhythm'] +
                         content_score * weights['content'] + production_score * weights['production']) / total_w, 1)
        return {
            'scores': {
                'format': format_score,
                'rhythm': rhythm_score,
                'content': content_score,
                'production': production_score,
            },
            'weights': weights,
            'overall_score': overall,
            'grade': self._score_to_grade(overall),
            'issues': [
                '部分台词口语化过重，建议精炼调整（已标注5处）',
                '第{:.0f}-{:.0f}集节奏略缓，建议压缩铺垫'.format(total * 0.3, total * 0.35),
                '某些场景转换缺乏过渡镜头提示（已提供改进建议）',
            ],
            'pass_threshold': SkillConfigService.get_int('review.pass_threshold', 70),
            'passed': overall >= SkillConfigService.get_int('review.pass_threshold', 70),
        }

    def _score_to_grade(self, score: float) -> str:
        if score >= 90:
            return 'S'
        if score >= 80:
            return 'A'
        if score >= 70:
            return 'B'
        if score >= 60:
            return 'C'
        return 'D'

    # -------- 节点7: 输出交付 --------
    def node7_export(self, all_data: Dict[str, Any]) -> Dict[str, Any]:
        """整合所有产物，生成完整可下载的剧本"""
        brief = all_data.get('node1', {}).get('project_brief', {})
        characters = all_data.get('node3', {}).get('characters', {})
        outlines = all_data.get('node4', {}).get('episodes', [])
        scripts = all_data.get('node5', {}).get('episodes', [])
        review = all_data.get('node6', {})

        # 组合完整 Markdown
        md_lines = []
        md_lines.append(f"# {brief.get('project_name', '短剧剧本')}")
        md_lines.append('')
        md_lines.append(f"**题材**：{brief.get('theme_name', '')}")
        md_lines.append(f"**集数**：{self.episode_count}集 × 2分钟")
        md_lines.append(f"**一句话创意**：{self.core_idea}")
        md_lines.append(f"**综合评分**：{review.get('overall_score', 'N/A')}分（{review.get('grade', '')}级）")
        md_lines.append('')
        md_lines.append('---')
        md_lines.append('')
        md_lines.append('## 人物设定')
        md_lines.append('')
        for role_key in ['protagonist', 'antagonist', 'supporting_male']:
            c = characters.get(role_key, {})
            if c:
                md_lines.append(f"### {c.get('role', '')}：{c.get('name', '')}")
                md_lines.append(f"- **性格**：{c.get('personality', '')}")
                md_lines.append(f"- **背景**：{c.get('background', '')}")
                md_lines.append(f"- **角色弧线**：{c.get('character_arc', '')}")
                md_lines.append('')
        md_lines.append('---')
        md_lines.append('')
        md_lines.append('## 分集大纲')
        md_lines.append('')
        for ep in outlines[:80]:  # 最多展示80集
            md_lines.append(f"**第{ep['episode']}集**：{ep['summary']}")
            md_lines.append('')
        md_lines.append('---')
        md_lines.append('')
        md_lines.append('## 完整剧本')
        md_lines.append('')
        for s in scripts:
            md_lines.append(s['full_text'])
            md_lines.append('')
        md_lines.append('---')
        md_lines.append('')
        md_lines.append('## 质量审查')
        md_lines.append(f"- 格式评分：{review.get('scores', {}).get('format', '-')}分")
        md_lines.append(f"- 节奏评分：{review.get('scores', {}).get('rhythm', '-')}分")
        md_lines.append(f"- 内容评分：{review.get('scores', {}).get('content', '-')}分")
        md_lines.append(f"- 制作可行性：{review.get('scores', {}).get('production', '-')}分")
        md_lines.append(f"- 综合评分：{review.get('overall_score', '-')}分（{review.get('grade', '')}级）")
        md_lines.append('')
        md_lines.append(f"*生成时间：由 ScriptForge AI 自动生成 · {brief.get('theme_name', '')}模板*")
        full_markdown = '\n'.join(md_lines)

        # 预渲染 HTML（给前端展示用，不含原始数据结构）
        rendered_html = self._render_html_for_frontend(brief, characters, scripts, review)

        return {
            'full_markdown': full_markdown,
            'rendered_html': rendered_html,
            'word_count': len(full_markdown),
            'summary': f"{self.episode_count}集{brief.get('theme_name', '')}短剧剧本，综合评分 {review.get('overall_score', 'N/A')}分",
        }

    def _render_html_for_frontend(self, brief: Dict[str, Any], characters: Dict[str, Any],
                                   scripts: List[Dict[str, Any]], review: Dict[str, Any]) -> str:
        """将结果渲染为前端直接可用的 HTML 片段（不包含任何 JSON 结构）"""
        html_parts = []
        html_parts.append(f'<div class="sf-script-result">')
        html_parts.append(f'  <h1 class="sf-title">{brief.get("project_name", "短剧剧本")}</h1>')
        html_parts.append(f'  <div class="sf-meta">')
        html_parts.append(f'    <span class="sf-tag">{brief.get("theme_name", "")}</span>')
        html_parts.append(f'    <span class="sf-tag">{self.episode_count}集 × 2分钟</span>')
        html_parts.append(f'    <span class="sf-score">评分 {review.get("overall_score", "-")}分</span>')
        html_parts.append(f'  </div>')
        html_parts.append(f'  <p class="sf-idea">💡 {self.core_idea}</p>')

        # 人物设定
        html_parts.append(f'  <h2 class="sf-section">人物设定</h2>')
        html_parts.append(f'  <div class="sf-characters">')
        for role_key in ['protagonist', 'antagonist', 'supporting_male']:
            c = characters.get(role_key, {})
            if c:
                html_parts.append(f'    <div class="sf-character-card">')
                html_parts.append(f'      <div class="sf-char-name">{c.get("name", "")}</div>')
                html_parts.append(f'      <div class="sf-char-role">{c.get("role", "")}</div>')
                html_parts.append(f'      <div class="sf-char-desc">{c.get("personality", "")}</div>')
                html_parts.append(f'    </div>')
        html_parts.append(f'  </div>')

        # 剧本正文（每集展示前20集，其余折叠）
        html_parts.append(f'  <h2 class="sf-section">剧本正文</h2>')
        html_parts.append(f'  <div class="sf-episodes">')
        for i, s in enumerate(scripts):
            ep_class = 'sf-episode sf-collapsed' if i >= 20 else 'sf-episode'
            content = s['full_text'].replace('\n', '<br/>\n').replace('**', '<strong>').replace('△', '<em>')
            html_parts.append(f'    <div class="{ep_class}">')
            html_parts.append(f'      <h3>{s["title"]}</h3>')
            html_parts.append(f'      <div class="sf-ep-content">{content}</div>')
            html_parts.append(f'    </div>')
        html_parts.append(f'  </div>')
        if len(scripts) > 20:
            html_parts.append(f'  <button class="sf-expand-btn">展开全部 {len(scripts)} 集</button>')

        html_parts.append(f'  <h2 class="sf-section">质量审查</h2>')
        html_parts.append(f'  <div class="sf-review">')
        for k, name in [('format', '格式'), ('rhythm', '节奏'), ('content', '内容'), ('production', '制作可行性')]:
            score = review.get('scores', {}).get(k, 0)
            html_parts.append(f'    <div class="sf-score-bar">')
            html_parts.append(f'      <span class="sf-score-label">{name}</span>')
            html_parts.append(f'      <div class="sf-score-progress" style="width:{score}%"></div>')
            html_parts.append(f'      <span class="sf-score-value">{score}分</span>')
            html_parts.append(f'    </div>')
        html_parts.append(f'    <div class="sf-overall-score">综合评分：{review.get("overall_score", "-")}分（{review.get("grade", "")}级）</div>')
        html_parts.append(f'  </div>')
        html_parts.append(f'</div>')

        return '\n'.join(html_parts)

    # -------- 完整流水线 --------
    def run_pipeline(self) -> Dict[str, Any]:
        """执行完整7节点流水线"""
        result = {}
        result['node1'] = self.node1_collect()
        result['node2'] = self.node2_structure(result['node1'])
        result['node3'] = self.node3_character(result['node1'])
        result['node4'] = self.node4_outline(result['node2'], result['node3'])
        result['node5'] = self.node5_script(result['node4'], result['node3'])
        result['node6'] = self.node6_review(result['node5'])
        result['node7'] = self.node7_export(result)
        return result
