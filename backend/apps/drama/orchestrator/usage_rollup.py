# -*- coding: utf-8 -*-
"""V3 用量日汇总：按 call log 增量 upsert。"""
from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.db.models import F

from apps.drama.models import (
    DramaLlmCallLog,
    DramaLlmProvider,
    V3ModelPrice,
    V3UsageDailyRollup,
)

logger = logging.getLogger(__name__)

_SHANGHAI = ZoneInfo("Asia/Shanghai")
_ZERO = Decimal("0")


def shanghai_date(dt: datetime | date) -> date:
    """将时刻转为 Asia/Shanghai 日历日。"""
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(_SHANGHAI).date()


def estimate_cost(
    *,
    provider_id: UUID | str | None,
    model_name: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    cached_prompt_tokens: int | None = None,
) -> Decimal | None:
    """按单价估算费用；无单价返回 None。

    优先 provider_id + model_name；provider 缺失时回退到同名模型单价。
    缓存命中部分：有 price_cache_in_per_1k 则用缓存价，否则回退输入价。
    """
    model_name = (model_name or "").strip()
    if not model_name:
        return None
    price = None
    if provider_id:
        price = (
            V3ModelPrice.objects.filter(
                provider_id=provider_id, model_name=model_name
            )
            .only("price_in_per_1k", "price_out_per_1k", "price_cache_in_per_1k")
            .first()
        )
    if price is None:
        price = (
            V3ModelPrice.objects.filter(model_name=model_name)
            .only("price_in_per_1k", "price_out_per_1k", "price_cache_in_per_1k")
            .order_by("id")
            .first()
        )
    if price is None:
        return None

    prompt = max(int(prompt_tokens or 0), 0)
    cached = max(int(cached_prompt_tokens or 0), 0)
    if cached > prompt:
        cached = prompt
    fresh = prompt - cached
    cache_rate = (
        price.price_cache_in_per_1k
        if price.price_cache_in_per_1k is not None
        else price.price_in_per_1k
    )
    pin = Decimal(fresh) / Decimal(1000)
    pcache = Decimal(cached) / Decimal(1000)
    pout = Decimal(completion_tokens or 0) / Decimal(1000)
    return (
        pin * price.price_in_per_1k
        + pcache * cache_rate
        + pout * price.price_out_per_1k
    ).quantize(Decimal("0.000001"))


def _resolve_provider_id(call_log: DramaLlmCallLog) -> UUID | None:
    base_url = (call_log.base_url or "").strip()
    model_name = (call_log.model_name or "").strip()
    if not base_url and not model_name:
        return None
    qs = DramaLlmProvider.objects.all()
    if base_url:
        qs = qs.filter(base_url=base_url)
    if model_name:
        by_model = qs.filter(model_name=model_name).first()
        if by_model is not None:
            return by_model.id
    return qs.first().id if qs.exists() else None


def _resolve_owner_id(call_log: DramaLlmCallLog) -> int | None:
    run = getattr(call_log, "v3_command_run", None)
    if run is not None and getattr(run, "owner_id", None):
        return int(run.owner_id)
    project = getattr(call_log, "v3_project", None)
    if project is not None and getattr(project, "owner_id", None):
        return int(project.owner_id)
    if call_log.v3_command_run_id:
        from apps.drama.models import V3CommandRun

        owner_id = (
            V3CommandRun.objects.filter(pk=call_log.v3_command_run_id)
            .values_list("owner_id", flat=True)
            .first()
        )
        if owner_id is not None:
            return int(owner_id)
    if call_log.v3_project_id:
        from apps.drama.models import V3Project

        owner_id = (
            V3Project.objects.filter(pk=call_log.v3_project_id)
            .values_list("owner_id", flat=True)
            .first()
        )
        if owner_id is not None:
            return int(owner_id)
    return None


def _resolve_command_type(call_log: DramaLlmCallLog) -> str | None:
    run = getattr(call_log, "v3_command_run", None)
    if run is not None:
        ct = getattr(run, "command_type", None) or None
        return ct or None
    if call_log.v3_command_run_id:
        from apps.drama.models import V3CommandRun

        return (
            V3CommandRun.objects.filter(pk=call_log.v3_command_run_id)
            .values_list("command_type", flat=True)
            .first()
        )
    return None


def apply_call_to_rollup(call_log: DramaLlmCallLog) -> None:
    """按 Asia/Shanghai 日 + owner/project/command_type/model/provider 维度 upsert 累加。

    无单价：estimated_cost 不加，unpriced_call_count += 1。
    command_type 从 call.v3_command_run.command_type 取（可空）。
    provider_id：能从 base_url/model 反查则填，否则空。
    """
    owner_id = _resolve_owner_id(call_log)
    if owner_id is None:
        logger.debug("skip usage rollup: no owner for call_log=%s", call_log.pk)
        return

    day = shanghai_date(call_log.created_at)
    project_id = call_log.v3_project_id
    command_type = _resolve_command_type(call_log)
    model_name = call_log.model_name or ""
    provider_id = _resolve_provider_id(call_log)

    prompt_tokens = int(call_log.prompt_tokens or 0)
    cached_prompt_tokens = int(call_log.cached_prompt_tokens or 0)
    if cached_prompt_tokens > prompt_tokens:
        cached_prompt_tokens = prompt_tokens
    completion_tokens = int(call_log.completion_tokens or 0)
    total_tokens = int(
        call_log.total_tokens
        if call_log.total_tokens is not None
        else prompt_tokens + completion_tokens
    )
    is_success = call_log.status == DramaLlmCallLog.Status.SUCCESS
    cost = estimate_cost(
        provider_id=provider_id,
        model_name=model_name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cached_prompt_tokens=cached_prompt_tokens,
    )
    is_priced = cost is not None
    cost_delta = cost if is_priced else _ZERO
    unpriced_delta = 0 if is_priced else 1

    dims: dict[str, Any] = {
        "date": day,
        "owner_id": owner_id,
        "project_id": project_id,
        "command_type": command_type,
        "model_name": model_name,
        "provider_id": provider_id,
    }

    with transaction.atomic():
        qs = V3UsageDailyRollup.objects.select_for_update().filter(**dims)
        row = qs.first()
        if row is None:
            try:
                V3UsageDailyRollup.objects.create(
                    **dims,
                    prompt_tokens=prompt_tokens,
                    cached_prompt_tokens=cached_prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    call_count=1,
                    success_count=1 if is_success else 0,
                    estimated_cost=cost_delta,
                    unpriced_call_count=unpriced_delta,
                )
                return
            except IntegrityError:
                row = qs.first()
                if row is None:
                    raise

        V3UsageDailyRollup.objects.filter(pk=row.pk).update(
            prompt_tokens=F("prompt_tokens") + prompt_tokens,
            cached_prompt_tokens=F("cached_prompt_tokens") + cached_prompt_tokens,
            completion_tokens=F("completion_tokens") + completion_tokens,
            total_tokens=F("total_tokens") + total_tokens,
            call_count=F("call_count") + 1,
            success_count=F("success_count") + (1 if is_success else 0),
            estimated_cost=F("estimated_cost") + cost_delta,
            unpriced_call_count=F("unpriced_call_count") + unpriced_delta,
        )
