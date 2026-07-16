# -*- coding: utf-8 -*-
"""敏感字段加解密（基于 Django signing，无需额外依赖）。"""
from __future__ import annotations

from typing import Optional

from django.core import signing

_SALT = "drama-llm-api-key"


def encrypt_secret(plain_text: str) -> str:
    if plain_text is None or plain_text == "":
        return ""
    return signing.dumps(plain_text, salt=_SALT)


def decrypt_secret(cipher_text: str) -> Optional[str]:
    if not cipher_text:
        return None
    try:
        return signing.loads(cipher_text, salt=_SALT)
    except signing.BadSignature:
        return None
