# apps/console/filters.py
# 后台管理 API 过滤器集合
#
# 各 ViewSet 通过 filterset_class 挂载，提供统一过滤、排序能力。
# REST_FRAMEWORK.DEFAULT_FILTER_BACKENDS 已全局注册 DjangoFilterBackend。

import django_filters
from apps.membership.models import MembershipPlan, PromoCode, UserMembership
from apps.orders.models import Order
from apps.billing.models import CoinLedger, ActionPricing


class MembershipPlanFilter(django_filters.FilterSet):
    """会员套餐过滤：?is_active=true"""

    class Meta:
        model = MembershipPlan
        fields = {
            "is_active": ["exact"],
        }


class OrderFilter(django_filters.FilterSet):
    """订单过滤：?status=paid&created_at_after=2025-01-01"""

    created_at_after = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_at_before = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Order
        fields = {
            "status": ["exact"],
            "order_type": ["exact"],
        }


class CoinLedgerFilter(django_filters.FilterSet):
    """站点币流水过滤：?entry_type=debit"""

    class Meta:
        model = CoinLedger
        fields = {
            "entry_type": ["exact"],
        }


class ActionPricingFilter(django_filters.FilterSet):
    """动作定价过滤：?is_active=true"""

    class Meta:
        model = ActionPricing
        fields = {
            "is_active": ["exact"],
            "action_key": ["exact"],
        }
