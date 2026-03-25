"""
Configuration for the product monitoring system.

All thresholds and behaviour switches live here.
"""

MONITORING_CONFIG = {
    "request_timeout": 10,
    "max_redirects": 5,
    "delay_between_requests_sec": 0.6,
    "user_agent": (
        "Mozilla/5.0 (compatible; LeefNatuurlijkenGezond-Monitor/1.0; "
        "automated product-link check)"
    ),
    "live_checks_enabled": True,
    "price_change_alert_pct": 10.0,
    "static_images_base": "static/",
}

VALID_AVAILABILITY_VALUES = frozenset([
    "InStock",
    "OutOfStock",
    "PreOrder",
    "LimitedAvailability",
    "Unknown",
])

VALID_CURRENCIES = frozenset(["EUR", "USD", "GBP"])

EXPECTED_RATING_RANGE = (0.0, 5.0)

PRICE_RANGE_THRESHOLDS = {
    "€":    (0.01,  30.0),
    "€€":   (10.0,  80.0),
    "€€€":  (40.0, 200.0),
    "€€€€": (80.0, 9_999.0),
}

PLACEHOLDER_URL_INDICATORS = frozenset([
    "TODO", "todo", "example.com", "placeholder", "#",
])

PAGE_STATUS_OK = "OK"
PAGE_STATUS_REDIRECTED = "REDIRECTED"
PAGE_STATUS_BROKEN = "BROKEN"
PAGE_STATUS_BLOCKED = "BLOCKED"
PAGE_STATUS_UNKNOWN = "UNKNOWN"

AVAIL_CONSISTENCY_MATCH = "MATCH"
AVAIL_CONSISTENCY_MISMATCH = "MISMATCH"
AVAIL_CONSISTENCY_UNKNOWN = "UNKNOWN"
