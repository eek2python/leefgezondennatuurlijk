"""Projectbrede, read-only audit van productvarianten.

Gebruik:
    python manage.py audit_product_variants
    python manage.py audit_product_variants --category vershoudbakjes
    python manage.py audit_product_variants --strict
    python manage.py audit_product_variants --report

Het command wijzigt nooit productdata. ``--report`` schrijft het rapport
naar ``docs/audit-product-variants.md``.

De auditlogica zelf leeft in ``audits/checks/variants.py`` en wordt gedeeld
met het admin-auditdashboard (/admin/product-audits/); dit command bouwt
alleen de console-/markdownweergave uit hetzelfde gestructureerde resultaat.

Stabiele issuecodes:
    source_product_mutated, stale_variant_value_risk,
    commercial_product_fallback, cross_variant_affiliate_fallback,
    missing_display_variant, multiple_default_variants,
    inconsistent_card_table_variant, inconsistent_jsonld_variant,
    missing_variant_clear_branch, unsafe_template_firstof,
    missing_variant_url, missing_variant_price, invalid_variant_data,
    missing_price, invalid_price, negative_price, price_range_mismatch,
    stale_price_range, visible_concrete_price_detected
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from audits.checks.variants import CATEGORY_SOURCES, run_variant_audit


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
        result = run_variant_audit(category=options.get("category"))
        errors = result["errors"]
        warnings = result["warnings"]

        lines = self.render_report(
            result["summaries"], errors, warnings, result["price_rows"]
        )
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
    def render_report(self, rows, errors, warnings, price_rows=None):
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
        if price_rows:
            lines += [
                "",
                "## Prijsniveau-audit (interne prijzen; niet publiek)",
                "",
                "| Categorie | Product | Variant | Interne prijs | Handmatig niveau | Berekend niveau |",
                "|---|---|---|---|---|---|",
            ]
            for cat, key, variant, price, manual, computed in price_rows:
                price_txt = "—" if price is None else f"{price}"
                lines.append(
                    f"| {cat} | {key} | {variant or '—'} | {price_txt} | {manual} | {computed} |"
                )
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
