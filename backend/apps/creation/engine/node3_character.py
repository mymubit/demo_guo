# -*- coding: utf-8 -*-
"""
节点3：人设开发节点
主角/反派/配角完整设定 + 人物关系图谱
"""
import random
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class Node3Character:
    """节点3：人设开发 - 生成完整的角色体系"""

    index: int = 3
    name: str = "人设开发"
    description: str = "主角/反派/配角完整设定 + 人物关系图谱"

    # 主角原型库
    PROTAGONIST_ARCHETYPES = {
        'family-revenge': {
            'default_name': '林晓薇',
            'archetype': '隐忍型→觉醒型',
            'age_range': '25-28岁',
            'personality': '外表温柔贤淑，内心坚韧不屈，经历重大事件后觉醒，行事果决',
            'background': '传统家庭出身，为家庭牺牲自我，发现真相后开始反击',
            'goal': '守护家人、夺回尊严、掌握自己的命运',
            'conflict': '内心的善良与现实的残酷之间的持续拉锯',
            'character_arc': '隐忍期→压抑期→觉醒期→反击期→蜕变期',
            'representative_lines': [
                '有些事情，忍无可忍便无需再忍。',
                '你以为我不敢，是因为我还在乎。',
                '从今天起，我不会再退让一步。',
                '我不是变了，而是终于醒了。',
            ],
            'appearance_desc': '长发披肩，眼神从温柔逐渐变得坚定，气质从柔弱转为干练',
            'skills': ['隐藏情绪', '观察入微', '以退为进', '绝地反击'],
        },
        'overbearing-ceo': {
            'default_name': '顾承泽',
            'archetype': '隐藏身份型',
            'age_range': '28-32岁',
            'personality': '外冷内热，理性克制，关键时刻展现出超强行动力和保护欲',
            'background': '顶级豪门继承人，为证明自己隐藏身份从底层做起',
            'goal': '证明自己、守护真爱、承担家族责任',
            'conflict': '身份与真心的矛盾，商业帝国与真爱的抉择',
            'character_arc': '伪装期→试探期→动心期→坦白期→守护期',
            'representative_lines': [
                '站在我身后，剩下的交给我。',
                '你以为你了解我，其实你什么都不知道。',
                '从遇见你的那一刻起，我就知道逃不掉了。',
                '我不要整个世界，我只要你。',
            ],
            'appearance_desc': '西装革履，眼神锐利却偶尔流露出温柔，气场强大',
            'skills': ['商业头脑', '格斗技能', '洞察人心', '资源整合'],
        },
        'sweet-pet': {
            'default_name': '苏念',
            'archetype': '元气治愈型',
            'age_range': '22-26岁',
            'personality': '乐观开朗，阳光积极，用正能量感染周围的人',
            'background': '普通家庭出身，热爱生活，用微笑面对一切困难',
            'goal': '守护身边的人，追求梦想，找到真爱',
            'conflict': '现实的残酷与理想主义的碰撞',
            'character_arc': '乐观期→受伤期→坚强期→守护期→幸福期',
            'representative_lines': [
                '就算全世界都放弃你，我也不会。',
                '我相信，只要努力就会有奇迹。',
                '你的难过，让我来分担。',
                '我不会走，永远都不会。',
            ],
            'appearance_desc': '马尾辫或丸子头，眼神明亮，笑起来有酒窝，活力满满',
            'skills': ['共情能力', '乐观感染', '治愈能力', '不离不弃'],
        },
        'time-travel': {
            'default_name': '陆子衿',
            'archetype': '重生智谋型',
            'age_range': '28-30岁',
            'personality': '冷静理智，深谋远虑，利用未来信息步步为营',
            'background': '重生者，带着前世记忆回到关键时间点',
            'goal': '改写命运、避免悲剧、守护重要的人',
            'conflict': '知道未来却无法说出，用行动代替言语',
            'character_arc': '利用期→动摇期→抉择期→牺牲期→改写期',
            'representative_lines': [
                '有些事情，就算知道结局，我也要亲手改变。',
                '你不需要知道为什么，只需要相信我。',
                '这一次，我要护你周全。',
                '命运给我的，我会加倍奉还。',
            ],
            'appearance_desc': '眼神深邃，仿佛能看穿一切，举止从容不迫',
            'skills': ['预知能力', '策略布局', '人际关系', '情报收集'],
        },
    }

    # 反派原型库
    ANTAGONIST_ARCHETYPES = {
        'family-revenge': {
            'default_name': '赵雅琴',
            'archetype': '势利恶婆婆型',
            'age_range': '50-55岁',
            'personality': '势利眼，虚荣伪善，精于算计，擅长情感操控',
            'background': '靠着儿子成功的依附者，害怕失去既得利益',
            'weakness': '对儿子的过度控制欲',
            'representative_lines': [
                '你以为你赢了？游戏才刚刚开始。',
                '有些人注定是失败者，永远上不了台面。',
                '在这个家里，你什么都不是。',
            ],
        },
        'overbearing-ceo': {
            'default_name': '沈墨寒',
            'archetype': '商业对手型',
            'age_range': '30-35岁',
            'personality': '阴险狡诈，为达目的不择手段，表面风度翩翩',
            'background': '同父异母的兄弟，为争夺继承权不择手段',
            'weakness': '对成功的极度渴望导致判断失误',
            'representative_lines': [
                '商场如战场，仁慈是最大的弱点。',
                '你注定是我的垫脚石。',
            ],
        },
    }

    # 配角模板
    SUPPORTING_CHARACTERS = [
        {
            'role': '男二/闺蜜',
            'function': '助攻+喜剧担当',
            'archetype': '阳光话痨型',
            'name_templates': ['林浩', '小杰', '阿飞'],
            'personality': '大大咧咧，重义气，是主角最坚实的后盾',
            'key_scene': '在主角最低落时给予支持和鼓励',
        },
        {
            'role': '知情者',
            'function': '信息传递+推动剧情',
            'archetype': '神秘老者型',
            'name_templates': ['顾老', '陈叔', '老周'],
            'personality': '看透一切，关键时刻给予提示',
            'key_scene': '揭示关键信息，帮助主角找到突破口',
        },
        {
            'role': '对手/情敌',
            'function': '制造冲突+推动成长',
            'archetype': '绿茶白莲花型',
            'name_templates': ['苏婉儿', '白琳', '陈玉'],
            'personality': '表面柔弱，实则心机深沉',
            'key_scene': '在公众场合陷害主角，最终被揭穿',
        },
    ]

    def generate_protagonist(self, theme_code: str, core_idea: str = '') -> Dict[str, Any]:
        """生成主角设定"""
        archetype = self.PROTAGONIST_ARCHETYPES.get(
            theme_code,
            self.PROTAGONIST_ARCHETYPES['family-revenge']
        )

        protagonist = {
            'character_type': 'protagonist',
            'name': archetype['default_name'],
            'role': '主角',
            'archetype': archetype['archetype'],
            'age_range': archetype['age_range'],
            'personality': archetype['personality'],
            'background': archetype['background'],
            'goal': archetype['goal'],
            'conflict': archetype['conflict'],
            'character_arc': archetype['character_arc'],
            'representative_lines': archetype['representative_lines'],
            'appearance_desc': archetype['appearance_desc'],
            'skills': archetype['skills'],
            'theme_code': theme_code,
        }

        # 根据创意调整背景
        if core_idea:
            protagonist['background'] = core_idea[:50] + '...的绝对核心人物'

        return protagonist

    def generate_antagonist(self, theme_code: str, protagonist_name: str = '') -> Dict[str, Any]:
        """生成反派设定"""
        archetype = self.ANTAGONIST_ARCHETYPES.get(
            theme_code,
            self.ANTAGONIST_ARCHETYPES['family-revenge']
        )

        protagonist_archetype = self.PROTAGONIST_ARCHETYPES.get(
            theme_code,
            self.PROTAGONIST_ARCHETYPES['family-revenge']
        )

        antagonist = {
            'character_type': 'antagonist',
            'name': archetype['default_name'],
            'role': '主要反派',
            'archetype': archetype['archetype'],
            'age_range': archetype['age_range'],
            'personality': archetype['personality'],
            'background': archetype.get('background', ''),
            'goal': f'击败{protagonist_name}，达成自己的目的',
            'conflict': archetype.get('conflict', '与主角的根本对立'),
            'weakness': archetype.get('weakness', '过度自信'),
            'character_arc': '嚣张期→受挫期→疯狂期→溃败期',
            'representative_lines': archetype['representative_lines'],
            'relationship_to_protagonist': self._get_antagonist_relationship(theme_code),
        }

        return antagonist

    def _get_antagonist_relationship(self, theme_code: str) -> str:
        """获取反派与主角的关系"""
        relationships = {
            'family-revenge': '婆婆/继母 vs 儿媳，压迫与被压迫',
            'overbearing-ceo': '商业竞争对手/情敌，真爱争夺',
            'sweet-pet': '情敌/误会制造者，感情考验',
            'time-travel': '前世仇人/今生对手，命运对抗',
            'urban-rebirth': '上司/同事，职场打压',
            'ancient-costume': '后宫嫔妃/政敌，宫廷斗争',
            'suspense-reversal': '隐藏身份的幕后黑手，真相揭露',
            'mixed-theme': '多面敌人，复杂对立',
        }
        return relationships.get(theme_code, '对立关系')

    def generate_supporting_characters(self, theme_code: str, protagonist_name: str, antagonist_name: str) -> List[Dict[str, Any]]:
        """生成配角设定"""
        supporting = []

        # 固定配角
        for i, template in enumerate(self.SUPPORTING_CHARACTERS[:2]):
            name = random.choice(template['name_templates'])
            supporting.append({
                'character_type': 'supporting',
                'name': name,
                'role': template['role'],
                'function': template['function'],
                'archetype': template['archetype'],
                'personality': template['personality'],
                'relationship_to_protagonist': f'{name}是{protagonist_name}最信任的朋友/盟友',
                'key_contribution': template['key_scene'],
                'representative_line': self._generate_supporting_line(template['archetype']),
            })

        # 根据题材添加特定配角
        if theme_code in ['family-revenge', 'overbearing-ceo']:
            # 添加家庭成员/长辈
            supporting.append({
                'character_type': 'supporting',
                'name': random.choice(['顾父', '林母', '陈老']),
                'role': '长辈/知情者',
                'function': '关键信息源+情感推动',
                'archetype': '慈爱但无奈型',
                'personality': '疼爱主角，但受限于身份无法直接帮助',
                'relationship_to_protagonist': f'{protagonist_name}的血缘长辈，知晓家族秘密',
                'key_contribution': '在关键时刻揭示关键证据或信息',
                'representative_line': '有些事情，是时候让你知道了...',
            })

        return supporting

    def _generate_supporting_line(self, archetype: str) -> str:
        """生成配角的代表性台词"""
        lines_by_archetype = {
            '阳光话痨型': [
                '别怕，有我在！',
                '走，我请你吃火锅去！',
                '天塌了有我顶着，你先歇着！',
            ],
            '神秘老者型': [
                '年轻人，有些事情急不得。',
                '答案就在你心里。',
                '时候到了，你自然会明白。',
            ],
            '绿茶白莲花型': [
                '姐姐，我真的不是故意的...',
                '大家都看到了，不是我先动的手...',
            ],
        }
        lines = lines_by_archetype.get(archetype, ['我会一直支持你的！'])
        return random.choice(lines)

    def generate_relationship_map(self, characters: List[Dict], theme_code: str) -> List[Dict[str, str]]:
        """生成人物关系图谱"""
        protagonist = next((c for c in characters if c.get('character_type') == 'protagonist'), None)
        antagonist = next((c for c in characters if c.get('character_type') == 'antagonist'), None)
        supporting = [c for c in characters if c.get('character_type') == 'supporting']

        relationships = []

        if protagonist and antagonist:
            relationships.append({
                'from': protagonist['name'],
                'to': antagonist['name'],
                'type': '核心对立',
                'description': '贯穿全剧的主要矛盾双方',
            })

            # 根据题材添加特定关系
            if theme_code in ['family-revenge', 'overbearing-ceo']:
                relationships.append({
                    'from': antagonist['name'],
                    'to': protagonist['name'],
                    'type': '压迫/对抗',
                    'description': antagonist.get('relationship_to_protagonist', '对立关系'),
                })

        if protagonist and supporting:
            for s in supporting[:2]:
                relationships.append({
                    'from': protagonist['name'],
                    'to': s['name'],
                    'type': '信任/盟友',
                    'description': f'{protagonist["name"]}与{s["name"]}的铁杆友情',
                })

        if antagonist and supporting:
            for s in supporting[1:2]:
                relationships.append({
                    'from': antagonist['name'],
                    'to': s['name'],
                    'type': '利用/拉拢',
                    'description': f'{antagonist["name"]}试图拉拢{s["name"]}',
                })

        return relationships

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行节点3：人设开发

        输入:
            context.project_brief: 项目简报
            context.structure: 结构规划

        处理:
            1. 生成主角设定
            2. 生成反派设定
            3. 生成配角设定
            4. 生成关系图谱

        输出:
            characters: 完整角色体系
        """
        brief = context.get('project_brief', {})
        theme_code = brief.get('theme_code', 'mixed-theme')
        core_idea = brief.get('core_idea', '')

        # 生成主角
        protagonist = self.generate_protagonist(theme_code, core_idea)

        # 生成反派
        antagonist = self.generate_antagonist(theme_code, protagonist['name'])

        # 生成配角
        supporting = self.generate_supporting_characters(
            theme_code,
            protagonist['name'],
            antagonist['name']
        )

        # 组合所有角色
        all_characters = [protagonist, antagonist] + supporting

        # 生成关系图谱
        relationship_map = self.generate_relationship_map(all_characters, theme_code)

        characters = {
            'protagonist': protagonist,
            'antagonist': antagonist,
            'supporting_characters': supporting,
            'all_characters': all_characters,
            'relationship_map': relationship_map,
            'theme_code': theme_code,
            'character_count': len(all_characters),
            'estimated_time_minutes': self._estimate_time(len(all_characters)),
        }

        context['characters'] = characters
        context['next_params'].update({
            'protagonist': protagonist,
            'antagonist': antagonist,
        })
        context['current_node'] = self.index

        return context

    def _estimate_time(self, character_count: int) -> int:
        """估算该节点执行时间（分钟）"""
        return max(30, min(60, character_count * 10))
