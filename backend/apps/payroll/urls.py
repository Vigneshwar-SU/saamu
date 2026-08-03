from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import PayrollEntryViewSet, PayrollPeriodViewSet

router = SimpleRouter()
router.register("payroll/periods", PayrollPeriodViewSet, basename="payroll-period")
router.register("payroll/entries", PayrollEntryViewSet, basename="payroll-entry")

urlpatterns = [
    path("", include(router.urls)),
]
