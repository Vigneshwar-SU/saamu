from django.test import RequestFactory
from rest_framework.exceptions import AuthenticationFailed, NotFound, ValidationError

from apps.common.exceptions import api_exception_handler


def _build_context():
    factory = RequestFactory()
    request = factory.get("/api/v1/example/")
    return {"request": request}


def _assert_standard_shape(body, expected_code):
    assert body["success"] is False
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert body["error"]["code"] == expected_code
    assert isinstance(body["error"]["message"], str)
    assert body["error"]["message"]


def test_authentication_failed_error_shape():
    response = api_exception_handler(AuthenticationFailed(), _build_context())
    assert response.status_code == 401
    _assert_standard_shape(response.data, "authentication_failed")


def test_not_found_error_shape():
    response = api_exception_handler(NotFound(), _build_context())
    assert response.status_code == 404
    _assert_standard_shape(response.data, "not_found")


def test_validation_error_includes_details():
    exc = ValidationError({"name": ["This field is required."]})
    response = api_exception_handler(exc, _build_context())
    assert response.status_code == 400
    _assert_standard_shape(response.data, "validation_error")
    assert "details" in response.data["error"]


def test_unhandled_exception_returns_internal_error():
    response = api_exception_handler(RuntimeError("boom"), _build_context())
    assert response.status_code == 500
    _assert_standard_shape(response.data, "internal_error")
