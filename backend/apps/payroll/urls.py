from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    PayrollEntryViewSet,
    PayrollPeriodViewSet,
    SalaryConfigurationViewSet,
)

router = SimpleRouter()
router.register("payroll/periods", PayrollPeriodViewSet, basename="payroll-period")
router.register("payroll/entries", PayrollEntryViewSet, basename="payroll-entry")
router.register(
    "salary-configurations",
    SalaryConfigurationViewSet,
    basename="salary-configuration",
)

urlpatterns = [
    path("", include(router.urls)),
]
