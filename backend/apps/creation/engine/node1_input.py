# -*- coding: utf-8 -*-
"""
节点1：信息收集节点
从用户输入提取8项关键信息，生成项目简报
"""
import re
from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class Node1Input(BaseNode):
    """节点1：信息收集 - 收集用户创作需求的8项关键信息"""

    index: int = 1
    name: str = "信息收集"
    description: str = "收集用户创作需求，生成项目简报"

    # 必需输入字段
    required_fields: List[str] = field(default_factory=lambda: [
        'theme', 'episode_count', 'core_idea'
    ])

    # 可选输入字段
    optional_fields: List[str] = field(default_factory=lambda: [
        'episode_duration', 'target_platform', 'target_audience',
        'core_hook', 'reference_work', 'budget_level'
    ])

    # 题材代码映射
    THEME_CODES = {
        'family-revenge': '家庭伦理复仇',
        'overbearing-ceo': '豪门霸总',
        'sweet-pet': '甜宠虐恋',
        'time-travel': '穿越重生',
        'urban-rebirth': '都市逆袭',
        'ancient-costume': '古装权谋',
        'suspense-reversal': '悬疑反转',
        'male-advancement': '都市男频',
        'mixed-theme': '混合题材',
    }

    # 默认值
    DEFAULTS = {
        'episode_duration': 2,
        'target_platform': '抖音/快手',
        'target_audience': '25-45岁都市女性',
        'budget_level': '中高端网剧标准',
    }

    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """验证并规范化输入"""
        errors = []

        # 验证必填字段
        for field in self.required_fields:
            if field not in inputs or not inputs[field]:
                errors.append(f"缺少必填字段: {field}")

        # 验证题材代码
        if 'theme' in inputs:
            theme = inputs['theme']
            if theme not in self.THEME_CODES:
                # 尝试模糊匹配
                matched = False
                for code in self.THEME_CODES:
                    if code in theme.lower() or self.THEME_CODES[code] in theme:
                        inputs['theme'] = code
                        matched = True
                        break
                if not matched:
                    inputs['theme'] = 'mixed-theme'

        # 验证集数范围
        if 'episode_count' in inputs:
            try:
                ep_count = int(inputs['episode_count'])
                if ep_count < 10:
                    ep_count = 10
                    errors.append("集数最小为10集，已自动调整为10集")
                elif ep_count > 300:
                    ep_count = 300
                    errors.append("集数最大为300集，已自动调整为300集")
                inputs['episode_count'] = ep_count
            except (ValueError, TypeError):
                inputs['episode_count'] = 80
                errors.append("集数格式错误，已设置为默认值80集")

        # 应用默认值
        for key, default_value in self.DEFAULTS.items():
            if key not in inputs or not inputs[key]:
                inputs[key] = default_value

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'data': inputs
        }

    def extract_hook_from_idea(self, core_idea: str) -> str:
        """从一句话创意中提取核心钩子"""
        if not core_idea:
            return "待定"

        # 移除标点符号
        clean_idea = re.sub(r'[，。！？、；：""''（）【】]', '', core_idea)

        # 尝试提取核心冲突点
        hook_patterns = [
            (r'隐忍(\d+)年', r'隐忍\1年后反击'),
            (r'发现(.+?)的秘密', r'揭露隐藏的\1秘密'),
            (r'(.+?)隐藏身份', r'\1的真实身份'),
            (r'(.+?)觉醒', r'\1的觉醒时刻'),
        ]

        for pattern, replacement in hook_patterns:
            match = re.search(pattern, clean_idea)
            if match:
                return re.sub(pattern, replacement, clean_idea)

        # 如果没有匹配，返回前20个字符
        return clean_idea[:20] + "..." if len(clean_idea) > 20 else clean_idea

    def generate_project_brief(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成项目简报"""
        theme_code = validated_data.get('theme', 'mixed-theme')
        episode_count = validated_data.get('episode_count', 80)

        # 计算预估时间（分钟）
        estimated_runtime = episode_count * validated_data.get('episode_duration', 2)

        # 生成项目代号
        project_code = f"SF-{theme_code.upper()[:3]}-{episode_count}E"

        brief = {
            'project_code': project_code,
            'project_name': f"{self.THEME_CODES.get(theme_code, '短剧')}项目",
            'theme_code': theme_code,
            'theme_name': self.THEME_CODES.get(theme_code, '混合题材'),
            'core_idea': validated_data.get('core_idea', ''),
            'episode_count': episode_count,
            'episode_duration': validated_data.get('episode_duration', 2),
            'estimated_runtime': estimated_runtime,
            'format_variant': validated_data.get('format_variant', 'B'),
            'target_platform': validated_data.get('target_platform', '抖音/快手'),
            'target_audience': validated_data.get('target_audience', '25-45岁都市女性'),
            'core_hook': validated_data.get('core_hook') or self.extract_hook_from_idea(
                validated_data.get('core_idea', '')
            ),
            'reference_work': validated_data.get('reference_work', ''),
            'budget_level': validated_data.get('budget_level', '中高端网剧标准'),
            'creation_timestamp': self._get_timestamp(),
        }

        return brief

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行节点1：信息收集

        输入:
            context.inputs: 用户提交的原始输入

        处理:
            1. 验证输入
            2. 提取核心钩子
            3. 生成项目简报

        输出:
            project_brief: 项目简报字典
        """
        inputs = context.get('inputs', {})

        # 步骤1：验证输入
        validation_result = self.validate_inputs(inputs)
        if not validation_result['valid']:
            context['errors'] = context.get('errors', []) + validation_result['errors']
        validated_data = validation_result['data']

        # 步骤2：生成项目简报
        brief = self.generate_project_brief(validated_data)

        # 步骤3：生成下一步需要的参数
        next_params = {
            'theme_code': brief['theme_code'],
            'theme_name': brief['theme_name'],
            'episode_count': brief['episode_count'],
            'core_idea': brief['core_idea'],
            'core_hook': brief['core_hook'],
        }

        # 更新上下文
        context['project_brief'] = brief
        context['next_params'] = next_params
        context['current_node'] = self.index

        return context

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
