"""
订单模块路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import OrderViewSet, MyLatestOrderView

router = DefaultRouter()
router.register(r"", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
    path("me/latest/", MyLatestOrderView.as_view(), name="my-latest-order"),
]
