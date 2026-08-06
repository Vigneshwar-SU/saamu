from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    DashboardSummaryView,
    ExpenseViewSet,
    IncomeViewSet,
    ReportsExportView,
    ReportsSummaryView,
)

router = SimpleRouter()
router.register("income", IncomeViewSet, basename="income")
router.register("expenses", ExpenseViewSet, basename="expense")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"
    ),
    path("reports/summary/", ReportsSummaryView.as_view(), name="reports-summary"),
    path(
        "reports/export/csv/",
        ReportsExportView.as_view(export_format="csv"),
        name="reports-export-csv",
    ),
    path(
        "reports/export/pdf/",
        ReportsExportView.as_view(export_format="pdf"),
        name="reports-export-pdf",
    ),
]
