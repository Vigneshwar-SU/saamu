"""Phase 21 tests for the secret-redaction logging filter.

The filter runs on the ``LogRecord`` before formatting, so these tests capture
output through a ``StreamHandler`` with the filter attached and assert that
secret values never reach the rendered log line.
"""

import io
import logging
import sys

from config.logging_filters import REDACTED, SanitizeSecretsFilter


def _make_logger(name):
    logger = logging.getLogger(name)
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    return logger


def _render(record):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.addFilter(SanitizeSecretsFilter())
    handler.handle(record)
    return stream.getvalue()


def test_redacts_password_key_value_pair_in_message():
    logger = _make_logger("test-redact-password")
    record = logger.makeRecord(
        logger.name,
        logging.ERROR,
        __file__,
        1,
        "database password=%s",
        ("s3cret-123",),
        None,
    )
    out = _render(record)
    assert "s3cret-123" not in out
    assert REDACTED in out


def test_redacts_authorization_bearer_token():
    logger = _make_logger("test-redact-bearer")
    record = logger.makeRecord(
        logger.name,
        logging.ERROR,
        __file__,
        1,
        "Authorization: Bearer abc.def.ghi-jkl",
        (),
        None,
    )
    out = _render(record)
    assert "abc.def.ghi-jkl" not in out
    assert REDACTED in out


def test_redacts_credentials_embedded_in_url():
    logger = _make_logger("test-redact-url")
    record = logger.makeRecord(
        logger.name,
        logging.ERROR,
        __file__,
        1,
        "connecting to postgres://app_user:hunter2@db.example.com:5432/saamu",
        (),
        None,
    )
    out = _render(record)
    assert "hunter2" not in out
    assert "app_user" not in out
    assert "postgres://%s@db.example.com:5432/saamu" % REDACTED in out


def test_redacts_traceback_exception_message():
    logger = _make_logger("test-redact-traceback")

    try:
        raise ValueError("database rejected connection password=hunter2")
    except ValueError:
        record = logger.makeRecord(
            logger.name,
            logging.ERROR,
            __file__,
            1,
            "operation failed",
            (),
            sys.exc_info(),
        )

    out = _render(record)
    assert "hunter2" not in out
    assert REDACTED in out
    assert "ValueError" in out


def test_plain_messages_are_unchanged():
    logger = _make_logger("test-redact-plain")
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        __file__,
        1,
        "health check completed status=ok",
        (),
        None,
    )
    out = _render(record)
    assert "health check completed status=ok" in out
    assert REDACTED not in out


def test_redaction_is_idempotent():
    logger = _make_logger("test-redact-idempotent")
    record = logger.makeRecord(
        logger.name,
        logging.ERROR,
        __file__,
        1,
        "password=%s",
        ("hunter2",),
        None,
    )
    first = _render(record)
    second = _render(record)
    assert "hunter2" not in first
    assert "hunter2" not in second
    assert first == second
