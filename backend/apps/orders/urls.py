from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.orders.views import OrderViewSet

router = SimpleRouter()
router.register("orders", OrderViewSet, basename="order")

urlpatterns = []
urlpatterns += router.urls
