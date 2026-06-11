# -*- coding: utf-8 -*-
"""
节点7：输出交付节点
整合所有产物 → 多格式输出 → 预渲染HTML → 数字水印
"""
import hashlib
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Node7Export:
    """节点7：输出交付 - 整合产物并生成可交付文件"""

    index: int = 7
    name: str = "输出交付"
    description: str = "多格式导出 + 数字水印 + 生成分享链接"

    # 目录结构
    DIRECTORY_STRUCTURE = {
        'root': 'drama-{project_code}',
        'readme': 'README.md',
        'manifest': 'project-manifest.json',
        'project_brief': '01-项目简报',
        'structure': '02-结构规划',
        'characters': '03-人物圣经',
        'outline': '04-分集大纲',
        'scripts': '05-完整剧本',
        'review': '06-质量报告',
        'extras': '07-附加材料',
    }

    def generate_project_readme(self, context: Dict[str, Any]) -> str:
        """生成项目README"""
        brief = context.get('project_brief', {})
        review = context.get('review', {})

        lines = []
        lines.append(f"# {brief.get('project_name', '短剧剧本')} - 项目说明")
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('## 📋 基本信息')
        lines.append('')
        lines.append(f"| 项目代号 | {brief.get('project_code', 'N/A')} |")
        lines.append(f"| 题材 | {brief.get('theme_name', '')} |")
        lines.append(f"| 集数 | {brief.get('episode_count', 0)}集 × {brief.get('episode_duration', 2)}分钟 |")
        lines.append(f"| 目标平台 | {brief.get('target_platform', '')} |")
        lines.append(f"| 目标受众 | {brief.get('target_audience', '')} |")
        lines.append(f"| 预算级别 | {brief.get('budget_level', '')} |")
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('## 💡 核心创意')
        lines.append('')
        lines.append(brief.get('core_idea', ''))
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('## ⭐ 质量评分')
        lines.append('')
        lines.append(f"- **综合评分**：{review.get('overall_score', 'N/A')}分（{review.get('grade', 'N/A')}级）")
        lines.append(f"- **格式评分**：{review.get('dimension_scores', {}).get('format', 'N/A')}分")
        lines.append(f"- **节奏评分**：{review.get('dimension_scores', {}).get('rhythm', 'N/A')}分")
        lines.append(f"- **内容评分**：{review.get('dimension_scores', {}).get('content', 'N/A')}分")
        lines.append(f"- **制作可行性**：{review.get('dimension_scores', {}).get('production', 'N/A')}分")
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('## 📁 文件清单')
        lines.append('')
        lines.append('- `01-项目简报/` - 项目基本信息与简报')
        lines.append('- `02-结构规划/` - 6阶段架构与情绪曲线')
        lines.append('- `03-人物圣经/` - 完整角色设定')
        lines.append('- `04-分集大纲/` - 每集梗概与钩子设计')
        lines.append('- `05-完整剧本/` - 完整剧本正文')
        lines.append('- `06-质量报告/` - 审查报告与改进建议')
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append(f'*本项目由 ScriptForge AI 自动生成 | 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*')

        return '\n'.join(lines)

    def generate_markdown_export(self, context: Dict[str, Any]) -> Dict[str, str]:
        """生成Markdown格式输出"""
        brief = context.get('project_brief', {})
        structure = context.get('structure', {})
        characters = context.get('characters', {})
        outlines = context.get('outlines', {})
        scripts_data = context.get('scripts', {})
        review = context.get('review', {})

        scripts = scripts_data.get('episodes', [])
        lines = []

        # 标题
        lines.append(f"# {brief.get('project_name', '短剧剧本')}")
        lines.append('')
        lines.append(f"**题材**：{brief.get('theme_name', '')}")
        lines.append(f"**集数**：{brief.get('episode_count', 0)}集 × {brief.get('episode_duration', 2)}分钟")
        lines.append(f"**一句话创意**：{brief.get('core_idea', '')}")
        lines.append(f"**综合评分**：{review.get('overall_score', 'N/A')}分（{review.get('grade', 'N/A')}级）")
        lines.append('')
        lines.append('---')
        lines.append('')

        # 人物设定
        lines.append('## 人物设定')
        lines.append('')
        for char in characters.get('all_characters', []):
            lines.append(f"### {char.get('name', '')}（{char.get('role', '')}）")
            lines.append(f"- **原型**：{char.get('archetype', '')}")
            lines.append(f"- **性格**：{char.get('personality', '')}")
            lines.append(f"- **目标**：{char.get('goal', '')}")
            lines.append(f"- **角色弧线**：{char.get('character_arc', '')}")
            if char.get('representative_lines'):
                lines.append(f"- **代表台词**：")
                for line in char.get('representative_lines', [])[:2]:
                    lines.append(f"  - {line}")
            lines.append('')

        lines.append('---')
        lines.append('')

        # 分集大纲
        lines.append('## 分集大纲')
        lines.append('')
        for outline in outlines.get('episodes', [])[:30]:  # 最多展示前30集
            lines.append(f"**{outline.get('title', '')}**：{outline.get('summary', '')}")
            if outline.get('is_reversal'):
                lines.append(f"  🎬 **{outline.get('reversal_type', '反转')}**")
            lines.append('')

        if outlines.get('total_episodes', 0) > 30:
            lines.append(f'*...共{outlines.get("total_episodes", 0)}集，此处展示前30集...*')
            lines.append('')

        lines.append('---')
        lines.append('')

        # 完整剧本
        lines.append('## 完整剧本')
        lines.append('')
        for script in scripts:
            lines.append(script.get('full_script_text', ''))
            lines.append('')

        lines.append('---')
        lines.append('')

        # 质量审查
        lines.append('## 质量审查')
        lines.append('')
        lines.append(f"- 格式评分：{review.get('dimension_scores', {}).get('format', '-')}分")
        lines.append(f"- 节奏评分：{review.get('dimension_scores', {}).get('rhythm', '-')}分")
        lines.append(f"- 内容评分：{review.get('dimension_scores', {}).get('content', '-')}分")
        lines.append(f"- 制作可行性：{review.get('dimension_scores', {}).get('production', '-')}分")
        lines.append(f"- 综合评分：{review.get('overall_score', '-')}分（{review.get('grade', '')}级）")
        lines.append('')
        lines.append(f'*生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | ScriptForge AI*')

        return {
            'full_markdown': '\n'.join(lines),
            'word_count': len('\n'.join(lines)),
        }

    def generate_preview_html(self, context: Dict[str, Any]) -> str:
        """生成预览用HTML片段（前端直接展示）"""
        brief = context.get('project_brief', {})
        characters = context.get('characters', {})
        scripts_data = context.get('scripts', {})
        review = context.get('review', {})

        scripts = scripts_data.get('episodes', [])

        html_parts = []
        html_parts.append('<div class="sf-script-result">')

        # 标题区
        html_parts.append(f'''
        <div class="sf-header">
            <h1 class="sf-title">{brief.get("project_name", "短剧剧本")}</h1>
            <div class="sf-meta">
                <span class="sf-tag">{brief.get("theme_name", "")}</span>
                <span class="sf-tag">{brief.get("episode_count", 0)}集 × {brief.get("episode_duration", 2)}分钟</span>
                <span class="sf-score">评分 {review.get("overall_score", "-")}分</span>
            </div>
            <p class="sf-idea">💡 {brief.get("core_idea", "")}</p>
        </div>
        ''')

        # 人物设定区
        html_parts.append('<div class="sf-section">')
        html_parts.append('<h2>人物设定</h2>')
        html_parts.append('<div class="sf-characters">')

        for char in characters.get('all_characters', [])[:4]:
            html_parts.append(f'''
            <div class="sf-character-card">
                <div class="sf-char-name">{char.get('name', '')}</div>
                <div class="sf-char-role">{char.get('role', '')}</div>
                <div class="sf-char-archetype">{char.get('archetype', '')}</div>
                <div class="sf-char-personality">{char.get('personality', '')}</div>
            </div>
            ''')

        html_parts.append('</div>')
        html_parts.append('</div>')

        # 剧本正文区
        html_parts.append('<div class="sf-section">')
        html_parts.append('<h2>剧本正文</h2>')
        html_parts.append('<div class="sf-episodes">')

        # 只展示前5集，其余折叠
        for i, script in enumerate(scripts[:5]):
            html_parts.append(f'''
            <div class="sf-episode">
                <h3>{script.get('title', '')}</h3>
                <div class="sf-ep-content">{script.get('full_script_text', '').replace(chr(10), '<br/>')}</div>
            </div>
            ''')

        if len(scripts) > 5:
            html_parts.append(f'''
            <div class="sf-collapsed-note">
                <p>...共{len(scripts)}集，此处展示前5集预览</p>
                <p>下载完整剧本查看全部内容</p>
            </div>
            ''')

        html_parts.append('</div>')
        html_parts.append('</div>')

        # 评分区
        html_parts.append('<div class="sf-section">')
        html_parts.append('<h2>质量审查</h2>')
        html_parts.append('<div class="sf-review">')

        dim_scores = review.get('dimension_scores', {})
        for key, name in [('format', '格式'), ('rhythm', '节奏'), ('content', '内容'), ('production', '制作可行性')]:
            score = dim_scores.get(key, 0)
            html_parts.append(f'''
            <div class="sf-score-item">
                <span class="sf-score-label">{name}</span>
                <div class="sf-score-bar" style="width: {score}%"></div>
                <span class="sf-score-value">{score}分</span>
            </div>
            ''')

        html_parts.append(f'''
            <div class="sf-overall-score">
                综合评分：{review.get('overall_score', '-')}分（{review.get('grade', '')}级）
            </div>
        ''')
        html_parts.append('</div>')
        html_parts.append('</div>')

        html_parts.append('</div>')  # sf-script-result

        return '\n'.join(html_parts)

    def embed_watermark(self, content: str, user_id: str, project_id: str) -> str:
        """在内容中嵌入数字水印"""
        import base64
        import secrets

        # 生成水印信息
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        watermark_data = f"{user_id}|{project_id}|{timestamp}"

        # 生成随机偏移量
        offset = secrets.randbelow(1000) + 500

        # 计算水印的插入位置（每隔一定字符插入一小段）
        watermark_bytes = base64.b64encode(watermark_data.encode()).decode()
        chunk_size = 4  # 每4个字符一段

        # 将水印分段插入内容
        watermarked = []
        wm_idx = 0

        for i, char in enumerate(content):
            watermarked.append(char)
            # 每100个字符插入一段水印
            if (i + 1) % 100 == 0 and wm_idx < len(watermark_bytes):
                chunk = watermark_bytes[wm_idx:wm_idx + chunk_size]
                # 使用零宽字符插入（不可见）
                watermarked.append('\u200B')  # Zero Width Space
                watermarked.append(chunk)
                watermarked.append('\u200B')
                wm_idx += chunk_size

        return ''.join(watermarked)

    def generate_export_package(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成完整的导出包"""
        brief = context.get('project_brief', {})
        user_id = context.get('user_id', 'anonymous')
        project_id = context.get('project_id', 'unknown')

        # 生成各部分内容
        md_export = self.generate_markdown_export(context)
        preview_html = self.generate_preview_html(context)
        readme = self.generate_project_readme(context)

        # 嵌入水印
        watermarked_markdown = self.embed_watermark(
            md_export['full_markdown'],
            str(user_id),
            str(project_id)
        )

        # 计算文件大小
        from sys import getsizeof
        markdown_size = getsizeof(watermarked_markdown.encode('utf-8'))
        html_size = getsizeof(preview_html.encode('utf-8'))

        return {
            'project_code': brief.get('project_code', ''),
            'project_name': brief.get('project_name', ''),
            'files': {
                'readme.md': {
                    'content': readme,
                    'size': getsizeof(readme.encode('utf-8')),
                },
                'full_script.md': {
                    'content': watermarked_markdown,
                    'size': markdown_size,
                    'watermarked': True,
                },
                'preview.html': {
                    'content': preview_html,
                    'size': html_size,
                },
            },
            'total_files': 3,
            'total_size': markdown_size + html_size,
            'export_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行节点7：输出交付

        输入:
            context: 所有上游节点的数据

        处理:
            1. 整合所有产物
            2. 生成多格式文件
            3. 预渲染HTML
            4. 嵌入数字水印
            5. 生成交付清单

        输出:
            export: 完整的交付包
        """
        brief = context.get('project_brief', {})
        scripts_data = context.get('scripts', {})
        review = context.get('review', {})

        # 生成导出包
        export_package = self.generate_export_package(context)

        # 生成最终结果摘要
        summary = {
            'project_name': brief.get('project_name', ''),
            'theme_name': brief.get('theme_name', ''),
            'episode_count': brief.get('episode_count', 0),
            'format_variant': brief.get('format_variant', 'B'),
            'overall_score': review.get('overall_score', 0),
            'grade': review.get('grade', ''),
            'passed': review.get('passed', False),
            'total_words': scripts_data.get('total_words', 0),
            'total_files': export_package['total_files'],
            'total_size': export_package['total_size'],
            'export_timestamp': export_package['export_timestamp'],
        }

        result = {
            'summary': summary,
            'export_package': export_package,
            'preview_html': export_package['files']['preview.html']['content'],
            'full_markdown': export_package['files']['full_script.md']['content'],
            'readme': export_package['files']['readme.md']['content'],
            'rendered_html': export_package['files']['preview.html']['content'],
            'estimated_time_minutes': self._estimate_time(),
        }

        # 更新上下文
        context['export'] = result
        context['final_result'] = summary
        context['current_node'] = self.index
        context['status'] = 'completed'

        return context

    def _estimate_time(self) -> int:
        """估算该节点执行时间（分钟）"""
        return 10  # 通常5-10分钟
