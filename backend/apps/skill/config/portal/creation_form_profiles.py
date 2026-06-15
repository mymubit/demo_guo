# -*- coding: utf-8 -*-
"""C 端创作入口 profile 种子默认值（运行时只读 DB；磁盘仅 import/seed 时合并写入）。"""

DEFAULT_SHOW = {
    "theme": True,
    "coreIdea": True,
    "outline": False,
    "novel": False,
    "referenceBlock": "hidden",
    "ipSequel": False,
    "projectParams": True,
    "audience": True,
}

DEFAULT_CREATION_ENTRY_PROFILES = {
    "from-scratch": {
        "summary": "从一句话创意出发，完整走主链创作流程。",
        "tag": "原创",
        "headline": "原创短剧",
        "description": "从一句话创意出发，7 项技能依次产出简报、结构、人物、大纲、剧本与质检。",
        "steps": ["选题材", "写创意", "确认简报", "技能流水线"],
        "iconKey": "sparkles",
        "pipelineHints": {
            "prefilledSteps": [],
            "caption": "完整 7 步：从创意简报到结构、人物、大纲、剧本与质检",
        },
        "requiresAdapt": False,
        "validation": {"requiredFields": {}},
        "show": dict(DEFAULT_SHOW),
    },
    "from-outline": {
        "summary": "已有分集大纲，跳过创意环节，从结构规划起扩写。",
        "tag": "扩写",
        "headline": "大纲扩写",
        "description": "已有分集大纲，跳过创意环节，直接从结构规划技能开始扩写。",
        "steps": ["粘贴大纲", "补全参数", "确认简报", "技能流水线"],
        "iconKey": "fileText",
        "pipelineHints": {
            "prefilledSteps": [1],
            "caption": "第 1 步由你的大纲预填，从第 2 步结构规划起扩写",
        },
        "requiresAdapt": False,
        "validation": {"requiredFields": {"outline_text": {"minLength": 30}}},
        "show": {**DEFAULT_SHOW, "coreIdea": False, "outline": True},
    },
    "from-reference": {
        "summary": "对标热门短剧叙事节奏与情绪曲线，走完整技能流水线。",
        "tag": "风格",
        "headline": "风格对标",
        "description": "对标热门短剧叙事节奏与情绪曲线，走完整技能流水线生成原创剧本。",
        "steps": ["选题材", "写创意", "确认简报", "技能流水线"],
        "iconKey": "film",
        "pipelineHints": {
            "prefilledSteps": [],
            "caption": "风格对标思路写入简报后，走完整主链",
        },
        "requiresAdapt": True,
        "validation": {"requiredFields": {"reference_work": {"minLength": 10}}},
        "show": dict(DEFAULT_SHOW),
    },
    "ip-sequel": {
        "summary": "在既有 IP 世界观下创作续作/前传/衍生，须声明约束规则。",
        "tag": "IP",
        "headline": "IP 续作",
        "description": "在既有 IP 世界观下创作续作/前传/衍生，须声明约束规则。",
        "steps": ["IP 约束", "选题材", "确认简报", "技能流水线"],
        "iconKey": "users",
        "pipelineHints": {
            "prefilledSteps": [],
            "caption": "IP 约束写入简报后，走完整主链",
        },
        "requiresAdapt": True,
        "validation": {"requiredFields": {"ip_keep_rules": {"minLength": 10}}},
        "show": {**DEFAULT_SHOW, "ipSequel": True},
    },
    "novel-adaptation": {
        "summary": "粘贴小说原文，技能链自动拆解并改编为分集短剧剧本。",
        "tag": "改编",
        "headline": "网文改编",
        "description": "上传或粘贴小说正文，技能链自动拆解章节并改编为分集短剧剧本。",
        "steps": ["上传小说", "选题材与集数", "章节拆解", "技能流水线"],
        "iconKey": "bookOpen",
        "pipelineHints": {
            "prefilledSteps": [1],
            "caption": "第 1 步由小说原文预填，后续自动拆解改编",
        },
        "requiresAdapt": True,
        "validation": {"requiredFields": {"novel_text": {"minLength": 100}}},
        "show": {
            **DEFAULT_SHOW,
            "coreIdea": False,
            "novel": True,
            "referenceBlock": "hidden",
            "audience": False,
        },
    },
}
