"""
Product field normalization and consistency checks.

All normalization is in-memory only.
Source files are NEVER modified.
"""

from services.monitoring_config import (
    VALID_AVAILABILITY_VALUES,
    VALID_CURRENCIES,
    EXPECTED_RATING_RANGE,
    PRICE_RANGE_THRESHOLDS,
    PLACEHOLDER_URL_INDICATORS,
    MONITORING_CONFIG,
)


# ---------------------------------------------------------------------------
# Field alias map for RVS products
# ---------------------------------------------------------------------------

RVS_FIELD_ALIASES = {
    "diameter": "diameter_cm",
    "price_range": "price_segment",
    "features": "key_features",
}


def _get(product: dict, field: str, is_rvs: bool = False) -> object:
    if is_rvs:
        actual = RVS_FIELD_ALIASES.get(field, field)
        return product.get(actual)
    return product.get(field)


def _is_rvs(product: dict) -> bool:
    rule_key = product.get("_rule_key", "")
    return "rvs" in str(rule_key).lower()


# ---------------------------------------------------------------------------
# Individual field checks
# ---------------------------------------------------------------------------

def _check_name(product: dict) -> list[str]:
    issues = []
    name = product.get("name")
    if not name:
        issues.append("Veld 'name' ontbreekt of is leeg.")
    elif len(str(name).strip()) < 3:
        issues.append(f"Productnaam '{name}' is te kort om betrouwbaar te zijn.")
    return issues


def _check_brand(product: dict) -> list[str]:
    issues = []
    brand = product.get("brand")
    if not brand:
        issues.append("Veld 'brand' ontbreekt of is leeg.")
    elif len(str(brand).strip()) < 2:
        issues.append(f"Merk '{brand}' is verdacht kort.")
    return issues


def _check_material(product: dict) -> list[str]:
    issues = []
    material = product.get("material")
    if not material:
        issues.append("Veld 'material' ontbreekt. Categoriefitness kan niet worden gecontroleerd.")
    return issues


def _check_price(product: dict, is_rvs: bool = False) -> list[str]:
    issues = []
    if is_rvs:
        price_segment = product.get("price_segment")
        if not price_segment:
            issues.append("RVS product: veld 'price_segment' ontbreekt.")
        return issues

    price = product.get("price")
    if price is None:
        issues.append("Veld 'price' ontbreekt.")
        return issues
    try:
        price_float = float(price)
        if price_float <= 0:
            issues.append(f"Prijs '{price}' is nul of negatief.")
        elif price_float > 5000:
            issues.append(f"Prijs '{price}' is onwaarschijnlijk hoog (>€5000).")
    except (TypeError, ValueError):
        issues.append(f"Prijs '{price}' is geen geldig getal.")
    return issues


def _check_currency(product: dict) -> list[str]:
    issues = []
    currency = product.get("currency")
    if not currency:
        return []
    if str(currency).upper() not in VALID_CURRENCIES:
        issues.append(f"Valuta '{currency}' is niet EUR/USD/GBP.")
    return issues


def _check_availability(product: dict) -> list[str]:
    issues = []
    avail = product.get("availability")
    if not avail:
        issues.append("Veld 'availability' ontbreekt.")
        return issues
    if str(avail) not in VALID_AVAILABILITY_VALUES:
        issues.append(
            f"Beschikbaarheidsstatus '{avail}' is niet één van de verwachte waarden: "
            f"{sorted(VALID_AVAILABILITY_VALUES)}."
        )
    return issues


def _check_affiliate_url(product: dict) -> list[str]:
    issues = []
    url = product.get("affiliate_url")
    if not url:
        issues.append("Veld 'affiliate_url' ontbreekt of is leeg.")
        return issues
    url_str = str(url)
    if not url_str.startswith("http"):
        issues.append(f"Affiliate-URL begint niet met http(s): '{url_str[:80]}'.")
    for indicator in PLACEHOLDER_URL_INDICATORS:
        if indicator in url_str:
            issues.append(f"Affiliate-URL lijkt een placeholder te zijn (bevat '{indicator}').")
            break
    return issues


def _check_image(product: dict) -> list[str]:
    issues = []
    image = product.get("image")
    image_path = product.get("image_path")
    if not image:
        issues.append("Veld 'image' ontbreekt.")
    if not image_path:
        issues.append("Veld 'image_path' ontbreekt.")
    if image and image_path:
        static_base = MONITORING_CONFIG.get("static_images_base", "static/")
        full_path = f"{static_base}{image_path}/{image}"
        from pathlib import Path
        p = Path(full_path)
        if not p.exists():
            issues.append(f"Afbeeldingsbestand niet gevonden op verwacht pad: '{full_path}'.")
    return issues


def _check_rating(product: dict) -> list[str]:
    issues = []
    rating = product.get("rating")
    rating_count = product.get("rating_count")
    if rating is None:
        issues.append("Veld 'rating' ontbreekt.")
    else:
        try:
            r = float(rating)
            lo, hi = EXPECTED_RATING_RANGE
            if not (lo <= r <= hi):
                issues.append(f"Rating '{rating}' valt buiten het verwachte bereik ({lo}–{hi}).")
        except (TypeError, ValueError):
            issues.append(f"Rating '{rating}' is geen geldig getal.")

    if rating_count is None:
        issues.append("Veld 'rating_count' ontbreekt.")
    else:
        try:
            rc = int(rating_count)
            if rc < 0:
                issues.append(f"rating_count '{rating_count}' is negatief.")
        except (TypeError, ValueError):
            issues.append(f"rating_count '{rating_count}' is geen geheel getal.")
    return issues


def _check_price_range_vs_price(product: dict) -> list[str]:
    issues = []
    price_range = product.get("price_range")
    price = product.get("price")
    if not price_range or price is None:
        return issues
    thresholds = PRICE_RANGE_THRESHOLDS.get(str(price_range))
    if thresholds is None:
        issues.append(f"price_range '{price_range}' is geen verwachte waarde (€/€€/€€€/€€€€).")
        return issues
    try:
        price_float = float(price)
        lo, hi = thresholds
        if not (lo <= price_float <= hi):
            issues.append(
                f"Prijs €{price_float:.2f} past niet bij price_range '{price_range}' "
                f"(verwacht: €{lo}–€{hi})."
            )
    except (TypeError, ValueError):
        pass
    return issues


def _check_award_vs_badge_policy(product: dict, rules: dict) -> list[str]:
    issues = []
    award = product.get("award", "")
    if not award:
        return issues
    badge_policy = rules.get("badge_policy", {})
    core = badge_policy.get("core", [])
    optional = badge_policy.get("optional", [])
    allowed = core + optional
    if not allowed:
        return issues
    award_text = str(award)
    for badge in allowed:
        if badge.lower() in award_text.lower():
            return issues
    if award_text.strip():
        issues.append(
            f"Badgetekst '{award_text}' komt niet overeen met het toegestane badgebeleid: {allowed}."
        )
    return issues


# ---------------------------------------------------------------------------
# Normalize a single product (in-memory only)
# ---------------------------------------------------------------------------

def normalize_product(product: dict) -> dict:
    """
    Return a normalized in-memory copy of the product dict.
    Source file is NEVER modified.

    Normalization applies:
    - strip whitespace from string fields
    - lowercase availability for comparison
    - coerce price to float if possible
    """
    normalized = {}
    for key, value in product.items():
        if isinstance(value, str):
            normalized[key] = value.strip()
        else:
            normalized[key] = value

    if "price" in normalized and normalized["price"] is not None:
        try:
            normalized["price"] = float(normalized["price"])
        except (TypeError, ValueError):
            pass

    if "rating" in normalized and normalized["rating"] is not None:
        try:
            normalized["rating"] = float(normalized["rating"])
        except (TypeError, ValueError):
            pass

    if "rating_count" in normalized and normalized["rating_count"] is not None:
        try:
            normalized["rating_count"] = int(normalized["rating_count"])
        except (TypeError, ValueError):
            pass

    return normalized


# ---------------------------------------------------------------------------
# Consistency check for a single product
# ---------------------------------------------------------------------------

def check_field_consistency(product: dict, rules: dict) -> dict:
    """
    Run all field consistency checks against a product dict.

    Returns:
      - product_name: str
      - slug: str
      - issues: list[str]  — any detected inconsistency
      - warnings: list[str]
      - missing_fields: list[str]
      - has_issues: bool
    """
    is_rvs_product = "rvs" in rules.get("category_key", "").lower()
    normalized = normalize_product(product)

    all_issues = []
    warnings = []
    missing_fields = []

    for issue in _check_name(normalized):
        if "ontbreekt" in issue:
            missing_fields.append("name")
        else:
            warnings.append(issue)

    for issue in _check_brand(normalized):
        if "ontbreekt" in issue:
            missing_fields.append("brand")
        else:
            warnings.append(issue)

    for issue in _check_material(normalized):
        missing_fields.append("material")

    for issue in _check_price(normalized, is_rvs=is_rvs_product):
        if "ontbreekt" in issue:
            missing_fields.append("price" if not is_rvs_product else "price_segment")
        else:
            all_issues.append(issue)

    all_issues.extend(_check_currency(normalized))
    
    for issue in _check_availability(normalized):
        if "ontbreekt" in issue:
            missing_fields.append("availability")
        else:
            all_issues.append(issue)

    for issue in _check_affiliate_url(normalized):
        if "ontbreekt" in issue:
            missing_fields.append("affiliate_url")
        else:
            all_issues.append(issue)

    warnings.extend(_check_image(normalized))

    for issue in _check_rating(normalized):
        if "ontbreekt" in issue:
            field = "rating" if "rating'" in issue else "rating_count"
            missing_fields.append(field)
        else:
            all_issues.append(issue)

    all_issues.extend(_check_price_range_vs_price(normalized))
    warnings.extend(_check_award_vs_badge_policy(normalized, rules))

    return {
        "product_name": product.get("name", "(no name)"),
        "slug": product.get("slug", ""),
        "issues": all_issues,
        "warnings": warnings,
        "missing_fields": list(set(missing_fields)),
        "has_issues": len(all_issues) > 0 or len(missing_fields) > 0,
    }


def check_category_consistency(products: list[dict], rules: dict) -> list[dict]:
    """Run consistency checks on all products in a category."""
    return [check_field_consistency(p, rules) for p in products]


def derive_full_image_path(product: dict) -> str | None:
    """Derive the full relative static path for a product's image."""
    image = product.get("image")
    image_path = product.get("image_path")
    if not image or not image_path:
        return None
    base = MONITORING_CONFIG.get("static_images_base", "static/")
    return f"{base}{image_path}/{image}"
