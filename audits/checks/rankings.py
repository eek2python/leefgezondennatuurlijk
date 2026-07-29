"""Ranking-audit: merkdiversiteit per ranking.

Hergebruikt services/product_validation.py (check_brand_diversity[_scoped])
met het bestaande projectmaximum uit rules/base_rules.py.
"""

from audits.result import SEVERITY_WARNING, AuditIssue
from services.product_sources import CATEGORY_PRODUCT_SOURCES, load_category
from services.product_validation import (
    check_brand_diversity,
    check_brand_diversity_scoped,
)


def _max_per_brand():
    try:
        from rules.base_rules import GLOBAL_RULES
        return int(GLOBAL_RULES.get("max_products_per_brand", 2))
    except (ImportError, AttributeError, TypeError, ValueError):
        return 2


def run_brand_diversity_check(category=None, params=None):
    slugs = [category] if category else list(CATEGORY_PRODUCT_SOURCES)
    if category and category not in CATEGORY_PRODUCT_SOURCES:
        raise ValueError(f"Onbekende categorie: {category!r}")

    max_per_brand = _max_per_brand()
    issues = []
    for slug in slugs:
        data = load_category(slug)
        rankings_raw = data.get("rankings_raw")
        products_dict = data.get("products_dict") or {}
        if data.get("rankings_type") == "dict_by_size" and isinstance(rankings_raw, dict):
            products_by_size = {
                str(size): [products_dict[k] for k in keys if k in products_dict]
                for size, keys in rankings_raw.items()
            }
            result = check_brand_diversity_scoped(products_by_size, max_per_brand)
        else:
            result = check_brand_diversity(
                data.get("ranked_products") or [], max_per_brand
            )
        for brand, info in (result.get("violations") or {}).items():
            names = info.get("products") or info.get("names") or []
            issues.append(
                AuditIssue(
                    code="brand_max_exceeded",
                    severity=SEVERITY_WARNING,
                    message=(
                        f"Merk '{brand}' overschrijdt het maximum van "
                        f"{max_per_brand} producten per ranking: "
                        f"{', '.join(map(str, names))}"
                    ),
                    category=slug,
                    expected=f"≤ {max_per_brand}",
                    actual=str(info.get("count", len(names))),
                )
            )
    return issues, {"max_per_brand": max_per_brand}
