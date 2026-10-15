"""Optional, response-only diagnostics for requests that reach Django."""

import json
import logging
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings


logger = logging.getLogger("http404")
HEADER_LIMIT = 250


def _referrer(value):
    """Drop queries, fragments and URL credentials before limiting length."""
    if not value:
        return "-"
    try:
        parts = urlsplit(value)
        if parts.scheme not in ("", "http", "https"):
            return "-"
        if parts.scheme and not parts.netloc:
            return "-"
        return urlunsplit((
            parts.scheme,
            parts.netloc.rsplit("@", 1)[-1],
            parts.path,
            "",
            "",
        ))[:HEADER_LIMIT] or "-"
    except ValueError:
        return "-"


def _token(value):
    """Escape control characters and whitespace in unquoted log fields."""
    return json.dumps(value, ensure_ascii=True)[1:-1].replace(" ", r"\u0020")


class Log404RequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if settings.LOG_404_REQUESTS and response.status_code == 404:
            logger.warning(
                "HTTP404 method=%s path=%s referrer=%s user_agent=%s",
                _token(request.method),
                _token(request.path),
                _token(_referrer(request.META.get("HTTP_REFERER", ""))),
                json.dumps(
                    request.META.get("HTTP_USER_AGENT", "-")[:HEADER_LIMIT],
                    ensure_ascii=True,
                ),
            )
        return response
