"""Productdata-audit: veldconsistentie per categorie.

Hergebruikt services/product_normalization.py en services/product_sources.py
— dezelfde logica als scripts/check_products.py, zonder netwerk en zonder
bestanden te schrijven.
"""

import importlib

from audits.result import SEVERITY_ERROR, SEVERITY_WARNING, AuditIssue
from services.product_normalization import check_field_consistency
from services.product_sources import CATEGORY_PRODUCT_SOURCES, load_category


def _load_rules(rule_key):
    try:
        return importlib.import_module(f"rules.{rule_key}").RULES
    except (ImportError, AttributeError):
        return {}


def run_product_data_check(category=None, params=None):
    slugs = [category] if category else list(CATEGORY_PRODUCT_SOURCES)
    if category and category not in CATEGORY_PRODUCT_SOURCES:
        raise ValueError(f"Onbekende categorie: {category!r}")

    issues = []
    checked = 0
    for slug in slugs:
        data = load_category(slug)
        for err in data.get("load_errors") or []:
            issues.append(
                AuditIssue(
                    code="category_load_error",
                    severity=SEVERITY_ERROR,
                    message=err,
                    category=slug,
                )
            )
        rules = _load_rules(data.get("rule_key") or "")
        rules = {**rules, "category_key": data.get("rule_key") or slug}
        for product in data.get("ranked_products") or []:
            checked += 1
            result = check_field_consistency(product, rules)
            slug_or_name = result.get("slug") or result.get("product_name")
            for msg in result.get("issues") or []:
                issues.append(
                    AuditIssue(
                        code="field_inconsistency",
                        severity=SEVERITY_ERROR,
                        message=msg,
                        category=slug,
                        product_slug=slug_or_name,
                    )
                )
            for msg in result.get("warnings") or []:
                issues.append(
                    AuditIssue(
                        code="field_warning",
                        severity=SEVERITY_WARNING,
                        message=msg,
                        category=slug,
                        product_slug=slug_or_name,
                    )
                )
            for field_name in result.get("missing_fields") or []:
                issues.append(
                    AuditIssue(
                        code="missing_field",
                        severity=SEVERITY_WARNING,
                        message=f"Veld '{field_name}' ontbreekt",
                        category=slug,
                        product_slug=slug_or_name,
                        field=field_name,
                    )
                )
    return issues, {"products_checked": checked}
