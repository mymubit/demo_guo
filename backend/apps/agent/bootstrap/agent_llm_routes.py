# -*- coding: utf-8 -*-
"""Agent LLM 路由占位 — 仅 seed_defaults / setup 命令写入 AgentLlmRouteConfig。"""
from __future__ import annotations

from typing import Any

ROUTE_SEED: list[dict[str, Any]] = [
    {"route_key": "brief", "display_name": "BriefAgent", "max_tokens": 4096, "sort_order": 10},
    {"route_key": "world", "display_name": "WorldAgent", "max_tokens": 12288, "sort_order": 20},
    {"route_key": "character", "display_name": "CharacterAgent", "max_tokens": 16384, "sort_order": 30},
    {"route_key": "outline", "display_name": "OutlineAgent", "max_tokens": 8192, "sort_order": 35},
    {"route_key": "outline_framework", "display_name": "Outline 框架", "max_tokens": 8192, "sort_order": 40},
    {"route_key": "outline_episode", "display_name": "Outline 逐集", "max_tokens": 2560, "sort_order": 41},
    {"route_key": "script", "display_name": "ScriptAgent", "max_tokens": 6000, "sort_order": 45},
    {"route_key": "script_batch", "display_name": "Script 分批", "max_tokens": 6000, "sort_order": 50},
    {"route_key": "review", "display_name": "ReviewAgent", "max_tokens": 4096, "sort_order": 55},
    {"route_key": "score", "display_name": "ScoreAgent", "max_tokens": 4096, "sort_order": 56},
    {"route_key": "polish", "display_name": "PolishAgent", "max_tokens": 2048, "sort_order": 60},
    {"route_key": "insight", "display_name": "InsightAgent", "max_tokens": 2048, "sort_order": 70},
    {"route_key": "emotion_architect", "display_name": "EmotionArchitectAgent", "max_tokens": 4096, "sort_order": 72},
    {"route_key": "ai_field", "display_name": "AI 字段", "max_tokens": 1024, "sort_order": 80},
]

AUXILIARY_AGENT_ROUTE_KEYS = frozenset({"polish", "insight", "ai_field", "emotion_architect"})
