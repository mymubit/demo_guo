# -*- coding: utf-8 -*-
"""供应商主 Key + 附加 Key 有序列表（供 failover 轮询）。"""
from __future__ import annotations

from dataclasses import dataclass

from apps.drama.models import DramaLlmProvider, V3LlmProviderKey
from apps.drama.services.secret_crypto import decrypt_secret

PRIMARY_KEY_LABEL = "主密钥"


@dataclass(frozen=True)
class ProviderKeySlot:
    """单次可尝试的密钥槽位（永不用于日志明文）。"""

    label: str
    api_key: str
    is_primary: bool = False


def iter_provider_key_slots(provider: DramaLlmProvider) -> list[ProviderKeySlot]:
    """主 Key（若非空）在前，其后为已启用附加 Key（按 sort_order）。"""
    slots: list[ProviderKeySlot] = []
    primary = decrypt_secret(provider.api_key_encrypted) or ""
    if primary.strip():
        slots.append(
            ProviderKeySlot(
                label=PRIMARY_KEY_LABEL,
                api_key=primary,
                is_primary=True,
            )
        )
    extras = (
        V3LlmProviderKey.objects.filter(provider=provider, is_enabled=True)
        .order_by("sort_order", "created_at")
    )
    for row in extras:
        key = decrypt_secret(row.api_key_encrypted) or ""
        if not key.strip():
            continue
        label = (row.label or "").strip() or f"附加密钥#{row.sort_order}"
        slots.append(
            ProviderKeySlot(label=label, api_key=key, is_primary=False)
        )
    return slots


def iter_api_keys(provider: DramaLlmProvider) -> list[str]:
    """解密后的密钥明文列表：主 Key → 启用的附加 Key。"""
    return [slot.api_key for slot in iter_provider_key_slots(provider)]
