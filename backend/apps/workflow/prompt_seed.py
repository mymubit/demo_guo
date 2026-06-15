# -*- coding: utf-8 -*-
"""融合节点 LLM 提示词 SSOT 默认值（空表示由 prompt_builder 自动生成）。"""

DEFAULT_USER_TEMPLATE = (
    "请根据以下上游产物生成符合 Schema 的 JSON（只输出 JSON，无 markdown）：\n\n"
    "上游数据：\n{upstream_json}"
)


def get_default_user_template() -> str:
    """运行时默认 user 模板；节点级覆盖见 FusionPipelineNode.user_prompt_tpl。"""
    return DEFAULT_USER_TEMPLATE
