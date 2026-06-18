# -*- coding: utf-8 -*-
"""
多模型智能路由引擎。

按多维度（题材 / 节点类型 / 用户等级 / 时段成本）自动选择最优 LLM Provider。

路由决策流程：
1. 收集维度：题材、节点类型、用户付费等级、当前时段、各 Provider 配额
2. 匹配路由规则（AgentLlmRouteConfig.routing_rules JSON 字段）
3. 按优先级排序候选 Provider
4. 选择第一个有可用配额的 Provider

路由规则 JSON 格式：
{
  "rules": [
    {
      "priority": 1,
      "conditions": {
        "theme": ["family-revenge", "overbearing-ceo"],
        "node_type": ["script", "dialogue"],
        "user_tier": ["vip", "svip"],
        "time_window": {"start": "22:00", "end": "08:00"}  // 夜间低价窗口
      },
      "model_name": "gpt-4o-mini",
      "provider_id": "openai"
    }
  ]
}
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, time
from typing import Any, Dict, List, Optional

from django.utils import timezone

logger = logging.getLogger(__name__)


class LlmRouter:
    """多维智能路由主类"""

    def route(self, theme: str, node_type: str, user_tier: str) -> Optional[Dict[str, str]]:
        """
        根据维度路由，返回 {"provider_id", "model_name"} 或 None。

        当无匹配规则时返回 None，上游调用方 fallback 到默认 Provider。
        """
        rules = self._load_routing_rules()
        if not rules:
            return None

        context = {
            "theme": theme,
            "node_type": node_type,
            "user_tier": user_tier,
        }

        # 按 priority 降序排列，优先匹配高优先级规则
        candidates = []
        for rule in rules:
            if self._match_conditions(rule, context):
                candidates.append(rule)

        if not candidates:
            return None

        # 按优先级排序后选择最优候选
        candidates.sort(key=lambda r: r.get("priority", 0), reverse=True)
        return self._select_best_candidate(candidates)

    def _load_routing_rules(self) -> list:
        """
        加载所有启用的路由规则，按 priority 降序排列。
        规则从 AgentLlmRouteConfig.routing_rules JSON 字段读取。
        """
        from apps.agent.models import AgentLlmRouteConfig

        rows = AgentLlmRouteConfig.objects.filter(
            is_active=True,
        ).order_by("-sort_order")

        all_rules = []
        for row in rows:
            rules_json = getattr(row, "routing_rules", None) or {}
            rules_list = rules_json.get("rules") if isinstance(rules_json, dict) else None
            if not isinstance(rules_list, list):
                continue
            for rule in rules_list:
                if isinstance(rule, dict):
                    all_rules.append(rule)

        # 按 priority 降序
        all_rules.sort(key=lambda r: r.get("priority", 0), reverse=True)
        return all_rules

    def _match_conditions(self, rule: dict, context: dict) -> bool:
        """
        判断规则条件是否匹配当前上下文。

        条件字段（均为可选）：
        - theme: list[str] 题材代码列表
        - node_type: list[str] 节点类型列表
        - user_tier: list[str] 用户等级列表
        - time_window: {"start": "HH:MM", "end": "HH:MM"} 低价时段窗口
        """
        conditions = rule.get("conditions") or {}

        # 题材匹配
        themes = conditions.get("theme")
        if themes and isinstance(themes, list):
            ctx_theme = context.get("theme", "")
            if ctx_theme and ctx_theme not in themes:
                return False

        # 节点类型匹配
        node_types = conditions.get("node_type")
        if node_types and isinstance(node_types, list):
            ctx_node = context.get("node_type", "")
            if ctx_node and ctx_node not in node_types:
                return False

        # 用户等级匹配
        user_tiers = conditions.get("user_tier")
        if user_tiers and isinstance(user_tiers, list):
            ctx_tier = context.get("user_tier", "")
            if ctx_tier and ctx_tier not in user_tiers:
                return False

        # 时段匹配
        time_window = conditions.get("time_window")
        if time_window and isinstance(time_window, dict):
            start_str = time_window.get("start", "00:00")
            end_str = time_window.get("end", "23:59")
            if not self._is_in_time_window(start_str, end_str):
                return False

        return True

    def _is_in_time_window(self, start_str: str, end_str: str) -> bool:
        """
        判断当前时间是否在指定时段窗口内。
        支持跨午夜时段（如 22:00-08:00）。
        """
        try:
            now = datetime.now().time()
            start = datetime.strptime(start_str, "%H:%M").time()
            end = datetime.strptime(end_str, "%H:%M").time()

            if start <= end:
                # 同一天内，如 09:00-17:00
                return start <= now <= end
            else:
                # 跨午夜，如 22:00-08:00
                return now >= start or now <= end
        except ValueError:
            logger.warning("[LlmRouter] 时段格式错误 start=%s end=%s", start_str, end_str)
            return False

    def _check_quota_available(self, provider_id: str, model_name: str) -> bool:
        """
        检查 Provider + Model 配额是否充足。

        配额检查逻辑：
        - 从 LlmUsageLog 统计当日调用量
        - 与 Provider 上的配额上限比较（暂无配额字段时默认充足）
        """
        from apps.skill.models import LlmProvider

        try:
            provider = LlmProvider.objects.get(pk=provider_id)
        except LlmProvider.DoesNotExist:
            return True  # Provider 不存在时放行

        # Provider 上暂无配额字段，默认视为充足；后续可在 LlmProvider 增加 quota 字段后再启用检查。
        return True

    def _get_time_window_discount(self, provider_id: str) -> float:
        """
        获取时段折扣系数（低价窗口返回 < 1.0）。

        目前返回固定值 1.0，后续可扩展为按时间段返回不同折扣。
        """
        # 时段折扣暂未配置，固定 1.0；可在系统配置中扩展低价窗口。
        return 1.0

    def _select_best_candidate(self, candidates: list) -> Optional[Dict[str, str]]:
        """
        从候选列表中选最优（综合成本 + 配额 + 时段折扣）。

        选择策略：
        1. 过滤掉配额不足的候选
        2. 按 cost_score（越低越好）排序
        3. 返回最优候选的 provider_id 和 model_name
        """
        valid: List[Dict] = []

        for candidate in candidates:
            provider_id = str(candidate.get("provider_id") or "")
            model_name = str(candidate.get("model_name") or "")

            if not provider_id or not model_name:
                continue

            if not self._check_quota_available(provider_id, model_name):
                continue

            discount = self._get_time_window_discount(provider_id)
            # cost_score 越低越优（已考虑时段折扣）
            cost_score = candidate.get("cost_score") or 0
            effective_score = cost_score * discount

            valid.append({
                "provider_id": provider_id,
                "model_name": model_name,
                "cost_score": effective_score,
                "original_cost_score": cost_score,
            })

        if not valid:
            return None

        # 选择 cost_score 最低的
        best = min(valid, key=lambda x: x["cost_score"])
        return {
            "provider_id": best["provider_id"],
            "model_name": best["model_name"],
        }
