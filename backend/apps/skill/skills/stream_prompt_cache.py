# -*- coding: utf-8 -*-
"""流式 Prompt 缓存（skill-agent/41 §5）。"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Optional, Tuple

from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_PREFIX = "skill_stream_prompt:"
DEFAULT_TTL = 3600


def _cache_key(payload: Dict[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return f"{CACHE_PREFIX}{digest}"


def get_cached_prompt(payload: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    key = _cache_key(payload)
    cached = cache.get(key)
    if isinstance(cached, dict):
        system_prompt = cached.get("system_prompt")
        user_prompt = cached.get("user_prompt")
        if system_prompt is not None and user_prompt is not None:
            return str(system_prompt), str(user_prompt)
    return None


def set_cached_prompt(payload: Dict[str, Any], system_prompt: str, user_prompt: str, *, ttl: int = DEFAULT_TTL) -> None:
    key = _cache_key(payload)
    cache.set(key, {"system_prompt": system_prompt, "user_prompt": user_prompt}, timeout=ttl)
