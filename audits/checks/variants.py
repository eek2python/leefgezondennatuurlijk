"""Gedeelde variant- en prijsniveauauditlogica.

Eén implementatie voor zowel ``python manage.py audit_product_variants``
als het admin-auditdashboard. Read-only: wijzigt nooit productdata.
"""

import copy
import json
import re
from pathlib import Path

from django.conf import settings
from django.test import RequestFactory

from audits.result import (
    SEVERITY_ERROR,
    SEVERITY_WARNING,
    AuditIssue,
)
from utils.pricing import get_price_range, has_price_range_config
from utils.variant_helpers import prepare_product_variants

CATEGORY_SOURCES = {
    "koekenpannen": "products.products_koekenpannen",
    "hapjespannen": "products.products_hapjespannen",
    "wokpannen": "products.products_wokpannen",
    "rvs-koekenpannen": "products.products_rvs_koekenpannen",
    "koolstofstalen-koekenpannen": "products.products_koolstofstaal_koekenpannen",
    "gietijzeren-koekenpannen": "products.products_gietijzeren_koekenpannen",
    "snijplanken": "products.products_snijplanken",
    "airfryers": "products.products_airfryers",
    "vershoudbakjes": "products.products_vershoudcontainers",
}

#: Categoriekeys zoals het dashboard/command ze aanbiedt.
AUDIT_CATEGORIES = tuple(sorted(CATEGORY_SOURCES))

#: Auditcategorienaam → categoriekey van utils/pricing.py.
PRICING_CATEGORY_KEYS = {
    "koekenpannen": "koekenpannen",
    "hapjespannen": "hapjespannen",
    "wokpannen": "wokpannen",
    "rvs-koekenpannen": "rvs-koekenpannen",
    "koolstofstalen-koekenpannen": "koolstofstalen-koekenpannen",
    "gietijzeren-koekenpannen": "gietijzeren-koekenpannen",
    "snijplanken": "snijplanken",
    "airfryers": "airfryers",
    "vershoudbakjes": "vershoudcontainers",
}

#: Templates met vergelijkingstabellen die op onveilige commerciële
#: fallbacks worden gescand.
COMPARISON_TEMPLATES = [
    "templates/vershoudcontainers.html",
    "templates/koekenpannen.html",
    "templates/hapjespannen.html",
    "templates/wokpannen.html",
    "templates/rvs-koekenpannen.html",
    "templates/koolstofstaal-koekenpannen.html",
    "templates/gietijzeren-koekenpannen.html",
    "templates/snijplanken.html",
    "templates/airfryers.html",
]

#: Variant-JavaScript en de wisbranches die aanwezig moeten zijn om
#: stale waarden bij variantwissel te voorkomen.
JS_CLEAR_REQUIREMENTS = {
    "static/assets/js/variant-selector.js": [
        'removeAttribute("href")',   # koopknop zonder URL wist oude href
        'variant.summary || ""',      # samenvatting wordt gezet óf gewist
        'variant.capacity || ""',     # capaciteit wordt gezet óf gewist
    ],
    "static/assets/js/variants.js": [
        'removeAttribute("href")',   # swatch zonder URL (en zonder base) wist href
        'price || ""',                # prijs wordt gezet óf gewist
    ],
}

_UNSAFE_FIRSTOF_RE = re.compile(
    r"\{%\s*firstof\s+[^%]*affiliate_url[^%]*affiliate_url[^%]*%\}"
)

#: Patronen die op een zichtbare concrete prijs in publieke templates duiden.
#: price_range/display_price_range zijn prijsniveaus en dus toegestaan.
_CONCRETE_PRICE_RE = re.compile(
    r"\{\{\s*[\w.]*\bprice\s*(?:\|[^}]*)?\}\}|€\s*\{\{"
)


def _load_products(module_path):
    import importlib

    return importlib.import_module(module_path).PRODUCTS


def _is_button_variant(variant):
    return isinstance(variant, dict) and bool(variant.get("id"))


def _selected_sources(category=None):
    if category:
        if category not in CATEGORY_SOURCES:
            raise ValueError(f"Onbekende categorie: {category!r}")
        return {category: CATEGORY_SOURCES[category]}
    return dict(CATEGORY_SOURCES)


# ---------------------------------------------------------------------------
# Structurele variantaudit per categorie
# ---------------------------------------------------------------------------
def audit_category(name, module_path):
    errors, warnings = [], []
    products = _load_products(module_path)
    button_count = 0
    swatch_count = 0

    for key, product in products.items():
        variants = product.get("variants")
        if not variants:
            continue
        if all(_is_button_variant(v) for v in variants):
            button_count += 1
            e, w = _audit_button_product(name, key, product)
            errors.extend(e)
            warnings.extend(w)
        else:
            swatch_count += 1
            warnings.extend(_audit_swatch_product(name, key, product))

    # Mutatiecontrole op de voorbereidingshelper zelf (deep-copy pad).
    before = copy.deepcopy(products)
    for key in products:
        work = copy.deepcopy(products[key])
        try:
            prepare_product_variants(work)
        except Exception as exc:  # structurele datafout
            errors.append(("invalid_variant_data", name, key, str(exc)))
    if products != before:
        errors.append(
            (
                "source_product_mutated",
                name,
                "-",
                "Brondata gewijzigd tijdens audit (mag nooit gebeuren)",
            )
        )

    return {
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "category": name,
            "products": len(products),
            "button_variants": button_count,
            "swatch_variants": swatch_count,
        },
    }


def _audit_button_product(category, key, product):
    errors, warnings = [], []
    variants = product["variants"]
    defaults = [v for v in variants if v.get("is_default")]
    if len(defaults) > 1:
        errors.append(
            ("multiple_default_variants", category, key, "Meerdere is_default")
        )
    if not defaults:
        errors.append(
            (
                "missing_display_variant",
                category,
                key,
                "Geen is_default-variant (eerste variant wordt gebruikt)",
            )
        )
    for v in variants:
        vid = v.get("id", "?")
        if not v.get("affiliate_url"):
            warnings.append(
                (
                    "missing_variant_url",
                    category,
                    key,
                    f"Variant '{vid}' zonder eigen affiliate-URL "
                    "(CTA toont bewust de uitgeschakelde staat)",
                )
            )
        if v.get("price") in (None, ""):
            warnings.append(
                (
                    "missing_variant_price",
                    category,
                    key,
                    f"Variant '{vid}' zonder eigen prijs "
                    "(geen Offer in JSON-LD voor deze displayvariant)",
                )
            )
    return errors, warnings


def _audit_swatch_product(category, key, product):
    """Kleurswatches: productniveau is de gedocumenteerde familiefallback.
    Alleen inconsistenties tussen JSON-LD-basis (productniveau) en de
    default (eerste) swatch worden gerapporteerd."""
    issues = []
    first = product["variants"][0]
    for variant in product["variants"]:
        if not variant.get("affiliate_url") and not product.get("affiliate_url"):
            issues.append(
                (
                    "missing_variant_url",
                    category,
                    key,
                    f"Swatch '{variant.get('name')}' zonder URL en zonder familiefallback",
                )
            )
    if (
        first.get("price") is not None
        and product.get("price") is not None
        and first["price"] != product["price"]
    ):
        issues.append(
            (
                "inconsistent_jsonld_variant",
                category,
                key,
                f"JSON-LD gebruikt productniveauprijs {product['price']} maar de "
                f"getoonde defaultswatch '{first.get('name')}' kost {first['price']}",
            )
        )
    if first.get("affiliate_url") and product.get("affiliate_url") and (
        first["affiliate_url"] != product["affiliate_url"]
    ):
        issues.append(
            (
                "inconsistent_jsonld_variant",
                category,
                key,
                "Default-swatch-URL wijkt af van productniveau-URL (JSON-LD-basis)",
            )
        )
    return issues


# ---------------------------------------------------------------------------
# Prijsniveau-audit
# ---------------------------------------------------------------------------
def audit_price_levels(name, module_path):
    """Read-only prijsniveau-audit: vergelijkt handmatige
    ``price_range``-velden met het uit ``price`` berekende niveau.
    Alleen categorieën met definitieve grenzen (utils/pricing.py) geven
    ``price_range_mismatch``-waarschuwingen; overige zijn report-only.
    Er worden nooit prijzen of productdata gewijzigd."""
    errors, warnings, price_rows = [], [], []
    pricing_key = PRICING_CATEGORY_KEYS.get(name, name)
    configured = has_price_range_config(pricing_key)

    def check_price(key, variant_label, price, manual):
        computed = get_price_range(price, pricing_key) if configured else None
        price_rows.append(
            (name, key, variant_label, price, manual or "—", computed or "—")
        )
        if price is None:
            warnings.append(
                ("missing_price", name, key,
                 f"{variant_label or 'product'}: geen numerieke prijs")
            )
            return
        try:
            numeric = float(price)
        except (TypeError, ValueError):
            errors.append(
                ("invalid_price", name, key,
                 f"{variant_label or 'product'}: prijs {price!r} is niet numeriek")
            )
            return
        if numeric < 0:
            errors.append(
                ("negative_price", name, key,
                 f"{variant_label or 'product'}: negatieve prijs {price!r}")
            )
            return
        if configured and manual and manual != computed:
            warnings.append(
                ("price_range_mismatch", name, key,
                 f"{variant_label or 'product'}: handmatig '{manual}' ≠ "
                 f"berekend '{computed}' (berekend niveau is leidend "
                 "bij rendering; brondata blijft ongewijzigd)")
            )
        if configured and computed and not manual and variant_label == "":
            warnings.append(
                ("stale_price_range", name, key,
                 "price_range ontbreekt terwijl een geldige prijs bestaat "
                 "(niveau wordt bij rendering berekend)")
            )

    products = _load_products(module_path)
    for key, product in products.items():
        variants = product.get("variants") or []
        swatch = bool(variants) and not all(_is_button_variant(v) for v in variants)
        if swatch:
            for v in variants:
                check_price(key, v.get("name") or "?", v.get("price"),
                            v.get("price_range"))
        elif variants:
            for v in variants:
                check_price(key, v.get("id") or "?", v.get("price"),
                            v.get("price_range"))
        else:
            check_price(key, "", product.get("price"), product.get("price_range"))
    return errors, warnings, price_rows


# ---------------------------------------------------------------------------
# Template-, JS- en view-audits (projectbreed)
# ---------------------------------------------------------------------------
def audit_concrete_price_templates():
    """Publieke templates mogen alleen prijsniveaus tonen; een zichtbare
    concrete prijs ({{ ...price }}, € {{ ... }}) is een fout."""
    issues = []
    base = Path(settings.BASE_DIR)
    for path in sorted((base / "templates").rglob("*.html")):
        rel = str(path.relative_to(base))
        if "/admin" in rel:
            continue
        for i, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            for match in _CONCRETE_PRICE_RE.finditer(line):
                snippet = match.group(0)
                if "price_range" in snippet or "price_last_checked" in snippet:
                    continue
                issues.append(
                    ("visible_concrete_price_detected", "templates", rel,
                     f"regel {i}: {snippet[:60]}")
                )
    return issues


def audit_templates():
    issues = []
    base = Path(settings.BASE_DIR)
    for rel in COMPARISON_TEMPLATES:
        path = base / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for match in _UNSAFE_FIRSTOF_RE.finditer(text):
            issues.append(
                (
                    "unsafe_template_firstof",
                    "templates",
                    rel,
                    f"Commerciële firstof-fallback: {match.group(0)[:80]}",
                )
            )
    return issues


def audit_js_clear_branches():
    """Statische controle: variant-JavaScript moet expliciete
    wisbranches bevatten (set-or-clear), anders blijven waarden van een
    vorige variant staan."""
    issues = []
    base = Path(settings.BASE_DIR)
    for rel, needles in JS_CLEAR_REQUIREMENTS.items():
        path = base / rel
        if not path.exists():
            issues.append(
                ("missing_variant_clear_branch", "javascript", rel, "Bestand ontbreekt")
            )
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                issues.append(
                    (
                        "missing_variant_clear_branch",
                        "javascript",
                        rel,
                        f"Verwachte wisbranche ontbreekt: {needle}",
                    )
                )
    return issues


def audit_view_deepcopy_usage():
    """Views die knopvariantproducten verrijken moeten deep copies
    gebruiken; shallow dict() deelt geneste variant-dicts met de
    brondata."""
    issues = []
    views_path = Path(settings.BASE_DIR) / "products" / "views.py"
    text = views_path.read_text(encoding="utf-8")
    for pattern, where in (
        (r"copy\.deepcopy\(VERSHOUDCONTAINERS_PRODUCTS\[", "vershoudcontainers-view"),
        (r"copy\.deepcopy\(entry\[\"data\"\]\)", "product_detail-view"),
    ):
        if not re.search(pattern, text):
            issues.append(
                (
                    "stale_variant_value_risk",
                    "views",
                    where,
                    "Geen deep copy vóór verrijking van variantproducten",
                )
            )
    return issues


def audit_runtime_consistency():
    """Realistische flow: draai de echte vershoudbakjesview en controleer
    (a) brondata-non-mutatie, (b) kaart/tabel-consistentie en
    (c) JSON-LD-consistentie met de displayvariant."""
    errors, warnings = [], []
    from products import views as product_views
    from products.products_vershoudcontainers import PRODUCTS

    factory = RequestFactory()
    before = copy.deepcopy(PRODUCTS)
    for query in ("", "?uitvoering=enkel&formaat=groot", "?uitvoering=3-delig"):
        request = factory.get(f"/vershoudcontainers/{query}")
        response = product_views.vershoudcontainers(request)
        html = response.content.decode()

        rows = _extract_context_rows(request)
        for row in rows:
            product = row["product"]
            if product.get("shape_variants"):
                dv = product.get("default_variant") or {}
                if row.get("display_variant_id") != dv.get("id"):
                    errors.append(
                        (
                            "inconsistent_card_table_variant",
                            "vershoudbakjes",
                            product.get("slug", "?"),
                            f"Tabelvariant {row.get('display_variant_id')} ≠ "
                            f"kaartvariant {dv.get('id')} ({query or 'default'})",
                        )
                    )
                if row.get("affiliate_url") != (dv.get("affiliate_url") or ""):
                    errors.append(
                        (
                            "cross_variant_affiliate_fallback",
                            "vershoudbakjes",
                            product.get("slug", "?"),
                            f"Tabel-URL wijkt af van displayvariant ({query or 'default'})",
                        )
                    )

        for ld in re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S
        ):
            data = json.loads(ld)
            if data.get("@type") != "ItemList":
                continue
            for element in data.get("itemListElement", []):
                item = element.get("item", {})
                offer = item.get("offers")
                if offer is not None and (
                    not offer.get("url") or offer.get("price") in (None, "")
                ):
                    errors.append(
                        (
                            "inconsistent_jsonld_variant",
                            "vershoudbakjes",
                            item.get("name", "?"),
                            f"Offer zonder geldige prijs/URL ({query or 'default'})",
                        )
                    )
    if PRODUCTS != before:
        errors.append(
            (
                "source_product_mutated",
                "vershoudbakjes",
                "-",
                "Brondata gemuteerd door de echte view-flow",
            )
        )
    return errors, warnings


def _extract_context_rows(request):
    """Herbouw comparison_rows via dezelfde codepaden als de view."""
    from products import views as product_views

    selected_type = product_views.get_selected_storage_type(request)
    selected_size = product_views.get_selected_storage_size(request)
    type_key = selected_type["key"]
    size_key = selected_size["key"]
    keys = product_views.VERSHOUDCONTAINERS_RANKINGS.get(type_key, [])
    products = [
        copy.deepcopy(product_views.VERSHOUDCONTAINERS_PRODUCTS[k])
        for k in keys
        if k in product_views.VERSHOUDCONTAINERS_PRODUCTS
    ]
    product_views._enrich_products(products)
    for p in products:
        product_views.prepare_storage_product(p, size_key)
    from utils.product_helpers import filter_products_by_storage_size
    from utils.variant_helpers import resolve_commercial_fields

    products = filter_products_by_storage_size(products, size_key)
    rows = []
    for p in products:
        dv = p.get("default_variant") if p.get("shape_variants") else None
        commercial = resolve_commercial_fields(p, dv)
        rows.append(
            {
                "product": p,
                "display_variant_id": dv.get("id") if dv else None,
                "affiliate_url": commercial["affiliate_url"],
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Volledige variantaudit (gestructureerd; gedeeld door command en admin)
# ---------------------------------------------------------------------------
def run_variant_audit(category=None):
    """Voer de volledige variantaudit uit.

    Returns dict met ``errors``/``warnings`` (tuples van (code, categorie,
    key, bericht)), ``summaries`` en ``price_rows``. Zowel het
    managementcommand als het admindashboard bouwen hun weergave hieruit op.
    """
    sources = _selected_sources(category)
    errors, warnings, summaries, price_rows = [], [], [], []
    for name, module_path in sources.items():
        result = audit_category(name, module_path)
        errors.extend(result["errors"])
        warnings.extend(result["warnings"])
        summaries.append(result["summary"])

        e, w, pr = audit_price_levels(name, module_path)
        errors.extend(e)
        warnings.extend(w)
        price_rows.extend(pr)

    warnings.extend(audit_templates())
    errors.extend(audit_concrete_price_templates())
    errors.extend(audit_js_clear_branches())
    errors.extend(audit_view_deepcopy_usage())

    if category in (None, "vershoudbakjes"):
        e, w = audit_runtime_consistency()
        errors.extend(e)
        warnings.extend(w)

    return {
        "errors": errors,
        "warnings": warnings,
        "summaries": summaries,
        "price_rows": price_rows,
    }


def _tuples_to_issues(errors, warnings):
    issues = []
    for severity, items in ((SEVERITY_ERROR, errors), (SEVERITY_WARNING, warnings)):
        for code, cat, key, msg in items:
            issues.append(
                AuditIssue(
                    code=code,
                    severity=severity,
                    message=msg,
                    category=cat,
                    product_slug=None if key in ("-", "") else str(key),
                )
            )
    return issues


def run_variant_check(category=None, params=None):
    """Registry-runner: variantaudit zonder de prijsniveau-issues
    (die heeft een eigen audit)."""
    sources = _selected_sources(category)
    errors, warnings, summaries = [], [], []
    for name, module_path in sources.items():
        result = audit_category(name, module_path)
        errors.extend(result["errors"])
        warnings.extend(result["warnings"])
        summaries.append(result["summary"])
    warnings.extend(audit_templates())
    errors.extend(audit_concrete_price_templates())
    errors.extend(audit_js_clear_branches())
    errors.extend(audit_view_deepcopy_usage())
    if category in (None, "vershoudbakjes"):
        e, w = audit_runtime_consistency()
        errors.extend(e)
        warnings.extend(w)
    return _tuples_to_issues(errors, warnings), {"summaries": summaries}


def run_price_level_check(category=None, params=None):
    """Registry-runner: prijzen en prijsniveaus, inclusief de interne
    prijstabel (alleen zichtbaar in admin/rapport, nooit publiek)."""
    sources = _selected_sources(category)
    errors, warnings, price_rows = [], [], []
    for name, module_path in sources.items():
        e, w, pr = audit_price_levels(name, module_path)
        errors.extend(e)
        warnings.extend(w)
        price_rows.extend(pr)
    issues = _tuples_to_issues(errors, warnings)
    table = [
        {
            "category": cat,
            "product": key,
            "variant": variant or "—",
            "price": None if price is None else float(price),
            "manual": manual,
            "computed": computed,
        }
        for cat, key, variant, price, manual, computed in price_rows
    ]
    return issues, {"price_table": table}
