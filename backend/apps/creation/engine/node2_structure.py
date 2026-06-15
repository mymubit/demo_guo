# -*- coding: utf-8 -*-
"""
节点2：结构规划节点
6阶段宏观架构 + 情绪节奏曲线 + 关键反转位置设计
"""
import random
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class Node2Structure:
    """节点2：结构规划 - 设计6阶段宏观架构"""

    index: int = 2
    name: str = "结构规划"
    description: str = "6阶段架构 + 情绪节奏曲线 + 关键反转点"

    # 6阶段名称
    ACT_NAMES = [
        '第一幕·铺垫引入',
        '第二幕·冲突升级',
        '第三幕·中段高潮',
        '第四幕·反转入局',
        '第五幕·高燃对决',
        '第六幕·结局升华',
    ]

    # 标准6阶段集数比例
    STANDARD_RATIOS = [0.10, 0.20, 0.20, 0.20, 0.15, 0.15]

    # 题材特定的阶段比例调整
    THEME_RATIO_ADJUSTMENTS = {
        'family-revenge': [0.08, 0.18, 0.22, 0.22, 0.18, 0.12],
        'overbearing-ceo': [0.10, 0.20, 0.25, 0.20, 0.15, 0.10],
        'sweet-pet': [0.15, 0.25, 0.25, 0.15, 0.10, 0.10],
        'time-travel': [0.10, 0.15, 0.25, 0.25, 0.15, 0.10],
        'urban-rebirth': [0.10, 0.20, 0.25, 0.20, 0.15, 0.10],
        'ancient-costume': [0.10, 0.15, 0.25, 0.20, 0.20, 0.10],
        'suspense-reversal': [0.10, 0.20, 0.20, 0.25, 0.15, 0.10],
        'healing': [0.12, 0.22, 0.20, 0.18, 0.14, 0.14],
        'mixed-theme': [0.10, 0.20, 0.20, 0.20, 0.15, 0.15],
    }

    # 情绪曲线配置
    EMOTION_CURVE_CONFIGS = {
        'family-revenge': {
            'start': 3, 'peak': 10,
            'curve': [3, 2, 1, 4, 7, 8, 9, 10],
            'description': '压抑→爆发→爽感递进'
        },
        'overbearing-ceo': {
            'start': 4, 'peak': 10,
            'curve': [4, 3, 5, 6, 8, 7, 9, 10],
            'description': '对立→误会→心动→坦诚'
        },
        'sweet-pet': {
            'start': 5, 'peak': 10,
            'curve': [5, 4, 6, 5, 7, 8, 9, 10],
            'description': '甜→虐→甜→高甜'
        },
        'time-travel': {
            'start': 3, 'peak': 10,
            'curve': [3, 5, 4, 7, 8, 6, 9, 10],
            'description': '困惑→先知→危机→改变'
        },
        'urban-rebirth': {
            'start': 2, 'peak': 10,
            'curve': [2, 3, 4, 6, 7, 8, 9, 10],
            'description': '低谷→崛起→巅峰'
        },
        'ancient-costume': {
            'start': 3, 'peak': 10,
            'curve': [3, 2, 5, 4, 7, 6, 9, 10],
            'description': '隐忍→翻盘→帝王之路'
        },
        'suspense-reversal': {
            'start': 5, 'peak': 10,
            'curve': [5, 6, 5, 7, 6, 8, 9, 10],
            'description': '迷雾→真相层层揭露'
        },
        'healing': {
            'start': 4, 'peak': 8,
            'curve': [4, 3, 4, 5, 5, 6, 7, 8],
            'description': '痛点共鸣→缓慢修复→温暖出口（禁大起大落）'
        },
        'mixed-theme': {
            'start': 4, 'peak': 10,
            'curve': [4, 4, 5, 6, 7, 8, 9, 10],
            'description': '稳定上升，有波动'
        },
    }

    def calculate_act_distribution(self, episode_count: int, theme_code: str = 'mixed-theme') -> List[Dict]:
        """计算6个阶段集数分配"""
        # 获取该题材的比例
        ratios = self.THEME_RATIO_ADJUSTMENTS.get(theme_code, self.STANDARD_RATIOS)

        acts = []
        current_ep = 1

        for i, ratio in enumerate(ratios):
            # 计算该阶段集数
            act_eps = max(2, int(round(episode_count * ratio)))
            act_end = min(current_ep + act_eps - 1, episode_count)

            act = {
                'act_index': i + 1,
                'act_name': self.ACT_NAMES[i],
                'episode_range': f"第{current_ep}-{act_end}集",
                'episode_start': current_ep,
                'episode_end': act_end,
                'episode_count': act_end - current_ep + 1,
                'ratio': ratio,
                'purpose': self._get_act_purpose(i),
                'key_events': self._generate_key_events(i, theme_code),
                'emotion_target': self._get_emotion_target(i),
            }
            acts.append(act)
            current_ep = act_end + 1

        # 修正最后一幕
        if acts:
            last_act = acts[-1]
            last_act['episode_end'] = episode_count
            last_act['episode_range'] = f"第{last_act['episode_start']}-{episode_count}集"
            last_act['episode_count'] = episode_count - last_act['episode_start'] + 1

        return acts

    def _get_act_purpose(self, act_index: int) -> str:
        """获取阶段目的"""
        purposes = [
            "建立世界观，介绍核心人物关系，抛出核心冲突引子，让观众快速入戏",
            "矛盾激化，反派登场施压，主角首次遭遇重大挫折或危机",
            "冲突持续拉锯，主角逐渐掌握主动权，观众情绪开始积累",
            "重大反转发生，反派揭露底牌，主角跌入最低谷",
            "主角觉醒/蜕变，制定终极计划，正邪对决开始",
            "终极对决，智与力的双重较量，所有悬念集中揭晓",
        ]
        return purposes[act_index] if act_index < len(purposes) else purposes[-1]

    def _generate_key_events(self, act_index: int, theme_code: str) -> List[str]:
        """生成该阶段的关键事件"""
        events_pool = {
            0: [  # 第一幕
                "主角登场，展示日常生活状态与内在渴望",
                "核心冲突事件突然触发，打破主角平静生活",
                "关键配角首次亮相，初步建立关系网络",
                "埋下第一条伏笔，为后续反转铺垫",
            ],
            1: [  # 第二幕
                "反派首次正面施压，主角措手不及",
                "盟友背叛或产生误会，主角陷入孤立",
                "关键信息揭露，真相的影子若隐若现",
                "主角第一次尝试反击，但以失败告终",
            ],
            2: [  # 第三幕
                "主角找到反击突破口，初战告捷",
                "反派察觉变化，调整策略加大压力",
                "重要配角完成关键转变，站队明确",
                "感情线升温，感情与事业的双重考验",
            ],
            3: [  # 第四幕
                "看似顺利的计划被反派彻底破坏",
                "隐藏身份或真相揭露，观众认知被颠覆",
                "主角最低谷时刻，重要角色受伤或离去",
                "情感关系出现重大危机，信任危机爆发",
            ],
            4: [  # 第五幕
                "主角经历重大事件后觉醒/蜕变",
                "获得关键资源或盟友归队",
                "制定终极计划，准备最后一战",
                "反派内部出现分裂，为最终溃败埋下种子",
            ],
            5: [  # 第六幕
                "终极对决，智与力的双重较量",
                "所有伏笔在高潮时刻回收",
                "核心悬念集中揭晓，真相大白",
                "结局揭晓，角色走向新人生，情感升华",
            ],
        }
        events = events_pool.get(act_index, events_pool[0])
        return random.sample(events, min(3, len(events)))

    def _get_emotion_target(self, act_index: int) -> int:
        """获取该阶段目标情绪值(1-10)"""
        targets = [3, 5, 6, 4, 8, 10]
        return targets[act_index] if act_index < len(targets) else 10

    def calculate_emotion_curve(self, episode_count: int, theme_code: str = 'mixed-theme') -> List[Dict]:
        """计算逐集情绪曲线"""
        config = self.EMOTION_CURVE_CONFIGS.get(theme_code, self.EMOTION_CURVE_CONFIGS['mixed-theme'])
        base_curve = config['curve']

        # 将8点曲线插值到实际集数
        curve_points = []
        step = (episode_count - 1) / (len(base_curve) - 1) if len(base_curve) > 1 else 0

        for i in range(episode_count):
            pos = i * step
            lower = int(pos)
            upper = min(lower + 1, len(base_curve) - 1)
            frac = pos - lower

            # 线性插值
            base_value = base_curve[lower] * (1 - frac) + base_curve[upper] * frac

            # 添加随机波动（±1）
            value = max(1, min(10, int(base_value) + random.randint(-1, 1)))

            # 标记关键反转点
            reversal_density = self._get_reversal_density(theme_code)
            is_key_point = (i + 1) % (10 // reversal_density) == 0 if reversal_density > 0 else False

            curve_points.append({
                'episode': i + 1,
                'emotion_value': value,
                'is_key_point': is_key_point,
                'note': self._get_emotion_note(value, is_key_point),
            })

        return curve_points

    def _get_reversal_density(self, theme_code: str) -> int:
        """获取反转密度（每多少集一个反转）"""
        densities = {
            'family-revenge': 3,
            'overbearing-ceo': 3,
            'sweet-pet': 4,
            'time-travel': 2,
            'urban-rebirth': 4,
            'ancient-costume': 2,
            'suspense-reversal': 2,
            'mixed-theme': 3,
        }
        return densities.get(theme_code, 3)

    def _get_emotion_note(self, value: int, is_key: bool) -> str:
        """获取情绪值描述"""
        notes = {
            1: "极度压抑",
            2: "压抑",
            3: "低沉",
            4: "平静",
            5: "平缓",
            6: "上升",
            7: "期待",
            8: "紧张",
            9: "高潮",
            10: "爆点",
        }
        base = notes.get(value, "待定")
        return f"【关键反转】{base}" if is_key else base

    def generate_reversal_points(self, episode_count: int, theme_code: str = 'mixed-theme') -> List[Dict]:
        """生成关键反转点位置"""
        density = self._get_reversal_density(theme_code)
        points = []

        # 通常在25%, 45%, 65%, 85%位置有重大反转
        key_positions = [0.25, 0.45, 0.65, 0.85]

        reversal_types = [
            "身份大反转",
            "立场转变",
            "真相揭露",
            "情感爆发",
            "绝地逆袭",
            "计划崩盘",
        ]

        for i, pos_ratio in enumerate(key_positions):
            ep = max(1, min(int(episode_count * pos_ratio), episode_count))

            # 根据阶段选择反转类型
            if pos_ratio < 0.35:
                rev_type = reversal_types[random.randint(0, 2)]  # 早期偏身份/立场
            elif pos_ratio < 0.65:
                rev_type = reversal_types[random.randint(1, 3)]  # 中期偏真相/情感
            else:
                rev_type = reversal_types[random.randint(3, 5)]  # 后期偏逆袭/崩盘

            points.append({
                'episode': ep,
                'position_ratio': pos_ratio,
                'reversal_type': rev_type,
                'description': f"第{ep}集：{rev_type}，剧情走向发生重大变化",
                'impact_level': 'high' if pos_ratio > 0.6 else 'medium',
            })

        return points

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行节点2：结构规划

        输入:
            context.project_brief: 项目简报（来自节点1）
            context.next_params: 下一步参数

        处理:
            1. 计算6阶段集数分配
            2. 计算情绪曲线
            3. 生成关键反转点

        输出:
            structure: 结构规划数据
        """
        brief = context.get('project_brief', {})
        theme_code = brief.get('theme_code', 'mixed-theme')
        episode_count = brief.get('episode_count', 80)

        # 计算6阶段分配
        acts = self.calculate_act_distribution(episode_count, theme_code)

        # 计算情绪曲线
        emotion_curve = self.calculate_emotion_curve(episode_count, theme_code)

        # 生成反转点
        reversal_points = self.generate_reversal_points(episode_count, theme_code)

        # 获取情绪曲线配置
        emotion_config = self.EMOTION_CURVE_CONFIGS.get(
            theme_code,
            self.EMOTION_CURVE_CONFIGS['mixed-theme']
        )

        structure = {
            'acts': acts,
            'emotion_curve': emotion_curve,
            'reversal_points': reversal_points,
            'theme_code': theme_code,
            'episode_count': episode_count,
            'emotion_config': {
                'start': emotion_config['start'],
                'peak': emotion_config['peak'],
                'description': emotion_config['description'],
            },
            'reversal_density': self._get_reversal_density(theme_code),
            'estimated_time_minutes': self._estimate_time(episode_count),
        }

        context['structure'] = structure
        context['next_params'].update({
            'acts': acts,
            'reversal_points': reversal_points,
        })
        context['current_node'] = self.index

        return context

    def _estimate_time(self, episode_count: int) -> int:
        """估算该节点执行时间（分钟）"""
        return max(15, min(30, episode_count // 3))
