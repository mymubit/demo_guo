"""独立创作 Agent 默认定义。"""
from __future__ import annotations

from typing import Any, Dict, List


AGENT_DEFAULTS: List[Dict[str, Any]] = [
    {
        "agent_id": "adapt",
        "name": "Adapt Agent",
        "name_zh": "小说改编",
        "description": "将小说原文改编为短剧创作简报与改编元数据，供后续 Agent 使用。",
        "workspace_order": 0,
        "default_output_artifact_key": "adaptation_meta",
        "input_contract": {
            "project_fields": ["novel_text", "theme", "episode_count", "target_platform"],
            "required_artifacts": [],
            "optional_artifacts": ["project_brief"],
            "params": ["novel_text"],
        },
        "output_contract": {
            "artifacts": ["adaptation_meta", "project_brief"],
            "schema_version": "adaptation-meta.v1",
        },
        "runtime_policy": {"max_prompt_tokens": 40000, "max_completion_tokens": 12000, "overwrite_mode": "replace"},
        "enabled": True,
    },
    {
        "agent_id": "brief",
        "name": "Brief Agent",
        "name_zh": "立项简报",
        "description": "整理项目核心设定，输出可供后续 Agent 使用的创作简报。",
        "workspace_order": 1,
        "default_output_artifact_key": "project_brief",
        "input_contract": {
            "project_fields": ["theme", "core_idea", "episode_count", "format_variant", "audience", "reference_work"],
            "required_artifacts": [],
            "optional_artifacts": [],
        },
        "output_contract": {"artifacts": ["project_brief"], "schema_version": "project-brief.v1"},
        "runtime_policy": {"max_prompt_tokens": 20000, "max_completion_tokens": 8000, "overwrite_mode": "replace"},
    },
    {
        "agent_id": "structure",
        "name": "Structure Agent",
        "name_zh": "结构设定",
        "description": "基于立项简报生成六阶段结构、世界观与节奏设计。",
        "workspace_order": 2,
        "default_output_artifact_key": "structure_plan",
        "input_contract": {
            "project_fields": ["episode_count", "target_platform"],
            "required_artifacts": ["project_brief"],
            "optional_artifacts": ["reference_style_fingerprint"],
        },
        "output_contract": {"artifacts": ["structure_plan"], "schema_version": "structure-plan.v1"},
        "runtime_policy": {"max_prompt_tokens": 30000, "max_completion_tokens": 12000, "overwrite_mode": "replace"},
    },
    {
        "agent_id": "character",
        "name": "Character Agent",
        "name_zh": "人物小传",
        "description": "基于简报与结构生成主要人物、关系网和人物弧光。",
        "workspace_order": 3,
        "default_output_artifact_key": "character_bible",
        "input_contract": {
            "required_artifacts": ["project_brief", "structure_plan"],
            "optional_artifacts": [],
        },
        "output_contract": {"artifacts": ["character_bible"], "schema_version": "character-bible.v1"},
        "runtime_policy": {"max_prompt_tokens": 30000, "max_completion_tokens": 12000, "overwrite_mode": "replace"},
    },
    {
        "agent_id": "outline",
        "name": "Outline Agent",
        "name_zh": "分集大纲",
        "description": "基于简报、结构与人物生成全剧分集大纲。",
        "workspace_order": 4,
        "default_output_artifact_key": "series_outline",
        "input_contract": {
            "required_artifacts": ["project_brief", "structure_plan", "character_bible"],
            "optional_artifacts": [],
        },
        "output_contract": {"artifacts": ["series_outline"], "schema_version": "series-outline.v1"},
        "runtime_policy": {"max_prompt_tokens": 40000, "max_completion_tokens": 16000, "overwrite_mode": "replace"},
    },
    {
        "agent_id": "script",
        "name": "Script Agent",
        "name_zh": "剧本正文",
        "description": "按分集范围生成剧本正文，默认一次处理 1 到 3 集。",
        "workspace_order": 5,
        "default_output_artifact_key": "episode_scripts",
        "input_contract": {
            "required_artifacts": ["series_outline", "character_bible"],
            "optional_artifacts": ["structure_plan", "project_brief"],
            "params": ["episode_from", "episode_to", "overwrite"],
        },
        "output_contract": {"artifacts": ["episode_scripts"], "schema_version": "episode-scripts.v1"},
        "runtime_policy": {
            "max_prompt_tokens": 40000,
            "max_completion_tokens": 16000,
            "overwrite_mode": "merge",
            "max_episode_batch": 3,
        },
        "ui_schema": {
            "params": [
                {"key": "episode_from", "label": "起始集", "type": "number", "default": 1, "min": 1},
                {"key": "episode_to", "label": "结束集", "type": "number", "default": 3, "min": 1},
                {
                    "key": "overwrite",
                    "label": "写入模式",
                    "type": "select",
                    "default": "merge",
                    "options": [
                        {"value": "merge", "label": "合并（仅更新指定集数）"},
                        {"value": "replace", "label": "全量替换"},
                    ],
                },
            ]
        },
    },
    {
        "agent_id": "review",
        "name": "Review Agent",
        "name_zh": "质量审查",
        "description": "审查剧本结构、合规、连贯性与可拍性。",
        "workspace_order": 6,
        "default_output_artifact_key": "review_report",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
            "optional_artifacts": ["project_brief", "series_outline"],
        },
        "output_contract": {"artifacts": ["review_report"], "schema_version": "review-report.v1"},
        "runtime_policy": {"max_prompt_tokens": 40000, "max_completion_tokens": 12000, "overwrite_mode": "replace"},
    },
    {
        "agent_id": "score",
        "name": "Score Agent",
        "name_zh": "剧本评分",
        "description": "对剧本进行量化评分并输出改进建议。",
        "workspace_order": 7,
        "default_output_artifact_key": "script_score_report",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
            "optional_artifacts": ["review_report", "project_brief"],
        },
        "output_contract": {"artifacts": ["script_score_report"], "schema_version": "script-score-report.v1"},
        "runtime_policy": {"max_prompt_tokens": 40000, "max_completion_tokens": 8000, "overwrite_mode": "replace"},
    },
    {
        "agent_id": "marketing",
        "name": "Marketing Agent",
        "name_zh": "宣发物料",
        "description": "基于简报与剧本生成标题、卖点、短视频切片和投放素材。",
        "workspace_order": 8,
        "default_output_artifact_key": "marketing_kit",
        "input_contract": {
            "required_artifacts": ["project_brief", "episode_scripts"],
            "optional_artifacts": ["script_score_report"],
        },
        "output_contract": {"artifacts": ["marketing_kit"], "schema_version": "marketing-kit.v1"},
        "runtime_policy": {"max_prompt_tokens": 25000, "max_completion_tokens": 8000, "overwrite_mode": "replace"},
    },
    {
        "agent_id": "insight",
        "name": "Insight Agent",
        "name_zh": "洞察报告",
        "description": "输出题材、受众和市场洞察。",
        "workspace_order": 9,
        "default_output_artifact_key": "insight_report",
        "input_contract": {"required_artifacts": ["project_brief"], "optional_artifacts": ["episode_scripts"]},
        "output_contract": {"artifacts": ["insight_report"], "schema_version": "insight-report.v1"},
        "runtime_policy": {"max_prompt_tokens": 25000, "max_completion_tokens": 8000, "overwrite_mode": "replace"},
        "enabled": False,
    },
    {
        "agent_id": "polish",
        "name": "Polish Agent",
        "name_zh": "剧本润色",
        "description": "润色既有剧本正文并记录修改说明。",
        "workspace_order": 10,
        "default_output_artifact_key": "episode_scripts",
        "input_contract": {"required_artifacts": ["episode_scripts"], "optional_artifacts": ["review_report"]},
        "output_contract": {"artifacts": ["episode_scripts", "polish_log"], "schema_version": "polish-log.v1"},
        "runtime_policy": {"max_prompt_tokens": 40000, "max_completion_tokens": 16000, "overwrite_mode": "merge"},
        "enabled": False,
    },
]


DEFAULT_SYSTEM_PROMPT = (
    "你是 ScriptForge 的独立短剧创作 Agent。"
    "只能基于输入中的项目字段、已有 artifacts 与知识规则工作；"
    "必须输出一个合法 JSON 对象，不要输出 Markdown、解释或额外文本。"
)

DEFAULT_USER_PROMPT_TEMPLATE = """请执行 {{ agent.name_zh }}。

项目字段：
{{ project }}

已有产物：
{{ artifacts }}

知识与规则：
{{ knowledge }}

运行参数：
{{ params }}
"""

AGENT_NAME_ZH_BY_ID: Dict[str, str] = {
    item["agent_id"]: item["name_zh"] for item in AGENT_DEFAULTS if item.get("name_zh")
}
