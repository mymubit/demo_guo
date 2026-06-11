# -*- coding: utf-8 -*-
"""
节点4：大纲撰写节点
每集1-2句话梗概 + 钩子/反转/悬念设计 + 情绪强度标注
"""
import random
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class Node4Outline:
    """节点4：大纲撰写 - 生成每集分集大纲"""

    index: int = 4
    name: str = "大纲撰写"
    description: str = "每集1-2句话梗概 + 钩子/反转/悬念设计"

    # 剧情走向模板库
    EPISODE_TEMPLATES = {
        'opening': [
            '在一次意想不到的事件中，{}意外发现了隐藏多年的秘密。',
            '{}与{}的首次正面交锋，气氛剑拔弩张。',
            '平静的日常被打破，{}被卷入了一场意想不到的风波。',
            '{}做出了一个改变命运的决定，却不知这只是一个开始。',
        ],
        'development': [
            '{}设下圈套，{}陷入两难境地，关键时刻{}出手相助。',
            '一场精心策划的相遇，让所有人物的关系发生了微妙变化。',
            '{}在调查过程中发现了关于{}的惊人真相。',
            '随着调查深入，{}意识到事情远比想象中复杂。',
        ],
        'conflict': [
            '{}与{}的矛盾终于爆发，双方在众人面前撕破脸皮。',
            '在众人的见证下，{}终于说出了那句被压抑多年的话。',
            '{}的计划看似成功，却没想到{}已经掌握了关键证据。',
            '关键时刻，{}做出了一个出人意料的选择。',
        ],
        'reversal': [
            '所有人都以为{}赢了，但真正的反转才刚刚开始。',
            '当{}以为自己胜券在握时，{}的真实身份被揭露。',
            '惊天大秘密曝光，所有人都震惊了！',
            '{}的真实目的终于浮出水面，剧情迎来最大反转。',
        ],
        'climax': [
            '{}与{}的终极对决，谁才是最后的赢家？',
            '时间紧迫，{}必须在最后一刻做出改变命运的选择。',
            '所有线索汇聚，真相即将大白于天下。',
            '{}倾尽所有，只为这最后一搏。',
        ],
        'resolution': [
            '尘埃落定，{}终于迎来了属于自己的胜利。',
            '经历了一切之后，{}和{}终于坦诚相待。',
            '新的篇章开启，{}将走向怎样的人生？',
            '大结局揭晓，所有人都得到了自己的归宿。',
        ],
    }

    # 钩子类型
    HOOK_TYPES = {
        'opening': ['冲突爆发', '身份悬念', '情感冲击', '秘密揭露'],
        'reversal': ['身份大反转', '立场转变', '情感突变', '计划崩盘'],
        'suspense': ['未完待续', '留有悬念', '下集预告', '意外发生'],
    }

    def generate_episode_title(self, episode: int, act_index: int) -> str:
        """生成单集标题"""
        title_prefixes = [
            '风起', '暗涌', '初遇', '试探', '裂痕', '危机', '反转',
            '真情', '反击', '暗流', '风暴', '曙光', '真相', '抉择',
            '对峙', '决裂', '觉醒', '燃战', '底牌', '终局', '新生',
            '救赎', '归来', '守护', '离别', '重逢', '阴谋', '信任',
            '背叛', '希望', '绝望', '突破', '巅峰'
        ]
        prefix = title_prefixes[(episode - 1) % len(title_prefixes)]
        return f"第{episode}集：{prefix}"

    def generate_episode_summary(
        self,
        episode: int,
        act_index: int,
        protagonist: Dict,
        antagonist: Dict,
        supporting: List[Dict],
        reversal_points: List[Dict],
    ) -> str:
        """生成单集摘要"""
        # 判断是否为反转集
        is_reversal = any(rp['episode'] == episode for rp in reversal_points)

        # 选择模板类型
        if act_index == 0:
            template_pool = self.EPISODE_TEMPLATES['opening']
        elif act_index <= 2:
            template_pool = self.EPISODE_TEMPLATES['development']
        elif act_index == 3:
            template_pool = self.EPISODE_TEMPLATES['conflict']
        elif act_index == 4:
            template_pool = self.EPISODE_TEMPLATES['reversal'] if is_reversal else self.EPISODE_TEMPLATES['development']
        else:
            template_pool = self.EPISODE_TEMPLATES['climax'] if episode % 10 == 0 else self.EPISODE_TEMPLATES['resolution']

        template = random.choice(template_pool)

        # 填充角色名
        names = [protagonist.get('name', '主角')]
        if antagonist:
            names.append(antagonist.get('name', '反派'))
        if supporting:
            names.append(supporting[0].get('name', '配角'))

        while len(names) < 3:
            names.append('神秘人')

        summary = template.format(*names[:template.count('{}'))]

        # 添加反转集特别说明
        if is_reversal:
            reversal_info = next((rp for rp in reversal_points if rp['episode'] == episode), None)
            if reversal_info:
                summary += f"（{reversal_info['reversal_type']}）"

        return summary

    def generate_hook(self, episode: int, act_index: int, is_reversal: bool) -> Dict[str, Any]:
        """生成集钩子"""
        if is_reversal:
            hook_type = random.choice(self.HOOK_TYPES['reversal'])
        elif act_index <= 1:
            hook_type = random.choice(self.HOOK_TYPES['opening'])
        else:
            hook_type = random.choice(list(self.HOOK_TYPES.values())[0])

        hook_library = [
            # 开场钩子
            f"第{episode}集开头：主角陷入前所未有的困境，生死一线间...",
            f"第{episode}集开场：隐藏三年的秘密即将被揭开！",
            f"神秘人物登场，所有人命运即将改变...",
            # 反转钩子
            f"惊天大反转！原来一切都是他的计划...",
            f"真相让人震惊！{random.choice(['他', '她', '他们'])}竟然是在演戏！",
            f"谁才是幕后黑手？惊人反转让人意想不到...",
            # 悬念钩子
            f"本集结尾：{random.choice(['他', '她'])}会做出怎样的选择？",
            f"悬念升级：下集将揭示更惊人的真相...",
            f"未完待续：{random.choice(['他', '她', '这件事'])}背后还有什么秘密？",
        ]

        return {
            'hook_type': hook_type,
            'hook_text': random.choice(hook_library),
            'hook_strength': random.randint(7, 10) if is_reversal else random.randint(5, 8),
        }

    def generate_scenes_hint(self, episode: int, act_index: int) -> Dict[str, Any]:
        """生成场景数量提示"""
        # 单集场景数限制：竖屏剧建议2-3个场景
        scene_count = 2 if random.random() > 0.3 else 3

        locations = [
            '豪华别墅客厅', '高级写字楼', '私密餐厅', '医院走廊',
            '公司会议室', '公寓客厅', '地下车库', '高端商场',
            '警察局门口', '法院外', '酒店大堂', '海边别墅',
        ]

        return {
            'suggested_scene_count': scene_count,
            'suggested_locations': random.sample(locations, min(scene_count, 3)),
            'note': '竖屏剧场景不宜过多，每场景1-2分钟为宜',
        }

    def calculate_emotion_intensity(self, episode: int, total_episodes: int, base_curve: List[int]) -> int:
        """计算单集情绪强度"""
        # 基于整体曲线计算
        ratio = episode / total_episodes
        curve_idx = min(int(ratio * len(base_curve)), len(base_curve) - 1)
        base = base_curve[curve_idx]

        # 添加随机波动
        intensity = base + random.randint(-1, 1)

        return max(1, min(10, intensity))

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行节点4：大纲撰写

        输入:
            context.project_brief: 项目简报
            context.structure: 结构规划
            context.characters: 角色体系

        处理:
            1. 为每集生成标题和摘要
            2. 为每集设计钩子
            3. 标注情绪强度
            4. 标记反转点

        输出:
            outlines: 分集大纲
        """
        brief = context.get('project_brief', {})
        structure = context.get('structure', {})
        characters = context.get('characters', {})

        episode_count = brief.get('episode_count', 80)
        acts = structure.get('acts', [])
        reversal_points = structure.get('reversal_points', [])
        emotion_curve = structure.get('emotion_curve', [])
        base_curve = [ec['emotion_value'] for ec in emotion_curve] if emotion_curve else [5, 6, 7, 8, 9, 10]

        protagonist = characters.get('protagonist', {})
        antagonist = characters.get('antagonist', {})
        supporting = characters.get('supporting_characters', [])

        outlines = []
        key_highlights = []

        for episode in range(1, episode_count + 1):
            # 确定所属幕
            act_index = 0
            for i, act in enumerate(acts):
                if act['episode_start'] <= episode <= act['episode_end']:
                    act_index = i
                    break

            # 是否为反转集
            is_reversal = any(rp['episode'] == episode for rp in reversal_points)

            # 生成标题
            title = self.generate_episode_title(episode, act_index)

            # 生成摘要
            summary = self.generate_episode_summary(
                episode, act_index, protagonist, antagonist, supporting, reversal_points
            )

            # 生成钩子
            hook = self.generate_hook(episode, act_index, is_reversal)

            # 场景提示
            scenes_hint = self.generate_scenes_hint(episode, act_index)

            # 情绪强度
            emotion_intensity = self.calculate_emotion_intensity(
                episode, episode_count, base_curve
            )

            # 组装大纲项
            outline_item = {
                'episode': episode,
                'title': title,
                'summary': summary,
                'act_index': act_index,
                'act_name': acts[act_index]['act_name'] if acts else f'第{act_index + 1}幕',
                'hook': hook,
                'is_reversal': is_reversal,
                'reversal_type': next(
                    (rp['reversal_type'] for rp in reversal_points if rp['episode'] == episode),
                    None
                ) if is_reversal else None,
                'emotion_intensity': emotion_intensity,
                'scenes_hint': scenes_hint,
                'word_count_estimate': scenes_hint['suggested_scene_count'] * 150,  # 每场景约150字
            }

            outlines.append(outline_item)

            # 标记关键集
            if is_reversal or episode % 20 == 0 or episode == episode_count:
                key_highlights.append({
                    'episode': episode,
                    'type': 'reversal' if is_reversal else ('milestone' if episode == episode_count else 'highlight'),
                    'title': title,
                    'summary': summary,
                })

        result = {
            'episodes': outlines,
            'total_episodes': episode_count,
            'reversal_count': sum(1 for o in outlines if o['is_reversal']),
            'key_highlights': key_highlights,
            'average_emotion_intensity': round(
                sum(o['emotion_intensity'] for o in outlines) / len(outlines), 1
            ) if outlines else 5,
            'estimated_total_words': sum(o['word_count_estimate'] for o in outlines),
            'theme_code': brief.get('theme_code', 'mixed-theme'),
            'estimated_time_minutes': self._estimate_time(episode_count),
        }

        context['outlines'] = result
        context['next_params'].update({
            'outlines': outlines,
            'reversal_points': reversal_points,
        })
        context['current_node'] = self.index

        return context

    def _estimate_time(self, episode_count: int) -> int:
        """估算该节点执行时间（分钟）"""
        return max(45, min(90, episode_count))
