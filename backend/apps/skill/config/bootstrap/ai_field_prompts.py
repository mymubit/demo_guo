# -*- coding: utf-8 -*-
"""创作页 AI 字段 Prompt 种子 — 仅 init/seed 命令写入 AiFieldPromptConfig。"""
from __future__ import annotations

from typing import Any

# 后台不展示：与主链节点能力重复，或 C 端尚未接入
ADMIN_HIDDEN_FIELD_KEYS = frozenset(
    {
        "ai.generate.worldview",
        "ai.generate.reference_work",
    }
)

AI_FIELD_DISPLAY_NAMES: dict[str, str] = {
    "ai.generate.core_idea": "核心创意",
    "ai.generate.audience": "目标受众",
    "ai.generate.reference_work": "参考作品",
    "ai.generate.worldview": "世界观设定",
    "ai.generate.inspiration_plan": "灵感策划",
    "ai.generate.pull_sheet": "拉片分析",
}


def resolve_ai_field_display_name(action_key: str, stored: str = "") -> str:
    """运营展示名：优先 DB 自定义名，否则用中文默认名。"""
    key = (action_key or "").strip()
    canonical = AI_FIELD_DISPLAY_NAMES.get(key, "")
    text = (stored or "").strip()
    if not text or text == key:
        return canonical or key
    slug = key.replace("ai.generate.", "")
    auto_variants = {
        key,
        slug,
        slug.replace("_", " "),
        f"AI·{slug.replace('_', ' ')}",
        f"AI-{slug.replace('_', '-')}",
        f"AI·{slug}",
    }
    if text in auto_variants:
        return canonical or text
    return text


DEFAULT_AI_FIELD_PROMPTS: dict[str, dict[str, Any]] = {
    "ai.generate.core_idea": {
        "display_name": AI_FIELD_DISPLAY_NAMES["ai.generate.core_idea"],
        "system_prompt": "你是短剧策划助手。只输出一段连续的中文梗概，不要标题、不要分条、不要 markdown。",
        "user_prompt_tpl": "题材：{theme}\n集数：{episode_count}\n请写一句 80–150 字的核心创意梗概。",
        "system_prompt_fallback": "",
        "response_json": False,
    },
    "ai.generate.audience": {
        "display_name": AI_FIELD_DISPLAY_NAMES["ai.generate.audience"],
        "system_prompt": (
            "你是短剧用户研究助手。严格按三行输出，不要 markdown、不要编号：\n"
            "年龄段：\n观影偏好：\n情绪诉求："
        ),
        "user_prompt_tpl": (
            "题材：{theme}\n创意：{core_idea}\n"
            "请写目标受众画像（每行一个字段，偏好用顿号分隔关键词，总 80–120 字）。"
        ),
        "system_prompt_fallback": "",
        "response_json": False,
    },
    "ai.generate.reference_work": {
        "display_name": AI_FIELD_DISPLAY_NAMES["ai.generate.reference_work"],
        "system_prompt": (
            "你是短剧对标分析助手。只输出 JSON 对象，格式："
            '{"items":[{"title":"作品名","note":"风格要点"}]}，共 2 项。'
            "不要 markdown，不要代码块，不要书名号。"
        ),
        "user_prompt_tpl": (
            "题材：{theme}\n创意：{core_idea}\n"
            "请推荐 2 个风格相近的参考短剧。"
        ),
        "system_prompt_fallback": (
            "你是短剧对标分析助手。严格输出两行，每行格式：作品名｜风格要点。"
            "不要 markdown，不要编号，不要书名号。"
        ),
        "response_json": True,
    },
    "ai.generate.worldview": {
        "display_name": AI_FIELD_DISPLAY_NAMES["ai.generate.worldview"],
        "system_prompt": "你是短剧世界观设计助手，只输出世界观设定摘要。",
        "user_prompt_tpl": "题材：{theme}\n创意：{core_idea}\n请写 80–120 字世界观设定。",
        "system_prompt_fallback": "",
        "response_json": False,
    },
    "ai.generate.inspiration_plan": {
        "display_name": AI_FIELD_DISPLAY_NAMES["ai.generate.inspiration_plan"],
        "system_prompt": (
            "你是短剧灵感策划师。必须严格按下面四行格式输出，每行以字段名开头、中文冒号结尾，"
            "不要 markdown 星号，不要 JSON：\n"
            "一句话梗概：\n核心冲突：\n情绪基调：\n前三集钩子："
        ),
        "user_prompt_tpl": (
            "题材：{theme}\n集数：{episode_count}\n"
            "已有梗概：{core_idea}\n"
            "请补全四行策划（每行一个字段，总字数 200 字内）。"
        ),
        "system_prompt_fallback": "",
        "response_json": False,
    },
    "ai.generate.pull_sheet": {
        "display_name": AI_FIELD_DISPLAY_NAMES["ai.generate.pull_sheet"],
        "system_prompt": "你是短剧拉片分析助手。",
        "user_prompt_tpl": "参考作品：{reference_work}\n创意：{core_idea}\n请输出拉片分析占位摘要（功能完善中）。",
        "system_prompt_fallback": "",
        "response_json": False,
    },
}
