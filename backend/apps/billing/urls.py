from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    CommunicationMessagePrepareView,
    InvoiceViewSet,
    ManualReminderViewSet,
    ReminderListAPIView,
    ReminderPrepareAPIView,
    ReminderSummaryView,
    ReminderV1ListView,
    ShopDetailsView,
)

router = SimpleRouter()
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("reminders/manual", ManualReminderViewSet, basename="manual-reminder")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "settings/shop-details/",
        ShopDetailsView.as_view(),
        name="settings-shop-details",
    ),
    path(
        "communications/messages/prepare/order/<int:order_id>/",
        CommunicationMessagePrepareView.as_view(),
        name="communication-message-prepare",
    ),
    path(
        "communications/reminders/",
        ReminderListAPIView.as_view(),
        name="communication-reminder-list",
    ),
    path(
        "communications/reminders/<str:reminder_id>/prepare/",
        ReminderPrepareAPIView.as_view(),
        name="communication-reminder-prepare",
    ),
    path("reminders/", ReminderV1ListView.as_view(), name="reminder-v1-list"),
    path(
        "reminders/summary/",
        ReminderSummaryView.as_view(),
        name="reminder-v1-summary",
    ),
]
