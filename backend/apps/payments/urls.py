from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import SalaryAdvanceViewSet

router = SimpleRouter()
router.register("advances", SalaryAdvanceViewSet, basename="advance")

urlpatterns = [
    path("", include(router.urls)),
]
