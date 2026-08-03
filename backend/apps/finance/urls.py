from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import DashboardSummaryView, ExpenseViewSet, IncomeViewSet

router = SimpleRouter()
router.register("income", IncomeViewSet, basename="income")
router.register("expenses", ExpenseViewSet, basename="expense")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"
    ),
]
