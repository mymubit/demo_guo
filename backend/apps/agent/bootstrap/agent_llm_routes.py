# -*- coding: utf-8 -*-
"""
LLM 路由种子 — drama.* 新体系。

旧的 brief/structure/outline/script 等路由配置已移除。
drama.* 角色的 LLM 路由由 seed_drama_skills 命令创建（在 AgentLlmRouteConfig 表中）。
此文件仅保留接口兼容性。
"""
from __future__ import annotations

from typing import Any, Dict, List

# drama.* 角色的参考路由配置（由 seed_drama_skills 在 AgentLlmRouteConfig 中创建）
# ROUTE_SEED 已由 seed_drama_skills 直接管理，此处仅作参考
# 此处仅作参考，实际路由配置通过 Admin 界面或 seed_drama_skills 管理
DRAMA_DEFAULT_LLM_ROUTES: List[Dict[str, Any]] = [
    # 高强度创作角色（需要强推理模型）
    {"route_key": "drama.plot-architect", "display_name": "情节架构师", "max_tokens": 16000, "sort_order": 302},
    {"route_key": "drama.script-writer", "display_name": "剧本执笔师", "max_tokens": 16000, "sort_order": 401},
    {"route_key": "drama.quality-reporter", "display_name": "质量报告官", "max_tokens": 8000, "sort_order": 504},
    {"route_key": "drama.compliance-guard", "display_name": "合规守卫", "max_tokens": 8000, "sort_order": 801},

    # 中等强度角色
    {"route_key": "drama.character-designer", "display_name": "人设设计师", "max_tokens": 10000, "sort_order": 202},
    {"route_key": "drama.world-architect", "display_name": "世界架构师", "max_tokens": 8000, "sort_order": 201},
    {"route_key": "drama.dialogue-expert", "display_name": "对白专家", "max_tokens": 12000, "sort_order": 402},
    {"route_key": "drama.script-editor", "display_name": "修稿师", "max_tokens": 16000, "sort_order": 601},

    # 轻量角色（适合轻量快速模型）
    {"route_key": "drama.formatter", "display_name": "格式规范师", "max_tokens": 10000, "sort_order": 603},
    {"route_key": "drama.word-governor", "display_name": "字数治理官", "max_tokens": 6000, "sort_order": 604},
    {"route_key": "drama.delivery-packer", "display_name": "交付打包官", "max_tokens": 20000, "sort_order": 802},
]
