"""
Product monitoring engine.

Performs weekly checks on availability, page reachability, price consistency,
and rule compliance. Uses urllib for lightweight HTTP HEAD checks.

GUARDRAILS:
  - NEVER modifies live product files.
  - NEVER modifies live rankings.
  - NEVER auto-publishes any changes.
  - All flagged results require manual editorial review.
"""

import time
import urllib.request
import urllib.error
from urllib.parse import urlparse

from services.product_validation import validate_product
from services.monitoring_config import (
    MONITORING_CONFIG,
    PAGE_STATUS_OK,
    PAGE_STATUS_REDIRECTED,
    PAGE_STATUS_BROKEN,
    PAGE_STATUS_BLOCKED,
    PAGE_STATUS_UNKNOWN,
    AVAIL_CONSISTENCY_MATCH,
    AVAIL_CONSISTENCY_MISMATCH,
    AVAIL_CONSISTENCY_UNKNOWN,
)


# ---------------------------------------------------------------------------
# HTTP adapter — lightweight HEAD check
# ---------------------------------------------------------------------------

def fetch_product_page_status(url: str, config: dict | None = None) -> dict:
    """
    Perform a lightweight HEAD (or GET) check on the given URL.

    Returns:
      - reachable: bool | None
      - status_code: int | None
      - final_url: str | None
      - classification: PAGE_STATUS_*
      - error: str | None

    Never crashes on network error. Times out safely.
    """
    if not url:
        return {
            "reachable": False, "status_code": None,
            "final_url": None, "classification": PAGE_STATUS_BROKEN,
            "error": "URL ontbreekt.",
        }
    url_str = str(url).strip()
    if not url_str.startswith("http"):
        return {
            "reachable": False, "status_code": None,
            "final_url": None, "classification": PAGE_STATUS_BROKEN,
            "error": f"URL begint niet met http(s): '{url_str[:80]}'.",
        }

    cfg = config or MONITORING_CONFIG
    timeout = cfg.get("request_timeout", 10)
    user_agent = cfg.get("user_agent", "Mozilla/5.0 (compatible; ProductMonitor/1.0)")

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
        "Connection": "close",
    }

    def _do_request(method: str):
        req = urllib.request.Request(url_str, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.geturl()

    try:
        status_code, final_url = _do_request("HEAD")
    except urllib.error.HTTPError as e:
        if e.code == 405:
            try:
                status_code, final_url = _do_request("GET")
            except urllib.error.HTTPError as e2:
                status_code, final_url = e2.code, None
            except Exception:
                return {
                    "reachable": None, "status_code": None,
                    "final_url": None, "classification": PAGE_STATUS_UNKNOWN,
                    "error": "GET-verzoek mislukt na HEAD 405.",
                }
        else:
            status_code, final_url = e.code, None
    except urllib.error.URLError as e:
        return {
            "reachable": False, "status_code": None,
            "final_url": None, "classification": PAGE_STATUS_BROKEN,
            "error": f"Verbindingsfout: {e.reason}",
        }
    except TimeoutError:
        return {
            "reachable": None, "status_code": None,
            "final_url": None, "classification": PAGE_STATUS_UNKNOWN,
            "error": f"Verzoek timeout na {timeout}s.",
        }
    except Exception as e:
        return {
            "reachable": None, "status_code": None,
            "final_url": None, "classification": PAGE_STATUS_UNKNOWN,
            "error": f"Onverwachte fout: {type(e).__name__}: {e}",
        }

    redirected = final_url is not None and final_url != url_str

    if status_code == 200:
        classification = PAGE_STATUS_REDIRECTED if redirected else PAGE_STATUS_OK
    elif status_code in (301, 302, 303, 307, 308):
        classification = PAGE_STATUS_REDIRECTED
    elif status_code == 404:
        classification = PAGE_STATUS_BROKEN
    elif status_code in (403, 429):
        classification = PAGE_STATUS_BLOCKED
    elif status_code is None:
        classification = PAGE_STATUS_UNKNOWN
    elif status_code >= 500:
        classification = PAGE_STATUS_UNKNOWN
    else:
        classification = PAGE_STATUS_UNKNOWN

    reachable = classification in (PAGE_STATUS_OK, PAGE_STATUS_REDIRECTED)

    return {
        "reachable": reachable,
        "status_code": status_code,
        "final_url": final_url,
        "classification": classification,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Availability consistency check
# ---------------------------------------------------------------------------

def check_availability_consistency(stored_availability: str, page_status: dict) -> dict:
    """
    Compare stored availability against signals from the live page check.

    Uses a conservative heuristic:
      - If page is BROKEN → possible mismatch if stored is InStock
      - If page is OK/REDIRECTED → likely consistent with InStock
      - If page is BLOCKED/UNKNOWN → cannot determine

    Returns:
      - stored_availability: str
      - detected_availability: str | None
      - consistency: AVAIL_CONSISTENCY_*
      - notes: str
    """
    classification = page_status.get("classification", PAGE_STATUS_UNKNOWN)

    if classification == PAGE_STATUS_BROKEN:
        detected = "OutOfStock"
        if str(stored_availability).lower() in ("instock", "in_stock", "available"):
            consistency = AVAIL_CONSISTENCY_MISMATCH
            notes = (
                "Pagina is onbereikbaar (BROKEN) maar opgeslagen beschikbaarheid is InStock. "
                "Controleer of het product nog beschikbaar is."
            )
        else:
            consistency = AVAIL_CONSISTENCY_MATCH
            notes = "Pagina is onbereikbaar en opgeslagen beschikbaarheid is ook niet InStock."
    elif classification in (PAGE_STATUS_OK, PAGE_STATUS_REDIRECTED):
        detected = "InStock"
        if str(stored_availability).lower() in ("outofstock", "out_of_stock"):
            consistency = AVAIL_CONSISTENCY_MISMATCH
            notes = (
                "Pagina is bereikbaar maar opgeslagen beschikbaarheid is OutOfStock. "
                "Mogelijk is het product inmiddels weer beschikbaar."
            )
        else:
            consistency = AVAIL_CONSISTENCY_MATCH
            notes = "Pagina bereikbaar, beschikbaarheid waarschijnlijk consistent."
    else:
        detected = None
        consistency = AVAIL_CONSISTENCY_UNKNOWN
        notes = (
            f"Paginastatus is '{classification}' — beschikbaarheidsconsistentie kan niet worden bepaald. "
            "Handmatige controle aanbevolen."
        )

    return {
        "stored_availability": stored_availability,
        "detected_availability": detected,
        "consistency": consistency,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Price consistency check
# ---------------------------------------------------------------------------

def fetch_product_price(url: str, config: dict | None = None) -> dict:
    """
    Placeholder for live price extraction.

    Live price scraping from affiliate redirect URLs is not reliably
    implementable without full HTML parsing and anti-scraping bypass.

    This adapter returns the structure expected by the monitoring engine.
    Replace with real extraction when a reliable data source is available.

    Returns:
      - price: float | None
      - currency: str | None
      - source: str
      - notes: str
    """
    return {
        "price": None,
        "currency": None,
        "source": "not_implemented",
        "notes": (
            "Live prijsextractie is nog niet geïmplementeerd. "
            "Affiliate redirect-URL's vereisen HTML-parsing die buiten de huidige scope valt. "
            "Gebruik de opgeslagen 'price' voor vergelijking."
        ),
    }


def check_price_consistency(
    stored_price: float | None,
    detected_price: float | None,
    alert_pct: float | None = None,
) -> dict:
    """
    Compare stored price with a detected live price.

    Returns:
      - stored_price
      - detected_price
      - price_change_pct: float | None
      - price_alert: bool
      - notes: str
    """
    cfg_alert = alert_pct or MONITORING_CONFIG.get("price_change_alert_pct", 10.0)

    if detected_price is None:
        return {
            "stored_price": stored_price,
            "detected_price": None,
            "price_change_pct": None,
            "price_alert": False,
            "notes": "Geen live prijs gedetecteerd. Opgeslagen prijs kan niet worden vergeleken.",
        }

    if stored_price is None:
        return {
            "stored_price": None,
            "detected_price": detected_price,
            "price_change_pct": None,
            "price_alert": True,
            "notes": f"Live prijs gedetecteerd (€{detected_price:.2f}) maar geen opgeslagen prijs om te vergelijken.",
        }

    try:
        change_pct = round((detected_price - stored_price) / stored_price * 100, 1)
        alert = abs(change_pct) >= cfg_alert
        return {
            "stored_price": stored_price,
            "detected_price": detected_price,
            "price_change_pct": change_pct,
            "price_alert": alert,
            "notes": (
                f"Prijswijziging: {change_pct:+.1f}% "
                f"(opgeslagen €{stored_price:.2f} → gedetecteerd €{detected_price:.2f}). "
                f"{'⚠️ Alert: wijziging > ' + str(cfg_alert) + '%.' if alert else 'Binnen normale marge.'}"
            ),
        }
    except (TypeError, ZeroDivisionError) as e:
        return {
            "stored_price": stored_price,
            "detected_price": detected_price,
            "price_change_pct": None,
            "price_alert": True,
            "notes": f"Prijsvergelijking mislukt: {e}. Handmatige controle aanbevolen.",
        }


# ---------------------------------------------------------------------------
# Status determination
# ---------------------------------------------------------------------------

def _determine_status(
    validation: dict,
    page: dict,
    avail: dict,
    price: dict,
) -> str:
    if validation.get("errors"):
        return "REPLACE"
    if validation.get("manual_review_required"):
        return "MANUAL_REVIEW"
    if page.get("classification") == PAGE_STATUS_BROKEN:
        return "FLAG"
    if avail.get("consistency") == AVAIL_CONSISTENCY_MISMATCH:
        return "FLAG"
    if price.get("price_alert"):
        return "FLAG"
    if validation.get("warnings"):
        return "FLAG"
    return "OK"


# ---------------------------------------------------------------------------
# Single-product monitoring
# ---------------------------------------------------------------------------

def monitor_product(
    product: dict,
    rules: dict,
    previous_price: float | None = None,
    live_check: bool = True,
    config: dict | None = None,
) -> dict:
    """
    Run a full monitoring check on a single product.

    live_check=True: performs real HEAD request to affiliate_url.
    live_check=False: skips HTTP check (for dry runs / testing).

    NEVER modifies product data.
    """
    cfg = config or MONITORING_CONFIG
    name = product.get("name", "(no name)")
    slug = product.get("slug", "")
    category = rules.get("category_key", "unknown")
    url = product.get("affiliate_url", "")

    validation = validate_product(product, rules)

    if live_check and cfg.get("live_checks_enabled", True):
        page_status = fetch_product_page_status(url, cfg)
    else:
        page_status = {
            "reachable": None,
            "status_code": None,
            "final_url": None,
            "classification": PAGE_STATUS_UNKNOWN,
            "error": "Live check uitgeschakeld.",
        }

    stored_avail = product.get("availability", "Unknown")
    avail_consistency = check_availability_consistency(stored_avail, page_status)

    price_data = fetch_product_price(url, cfg)
    detected_price = price_data.get("price")
    stored_price = product.get("price")
    try:
        stored_price = float(stored_price) if stored_price is not None else None
    except (TypeError, ValueError):
        stored_price = None

    price_consistency = check_price_consistency(
        stored_price, detected_price, cfg.get("price_change_alert_pct")
    )

    status = _determine_status(validation, page_status, avail_consistency, price_consistency)
    replacement_needed = status in ("REPLACE", "FLAG") and bool(validation.get("errors"))

    return {
        "product_name": name,
        "slug": slug,
        "brand": product.get("brand", ""),
        "category": category,
        "product_url": url,
        "status": status,
        "page_check": {
            "reachable": page_status["reachable"],
            "status_code": page_status["status_code"],
            "final_url": page_status["final_url"],
            "classification": page_status["classification"],
            "error": page_status["error"],
        },
        "availability": {
            "stored": stored_avail,
            "detected": avail_consistency["detected_availability"],
            "consistency": avail_consistency["consistency"],
            "notes": avail_consistency["notes"],
        },
        "price": {
            "stored": stored_price,
            "detected": detected_price,
            "change_pct": price_consistency["price_change_pct"],
            "alert": price_consistency["price_alert"],
            "notes": price_consistency["notes"],
        },
        "validation_summary": {
            "valid": validation["valid"],
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "missing_fields": validation["missing_fields"],
            "rule_flags": validation["rule_flags"],
            "inferred_price_segment": validation["inferred_price_segment"],
        },
        "manual_review_required": validation["manual_review_required"],
        "replacement_needed": replacement_needed,
    }


# ---------------------------------------------------------------------------
# Category-level monitoring
# ---------------------------------------------------------------------------

def monitor_category(
    products: list[dict],
    rules: dict,
    previous_prices: dict | None = None,
    live_check: bool = True,
    config: dict | None = None,
) -> list[dict]:
    """
    Run monitoring on all products in a category.

    previous_prices: {slug: float} — optional stored prices for change detection.
    live_check: whether to perform real HTTP HEAD checks.
    """
    if previous_prices is None:
        previous_prices = {}
    cfg = config or MONITORING_CONFIG
    delay = cfg.get("delay_between_requests_sec", 0.6)

    results = []
    for i, p in enumerate(products):
        slug = p.get("slug", "")
        prev_price = previous_prices.get(slug)
        result = monitor_product(p, rules, previous_price=prev_price, live_check=live_check, config=cfg)
        results.append(result)

        if live_check and i < len(products) - 1:
            time.sleep(delay)

    return results
