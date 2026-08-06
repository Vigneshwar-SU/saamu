from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import CommunicationMessagePrepareView, InvoiceViewSet

router = SimpleRouter()
router.register("invoices", InvoiceViewSet, basename="invoice")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "communications/messages/prepare/order/<int:order_id>/",
        CommunicationMessagePrepareView.as_view(),
        name="communication-message-prepare",
    ),
]
