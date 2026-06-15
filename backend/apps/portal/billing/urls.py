# -*- coding: utf-8 -*-
from django.urls import path

from .views import (
    BillingCatalogView,
    CoinLedgerListView,
    RechargeOrderCreateView,
    RechargeOrderMockPayView,
    RechargePackageListView,
    WalletView,
)

app_name = "billing"

urlpatterns = [
    path("wallet/", WalletView.as_view(), name="wallet"),
    path("catalog/", BillingCatalogView.as_view(), name="catalog"),
    path("recharge/packages/", RechargePackageListView.as_view(), name="recharge-packages"),
    path("recharge/orders/", RechargeOrderCreateView.as_view(), name="recharge-order-create"),
    path(
        "recharge/orders/<str:order_no>/mock_pay/",
        RechargeOrderMockPayView.as_view(),
        name="recharge-order-mock-pay",
    ),
    path("ledger/", CoinLedgerListView.as_view(), name="ledger"),
]
