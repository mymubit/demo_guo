# -*- coding: utf-8 -*-
"""LLM Provider 初始化预设 — 仅 setup_volcano_agent_llm 等命令使用。"""

# drama.* 新体系 LLM 预设（建议按角色重要性配置不同模型）
DRAMA_PRESET_KEYS: dict[str, str] = {
    # 高强度创作角色 - 推荐强推理模型
    "drama.series-architect": "ark-deepseek-v4-flash",
    "drama.episode-designer": "ark-deepseek-v4-flash",
    "drama.script-writer": "ark-deepseek-v4-flash",
    "drama.script-scorer": "ark-deepseek-v4-flash",
    "drama.compliance-guard": "ark-deepseek-v4-flash",
    # 中等角色 - 通用模型
    "drama.topic-director": "ark-deepseek-v4-flash",
    "drama.character-relations": "ark-deepseek-v4-flash",
    "drama.revision-master": "ark-deepseek-v4-flash",
    # 轻量角色 - 快速低成本模型
}

AGENT_PRESET_KEYS: dict[str, str] = {
    **DRAMA_PRESET_KEYS,
    "ai_field": "doubao-seed-2.0-lite",
}

# 兼容旧名（已废弃，仅保留避免 import 报错）
NODE_PRESET_KEYS: dict[str, str] = {}  # 旧 node_structure 等已不再使用

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
