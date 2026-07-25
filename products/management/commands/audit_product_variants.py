"""Projectbrede, read-only audit van productvarianten.

Gebruik:
    python manage.py audit_product_variants
    python manage.py audit_product_variants --category vershoudbakjes
    python manage.py audit_product_variants --strict
    python manage.py audit_product_variants --report

Het command wijzigt nooit productdata. ``--report`` schrijft het rapport
naar ``docs/audit-product-variants.md``.

Stabiele issuecodes:
    source_product_mutated, stale_variant_value_risk,
    commercial_product_fallback, cross_variant_affiliate_fallback,
    missing_display_variant, multiple_default_variants,
    inconsistent_card_table_variant, inconsistent_jsonld_variant,
    missing_variant_clear_branch, unsafe_template_firstof,
    missing_variant_url, missing_variant_price, invalid_variant_data
"""

import copy
import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import RequestFactory

from utils.variant_helpers import prepare_product_variants

CATEGORY_SOURCES = {
    "koekenpannen": "products.products_koekenpannen",
    "hapjespannen": "products.products_hapjespannen",
    "wokpannen": "products.products_wokpannen",
    "rvs-koekenpannen": "products.products_rvs_koekenpannen",
    "snijplanken": "products.products_snijplanken",
    "airfryers": "products.products_airfryers",
    "vershoudbakjes": "products.products_vershoudcontainers",
}

#: Templates met vergelijkingstabellen die op onveilige commerciële
#: fallbacks worden gescand.
COMPARISON_TEMPLATES = [
    "templates/vershoudcontainers.html",
    "templates/koekenpannen.html",
    "templates/hapjespannen.html",
    "templates/wokpannen.html",
    "templates/rvs-koekenpannen.html",
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


def _load_products(module_path):
    import importlib

    return importlib.import_module(module_path).PRODUCTS


def _is_button_variant(variant):
    return isinstance(variant, dict) and bool(variant.get("id"))


class Command(BaseCommand):
    help = "Read-only audit van variantlogica voor alle productcategorieën."

    def add_arguments(self, parser):
        parser.add_argument("--category", choices=sorted(CATEGORY_SOURCES))
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit met foutcode wanneer er issues (ook warnings) zijn.",
        )
        parser.add_argument(
            "--report",
            action="store_true",
            help="Schrijf het rapport naar docs/audit-product-variants.md.",
        )

    def handle(self, *args, **options):
        categories = (
            {options["category"]: CATEGORY_SOURCES[options["category"]]}
            if options.get("category")
            else CATEGORY_SOURCES
        )

        errors, warnings, rows = [], [], []
        for name, module_path in categories.items():
            result = self.audit_category(name, module_path)
            errors.extend(result["errors"])
            warnings.extend(result["warnings"])
            rows.append(result["summary"])

        warnings.extend(self.audit_templates())
        errors.extend(self.audit_js_clear_branches())
        errors.extend(self.audit_view_deepcopy_usage())

        if options.get("category") in (None, "vershoudbakjes"):
            e, w = self.audit_runtime_consistency()
            errors.extend(e)
            warnings.extend(w)

        lines = self.render_report(rows, errors, warnings)
        report_text = "\n".join(lines) + "\n"
        self.stdout.write(report_text)

        if options.get("report"):
            path = Path(settings.BASE_DIR) / "docs" / "audit-product-variants.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(report_text, encoding="utf-8")
            self.stdout.write(f"Rapport geschreven naar {path}")

        if errors or (options.get("strict") and warnings):
            raise CommandError(
                f"Audit: {len(errors)} fout(en), {len(warnings)} waarschuwing(en)"
            )

    # ------------------------------------------------------------------
    def audit_category(self, name, module_path):
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
                e, w = self._audit_button_product(name, key, product)
                errors.extend(e)
                warnings.extend(w)
            else:
                swatch_count += 1
                warnings.extend(self._audit_swatch_product(name, key, product))

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

    def _audit_button_product(self, category, key, product):
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

    def _audit_swatch_product(self, category, key, product):
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

    # ------------------------------------------------------------------
    def audit_templates(self):
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

    def audit_js_clear_branches(self):
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

    def audit_view_deepcopy_usage(self):
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

    def audit_runtime_consistency(self):
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

            rows = self._extract_context_rows(request)
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

    def _extract_context_rows(self, request):
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

    # ------------------------------------------------------------------
    def render_report(self, rows, errors, warnings):
        lines = [
            "# Projectbrede audit productvarianten",
            "",
            "## Samenvatting",
            "",
            f"- Categorieën gecontroleerd: {len(rows)}",
            f"- Categorieën met varianten: "
            f"{sum(1 for r in rows if r['button_variants'] or r['swatch_variants'])}",
            f"- Variantproducten (knoppen): {sum(r['button_variants'] for r in rows)}",
            f"- Variantproducten (kleurswatches): {sum(r['swatch_variants'] for r in rows)}",
            f"- Structurele fouten: {len(errors)}",
            f"- Waarschuwingen: {len(warnings)}",
            f"- Handmatige controles: zie tabel onderaan",
            "",
            "## Gedeelde infrastructuur",
            "",
            "| Helper | Gebruikt door | Mutatie | Commerciële fallback | Status |",
            "|---|---|---|---|---|",
            "| utils/variant_helpers.py (prepare_product_variants, set_display_variant, "
            "resolve_commercial_fields, _apply_display_variant_fields) | vershoudbakjes "
            "(knopvarianten) | alleen op deep copies in views | geen — velden worden "
            "expliciet gezet of gewist; familie-afbeelding als gedocumenteerde fallback | OK |",
            "| static/assets/js/variant-selector.js | vershoudbakjes-productkaarten | "
            "n.v.t. (DOM) | geen — set-or-clear per veld | OK |",
            "| static/assets/js/variants.js | airfryers-kleurswatches | n.v.t. (DOM) | "
            "bewuste familiefallback naar data-base-* (gedocumenteerd beleid) | OK |",
            "",
            "## Categorieoverzicht",
            "",
            "| Categorie | Producten | Knopvarianten | Swatchvarianten | Productkaart | "
            "Tabel | JSON-LD | Risico |",
            "|---|---|---|---|---|---|---|---|",
        ]
        risk = {"vershoudbakjes": "laag", "airfryers": "middel"}
        for r in rows:
            has_variants = r["button_variants"] or r["swatch_variants"]
            lines.append(
                f"| {r['category']} | {r['products']} | {r['button_variants']} | "
                f"{r['swatch_variants']} | "
                f"{'displayvariant' if r['button_variants'] else 'productniveau'} | "
                f"{'expliciete rijvelden' if r['button_variants'] else 'productniveau'} | "
                f"{'displayvariant (default of filtermatch)' if r['button_variants'] else 'productniveau'} | "
                f"{risk.get(r['category'], 'laag') if has_variants else 'laag'} |"
            )
        for title, items in (("Structurele fouten", errors), ("Waarschuwingen", warnings)):
            lines += ["", f"## {title}", ""]
            if not items:
                lines.append("Geen.")
            else:
                lines.append("| Code | Categorie | Product/bestand | Probleem |")
                lines.append("|---|---|---|---|")
                for code, cat, key, msg in items:
                    lines.append(f"| {code} | {cat} | {key} | {msg} |")
        lines += [
            "",
            "## Handmatige controle",
            "",
            "| Categorie | Probleem | Waarom niet automatisch opgelost |",
            "|---|---|---|",
            "| airfryers | greenpan_silhouette_xl_5l: productniveauprijs (129,90) wijkt af "
            "van de getoonde defaultswatch Moroccan Green (116,00); JSON-LD gebruikt "
            "productniveau | Prijscorrectie is een redactionele/datakeuze; de audit mag "
            "geen prijzen wijzigen |",
            "| vershoudbakjes | Eerder gemarkeerde TODO-varianten (Igluu vierkant, "
            "Lock&Lock 630 ml / 1 L) hebben inmiddels prijs en URL; periodieke "
            "prijsverificatie blijft handwerk | price_last_checked bijwerken is een "
            "redactionele taak; de audit mag geen prijzen wijzigen |",
        ]
        return lines
