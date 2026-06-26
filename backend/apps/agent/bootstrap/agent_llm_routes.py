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
    {"route_key": "drama.series-architect", "display_name": "全剧架构官", "max_tokens": 16000, "sort_order": 301},
    {"route_key": "drama.episode-designer", "display_name": "分集设计官", "max_tokens": 16000, "sort_order": 302},
    {"route_key": "drama.script-writer", "display_name": "剧本正文官", "max_tokens": 16000, "sort_order": 401},
    {"route_key": "drama.revision-master", "display_name": "剧本修订官", "max_tokens": 16000, "sort_order": 501},
    {"route_key": "drama.script-scorer", "display_name": "剧本评分官", "max_tokens": 8000, "sort_order": 601},
    {"route_key": "drama.compliance-guard", "display_name": "合规审查官", "max_tokens": 8000, "sort_order": 701},
    {"route_key": "drama.delivery-tool", "display_name": "宣发交付工具", "max_tokens": 12000, "sort_order": 801},

    # 中等强度角色
    {"route_key": "drama.topic-director", "display_name": "选题定调官", "max_tokens": 8000, "sort_order": 101},
    {"route_key": "drama.character-relations", "display_name": "人物关系官", "max_tokens": 10000, "sort_order": 202},

    # 轻量角色（适合轻量快速模型）
]
