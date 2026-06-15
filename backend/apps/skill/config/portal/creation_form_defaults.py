# -*- coding: utf-8 -*-
"""创作表单 Catalog 代码种子 — 运行时只读 DB；磁盘仅 import 引导。"""

VARIANT_LETTER_MAP = {"A": "variant-a", "B": "variant-b", "C": "variant-c", "D": "variant-d"}
LETTER_FROM_VARIANT = {v: k for k, v in VARIANT_LETTER_MAP.items()}

DEFAULT_EPISODE_SETTINGS = {
    "min": 20,
    "max": 200,
    "step": 10,
    "default": 80,
    "presets": [20, 40, 60, 80, 100, 120, 150, 200],
    "durationMinutes": 2,
}

DEFAULT_PLATFORMS = [
    {"key": "douyin", "name": "抖音", "description": ""},
]

DEFAULT_BUDGET_LEVELS = [
    {"key": "low", "name": "低预算", "description": ""},
    {"key": "medium", "name": "中预算", "description": ""},
    {"key": "high", "name": "高预算", "description": ""},
]

DEFAULT_CREATION_ENTRIES = [
    {"key": "from-scratch", "name": "从零创作"},
    {"key": "from-outline", "name": "已有大纲"},
    {"key": "from-reference", "name": "参考作品改编"},
    {"key": "ip-sequel", "name": "IP 续作"},
    {"key": "novel-adaptation", "name": "小说改编"},
]

DEFAULT_FORMAT_VARIANTS = [
    {
        "key": "B",
        "schemaKey": "variant-b",
        "name": "行业通用版",
        "description": "",
    },
]

DEFAULT_FORMAT_VARIANT_SCHEMA = "variant-b"

CREATION_ENTRY_LABEL_FALLBACK = {
    "from-scratch": "从零创作",
    "from-outline": "已有大纲",
    "from-reference": "参考作品改编",
    "ip-sequel": "IP 续作",
    "novel-adaptation": "小说改编",
}
