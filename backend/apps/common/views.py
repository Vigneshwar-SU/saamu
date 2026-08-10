import logging

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from rest_framework import status as http_status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("saamu.api")


class HealthCheckView(APIView):
    """
    Health check API endpoint.
    GET /api/v1/health/
    """

    permission_classes = []
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        database_status = "ok"
        try:
            connection.ensure_connection()
        except Exception:
            # Production logs never include the connection error detail, which
            # can contain database host/user information. Development keeps the
            # traceback for diagnosis (and the secret-redaction logging filter
            # still applies to it).
            logger.error(
                "Database connectivity check failed during health check.",
                exc_info=settings.DEBUG,
            )
            database_status = "unavailable"

        return Response(
            {
                "status": "ok",
                "application": "Saamu Tailors",
                "version": "1.0",
                "database": database_status,
            },
            status=http_status.HTTP_200_OK,
        )


def custom_404(request, exception=None):
    """JSON 404 handler so unmatched URLs return the API error contract."""
    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": "not_found",
                "message": "The requested resource was not found.",
            },
        },
        status=404,
    )


def custom_500(request):
    """JSON 500 handler that never exposes internal details."""
    logger.error("Unhandled server error (status 500).")
    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An internal server error occurred.",
            },
        },
        status=500,
    )
