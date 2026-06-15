# -*- coding: utf-8 -*-
"""大模型 Token 单价解析与费用估算（元）。"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional, Tuple

from apps.skill.models import LlmModelCatalog, LlmProvider

logger = logging.getLogger(__name__)

ZERO = Decimal("0")


def _as_decimal(value) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:  # noqa: BLE001
        return None


def _pricing_from_catalog(cat: Optional[LlmModelCatalog]) -> Tuple[Optional[Decimal], Optional[Decimal]]:
    if not cat:
        return None, None
    return _as_decimal(cat.input_price_per_million), _as_decimal(cat.output_price_per_million)


def _catalog_by_model_name(model_name: str) -> Optional[LlmModelCatalog]:
    name = str(model_name or "").strip()
    if not name:
        return None
    return LlmModelCatalog.objects.filter(model_name=name).order_by("sort_order").first()


def estimate_cost_breakdown(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    input_price_per_million: Optional[Decimal],
    output_price_per_million: Optional[Decimal],
) -> Tuple[Decimal, Decimal, Decimal]:
    """返回 (输入费用, 输出费用, 合计)，单位元。"""
    inp = input_price_per_million if input_price_per_million is not None else ZERO
    out = output_price_per_million if output_price_per_million is not None else ZERO
    if inp <= 0 and out <= 0:
        return ZERO, ZERO, ZERO
    prompt = Decimal(max(0, int(prompt_tokens or 0)))
    completion = Decimal(max(0, int(completion_tokens or 0)))
    input_cost = (prompt * inp / Decimal("1000000")).quantize(Decimal("0.000001"))
    output_cost = (completion * out / Decimal("1000000")).quantize(Decimal("0.000001"))
    return input_cost, output_cost, input_cost + output_cost


def estimate_cost_yuan(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    input_price_per_million: Optional[Decimal],
    output_price_per_million: Optional[Decimal],
) -> Decimal:
    _, _, total = estimate_cost_breakdown(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        input_price_per_million=input_price_per_million,
        output_price_per_million=output_price_per_million,
    )
    return total


def resolve_pricing(
    *,
    provider_id=None,
    model_name: str = "",
) -> Tuple[Optional[Decimal], Optional[Decimal]]:
    """按 Provider 关联目录解析单价（元/百万 Token）。

    优先级：Provider.catalog → 同 model 的 Provider.catalog → 目录 model_name 精确匹配。
    ep-xxx 不再回退到「第一个火山目录」，避免 Pro/Flash 串价。
    """
    provider = None
    if provider_id:
        provider = (
            LlmProvider.objects.select_related("catalog")
            .filter(pk=provider_id)
            .first()
        )
        if provider and provider.catalog_id:
            return _pricing_from_catalog(provider.catalog)

    name = str(model_name or "").strip()
    if provider and not provider.catalog_id:
        cat = _catalog_by_model_name(provider.model_name)
        if cat:
            return _pricing_from_catalog(cat)

    if name:
        cat = _catalog_by_model_name(name)
        if cat:
            return _pricing_from_catalog(cat)

    if name.startswith("ep-"):
        sibling = (
            LlmProvider.objects.select_related("catalog")
            .filter(model_name=name, catalog_id__isnull=False)
            .order_by("-is_active", "sort_order", "-updated_at")
            .first()
        )
        if sibling and sibling.catalog_id:
            return _pricing_from_catalog(sibling.catalog)

    if provider_id or name:
        logger.debug(
            "LLM 单价未命中: provider_id=%s model=%s（请确保接入时选择对应目录模板）",
            provider_id,
            name or (provider.model_name if provider else ""),
        )
    return None, None
