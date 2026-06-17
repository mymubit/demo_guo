# -*- coding: utf-8 -*-
"""大模型 API 调用用量记录与 Dashboard 聚合。"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import timedelta
from typing import Any, Dict, Iterator, Optional

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.skill.llm.pricing import estimate_cost_breakdown, resolve_pricing
from apps.skill.models import LlmUsageLog

logger = logging.getLogger(__name__)

_usage_ctx: ContextVar[Dict[str, Any]] = ContextVar("llm_usage_ctx", default={})


@contextmanager
def llm_usage_scope(
    *,
    source_type: str = LlmUsageLog.SOURCE_OTHER,
    source_key: str = "",
    project_id=None,
    user_id=None,
    execution_run_id=None,
    sub_skill_id: str = "",
) -> Iterator[None]:
    token = _usage_ctx.set(
        {
            "source_type": source_type or LlmUsageLog.SOURCE_OTHER,
            "source_key": str(source_key or "")[:64],
            "project_id": project_id,
            "user_id": user_id,
            "execution_run_id": execution_run_id,
            "sub_skill_id": str(sub_skill_id or "")[:128],
        }
    )
    try:
        yield
    finally:
        _usage_ctx.reset(token)


class LlmUsageService:
    @staticmethod
    def _normalize_source_key(source_type: str, source_key: str) -> str:
        """归一化来源 key，合并子技能后缀与空格/连字符变体。"""
        key = str(source_key or "").strip()
        if not key:
            return ""
        if ":" in key:
            key = key.split(":", 1)[0].strip()
        if source_type == LlmUsageLog.SOURCE_NODE:
            key = key.lower().replace(" ", "-")
            while "--" in key:
                key = key.replace("--", "-")
        elif source_type == LlmUsageLog.SOURCE_AI_FIELD:
            key = key.lower()
        return key[:64]

    @classmethod
    def _aggregate_usage_by_source(cls, base_qs, *, limit: int = 10) -> list[Dict[str, Any]]:
        rows = (
            base_qs.exclude(source_key="")
            .values("source_type", "source_key")
            .annotate(call_count=Count("id"), total_tokens=Sum("total_tokens"))
        )
        bucket: Dict[tuple[str, str], Dict[str, Any]] = {}
        for row in rows:
            source_type = str(row["source_type"] or LlmUsageLog.SOURCE_OTHER)
            normalized = cls._normalize_source_key(source_type, row["source_key"])
            if not normalized:
                continue
            key = (source_type, normalized)
            entry = bucket.setdefault(
                key,
                {"call_count": 0, "total_tokens": 0},
            )
            entry["call_count"] += int(row["call_count"] or 0)
            entry["total_tokens"] += int(row["total_tokens"] or 0)

        ranked = sorted(bucket.items(), key=lambda item: -item[1]["total_tokens"])[: max(1, limit)]
        return [
            {
                "source_type": source_type,
                "source_key": normalized,
                "call_count": stats["call_count"],
                "total_tokens": stats["total_tokens"],
            }
            for (source_type, normalized), stats in ranked
        ]

    @staticmethod
    def _resolve_sub_skill_id(ctx: Dict[str, Any], *, source_key: str) -> str:
        raw = ctx.get("sub_skill_id")
        text = str(raw).strip() if raw is not None else ""
        if text:
            return text[:128]
        if ":" in source_key:
            return source_key.rsplit(":", 1)[-1][:128]
        return ""

    @staticmethod
    def _parse_usage(raw: Any) -> Dict[str, int]:
        if not isinstance(raw, dict):
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        prompt = int(
            raw.get("prompt_tokens")
            or raw.get("input_tokens")
            or raw.get("promptTokens")
            or 0
        )
        completion = int(
            raw.get("completion_tokens")
            or raw.get("output_tokens")
            or raw.get("completionTokens")
            or 0
        )
        total = int(raw.get("total_tokens") or raw.get("totalTokens") or 0)
        if total <= 0:
            total = prompt + completion
        elif prompt <= 0 and completion <= 0:
            logger.debug("LLM usage 仅含 total_tokens=%s，无法拆分输入/输出，费用估算为 0", total)
        return {
            "prompt_tokens": max(0, prompt),
            "completion_tokens": max(0, completion),
            "total_tokens": max(0, total),
        }

    @classmethod
    def record(
        cls,
        *,
        cfg: Dict[str, Any],
        usage: Any,
        success: bool = True,
        source_type: Optional[str] = None,
        source_key: Optional[str] = None,
        project_id=None,
        user_id=None,
    ) -> None:
        ctx = _usage_ctx.get({})
        tokens = cls._parse_usage(usage)
        provider_id = cfg.get("provider_id")
        inp_price, out_price = resolve_pricing(
            provider_id=provider_id,
            model_name=str(cfg.get("model") or ""),
        )
        inp_cost, out_cost, cost = estimate_cost_breakdown(
            prompt_tokens=tokens["prompt_tokens"],
            completion_tokens=tokens["completion_tokens"],
            input_price_per_million=inp_price,
            output_price_per_million=out_price,
        )
        resolved_source_key = str(
            source_key if source_key is not None else ctx.get("source_key") or ""
        )[:64]
        try:
            with transaction.atomic():
                LlmUsageLog.objects.create(
                    provider_id=provider_id or None,
                    provider_name=str(cfg.get("provider_name") or "")[:100],
                    model_name=str(cfg.get("model") or "")[:128],
                    prompt_tokens=tokens["prompt_tokens"],
                    completion_tokens=tokens["completion_tokens"],
                    total_tokens=tokens["total_tokens"],
                    estimated_input_cost_yuan=inp_cost,
                    estimated_output_cost_yuan=out_cost,
                    estimated_cost_yuan=cost,
                    source_type=source_type or ctx.get("source_type") or LlmUsageLog.SOURCE_OTHER,
                    source_key=resolved_source_key,
                    project_id=project_id if project_id is not None else ctx.get("project_id"),
                    user_id=user_id if user_id is not None else ctx.get("user_id"),
                    execution_run_id=ctx.get("execution_run_id") or None,
                    sub_skill_id=cls._resolve_sub_skill_id(ctx, source_key=resolved_source_key),
                    success=success,
                )
                try:
                    from apps.creation.monitoring.llm_trace import merge_request_into_usage_record

                    merge_request_into_usage_record()
                except Exception as trace_exc:  # noqa: BLE001
                    logger.debug("LLM 轨迹 request 写入失败: %s", trace_exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("记录 LLM 用量失败: %s", exc)

    @classmethod
    def junk_log_filter(cls) -> Q:
        return (
            Q(provider_name="t", model_name="m")
            | Q(provider_name="test", model_name="test")
            | Q(model_name="ep-test")
            | Q(provider_name="volcano", model_name="ep-test")
        )

    @classmethod
    def junk_log_queryset(cls):
        """单元测试/调试写入、无 Provider 关联的占位用量。"""
        return LlmUsageLog.objects.filter(cls.junk_log_filter())

    @classmethod
    def cleanup_junk_logs(cls, *, dry_run: bool = False) -> int:
        qs = cls.junk_log_queryset()
        count = qs.count()
        if dry_run or count <= 0:
            return count
        deleted, _ = qs.delete()
        logger.info("已清理 LLM 占位用量日志 %d 条", deleted)
        return deleted

    @classmethod
    def recalculate_estimated_costs(
        cls,
        *,
        provider_ids=None,
        catalog_id=None,
        all_logs: bool = False,
    ) -> int:
        """按当前目录单价重算历史用量估算费用。"""
        if all_logs:
            qs = LlmUsageLog.objects.all()
        elif provider_ids:
            qs = LlmUsageLog.objects.filter(provider_id__in=list(provider_ids))
        elif catalog_id:
            from apps.skill.models import LlmProvider

            providers = LlmProvider.objects.filter(catalog_id=catalog_id)
            pids = list(providers.values_list("id", flat=True))
            model_names = [
                m for m in providers.values_list("model_name", flat=True) if str(m or "").strip()
            ]
            if not pids and not model_names:
                return 0
            q = Q()
            if pids:
                q |= Q(provider_id__in=pids)
            if model_names:
                q |= Q(model_name__in=model_names)
            qs = LlmUsageLog.objects.filter(q)
        else:
            return 0

        updated = 0
        for log in qs.iterator(chunk_size=500):
            inp, out = resolve_pricing(provider_id=log.provider_id, model_name=log.model_name)
            inp_cost, out_cost, cost = estimate_cost_breakdown(
                prompt_tokens=log.prompt_tokens,
                completion_tokens=log.completion_tokens,
                input_price_per_million=inp,
                output_price_per_million=out,
            )
            if (
                log.estimated_input_cost_yuan != inp_cost
                or log.estimated_output_cost_yuan != out_cost
                or log.estimated_cost_yuan != cost
            ):
                LlmUsageLog.objects.filter(pk=log.pk).update(
                    estimated_input_cost_yuan=inp_cost,
                    estimated_output_cost_yuan=out_cost,
                    estimated_cost_yuan=cost,
                )
                updated += 1
        return updated

    @classmethod
    def dashboard_payload(cls, *, days: int = 30) -> Dict[str, Any]:
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        since = today_start - timedelta(days=max(1, days) - 1)

        base_qs = LlmUsageLog.objects.filter(created_at__gte=since, success=True).exclude(
            cls.junk_log_filter()
        )
        today_qs = base_qs.filter(created_at__gte=today_start)

        today_agg = today_qs.aggregate(
            call_count=Count("id"),
            prompt_tokens=Sum("prompt_tokens"),
            completion_tokens=Sum("completion_tokens"),
            total_tokens=Sum("total_tokens"),
            estimated_input_cost_yuan=Sum("estimated_input_cost_yuan"),
            estimated_output_cost_yuan=Sum("estimated_output_cost_yuan"),
            estimated_cost_yuan=Sum("estimated_cost_yuan"),
        )
        period_agg = base_qs.aggregate(
            call_count=Count("id"),
            prompt_tokens=Sum("prompt_tokens"),
            completion_tokens=Sum("completion_tokens"),
            total_tokens=Sum("total_tokens"),
            estimated_input_cost_yuan=Sum("estimated_input_cost_yuan"),
            estimated_output_cost_yuan=Sum("estimated_output_cost_yuan"),
            estimated_cost_yuan=Sum("estimated_cost_yuan"),
        )

        llm_usage_7d = []
        for i in range(6, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            day_qs = LlmUsageLog.objects.filter(
                success=True,
                created_at__gte=day_start,
                created_at__lt=day_end,
            ).exclude(cls.junk_log_filter())
            agg = day_qs.aggregate(
                call_count=Count("id"),
                prompt_tokens=Sum("prompt_tokens"),
                completion_tokens=Sum("completion_tokens"),
                total_tokens=Sum("total_tokens"),
                estimated_input_cost_yuan=Sum("estimated_input_cost_yuan"),
                estimated_output_cost_yuan=Sum("estimated_output_cost_yuan"),
                estimated_cost_yuan=Sum("estimated_cost_yuan"),
            )
            llm_usage_7d.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "call_count": agg["call_count"] or 0,
                    "prompt_tokens": int(agg["prompt_tokens"] or 0),
                    "completion_tokens": int(agg["completion_tokens"] or 0),
                    "total_tokens": int(agg["total_tokens"] or 0),
                    "estimated_input_cost_yuan": float(agg["estimated_input_cost_yuan"] or 0),
                    "estimated_output_cost_yuan": float(agg["estimated_output_cost_yuan"] or 0),
                    "estimated_cost_yuan": float(agg["estimated_cost_yuan"] or 0),
                }
            )

        top_rows = (
            base_qs.values("provider_name", "model_name")
            .annotate(
                call_count=Count("id"),
                prompt_tokens=Sum("prompt_tokens"),
                completion_tokens=Sum("completion_tokens"),
                total_tokens=Sum("total_tokens"),
                estimated_input_cost_yuan=Sum("estimated_input_cost_yuan"),
                estimated_output_cost_yuan=Sum("estimated_output_cost_yuan"),
                estimated_cost_yuan=Sum("estimated_cost_yuan"),
            )
            .order_by("-total_tokens")[:12]
        )
        llm_usage_top = [
            {
                "provider_name": row["provider_name"] or "未命名",
                "model_name": row["model_name"] or "unknown",
                "display_name": f"{row['provider_name'] or '未命名'} / {row['model_name'] or 'unknown'}",
                "call_count": row["call_count"] or 0,
                "prompt_tokens": int(row["prompt_tokens"] or 0),
                "completion_tokens": int(row["completion_tokens"] or 0),
                "total_tokens": int(row["total_tokens"] or 0),
                "estimated_input_cost_yuan": float(row["estimated_input_cost_yuan"] or 0),
                "estimated_output_cost_yuan": float(row["estimated_output_cost_yuan"] or 0),
                "estimated_cost_yuan": float(row["estimated_cost_yuan"] or 0),
            }
            for row in top_rows
        ]

        llm_usage_by_source = cls._aggregate_usage_by_source(base_qs, limit=10)

        return {
            "summary": {
                "today_call_count": today_agg["call_count"] or 0,
                "today_total_tokens": int(today_agg["total_tokens"] or 0),
                "today_prompt_tokens": int(today_agg["prompt_tokens"] or 0),
                "today_completion_tokens": int(today_agg["completion_tokens"] or 0),
                "today_estimated_input_cost_yuan": float(today_agg["estimated_input_cost_yuan"] or 0),
                "today_estimated_output_cost_yuan": float(today_agg["estimated_output_cost_yuan"] or 0),
                "today_estimated_cost_yuan": float(today_agg["estimated_cost_yuan"] or 0),
                "period_call_count": period_agg["call_count"] or 0,
                "period_prompt_tokens": int(period_agg["prompt_tokens"] or 0),
                "period_completion_tokens": int(period_agg["completion_tokens"] or 0),
                "period_total_tokens": int(period_agg["total_tokens"] or 0),
                "period_estimated_input_cost_yuan": float(period_agg["estimated_input_cost_yuan"] or 0),
                "period_estimated_output_cost_yuan": float(period_agg["estimated_output_cost_yuan"] or 0),
                "period_estimated_cost_yuan": float(period_agg["estimated_cost_yuan"] or 0),
                "period_days": days,
            },
            "llm_usage_7d": llm_usage_7d,
            "llm_usage_top": llm_usage_top,
            "llm_usage_by_source": llm_usage_by_source,
        }
