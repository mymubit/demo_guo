# -*- coding: utf-8 -*-
"""会员/充值人民币定价与折扣解析。"""
from decimal import Decimal, InvalidOperation


def quantize_yuan(value) -> Decimal:
    if not isinstance(value, Decimal):
        value = to_decimal(value, Decimal("0"))
    return value.quantize(Decimal("0.01"))


def to_decimal(value, default=None):
    if value is None or value == "":
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def normalize_discount_percent(value) -> Decimal:
    discount = to_decimal(value, Decimal("100"))
    if discount is None or discount <= 0 or discount > 100:
        return Decimal("100")
    return discount.quantize(Decimal("0.01"))


def resolve_charge_price(*, original, discount_percent, manual_price) -> Decimal:
    """根据原价与折扣计算实付；无有效折扣时回退 manual_price。"""
    discount = normalize_discount_percent(discount_percent)
    manual = to_decimal(manual_price, Decimal("0")) or Decimal("0")
    orig = to_decimal(original)

    if orig is not None and orig > 0 and discount < Decimal("100"):
        return quantize_yuan(orig * discount / Decimal("100"))
    return quantize_yuan(manual)


def discount_display_label(discount_percent) -> str | None:
    discount = normalize_discount_percent(discount_percent)
    if discount >= Decimal("100"):
        return None
    zhe = discount / Decimal("10")
    text = f"{zhe:.1f}".rstrip("0").rstrip(".")
    return f"{text}折"
