# -*- coding: utf-8 -*-
"""
节点5：剧本创作节点
逐集生成符合格式的完整剧本 - 核心节点
"""
import random
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class Node5Script:
    """节点5：剧本创作 - 逐集生成完整剧本"""

    index: int = 5
    name: str = "剧本创作"
    description: str = "逐集生成符合格式的剧本正文"

    # 格式变体
    FORMAT_VARIANTS = {
        'A': {
            'name': '标准版',
            'description': '详细格式，适合学习研究',
            'template': 'variant_a.md',
        },
        'B': {
            'name': '行业通用版',
            'description': '行业标准格式，适合制作团队',
            'template': 'variant_b.md',
        },
        'C': {
            'name': '精简版',
            'description': '快速阅读/初稿',
            'template': 'variant_c.md',
        },
        'D': {
            'name': '详细分镜版',
            'description': '含景别、运镜、镜头时长',
            'template': 'variant_d.md',
        },
    }

    # 场景模板
    SCENE_TEMPLATES = {
        'location_templates': [
            '豪华别墅客厅', '高级写字楼', '私密餐厅包间', '医院走廊',
            '公司会议室', '高档公寓客厅', '地下车库', '奢侈品商场',
            '警察局门口', '法院外', '五星级酒店大堂', '海边别墅',
            '咖啡馆角落', '书店二楼', '健身房', '机场贵宾室',
        ],
        'time_of_day': ['日', '夜', '晨', '昏'],
        'temperature': ['暖色调', '冷色调', '中性色调'],
    }

    # 对话情绪词典
    EMOTION_DIALOGUE = {
        '愤怒': ['低吼', '咆哮', '压低声音', '咬牙切齿'],
        '悲伤': ['哽咽', '强忍', '颤抖', '无声落泪'],
        '惊讶': ['倒吸一口凉气', '瞪大眼睛', '后退一步', '捂住嘴'],
        '开心': ['眉开眼笑', '拍手', '拥抱', '跳起来'],
        '紧张': ['攥紧拳头', '频繁看表', '来回踱步', '咬嘴唇'],
        '冷漠': ['面无表情', '淡淡地', '不为所动', '漠不关心'],
    }

    # 动作描写库
    ACTION_DESCRIPTIONS = [
        '缓步走入，神色复杂地环视四周',
        '突然停下脚步，眼神变得锐利',
        '双手微微颤抖，努力控制情绪',
        '转身背对，肩膀轻轻颤抖',
        '深吸一口气，推门而入',
        '目光在人群中搜寻，最终定格在某处',
        '嘴角勾起一抹意味深长的微笑',
        '手中的文件不自觉地攥紧',
        '不经意间后退了半步',
        '眼神中闪过一丝不易察觉的慌乱',
    ]

    def generate_scene(
        self,
        scene_index: int,
        episode: int,
        protagonist: Dict,
        antagonist: Dict,
        supporting: List[Dict],
        scenes_count: int,
        format_variant: str,
    ) -> Dict[str, Any]:
        """生成单个场景"""
        location = random.choice(self.SCENE_TEMPLATES['location_templates'])
        time_of_day = random.choice(self.SCENE_TEMPLATES['time_of_day'])
        temperature = random.choice(self.SCENE_TEMPLATES['temperature'])

        # 生成场景动作
        scene_actions = random.sample(
            self.ACTION_DESCRIPTIONS,
            min(2, len(self.ACTION_DESCRIPTIONS))
        )

        # 确定出场角色
        if scene_index == 1:
            # 首场景通常主角登场
            characters_in_scene = [protagonist]
            if random.random() > 0.5:
                characters_in_scene.append(antagonist)
        elif scene_index == scenes_count:
            # 末场景通常是对话高潮
            characters_in_scene = [protagonist, antagonist]
            if supporting and random.random() > 0.7:
                characters_in_scene.append(random.choice(supporting))
        else:
            # 中间场景随机组合
            characters_in_scene = [protagonist]
            if random.random() > 0.3:
                characters_in_scene.append(
                    antagonist if random.random() > 0.5 and supporting else
                    random.choice(supporting) if supporting else antagonist
                )

        # 生成对话
        dialogues = []
        for char in characters_in_scene:
            emotion = random.choice(list(self.EMOTION_DIALOGUE.keys()))
            action_desc = random.choice(self.EMOTION_DIALOGUE[emotion])

            # 根据角色类型生成不同风格的台词
            if char.get('character_type') == 'protagonist':
                lines = [
                    f'你到底想怎么样？',
                    f'有些事情，我不会再退让了。',
                    f'你以为这样就能威胁到我？',
                    f'真相迟早会大白的。',
                ]
            elif char.get('character_type') == 'antagonist':
                lines = [
                    f'你以为你赢了？游戏才刚刚开始。',
                    f'有些人注定是失败者。',
                    f'我会让你后悔的。',
                    f'你什么都不懂。',
                ]
            else:
                lines = [
                    f'你们别这样...',
                    f'我觉得这里面有什么误会。',
                    f'要不先冷静一下？',
                    f'我来帮你们调解调解。',
                ]

            dialogues.append({
                'character_name': char.get('name', '角色'),
                'character_role': char.get('role', ''),
                'action': action_desc,
                'emotion': emotion,
                'line': random.choice(lines),
            })

        # 生成场景文字
        scene_text = self._format_scene_text(
            scene_index, location, time_of_day, temperature,
            scene_actions, dialogues, format_variant
        )

        return {
            'scene_index': scene_index,
            'location': location,
            'time_of_day': time_of_day,
            'temperature': temperature,
            'actions': scene_actions,
            'characters': [c.get('name') for c in characters_in_scene],
            'dialogues': dialogues,
            'scene_text': scene_text,
        }

    def _format_scene_text(
        self,
        scene_index: int,
        location: str,
        time_of_day: str,
        temperature: str,
        actions: List[str],
        dialogues: List[Dict],
        format_variant: str,
    ) -> str:
        """根据格式变体格式化场景文字"""
        lines = []

        if format_variant == 'A':
            # 标准版（详细格式）
            lines.append(f"### 场景{scene_index}：{location}（{time_of_day}）")
            lines.append(f"**场景编号**：{scene_index}-{time_of_day[0]}")
            lines.append(f"△ 色调：{temperature} | 声音：环境音")
            lines.append('')
            for action in actions:
                lines.append(f"△ {action}")
            lines.append('')
            for dlg in dialogues:
                lines.append(f"**{dlg['character_name']}**（{dlg['action']}）：{dlg['line']}")
            lines.append('')

        elif format_variant == 'B':
            # 行业通用版（默认）
            lines.append(f"△ {location} · {time_of_day} · {temperature}")
            lines.append('')
            for action in actions:
                lines.append(f"△ {action}")
            lines.append('')
            for dlg in dialogues:
                line_prefix = '→' if dlg['character_role'] == '主角' else '◇'
                lines.append(f"{line_prefix}{dlg['character_name']}：{dlg['line']}")
            lines.append('')

        elif format_variant == 'C':
            # 精简版
            lines.append(f"**{location}**")
            for dlg in dialogues:
                lines.append(f"{dlg['character_name']}：{dlg['line']}")
            lines.append('')

        else:
            # 格式D（分镜版）
            lines.append(f"【场景{scene_index}】{location} | {time_of_day} | {temperature}")
            lines.append(f"【镜头】{random.choice(['全景', '中景', '近景', '特写'])}")
            lines.append(f"【运镜】{random.choice(['固定', '推镜', '拉镜', '摇镜'])}")
            lines.append(f"【时长】约{random.randint(60, 120)}秒")
            lines.append('')
            for action in actions:
                lines.append(f"（{action}）")
            lines.append('')
            for dlg in dialogues:
                lines.append(f"{dlg['character_name']}：{dlg['line']}")
            lines.append('')

        return '\n'.join(lines)

    def generate_episode_script(
        self,
        episode_data: Dict,
        protagonist: Dict,
        antagonist: Dict,
        supporting: List[Dict],
        format_variant: str,
    ) -> Dict[str, Any]:
        """生成单集剧本"""
        episode = episode_data['episode']
        scenes_hint = episode_data.get('scenes_hint', {})
        scenes_count = scenes_hint.get('suggested_scene_count', 2)

        scenes = []
        for i in range(1, scenes_count + 1):
            scene = self.generate_scene(
                i, episode, protagonist, antagonist, supporting,
                scenes_count, format_variant
            )
            scenes.append(scene)

        # 组合完整剧本文字
        script_lines = []
        script_lines.append(f"## 第{episode}集：{episode_data.get('title', '待定').split('：')[1] if '：' in episode_data.get('title', '') else episode_data.get('title', '')}")
        script_lines.append('')
        script_lines.append(f"**集钩子**：{episode_data.get('hook', {}).get('hook_text', '本集精彩不容错过')}")
        script_lines.append('')
        script_lines.append('---')
        script_lines.append('')

        for scene in scenes:
            script_lines.append(scene['scene_text'])

        # 结尾悬念
        script_lines.append(f"△ 切黑。【{episode_data.get('hook', {}).get('hook_text', '未完待续')}】")
        script_lines.append('')
        script_lines.append('---')

        return {
            'episode': episode,
            'title': episode_data.get('title', f'第{episode}集'),
            'scenes_count': len(scenes),
            'scenes': scenes,
            'full_script_text': '\n'.join(script_lines),
            'word_count': sum(len(s['scene_text']) for s in scenes),
            'emotion_intensity': episode_data.get('emotion_intensity', 5),
        }

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行节点5：剧本创作

        输入:
            context.project_brief: 项目简报
            context.outlines: 分集大纲
            context.characters: 角色体系

        处理:
            1. 根据格式变体选择模板
            2. 逐集生成剧本
            3. 计算统计信息

        输出:
            scripts: 完整剧本数据
        """
        brief = context.get('project_brief', {})
        outlines = context.get('outlines', {})
        characters = context.get('characters', {})

        episode_count = brief.get('episode_count', 80)
        format_variant = brief.get('format_variant', 'B')
        episodes = outlines.get('episodes', [])

        protagonist = characters.get('protagonist', {})
        antagonist = characters.get('antagonist', {})
        supporting = characters.get('supporting_characters', [])

        # 逐集生成剧本
        scripts = []
        for episode_data in episodes:
            script = self.generate_episode_script(
                episode_data, protagonist, antagonist, supporting, format_variant
            )
            scripts.append(script)

        # 计算统计信息
        total_words = sum(s['word_count'] for s in scripts)
        total_scenes = sum(s['scenes_count'] for s in scripts)

        result = {
            'format_variant': format_variant,
            'format_name': self.FORMAT_VARIANTS.get(format_variant, self.FORMAT_VARIANTS['B'])['name'],
            'episodes': scripts,
            'total_episodes': len(scripts),
            'total_scenes': total_scenes,
            'total_words': total_words,
            'average_words_per_episode': round(total_words / len(scripts)) if scripts else 0,
            'average_scenes_per_episode': round(total_scenes / len(scripts), 1) if scripts else 0,
            'theme_code': brief.get('theme_code', 'mixed-theme'),
            'estimated_time_minutes': self._estimate_time(episode_count),
        }

        context['scripts'] = result
        context['next_params'].update({
            'scripts': scripts,
        })
        context['current_node'] = self.index

        return context

    def _estimate_time(self, episode_count: int) -> int:
        """估算该节点执行时间（分钟）- 核心节点，最耗时"""
        return max(90, min(180, episode_count * 2))
