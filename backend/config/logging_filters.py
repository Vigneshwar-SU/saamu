"""Logging filters that strip sensitive values before records are emitted.

Django logging filters run on the ``LogRecord`` before the formatter renders
it, so a single filter attached to every handler redacts secrets from every
log line regardless of where it goes (console, file, ...). Redaction covers the
documented leak patterns:

- ``key=value`` / ``key: value`` pairs for known secret names (``password``,
  ``secret``, ``token``, ``api_key``, ``authorization``, ``PGPASSWORD``, ...);
- ``Bearer <token>`` authorization headers;
- credentials embedded in URLs (``scheme://user:pass@host/...``).

The filter also redacts exception tracebacks (``record.exc_info``) so a secret
that appears inside an exception message never reaches the log. ``_redact`` is
idempotent, so a record passing through multiple handlers is safe.
"""

import logging
import re
import traceback

REDACTED = "[REDACTED]"

_BEARER_TOKEN = re.compile(r"(?i)(\bBearer\b\s+)(\S+)")

_CREDENTIAL_KEY_PAIR = re.compile(
    r"(?i)(\b(?:password|passwd|pass|secret|token|api[_-]?key|apikey|"
    r"authorization|pgpassword|access[_-]?key|client[_-]?secret)\b)"
    r"(\s*[=:]\s*)(\S+)"
)

_EMBEDDED_CREDENTIALS = re.compile(r"(?i)((?:[a-z][a-z0-9+.\-]*://))([^/@\s]+)(@)")


def _redact(text):
    text = _BEARER_TOKEN.sub(lambda m: m.group(1) + REDACTED, text)
    text = _CREDENTIAL_KEY_PAIR.sub(lambda m: m.group(1) + m.group(2) + REDACTED, text)
    text = _EMBEDDED_CREDENTIALS.sub(lambda m: m.group(1) + REDACTED + m.group(3), text)
    return text


class SanitizeSecretsFilter(logging.Filter):
    """Redact secret values from the message and traceback of a log record."""

    def filter(self, record):
        try:
            message = record.getMessage()
        except Exception:
            message = record.msg if isinstance(record.msg, str) else str(record.msg)
        record.msg = _redact(message)
        record.args = ()
        if record.exc_info:
            try:
                record.exc_text = _redact(
                    "".join(traceback.format_exception(*record.exc_info))
                )
            except Exception:
                pass
            record.exc_info = None
        return True
