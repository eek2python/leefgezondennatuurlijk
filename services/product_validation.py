"""
Product validation engine.

Validates product dicts against category rule dicts.
Never modifies live data. Never auto-publishes.
"""

from rules.base_rules import GLOBAL_RULES
from services.monitoring_config import AVAILABILITY_TYPO_MAP

_AVAILABILITY_NOTE_VALUES = frozenset([
    "limitedavailability", "limited_availability", "preorder",
])

_AVAILABILITY_VALID = frozenset([v.lower() for v in GLOBAL_RULES["valid_availability_values"]])


def _get_field(product: dict, field: str, rules: dict) -> str | None:
    aliases = rules.get("field_aliases", {})
    actual = aliases.get(field, field)
    return product.get(actual)


def _normalize(value) -> str:
    if isinstance(value, list):
        return " ".join(str(v) for v in value).lower()
    return str(value).lower() if value is not None else ""


def _check_url(url) -> tuple[bool, str]:
    if url is None or url in GLOBAL_RULES["empty_url_values"]:
        return False, "Affiliate-URL ontbreekt of is leeg."
    url_str = str(url)
    for indicator in GLOBAL_RULES["placeholder_url_indicators"]:
        if indicator == "#":
            if url_str.strip() == "#":
                return False, f"Affiliate-URL lijkt een placeholder te bevatten: '{indicator}'."
        elif indicator in url_str:
            return False, f"Affiliate-URL lijkt een placeholder te bevatten: '{indicator}'."
    if not url_str.startswith("http"):
        return False, "Affiliate-URL begint niet met http/https."
    return True, ""


def _infer_price_segment(product: dict, rules: dict) -> str | None:
    price_range_field = rules.get("price_range_field", "price_range")
    field_aliases = rules.get("field_aliases", {})
    actual_field = field_aliases.get(price_range_field, price_range_field)

    price_range = product.get(actual_field)
    if price_range:
        mapping = rules.get("price_segments", {})
        price_range_str = str(price_range)
        for segment, accepted_values in mapping.items():
            if price_range_str in accepted_values:
                return segment
        global_mapping = GLOBAL_RULES["price_range_to_segment"]
        return global_mapping.get(price_range_str)

    raw_price = product.get("price")
    if raw_price is not None:
        try:
            price = float(raw_price)
            thresholds = rules.get("price_thresholds", {})
            budget_max = thresholds.get("budget_max")
            premium_min = thresholds.get("premium_min")
            if budget_max and price <= budget_max:
                return "budget"
            if premium_min and price >= premium_min:
                return "premium"
            return "middenklasse"
        except (ValueError, TypeError):
            pass

    return None


def classify_price_segment(product: dict, rules: dict) -> str | None:
    return _infer_price_segment(product, rules)


def validate_product(product: dict, rules: dict) -> dict:
    errors = []
    warnings = []
    missing_fields = []
    rule_flags = []
    manual_review_required = False

    name = product.get("name", "(no name)")
    category_key = rules.get("category_key", "unknown")

    required = GLOBAL_RULES["required_fields"]
    for field in required:
        actual = rules.get("field_aliases", {}).get(field, field)
        val = product.get(actual)
        if val is None or val == "":
            missing_fields.append(actual)

    for field in GLOBAL_RULES.get("recommended_fields", []):
        actual = rules.get("field_aliases", {}).get(field, field)
        val = product.get(actual)
        if val is None or val == "":
            warnings.append(f"Aanbevolen veld '{actual}' ontbreekt.")

    url = product.get("affiliate_url")
    url_ok, url_msg = _check_url(url)
    if not url_ok:
        errors.append(url_msg)

    availability_raw = product.get("availability", "")
    availability = AVAILABILITY_TYPO_MAP.get(str(availability_raw), str(availability_raw))
    avail_lower = availability.strip().lower()
    if not availability_raw:
        missing_fields.append("availability")
    elif avail_lower in _AVAILABILITY_VALID:
        pass
    elif avail_lower in _AVAILABILITY_NOTE_VALUES:
        rule_flags.append(f"availability_note:{availability}")
    else:
        warnings.append(
            f"Beschikbaarheidsstatus '{availability}' is niet 'InStock'. Controleer beschikbaarheid."
        )

    material = _normalize(_get_field(product, "material", rules))

    allowed_kw = rules.get("allowed_material_keywords", [])
    if allowed_kw and material:
        if not any(kw.lower() in material for kw in allowed_kw):
            errors.append(
                f"Materiaal '{product.get('material', '')}' bevat geen van de toegestane keywords: {allowed_kw}."
            )
            manual_review_required = True

    forbidden_kw = rules.get("forbidden_material_keywords", [])
    for kw in forbidden_kw:
        if kw.lower() in material:
            errors.append(f"Materiaal bevat verboden keyword '{kw}'. Product past niet in deze categorie.")
            manual_review_required = True

    pfas_required = rules.get("pfas_free_required", False)
    if pfas_required:
        pfas_keywords = rules.get("pfas_free_keywords", [])
        search_fields = ["name", "description", "material"]
        combined = " ".join(
            _normalize(product.get(f, "")) for f in search_fields
        )
        if pfas_keywords and not any(kw.lower() in combined for kw in pfas_keywords):
            warnings.append(
                "Geen duidelijke PFAS-vrij aanduiding gevonden in naam, beschrijving of materiaal. "
                "Markeer voor handmatige beoordeling."
            )
            rule_flags.append("pfas_claim_uncertain")
            manual_review_required = True

    for criterion in rules.get("exclusion_criteria", []):
        field = criterion.get("field", "any")
        keyword = criterion.get("keyword", "").lower()
        severity = criterion.get("severity", "warning")
        message = criterion.get("message", "")

        if field == "any":
            search_text = _normalize(product)
        else:
            search_text = _normalize(product.get(field, ""))

        if keyword and keyword in search_text:
            if severity == "error":
                errors.append(message)
                manual_review_required = True
            else:
                warnings.append(message)
                rule_flags.append(f"exclusion_warning:{keyword}")

    if material and not rules.get("allowed_material_keywords"):
        pass
    elif not material and rules.get("allowed_material_keywords"):
        warnings.append("Materiaalveld is leeg — categoriefitness kan niet worden gecontroleerd.")
        rule_flags.append("material_missing")
        manual_review_required = True

    pfas_uncertainty = rules.get("pfas_uncertainty_check", False)
    if pfas_uncertainty:
        features = _normalize(_get_field(product, "features", rules))
        desc = _normalize(product.get("description", ""))
        combined = features + " " + desc
        if "pfas" in combined and "vrij" not in combined and "free" not in combined:
            warnings.append("PFAS-vermelding gevonden zonder 'vrij'/'free' aanduiding. Controleer de PFAS-claim.")
            rule_flags.append("pfas_claim_ambiguous")
            manual_review_required = True

    price_segment = _infer_price_segment(product, rules)

    is_valid = len(errors) == 0 and len(missing_fields) == 0

    return {
        "product_name": name,
        "category_key": category_key,
        "slug": product.get("slug", ""),
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "missing_fields": missing_fields,
        "inferred_price_segment": price_segment,
        "rule_flags": rule_flags,
        "manual_review_required": manual_review_required,
    }


def validate_category_products(products: list[dict], rules: dict) -> list[dict]:
    return [validate_product(p, rules) for p in products]


def check_brand_diversity_scoped(
    products_by_size: dict[str, list[dict]],
    max_per_brand: int = 2,
) -> dict:
    """
    Brand diversity check for dict_by_size categories.

    Evaluates brand diversity per individual size-list rather than
    across all sizes combined. A brand appearing in multiple size-lists
    does not constitute a violation — only exceeding max_per_brand
    within a single size-list does.

    Returns a merged view of violations across all size-lists.
    """
    all_violations: dict[str, dict] = {}
    size_details: dict[str, dict] = {}

    for size_key, size_products in products_by_size.items():
        result = check_brand_diversity(size_products, max_per_brand)
        size_details[str(size_key)] = result
        for brand, info in result["violations"].items():
            if brand not in all_violations:
                all_violations[brand] = {
                    "brand": brand,
                    "violations_in_sizes": [],
                    "message": (
                        f"Merk '{brand}' overschrijdt max {max_per_brand} producten "
                        f"in minstens één maatlijst."
                    ),
                }
            all_violations[brand]["violations_in_sizes"].append({
                "size": str(size_key),
                "count": info["count"],
                "products": info["products"],
            })

    return {
        "violations": all_violations,
        "has_violations": len(all_violations) > 0,
        "size_details": size_details,
        "scoped": True,
        "note": "Merkdiversiteit beoordeeld per maatlijst (niet over alle maten gecombineerd).",
    }


def check_brand_diversity(products: list[dict], max_per_brand: int = 2) -> dict:
    brand_counts: dict[str, list[str]] = {}
    for p in products:
        brand = str(p.get("brand", "unknown")).strip().lower()
        name = p.get("name", "unknown")
        if brand not in brand_counts:
            brand_counts[brand] = []
        brand_counts[brand].append(name)

    violations = {}
    for brand, names in brand_counts.items():
        if len(names) > max_per_brand:
            violations[brand] = {
                "count": len(names),
                "products": names,
                "max_allowed": max_per_brand,
                "message": (
                    f"Merk '{brand}' heeft {len(names)} producten in de lijst "
                    f"(max {max_per_brand} toegestaan): {names}"
                ),
            }

    return {
        "brand_counts": {b: len(ns) for b, ns in brand_counts.items()},
        "violations": violations,
        "has_violations": len(violations) > 0,
    }
