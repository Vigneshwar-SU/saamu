"""Centralized DRF exception handling for a predictable API error contract.

Every API error response uses the shape:

    {
        "success": false,
        "error": {
            "code": "stable_error_code",
            "message": "Human-readable message",
            "details": {...}   # optional, field-level validation errors
        }
    }

Sensitive implementation details are never exposed to clients.
"""

import logging

from django.http import Http404
from rest_framework import status as http_status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("saamu.api")

DEFAULT_ERROR_CODE = "internal_error"

EXCEPTION_CODE_MAP = {
    AuthenticationFailed: "authentication_failed",
    NotAuthenticated: "authentication_required",
    NotFound: "not_found",
    PermissionDenied: "permission_denied",
    ParseError: "parse_error",
    Throttled: "throttled",
    ValidationError: "validation_error",
}


def _extract_message(detail):
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        if "detail" in detail:
            return _extract_message(detail["detail"])
        parts = [
            part
            for value in detail.values()
            if (part := _extract_message(value)) != "The submitted data is invalid."
        ]
        if parts:
            return "; ".join(parts)
        return "The submitted data is invalid."
    if isinstance(detail, (list, tuple)):
        parts = [
            part
            for item in detail
            if (part := _extract_message(item)) != "The submitted data is invalid."
        ]
        if parts:
            return "; ".join(parts)
        return "The submitted data is invalid."
    return "The submitted data is invalid."


def api_exception_handler(exc, context):
    """Translate exceptions into the standardized error response."""
    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled API exception: %s", exc)
        return Response(
            {
                "success": False,
                "error": {
                    "code": DEFAULT_ERROR_CODE,
                    "message": "An unexpected error occurred.",
                },
            },
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, APIException):
        code = EXCEPTION_CODE_MAP.get(
            type(exc), getattr(exc, "default_code", None) or "api_error"
        )
        message = _extract_message(getattr(exc, "detail", None))
    elif isinstance(exc, Http404):
        # DRF converts Django's Http404 (e.g. get_object_or_404) into a 404
        # response, but the original exception is not an APIException.
        code = "not_found"
        message = "The requested resource was not found."
    else:
        code = DEFAULT_ERROR_CODE
        message = "An unexpected error occurred."

    body = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }

    if isinstance(exc, ValidationError):
        body["error"]["details"] = exc.detail

    response.data = body
    return response
