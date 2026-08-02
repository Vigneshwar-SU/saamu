from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    PieceRateViewSet,
    TailorEarningsSummaryView,
    TailorViewSet,
    WorkAssignmentViewSet,
)

router = SimpleRouter()
router.register("tailors", TailorViewSet, basename="tailor")
router.register("piece-rates", PieceRateViewSet, basename="piece-rate")
router.register("work-assignments", WorkAssignmentViewSet, basename="work-assignment")

urlpatterns = [
    path("", include(router.urls)),
    path("tailor-earnings/summary/", TailorEarningsSummaryView.as_view()),
]
