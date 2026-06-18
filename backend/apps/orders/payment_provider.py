# -*- coding: utf-8 -*-
"""支付渠道抽象 — 本期 mock，后续可插微信/支付宝。"""
from __future__ import annotations

import os
from typing import Tuple

from django.conf import settings
from django.core.exceptions import PermissionDenied


def default_payment_method() -> str:
    return getattr(settings, "PAYMENT_METHOD", None) or os.getenv("PAYMENT_METHOD", "mock")


class PaymentProvider:
    """统一支付入口，避免业务层散落 payment_method='mock'。"""

    @classmethod
    def catalog_payment_method(cls) -> str:
        """计费目录等只读场景：返回当前环境可用的支付方式。"""
        method = (default_payment_method() or "mock").strip().lower()
        allowed = {"mock"}
        if method not in allowed:
            return "mock"
        if method == "mock" and (
            not getattr(settings, "ALLOW_MOCK_PAYMENT", False)
            or not getattr(settings, "DEBUG", False)
        ):
            return "none"
        return method

    @classmethod
    def resolve_method(cls, requested: str | None = None) -> str:
        method = (requested or default_payment_method() or "mock").strip().lower()
        allowed = {"mock"}
        if method not in allowed:
            raise ValueError(f"不支持的支付方式: {method}")
        if method == "mock" and (
            not getattr(settings, "ALLOW_MOCK_PAYMENT", False)
            or not getattr(settings, "DEBUG", False)
        ):
            raise PermissionDenied("模拟支付已关闭")
        return method

    @classmethod
    def process_order_payment(
        cls,
        order_no: str,
        *,
        payment_method: str | None = None,
        user=None,
    ) -> Tuple[bool, str, object]:
        from apps.orders.services import PaymentService

        method = cls.resolve_method(payment_method)
        if method == "mock":
            return PaymentService.process_mock_payment(order_no, user=user)
        raise NotImplementedError(f"支付方式未实现: {method}")
