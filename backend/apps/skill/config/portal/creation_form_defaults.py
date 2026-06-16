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
        "key": "A",
        "schemaKey": "variant-a",
        "name": "标准版（文档阅读友好）",
        "description": "场景与台词结构清晰，适合内部评审与文档阅读",
        "sceneHeading": "1-1 日 内 地点",
        "dialogueMarker": "**角色**(动作)：台词",
        "actionMarker": "**(描述)**",
    },
    {
        "key": "B",
        "schemaKey": "variant-b",
        "name": "行业通用版（拍摄组默认）",
        "description": "拍摄组最常用格式，平衡可读性与落地执行",
        "sceneHeading": "1-1 日 内 地点",
        "dialogueMarker": "角色：台词",
        "actionMarker": "△ 描述",
    },
    {
        "key": "C",
        "schemaKey": "variant-c",
        "name": "精简版（AI生成高速模式）",
        "description": "字段更少、生成更快，适合快速试稿",
        "sceneHeading": "场景一 地点 日",
        "dialogueMarker": "角色(动作)：台词",
        "actionMarker": "散文描述",
    },
    {
        "key": "D",
        "schemaKey": "variant-d",
        "name": "详细分镜版（S级精品剧拍摄）",
        "description": "含景别与运镜提示，适合精品短剧与 S 级拍摄",
        "sceneHeading": "1-1 日 内 地点 色温+声音",
        "dialogueMarker": "**角色**(动作)：台词",
        "actionMarker": "△ 详细描述+景别+运镜",
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
