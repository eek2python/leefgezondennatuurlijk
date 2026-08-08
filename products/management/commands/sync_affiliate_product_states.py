"""
python manage.py sync_affiliate_product_states

Initialiseert AffiliateProductState-records vanuit de Python-productdata.

Gedrag:
  - Per slug: maak een record aan als het nog niet bestaat en importeer
    de effectieve prijs/beschikbaarheid/datum vanuit het Python-bestand.
  - Bestaande records worden NIET overschreven (handmatig bijgehouden
    waarden blijven intact), tenzij --force wordt meegegeven.
  - Idempotent: meerdere keren uitvoeren is veilig.
  - Normaliseert de typefout "OutofStock" → "OutOfStock".
  - Zet price_last_checked NOOIT op vandaag als die niet in de data staat:
    NULL staat voor "nog nooit gecontroleerd" en triggert de review-queue.
"""
from __future__ import annotations

import copy
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand

# Kanonieke spelling van beschikbaarheidsvarianten die we normaliseren.
_NORMALIZE_AVAILABILITY = {
    "OutofStock": "OutOfStock",  # typefout gevonden in products_*.py
}

VALID_AVAILABILITY = {"InStock", "OutOfStock", "PreOrder", "BackOrder", "Discontinued"}


def _get_effective_commercial_fields(product_data: dict) -> dict:
    """Geeft de effectieve commerciële velden terug voor het opgegeven productdict.

    Voor producten met button-varianten (shape_variants, te herkennen aan
    ``variant_selectors`` + variants met een ``id``-veld) wordt de
    default-variant gebruikt; anders het productniveau zelf.
    """
    variants = product_data.get("variants") or []
    shape_variants = [
        v for v in variants if isinstance(v, dict) and v.get("id")
    ]

    if shape_variants:
        # Default-variant = eerste met is_default=True, anders eerste variant.
        default = next((v for v in shape_variants if v.get("is_default")), shape_variants[0])
        price_raw = default.get("price")
        availability = default.get("availability") or product_data.get("availability") or ""
        price_last_checked = (
            default.get("price_last_checked") or product_data.get("price_last_checked")
        )
    else:
        price_raw = product_data.get("price")
        availability = product_data.get("availability") or ""
        price_last_checked = product_data.get("price_last_checked")

    # Normaliseer spelfouten in beschikbaarheid.
    availability = _NORMALIZE_AVAILABILITY.get(availability, availability)

    # Prijs omzetten naar Decimal voor opslag; None als niet aanwezig of ongeldig.
    price: Decimal | None = None
    if price_raw is not None and price_raw != "":
        try:
            price = Decimal(str(price_raw))
        except (InvalidOperation, ValueError):
            price = None

    # price_last_checked: alleen overnemen als het een geldige datum is.
    # "2026-06-31" is een typefout (juni heeft 30 dagen) → vangen als None.
    # NULL betekent "nog nooit gecontroleerd" en triggert de review-queue.
    if price_last_checked:
        from datetime import datetime
        try:
            datetime.strptime(str(price_last_checked), "%Y-%m-%d")
        except ValueError:
            price_last_checked = None  # Ongeldig of niet-bestaande datum
    else:
        price_last_checked = None

    return {
        "price": price,
        "availability": availability,
        "price_last_checked": price_last_checked,
    }


class Command(BaseCommand):
    help = (
        "Synchroniseer AffiliateProductState-records vanuit products_*.py data. "
        "Bestaande records blijven intact tenzij --force wordt gebruikt."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Overschrijf bestaande records met de Python-datawaarden. "
                "ALLEEN gebruiken voor ontwikkeling/testen — "
                "normaal productiegebruik mag handmatig bijgehouden waarden nooit overschrijven."
            ),
        )

    def handle(self, *args, **options):
        # Importeer hier om circulaire imports bij module-load te voorkomen.
        from products.models import AffiliateProductState, Product
        from products.views import ALL_PRODUCTS_BY_SLUG

        force = options["force"]

        total = len(ALL_PRODUCTS_BY_SLUG)
        created_count = 0
        retained_count = 0
        missing_price = 0
        missing_availability = 0
        normalized_count = 0
        missing_plc = 0
        errors = []

        product_count_before = Product.objects.count()

        for slug, entry in ALL_PRODUCTS_BY_SLUG.items():
            product_data = entry["data"]
            fields = _get_effective_commercial_fields(product_data)

            # Tel normalisaties
            raw_availability = (product_data.get("availability") or "")
            if raw_availability and raw_availability not in VALID_AVAILABILITY:
                normalized_count += 1

            if fields["price"] is None:
                missing_price += 1
            if not fields["availability"]:
                missing_availability += 1
            if fields["price_last_checked"] is None:
                missing_plc += 1

            try:
                state, is_new = AffiliateProductState.objects.get_or_create(
                    slug=slug,
                    defaults=fields,
                )
                if is_new:
                    created_count += 1
                elif force:
                    # Overschrijf handmatig bijgehouden waarden (alleen met --force).
                    for field_name, value in fields.items():
                        setattr(state, field_name, value)
                    state.save(update_fields=list(fields.keys()))
                    self.stdout.write(
                        self.style.WARNING(f"  Overschreven (--force): {slug}")
                    )
                else:
                    retained_count += 1
            except Exception as exc:
                errors.append(f"{slug}: {exc}")

        product_count_after = Product.objects.count()

        self.stdout.write(self.style.SUCCESS("\n=== sync_affiliate_product_states ==="))
        self.stdout.write(f"Python-producten gevonden:     {total}")
        self.stdout.write(f"Unieke slugs:                  {total}")
        self.stdout.write(f"Records aangemaakt:            {created_count}")
        self.stdout.write(f"Bestaande records behouden:    {retained_count}")
        self.stdout.write(f"Ontbrekende prijzen:           {missing_price}")
        self.stdout.write(f"Ontbrekende beschikbaarheid:   {missing_availability}")
        self.stdout.write(f"Legacy OutofStock genormaliseerd: {normalized_count}")
        self.stdout.write(f"NULL price_last_checked:       {missing_plc}")
        if errors:
            self.stdout.write(self.style.ERROR(f"Fouten: {len(errors)}"))
            for e in errors:
                self.stdout.write(self.style.ERROR(f"  {e}"))
        else:
            self.stdout.write("Fouten:                        0")

        # Veiligheidcheck: Product-model mag niet zijn aangeraakt.
        if product_count_after != product_count_before:
            self.stdout.write(
                self.style.ERROR(
                    f"WAARSCHUWING: Product.objects.count() veranderd van "
                    f"{product_count_before} naar {product_count_after}. "
                    "Dit had niet mogen gebeuren."
                )
            )
        else:
            self.stdout.write(
                f"Product-model ongewijzigd:     {product_count_after} records (correct)"
            )
