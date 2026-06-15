# -*- coding: utf-8 -*-
"""火山方舟接入常量与 Base URL 解析（单一数据源）。"""
from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

VOLCANO_KEY_PAYG = "payg"
VOLCANO_KEY_CODING_PLAN = "coding_plan"

VOLCANO_KEY_TYPE_CHOICES = (
    ("", "未指定"),
    (VOLCANO_KEY_PAYG, "按量付费"),
    (VOLCANO_KEY_CODING_PLAN, "Coding Plan / Agent Plan"),
)

DEFAULT_VOLCANO_PAYG_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_VOLCANO_CODING_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"


def get_volcano_payg_base_url() -> str:
    from django.conf import settings

    raw = getattr(settings, "VOLCANO_ARK_BASE_URL", "") or DEFAULT_VOLCANO_PAYG_BASE_URL
    return str(raw).strip().rstrip("/") or DEFAULT_VOLCANO_PAYG_BASE_URL


def get_volcano_coding_base_url() -> str:
    from django.conf import settings

    raw = getattr(settings, "VOLCANO_ARK_CODING_BASE_URL", "") or DEFAULT_VOLCANO_CODING_BASE_URL
    return str(raw).strip().rstrip("/") or DEFAULT_VOLCANO_CODING_BASE_URL


def get_volcano_key_type_from_env() -> str:
    from django.conf import settings
    import os

    raw = (
        getattr(settings, "VOLCANO_ARK_KEY_TYPE", "")
        or os.getenv("VOLCANO_ARK_KEY_TYPE", "")
        or ""
    ).strip().lower()
    if raw in {VOLCANO_KEY_CODING_PLAN, "coding", "coding_plan", "agent_plan"}:
        return VOLCANO_KEY_CODING_PLAN
    if raw in {VOLCANO_KEY_PAYG, "payg", "pay-as-you-go", "v3"}:
        return VOLCANO_KEY_PAYG
    return ""


def is_volcano_host(base_url: str) -> bool:
    host = ""
    try:
        host = urlparse(base_url or "").netloc or str(base_url or "")
    except Exception:  # noqa: BLE001
        host = str(base_url or "")
    host_lower = host.lower()
    return "volces.com" in host_lower or "volcengine" in host_lower


def infer_volcano_key_type(base_url: str) -> str:
    url = (base_url or "").rstrip("/")
    if not url:
        return ""
    if "/api/coding" in url:
        return VOLCANO_KEY_CODING_PLAN
    if is_volcano_host(url):
        return VOLCANO_KEY_PAYG
    return ""


def resolve_volcano_base_url(key_type: str) -> str:
    if key_type == VOLCANO_KEY_CODING_PLAN:
        return get_volcano_coding_base_url()
    return get_volcano_payg_base_url()


def effective_volcano_base_url(*, base_url: str, key_type: str = "") -> str:
    """运行时实际请求的 Base URL：key_type 优先于 base_url 字段。"""
    resolved_type = key_type or infer_volcano_key_type(base_url)
    if resolved_type:
        return resolve_volcano_base_url(resolved_type)
    return (base_url or "").strip().rstrip("/")


def volcano_alternate_base_url(base_url: str) -> str:
    """404 时尝试的另一套 Base URL。"""
    url = (base_url or "").rstrip("/")
    if "/api/coding" in url:
        return get_volcano_payg_base_url()
    return get_volcano_coding_base_url()


def infer_key_type_from_alternate_success(*, tried_base_url: str, success_base_url: str) -> str:
    if success_base_url == get_volcano_coding_base_url():
        return VOLCANO_KEY_CODING_PLAN
    if success_base_url == get_volcano_payg_base_url():
        return VOLCANO_KEY_PAYG
    return infer_volcano_key_type(success_base_url) or infer_volcano_key_type(tried_base_url)
