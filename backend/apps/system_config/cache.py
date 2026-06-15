# -*- coding: utf-8 -*-
"""动态配置缓存封装。"""
from __future__ import annotations

from django.core.cache import cache

CACHE_TTL = 60 * 15
CACHE_KEY_VERSION = "system_config:version"
CACHE_KEY_PUBLIC_ALL = "system_config:public:all"
CACHE_KEY_ITEM_PREFIX = "system_config:item:"
CACHE_KEY_CATEGORY_PREFIX = "system_config:category:"


def item_cache_key(config_key: str) -> str:
    return f"{CACHE_KEY_ITEM_PREFIX}{config_key}"


def category_cache_key(category_code: str) -> str:
    return f"{CACHE_KEY_CATEGORY_PREFIX}{category_code}"


def get_cache(key: str, default=None):
    try:
        value = cache.get(key)
    except Exception:
        return default
    return default if value is None else value


def set_cache(key: str, value, timeout: int = CACHE_TTL) -> None:
    try:
        cache.set(key, value, timeout)
    except Exception:
        pass


def delete_cache(key: str) -> None:
    try:
        cache.delete(key)
    except Exception:
        pass


def delete_pattern(pattern: str) -> None:
    try:
        cache.delete_pattern(pattern)
    except Exception:
        pass


def bump_version() -> int:
    version = get_cache(CACHE_KEY_VERSION, 0) or 0
    try:
        version = int(version) + 1
    except (TypeError, ValueError):
        version = 1
    set_cache(CACHE_KEY_VERSION, version, None)
    return version


def current_version() -> int:
    version = get_cache(CACHE_KEY_VERSION, 1)
    try:
        return int(version)
    except (TypeError, ValueError):
        return 1


def invalidate_config(config_key: str = "", category_code: str = "") -> None:
    if config_key:
        delete_cache(item_cache_key(config_key))
    if category_code:
        delete_cache(category_cache_key(category_code))
    delete_cache(CACHE_KEY_PUBLIC_ALL)
    bump_version()


def clear_all_config_cache() -> None:
    delete_pattern(f"{CACHE_KEY_ITEM_PREFIX}*")
    delete_pattern(f"{CACHE_KEY_CATEGORY_PREFIX}*")
    delete_cache(CACHE_KEY_PUBLIC_ALL)
    bump_version()
