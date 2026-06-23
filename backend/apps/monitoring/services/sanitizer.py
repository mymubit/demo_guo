# -*- coding: utf-8 -*-
import hashlib
import json
import re
from typing import Any

SENSITIVE_TOKENS = (
    "password",
    "passwd",
    "pwd",
    "token",
    "authorization",
    "cookie",
    "secret",
    "api_key",
    "apikey",
    "access",
    "refresh",
    "credential",
)

MAX_STRING_LENGTH = 1000
MAX_CONTAINER_ITEMS = 50
PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-]{2})[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def is_sensitive_key(key: str) -> bool:
    normalized = (key or "").lower()
    return any(token in normalized for token in SENSITIVE_TOKENS)


def mask_text(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
    text = value[:max_length]
    if len(value) > max_length:
        text = f"{text}...<truncated>"
    text = PHONE_RE.sub(lambda match: f"{match.group(0)[:3]}****{match.group(0)[-4:]}", text)
    return EMAIL_RE.sub(lambda match: f"{match.group(1)}***{match.group(2)}", text)


def sanitize_value(value: Any, *, depth: int = 0) -> Any:
    if depth > 4:
        return "<max_depth>"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return mask_text(value)
    if isinstance(value, (list, tuple, set)):
        return [sanitize_value(item, depth=depth + 1) for item in list(value)[:MAX_CONTAINER_ITEMS]]
    if isinstance(value, dict):
        result = {}
        for key, item in list(value.items())[:MAX_CONTAINER_ITEMS]:
            key_text = str(key)[:80]
            result[key_text] = "***" if is_sensitive_key(key_text) else sanitize_value(item, depth=depth + 1)
        return result
    return mask_text(str(value))


def sanitize_payload(payload: Any) -> dict:
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return sanitize_value(payload)
    return {"value": sanitize_value(payload)}


def json_size(payload: Any) -> int:
    try:
        return len(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"))
    except (TypeError, ValueError):
        return 0


def stable_hash(*parts: Any) -> str:
    raw = "|".join(str(part or "") for part in parts)
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()


def compact_sql(sql: str, max_length: int = 2000) -> str:
    text = " ".join((sql or "").split())
    text = re.sub(r"'[^']*'", "'?'", text)
    text = re.sub(r"\b\d+\b", "?", text)
    if len(text) > max_length:
        return f"{text[:max_length]}...<truncated>"
    return text
