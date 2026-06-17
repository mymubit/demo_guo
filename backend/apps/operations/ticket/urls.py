"""工单 URL。"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    TicketCategoryConfigViewSet,
    TicketEventViewSet,
    TicketMacroViewSet,
    TicketViewSet,
    UserTicketCreateView,
    UserTicketListView,
    UserTicketReplyView,
)

router = DefaultRouter()
router.register(r"tickets", TicketViewSet, basename="ops-ticket")
router.register(r"ticket-categories", TicketCategoryConfigViewSet, basename="ops-ticket-category")
router.register(r"ticket-macros", TicketMacroViewSet, basename="ops-ticket-macro")
router.register(r"ticket-events", TicketEventViewSet, basename="ops-ticket-event")

urlpatterns = router.urls + [
    # C 端
    path("my/tickets/", UserTicketListView.as_view(), name="ops-my-tickets"),
    path("my/tickets/create/", UserTicketCreateView.as_view(), name="ops-my-ticket-create"),
    path("my/tickets/<int:ticket_id>/reply/", UserTicketReplyView.as_view(), name="ops-my-ticket-reply"),
]
