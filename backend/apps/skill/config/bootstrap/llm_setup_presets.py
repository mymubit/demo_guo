# -*- coding: utf-8 -*-
"""LLM Provider 初始化预设 — 仅 setup_volcano_agent_llm 等命令使用。"""

NODE_PRESET_KEYS: dict[str, str] = {
    "node-2-structure": "ark-deepseek-v4-flash",
    "node-3-character": "ark-deepseek-v4-flash",
    "node-4-outline": "ark-deepseek-v4-flash",
    "node-5-script": "glm-5",
}

AGENT_PRESET_KEYS: dict[str, str] = {
    "polish": "doubao-seed-2.0-lite",
    "insight": "doubao-seed-2.0-lite",
    "ai_field": "doubao-seed-2.0-lite",
}

NATIVE_PRESET_KEYS = frozenset({"glm-5", "glm-5-turbo"})

NATIVE_PRESET_CONFIG: dict[str, dict[str, str]] = {
    "glm-5": {
        "api_key_env": "ZHIPU_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model_env": "ZHIPU_GLM5_MODEL",
        "model_default": "glm-5",
    },
    "glm-5-turbo": {
        "api_key_env": "ZHIPU_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model_env": "ZHIPU_GLM5_TURBO_MODEL",
        "model_default": "glm-5-turbo",
    },
}

DEFAULT_ACTIVE_PRESET = "ark-deepseek-v4-flash"
