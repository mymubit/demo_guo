"""模板沉淀 URL。"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import TemplatePromotionViewSet

router = DefaultRouter()
router.register(r"template-promotions", TemplatePromotionViewSet, basename="ops-template-promotion")

urlpatterns = router.urls
