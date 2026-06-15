# -*- coding: utf-8 -*-
"""火山方舟 Chat Completions 模型名解析（对齐官方：model = ep-xxx 或已开通 Model ID）。"""
from __future__ import annotations

import os
from typing import Optional

from apps.skill.llm.volcengine_config import VOLCANO_KEY_CODING_PLAN, VOLCANO_KEY_PAYG, is_volcano_host

# preset_key → settings / 环境变量名（推理接入点 ep-xxx）
PRESET_ENDPOINT_ENV: dict[str, str] = {
    "ark-deepseek-v4-flash": "VOLCANO_EP_DEEPSEEK_V4_FLASH",
    "ark-deepseek-v4-pro": "VOLCANO_EP_DEEPSEEK_V4_PRO",
    "doubao-seed-2.0-lite": "VOLCANO_EP_DOUBAO_LITE",
    "doubao-seed-2.0-pro": "VOLCANO_EP_DOUBAO_PRO",
    "ark-minimax-m2.7": "VOLCANO_EP_MINIMAX_M27",
}

# catalog model_name → env（无 preset 时的兜底）
MODEL_NAME_ENDPOINT_ENV: dict[str, str] = {
    "deepseek-v4-flash": "VOLCANO_EP_DEEPSEEK_V4_FLASH",
    "deepseek-v4-pro": "VOLCANO_EP_DEEPSEEK_V4_PRO",
    "doubao-seed-2.0-lite": "VOLCANO_EP_DOUBAO_LITE",
    "doubao-seed-2.0-pro": "VOLCANO_EP_DOUBAO_PRO",
    "minimax-m2.7": "VOLCANO_EP_MINIMAX_M27",
}


def is_volcano_endpoint_id(model: str) -> bool:
    return str(model or "").strip().lower().startswith("ep-")


def env_endpoint(env_var: str) -> str:
    from django.conf import settings

    return (getattr(settings, env_var, "") or os.getenv(env_var, "") or "").strip()


def resolve_volcano_chat_model(
    *,
    model: str,
    catalog_preset_key: str = "",
    volcano_key_type: str = "",
    base_url: str = "",
) -> str:
    """
    按火山官方 Chat API：按量付费优先使用推理接入点 ep-xxx 作为 model 字段。
    若 DB 存的是 Model ID，尝试从 VOLCANO_EP_* 环境变量解析到 ep。
    """
    raw = str(model or "").strip()
    if not raw:
        return raw

    key_type = (volcano_key_type or "").strip()
    if key_type == VOLCANO_KEY_CODING_PLAN:
        return raw
    if is_volcano_endpoint_id(raw):
        return raw
    if key_type and key_type != VOLCANO_KEY_PAYG:
        return raw
    if base_url and not is_volcano_host(base_url):
        return raw

    preset = str(catalog_preset_key or "").strip()
    env_name = PRESET_ENDPOINT_ENV.get(preset) or MODEL_NAME_ENDPOINT_ENV.get(raw.lower())
    if env_name:
        ep = env_endpoint(env_name)
        if ep:
            return ep
    return raw


def http_error_is_model_not_found(exc) -> bool:
    resp = getattr(exc, "response", None)
    if resp is None or getattr(resp, "status_code", None) != 404:
        return False
    text = (getattr(resp, "text", None) or "").lower()
    return (
        "invalidendpointornotfound" in text
        or "model.notfound" in text
        or "does not exist or you do not have access" in text
    )


def http_error_is_invalid_subscription(exc) -> bool:
    resp = getattr(exc, "response", None)
    if resp is None or getattr(resp, "status_code", None) != 400:
        return False
    text = (getattr(resp, "text", None) or "").lower()
    return "invalidsubscription" in text or "codingplan" in text
