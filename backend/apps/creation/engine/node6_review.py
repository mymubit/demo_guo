# -*- coding: utf-8 -*-
"""
节点6：质量审查节点
四维评分系统（格式/节奏/内容/制作可行性） + 问题清单 + 改进建议
"""
import re
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class Node6Review:
    """节点6：质量审查 - 四维评分 + 问题清单"""

    index: int = 6
    name: str = "质量审查"
    description: str = "格式/节奏/内容/制作可行性四维评分"

    # 评分权重配置
    DEFAULT_WEIGHTS = {
        'format': 20,
        'rhythm': 40,
        'content': 20,
        'production': 20,
    }

    # 评分等级
    GRADE_THRESHOLDS = {
        'S': 90,
        'A': 80,
        'B': 70,
        'C': 60,
        'D': 0,
    }

    # 格式检查规则
    FORMAT_CHECK_RULES = [
        {
            'name': '场景标题格式',
            'pattern': r'△\s*\S+.*?(?:日|夜|晨|昏)',
            'description': '场景应包含位置和时间信息',
        },
        {
            'name': '对话格式',
            'pattern': r'^\S+：',
            'description': '对话行应包含角色名和冒号',
        },
        {
            'name': '动作标记',
            'pattern': r'△',
            'description': '场景动作描述应有△标记',
        },
    ]

    # 节奏检查规则
    RHYTHM_CHECK_RULES = [
        {
            'name': '钩子密度',
            'description': '每集应有明显的开头钩子',
            'threshold': 0.95,
        },
        {
            'name': '反转密度',
            'description': '应保持合理的反转频率',
            'threshold': 0.30,
        },
        {
            'name': '悬念结尾率',
            'description': '每集结尾应有悬念',
            'threshold': 0.90,
        },
    ]

    def check_format(self, scripts: List[Dict]) -> Dict[str, Any]:
        """检查剧本格式规范性"""
        total_episodes = len(scripts)
        passed_checks = []
        failed_checks = []

        # 检查每集剧本
        format_issues = []

        for script in scripts[:10]:  # 抽样检查前10集
            script_text = script.get('full_script_text', '')

            for rule in self.FORMAT_CHECK_RULES:
                pattern = rule['pattern']
                if not re.search(pattern, script_text):
                    format_issues.append({
                        'episode': script['episode'],
                        'rule': rule['name'],
                        'description': rule['description'],
                        'suggestion': f"第{script['episode']}集缺少{rule['name']}，建议补充",
                    })

        # 计算格式分数
        base_score = 85
        penalty = min(30, len(format_issues) * 2)  # 每个问题扣2分，最多扣30分
        format_score = base_score - penalty

        # 检查结果
        passed = len(format_issues) == 0
        passed_checks.append('格式基本规范') if passed else None

        return {
            'score': max(0, min(100, format_score)),
            'passed': passed,
            'issues': format_issues,
            'passed_checks': [c for c in passed_checks if c],
            'total_checks': len(self.FORMAT_CHECK_RULES),
        }

    def check_rhythm(self, scripts: List[Dict], outlines: List[Dict]) -> Dict[str, Any]:
        """检查剧本节奏"""
        total_episodes = len(scripts)
        rhythm_issues = []

        # 检查钩子密度
        episodes_with_hooks = sum(
            1 for outline in outlines
            if outline.get('hook', {}).get('hook_text')
        )
        hook_ratio = episodes_with_hooks / total_episodes if total_episodes > 0 else 0

        if hook_ratio < 0.90:
            rhythm_issues.append({
                'type': '钩子密度不足',
                'description': f'有钩子的集数占比{hook_ratio:.0%}，低于90%标准',
                'suggestion': '建议每集开头增加强钩子，吸引观众继续观看',
            })

        # 检查反转密度
        reversal_count = sum(1 for outline in outlines if outline.get('is_reversal', False))
        reversal_ratio = reversal_count / total_episodes if total_episodes > 0 else 0

        if reversal_ratio < 0.25:
            rhythm_issues.append({
                'type': '反转密度偏低',
                'description': f'反转集数占比{reversal_ratio:.0%}，建议提升至30%以上',
                'suggestion': '在剧情关键节点增加反转，提升观众期待感',
            })

        # 检查场景数量
        scenes_per_episode_avg = sum(s.get('scenes_count', 0) for s in scripts) / total_episodes if scripts else 0
        if scenes_per_episode_avg > 4:
            rhythm_issues.append({
                'type': '场景过多',
                'description': f'平均每集{scenes_per_episode_avg:.1f}个场景，偏多',
                'suggestion': '竖屏剧建议每集2-3个场景，减少切换成本',
            })

        # 计算节奏分数
        base_score = 80
        penalty = min(25, len(rhythm_issues) * 5)
        rhythm_score = base_score - penalty

        return {
            'score': max(0, min(100, rhythm_score)),
            'hook_ratio': round(hook_ratio * 100, 1),
            'reversal_ratio': round(reversal_ratio * 100, 1),
            'avg_scenes_per_episode': round(scenes_per_episode_avg, 1),
            'issues': rhythm_issues,
        }

    def check_content(self, scripts: List[Dict], characters: Dict) -> Dict[str, Any]:
        """检查剧本内容质量"""
        content_issues = []

        # 检查角色台词一致性
        protagonist_name = characters.get('protagonist', {}).get('name', '')
        antagonist_name = characters.get('antagonist', {}).get('name', '')

        # 简单检查台词长度
        long_lines = []
        for script in scripts[:10]:
            script_text = script.get('full_script_text', '')
            for line in script_text.split('\n'):
                if '：' in line and len(line.split('：')[1].strip()) > 40:
                    long_lines.append({
                        'episode': script['episode'],
                        'line': line[:50] + '...' if len(line) > 50 else line,
                    })

        if len(long_lines) > 5:
            content_issues.append({
                'type': '台词过长',
                'description': f'发现{len(long_lines)}处超过40字的台词',
                'suggestion': '竖屏剧台词建议控制在30字以内，便于观众快速阅读',
                'examples': long_lines[:3],
            })

        # 检查情绪曲线
        emotion_intensities = [s.get('emotion_intensity', 5) for s in scripts]
        if emotion_intensities:
            # 检查是否单调或波动过大
            max_intensity = max(emotion_intensities)
            min_intensity = min(emotion_intensities)

            if max_intensity - min_intensity < 3:
                content_issues.append({
                    'type': '情绪曲线过于平稳',
                    'description': '全剧情绪波动较小，建议增加高潮设置',
                    'suggestion': '在关键节点（如第20/40/60/80集）设置更强的情绪爆点',
                })

        # 计算内容分数
        base_score = 78
        penalty = min(25, len(content_issues) * 5)
        content_score = base_score - penalty

        return {
            'score': max(0, min(100, content_score)),
            'issues': content_issues,
            'character_count': len(characters.get('all_characters', [])),
        }

    def check_production(self, scripts: List[Dict], format_variant: str) -> Dict[str, Any]:
        """检查制作可行性"""
        production_issues = []

        # 检查场景复杂度
        all_locations = set()
        for script in scripts:
            for scene in script.get('scenes', []):
                all_locations.add(scene.get('location', ''))

        # 场景过多可能导致拍摄成本上升
        if len(all_locations) > scripts.__len__() * 0.6:
            production_issues.append({
                'type': '场景过多',
                'description': f'全剧涉及{len(all_locations)}个不同场景，可能增加拍摄成本',
                'suggestion': '建议适当复用场景，降低制作难度',
            })

        # 检查格式变体适用性
        if format_variant == 'D':
            # 分镜版已包含制作信息
            pass
        else:
            # 检查是否需要补充制作信息
            production_issues.append({
                'type': '缺少分镜信息',
                'description': '当前格式未包含详细分镜信息',
                'suggestion': '如需专业制作，建议使用分镜版格式（Variant-D）',
            })

        # 计算制作分数
        base_score = 82
        penalty = min(20, len(production_issues) * 5)
        production_score = base_score - penalty

        return {
            'score': max(0, min(100, production_score)),
            'unique_locations': len(all_locations),
            'issues': production_issues,
        }

    def calculate_overall_score(
        self,
        scores: Dict[str, int],
        weights: Dict[str, int] = None
    ) -> Dict[str, Any]:
        """计算综合评分"""
        from apps.skill.config.portal.review_scoring import ReviewScoringService

        cfg = ReviewScoringService.resolve()
        weights = weights or cfg.get("weights") or self.DEFAULT_WEIGHTS
        grade_thresholds = cfg.get("grade_thresholds") or self.GRADE_THRESHOLDS
        total_weight = sum(weights.values())

        # 加权平均
        weighted_sum = sum(
            scores.get(key, 0) * weights.get(key, 0)
            for key in weights.keys()
        )
        overall = round(weighted_sum / total_weight, 1) if total_weight > 0 else 0

        # 确定等级
        grade = 'D'
        for g, threshold in sorted(grade_thresholds.items(), key=lambda x: x[1], reverse=True):
            if overall >= threshold:
                grade = g
                break

        # 判定是否通过
        pass_threshold = int(cfg.get("pass_threshold") or 70)
        passed = overall >= pass_threshold

        return {
            'overall_score': overall,
            'grade': grade,
            'passed': passed,
            'pass_threshold': pass_threshold,
            'weights_used': weights,
        }

    def generate_review_report(self, review_data: Dict) -> str:
        """生成审查报告"""
        lines = []
        lines.append('# 剧本质量审查报告')
        lines.append('')
        lines.append(f"**审查时间**：{review_data.get('timestamp', '')}")
        lines.append(f"**题材**：{review_data.get('theme_name', '')}")
        lines.append(f"**集数**：{review_data.get('total_episodes', 0)}集")
        lines.append(f"**格式**：{review_data.get('format_name', '')}")
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('## 综合评分')
        lines.append('')
        lines.append(f"| 维度 | 得分 | 权重 |")
        lines.append(f"|------|------|------|")

        dimension_scores = review_data.get('dimension_scores', {})
        weights = review_data.get('weights_used', self.DEFAULT_WEIGHTS)

        for dim, score in dimension_scores.items():
            dim_name = {'format': '格式', 'rhythm': '节奏', 'content': '内容', 'production': '制作'}.get(dim, dim)
            weight = weights.get(dim, 0)
            lines.append(f"| {dim_name} | {score}分 | {weight}% |")

        lines.append('')
        lines.append(f"**综合评分**：{review_data.get('overall_score', 0)}分（{review_data.get('grade', 'D')}级）")
        lines.append(f"**审查结论**：{'✅ 通过' if review_data.get('passed') else '⚠️ 需修改'}")
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('## 问题清单')

        all_issues = review_data.get('all_issues', [])
        if all_issues:
            lines.append('')
            for i, issue in enumerate(all_issues, 1):
                lines.append(f"### {i}. {issue.get('type', '问题')}")
                lines.append(f"- **描述**：{issue.get('description', '')}")
                lines.append(f"- **建议**：{issue.get('suggestion', '')}")
                lines.append('')
        else:
            lines.append('🎉 未发现重大问题！')

        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append(f'*本报告由 ScriptForge AI 自动生成*')

        return '\n'.join(lines)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行节点6：质量审查

        输入:
            context.project_brief: 项目简报
            context.scripts: 完整剧本
            context.characters: 角色体系
            context.outlines: 分集大纲

        处理:
            1. 格式检查
            2. 节奏检查
            3. 内容检查
            4. 制作可行性检查
            5. 计算综合评分

        输出:
            review: 质量审查报告
        """
        from datetime import datetime

        brief = context.get('project_brief', {})
        scripts_data = context.get('scripts', {})
        characters = context.get('characters', {})
        outlines_data = context.get('outlines', {})

        scripts = scripts_data.get('episodes', [])
        outlines = outlines_data.get('episodes', [])
        format_variant = brief.get('format_variant', 'B')

        # 四维检查
        format_result = self.check_format(scripts)
        rhythm_result = self.check_rhythm(scripts, outlines)
        content_result = self.check_content(scripts, characters)
        production_result = self.check_production(scripts, format_variant)

        # 收集所有问题
        all_issues = []
        for issue in format_result.get('issues', []):
            issue['dimension'] = '格式'
            all_issues.append(issue)
        for issue in rhythm_result.get('issues', []):
            issue['dimension'] = '节奏'
            all_issues.append(issue)
        for issue in content_result.get('issues', []):
            issue['dimension'] = '内容'
            all_issues.append(issue)
        for issue in production_result.get('issues', []):
            issue['dimension'] = '制作'
            all_issues.append(issue)

        # 计算综合评分
        scores = {
            'format': format_result['score'],
            'rhythm': rhythm_result['score'],
            'content': content_result['score'],
            'production': production_result['score'],
        }

        overall_result = self.calculate_overall_score(scores)
        weights_used = overall_result.get("weights_used") or self.DEFAULT_WEIGHTS

        # 生成审查报告
        review_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'theme_code': brief.get('theme_code', ''),
            'theme_name': brief.get('theme_name', ''),
            'total_episodes': len(scripts),
            'format_variant': format_variant,
            'format_name': scripts_data.get('format_name', ''),
            'dimension_scores': scores,
            'weights_used': weights_used,
            'overall_score': overall_result['overall_score'],
            'grade': overall_result['grade'],
            'passed': overall_result['passed'],
            'pass_threshold': overall_result['pass_threshold'],
            'all_issues': all_issues,
        }

        review_report = self.generate_review_report(review_data)

        result = {
            'dimension_scores': scores,
            'overall_score': overall_result['overall_score'],
            'grade': overall_result['grade'],
            'passed': overall_result['passed'],
            'pass_threshold': overall_result['pass_threshold'],
            'issues': all_issues,
            'issue_count_by_dimension': {
                'format': len(format_result['issues']),
                'rhythm': len(rhythm_result['issues']),
                'content': len(content_result['issues']),
                'production': len(production_result['issues']),
            },
            'review_report': review_report,
            'recommendations': self._generate_recommendations(all_issues, overall_result),
            'estimated_time_minutes': self._estimate_time(len(scripts)),
        }

        context['review'] = result
        context['next_params'].update({
            'review': result,
        })
        context['current_node'] = self.index

        return context

    def _generate_recommendations(self, issues: List[Dict], overall_result: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if not overall_result['passed']:
            recommendations.append('建议根据问题清单进行针对性修改')

        if overall_result['overall_score'] >= 85:
            recommendations.append('剧本质量优秀，可以直接进入拍摄准备阶段')

        if any(i.get('dimension') == 'rhythm' for i in issues):
            recommendations.append('建议重点优化剧本节奏，增强观众黏性')

        if any(i.get('dimension') == 'format' for i in issues):
            recommendations.append('建议统一剧本格式，便于制作团队使用')

        return recommendations

    def _estimate_time(self, episode_count: int) -> int:
        """估算该节点执行时间（分钟）"""
        return max(30, min(60, episode_count // 2))
