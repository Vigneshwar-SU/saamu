from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.customers.views import (
    CustomerMeasurementListCreateView,
    CustomerViewSet,
    MeasurementDetailView,
)

router = SimpleRouter()
router.register("customers", CustomerViewSet, basename="customer")

urlpatterns = [
    path(
        "customers/<int:customer_id>/measurements/",
        CustomerMeasurementListCreateView.as_view(),
        name="customer-measurement-list",
    ),
    path(
        "measurements/<int:pk>/",
        MeasurementDetailView.as_view(),
        name="measurement-detail",
    ),
]
urlpatterns += router.urls
