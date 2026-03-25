"""
Product monitoring engine.

Provides weekly-check support for availability, page validity, price changes,
and rule compliance.

Live HTTP checks are NOT auto-executed against production.
Placeholder adapters are provided for future integration.
This module NEVER auto-publishes changes or modifies live rankings.
"""

from services.product_validation import validate_product


# ---------------------------------------------------------------------------
# Placeholder adapters for live data fetching
# Replace these with real implementations when live scraping is available.
# ---------------------------------------------------------------------------

def fetch_product_page_status(url: str) -> dict:
    """
    Adapter: check whether a product page URL is reachable and valid.

    Returns a dict with:
      - reachable: bool
      - status_code: int | None
      - error: str | None

    This is a PLACEHOLDER. Replace with actual HTTP HEAD/GET request.
    """
    if not url or not str(url).startswith("http"):
        return {"reachable": False, "status_code": None, "error": "Invalid or missing URL."}
    return {"reachable": None, "status_code": None, "error": "Live check not yet implemented."}


def fetch_product_availability(url: str) -> dict:
    """
    Adapter: scrape or query availability from the product page.

    Returns a dict with:
      - available: bool | None
      - source: str

    This is a PLACEHOLDER. Replace with actual availability check.
    """
    return {"available": None, "source": "not_implemented"}


def fetch_product_price(url: str) -> dict:
    """
    Adapter: scrape or query the current price from the product page.

    Returns a dict with:
      - price: float | None
      - currency: str | None
      - source: str

    This is a PLACEHOLDER. Replace with actual price scraping.
    """
    return {"price": None, "currency": None, "source": "not_implemented"}


# ---------------------------------------------------------------------------
# Monitoring logic
# ---------------------------------------------------------------------------

def _determine_status(validation_result: dict, page_status: dict, avail_status: dict) -> str:
    if validation_result.get("errors"):
        return "REPLACE"
    if validation_result.get("manual_review_required"):
        return "MANUAL_REVIEW"
    if page_status.get("reachable") is False:
        return "FLAG"
    if avail_status.get("available") is False:
        return "FLAG"
    if validation_result.get("warnings"):
        return "FLAG"
    return "OK"


def monitor_product(product: dict, rules: dict, previous_price: float | None = None) -> dict:
    """
    Run a full weekly monitoring check on a single product.

    Does NOT perform live HTTP checks by default.
    To enable live checks, call with live=True once adapters are implemented.

    Returns a monitor result dict. Never modifies any product data.
    """
    name = product.get("name", "(no name)")
    category = rules.get("category_key", "unknown")
    url = product.get("affiliate_url", "")

    validation = validate_product(product, rules)

    page_status = fetch_product_page_status(url)
    avail_status = fetch_product_availability(url)
    price_data = fetch_product_price(url)

    current_price = price_data.get("price")
    if current_price is None:
        current_price = product.get("price")

    price_change_pct = None
    if current_price is not None and previous_price is not None:
        try:
            price_change_pct = round((float(current_price) - float(previous_price)) / float(previous_price) * 100, 1)
        except (TypeError, ZeroDivisionError):
            price_change_pct = None

    status = _determine_status(validation, page_status, avail_status)
    replacement_needed = status in ("REPLACE", "FLAG") and bool(validation.get("errors"))

    return {
        "product_name": name,
        "slug": product.get("slug", ""),
        "category": category,
        "product_url": url,
        "status": status,
        "availability_status": avail_status.get("available"),
        "page_status": page_status.get("reachable"),
        "current_price": current_price,
        "previous_price": previous_price,
        "price_change_pct": price_change_pct,
        "validation_summary": {
            "valid": validation["valid"],
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "missing_fields": validation["missing_fields"],
            "rule_flags": validation["rule_flags"],
        },
        "manual_review_required": validation["manual_review_required"],
        "replacement_needed": replacement_needed,
        "inferred_price_segment": validation["inferred_price_segment"],
    }


def monitor_category(products: list[dict], rules: dict, previous_prices: dict | None = None) -> list[dict]:
    """
    Run monitoring on all products in a category.

    previous_prices: dict mapping product slug → previous price float.
    """
    if previous_prices is None:
        previous_prices = {}

    results = []
    for p in products:
        slug = p.get("slug", "")
        prev_price = previous_prices.get(slug)
        result = monitor_product(p, rules, previous_price=prev_price)
        results.append(result)

    return results
