"""
URL configuration for Saamu Tailors project.
"""

from django.contrib import admin
from django.urls import include, path, re_path

from apps.common.views import custom_404, custom_500
from config.spa import spa_fallback

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
    path("api/v1/", include("apps.attendance.urls")),
    path("api/v1/", include("apps.payroll.urls")),
    path("api/v1/", include("apps.payments.urls")),
    path("api/v1/", include("apps.finance.urls")),
    path("api/v1/", include("apps.billing.urls")),
    # SPA fallback for the compiled React build (config/spa.py). Must be last:
    # it catches only requests that no backend route matched, and returns
    # index.html so React Router client routes (/customers, /orders, ...) work
    # on refresh/direct open. Backend-owned prefixes (api/admin/static/media)
    # are re-raised as Http404 and still produce the JSON error contract.
    re_path(r"^(?P<path>.*)$", spa_fallback),
]
