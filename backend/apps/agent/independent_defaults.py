# -*- coding: utf-8 -*-
"""
Drama Skills 36个角色定义。

主入口：apps.drama.defaults.DRAMA_ROLE_DEFAULTS
种入命令：python manage.py seed_drama_skills
"""
from __future__ import annotations

from typing import Any, Dict, List


def get_drama_agent_defaults() -> List[Dict[str, Any]]:
    """获取 drama.* 全部36角色定义。"""
    from apps.drama.defaults import DRAMA_FAST_TRACK_ROLES, DRAMA_ROLE_DEFAULTS

    return [
        {
            "agent_id": role["agent_id"],
            "name": role["name"],
            "name_zh": role["name_zh"],
            "description": role["description"],
            "workspace_order": role["workspace_order"],
            "default_output_artifact_key": role["default_output_artifact_key"],
            "input_contract": role.get("input_contract") or {},
            "output_contract": role.get("output_contract") or {},
            "runtime_policy": role.get("runtime_policy") or {},
            "enabled": True,
            "ui_schema": {
                "dept": role["dept"],
                "is_fast_track": role["agent_id"] in DRAMA_FAST_TRACK_ROLES,
            },
        }
        for role in DRAMA_ROLE_DEFAULTS
    ]


DEFAULT_SYSTEM_PROMPT = (
    "你是 ScriptForge Drama Skills 的专业短剧创作 Agent。"
    "基于输入中的项目字段、已有产物与知识规则进行专业创作；"
    "必须输出一个合法 JSON 对象，遵循对应 schema，不输出 Markdown、解释或额外文本。"
)

DEFAULT_USER_PROMPT_TEMPLATE = """请执行 {{ agent.name_zh }}。

项目字段：
{{ project }}

已有产物：
{{ artifacts }}

知识与规则（Tier1-4）：
{{ knowledge }}

运行参数：
{{ params }}
"""

AGENT_NAME_ZH_BY_ID: Dict[str, str] = {
    "drama.topic-planner": "选题策划官",
    "drama.world-architect": "世界架构师",
    "drama.character-designer": "人设设计师",
    "drama.plot-architect": "情节架构师",
    "drama.script-writer": "剧本执笔师",
    "drama.script-reviewer": "审稿官",
    "drama.quality-reporter": "质量报告官",
    "drama.compliance-guard": "合规守卫",
    "drama.market-analyst": "市场分析师",
    "drama.narrative-engineer": "叙事工程师",
    "drama.polish-master": "精修大师",
    "drama.production-pack": "制作发行师",
}
