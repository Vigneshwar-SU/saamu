"""
URL configuration for Saamu Tailors project.
"""

from django.contrib import admin
from django.urls import include, path

from apps.common.views import custom_404, custom_500

handler404 = custom_404
handler500 = custom_500

urlpatterns = [
    path("admin/", admin.site.urls),
    # API v1 Namespace
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/", include("apps.common.urls")),
    path("api/v1/", include("apps.customers.urls")),
    path("api/v1/", include("apps.orders.urls")),
    path("api/v1/", include("apps.tailors.urls")),
]
