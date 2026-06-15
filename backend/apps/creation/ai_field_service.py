# -*- coding: utf-8 -*-
"""表单字段级 AI 生成（扣币 + 纯文本，不暴露技能）。"""
from __future__ import annotations

import re
from typing import Any, Dict

from django.core.exceptions import PermissionDenied

from apps.billing.services import BillingService, InsufficientCoins
from apps.billing.ai_field_prompt_service import AiFieldPromptService
from apps.membership.services import MembershipService
from apps.creation.orchestration.llm_tokens import resolve_agent_max_tokens
from apps.agent.routes import AgentLlmRouteService
from apps.skill.llm.chat import LlmService, LlmServiceError


def _normalize_reference_items(payload) -> list:
    if isinstance(payload, list):
        raw_items = payload
    elif isinstance(payload, dict):
        raw_items = (
            payload.get("items")
            or payload.get("reference_items")
            or payload.get("works")
            or payload.get("references")
            or []
        )
    else:
        raw_items = []

    if not isinstance(raw_items, list):
        return []

    reference_items = []
    for row in raw_items[:3]:
        if isinstance(row, str):
            title = row.strip().strip("《》")
            if title:
                reference_items.append({"title": title, "note": ""})
            continue
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or row.get("name") or "").strip().strip("《》")
        note = str(row.get("note") or row.get("description") or row.get("style") or "").strip()
        if title:
            reference_items.append({"title": title, "note": note})
    return reference_items


def _reference_items_to_text(reference_items: list) -> str:
    return "\n".join(
        f"{it['title']}｜{it['note']}" if it.get("note") else it["title"]
        for it in reference_items
    )


def _clean_reference_title(raw: str) -> str:
    title = re.sub(r"^\d+[\.\)、]\s*", "", (raw or "").strip())
    return title.strip("《》").strip()


def _normalize_reference_items_from_text(text: str) -> list:
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", (text or "").strip())
    if not cleaned:
        return []

    reference_items = []
    seen = set()
    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        if not line or len(line) < 2:
            continue

        title = ""
        note = ""
        for sep in ("｜", "|", "：", ":"):
            idx = line.find(sep)
            if idx > 0:
                title = _clean_reference_title(line[:idx])
                note = line[idx + len(sep) :].strip()
                break

        if not title:
            book = re.match(r"^[《「]([^》」]+)[》」]\s*[：:]?\s*(.*)$", line)
            if book:
                title = book.group(1).strip()
                note = (book.group(2) or "").strip()
            else:
                colon_idx = line.find("：")
                if colon_idx < 0:
                    colon_idx = line.find(":")
                if colon_idx > 0:
                    title = _clean_reference_title(line[:colon_idx])
                    note = line[colon_idx + 1 :].strip()
                else:
                    title = _clean_reference_title(line[:40])
                    note = line[40:].strip() if len(line) > 40 else ""

        if not title:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        reference_items.append({"title": title, "note": note})
        if len(reference_items) >= 3:
            break
    return reference_items


def generate_field_content(user, action_key: str, context: Dict[str, Any]) -> Dict[str, Any]:
    meta = AiFieldPromptService.resolve(action_key)
    if not meta:
        raise PermissionDenied("未知生成动作")

    if action_key == "ai.generate.pull_sheet":
        pricing = BillingService.get_price_row(action_key)
        if pricing and pricing.member_only:
            ok, msg = MembershipService.check_membership_status(user)
            if not ok:
                raise PermissionDenied(msg or "拉片分析需有效会员")
        return {
            "text": (
                "【拉片分析 · 开发中】\n"
                "已记录你的参考作品与创意上下文。完整拉片能力（分镜/节奏/钩子拆解）"
                "将在后续版本开放，当前不扣创作币。"
            ),
            "action_key": action_key,
            "coin_cost": 0,
            "balance_after": BillingService.get_balance(user),
            "currency_name": BillingService.currency_name(),
            "coming_soon": True,
        }

    pricing = BillingService.get_price_row(action_key)
    if pricing and pricing.member_only:
        ok, msg = MembershipService.check_membership_status(user)
        if not ok:
            name = BillingService.action_display_name(action_key)
            raise PermissionDenied(f"{name}为会员专享，请先开通会员（开通后仍按创作币扣费）")

    try:
        wallet, balance = BillingService.charge(
            user,
            action_key,
            remark=BillingService.action_display_name(action_key),
        )
    except InsufficientCoins as exc:
        raise PermissionDenied(str(exc)) from exc

    theme = context.get("theme") or "都市情感"
    episode_count = context.get("episode_count") or 30
    core_idea = context.get("core_idea") or context.get("idea") or ""
    user_prompt = meta["user_tpl"].format(
        theme=theme,
        episode_count=episode_count,
        core_idea=core_idea,
        audience=context.get("audience") or "",
        reference_work=context.get("reference_work") or context.get("references") or "",
    )
    provider_id = AiFieldPromptService.resolve_provider_id(action_key) or AgentLlmRouteService.resolve_provider_id(
        "ai_field"
    )

    from apps.skill.llm.usage_log import llm_usage_scope
    from apps.skill.models import LlmUsageLog

    with llm_usage_scope(
        source_type=LlmUsageLog.SOURCE_AI_FIELD,
        source_key=action_key,
        user_id=getattr(user, "id", None),
    ):
        if action_key == "ai.generate.reference_work":
            reference_items = []
            text = ""

            if meta.get("json"):
                try:
                    payload = LlmService.generate_json(
                        system_prompt=meta["system"],
                        user_prompt=user_prompt,
                        provider_id=provider_id,
                        max_tokens=resolve_agent_max_tokens("ai_field"),
                    )
                    reference_items = _normalize_reference_items(payload)
                except LlmServiceError:
                    pass

            if reference_items:
                text = _reference_items_to_text(reference_items)
            else:
                try:
                    text = LlmService.generate_text(
                        system_prompt=meta.get("system_text") or meta["system"],
                        user_prompt=user_prompt,
                        provider_id=provider_id,
                        max_tokens=resolve_agent_max_tokens("ai_field"),
                    )
                except LlmServiceError as exc:
                    BillingService.credit(
                        user,
                        BillingService.get_price(action_key),
                        action_key="ai.generate.refund",
                        remark=BillingService.refund_remark(action_key),
                    )
                    raise PermissionDenied(str(exc)) from exc
                reference_items = _normalize_reference_items_from_text(text)

            cost = BillingService.get_price(action_key)
            return {
                "text": text,
                "reference_items": reference_items,
                "action_key": action_key,
                "coin_cost": cost,
                "balance_after": balance,
                "currency_name": BillingService.currency_name(),
            }

        try:
            text = LlmService.generate_text(
                system_prompt=meta["system"],
                user_prompt=user_prompt,
                provider_id=provider_id,
                max_tokens=resolve_agent_max_tokens("ai_field"),
            )
        except LlmServiceError as exc:
            BillingService.credit(
                user,
                BillingService.get_price(action_key),
                action_key="ai.generate.refund",
                remark=BillingService.refund_remark(action_key),
            )
            raise PermissionDenied(str(exc)) from exc

        cost = BillingService.get_price(action_key)
        return {
            "text": text,
            "action_key": action_key,
            "coin_cost": cost,
            "balance_after": balance,
            "currency_name": BillingService.currency_name(),
        }
