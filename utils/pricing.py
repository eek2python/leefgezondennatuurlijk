"""Centrale prijsniveaubepaling: ``price`` → ``price_range``.

``price`` is de interne numerieke bron; ``price_range`` (€/€€/€€€/€€€€) is
uitsluitend een afgeleide presentatiewaarde. De afleiding loopt altijd in
één richting (price → price_range) en maakt nooit een concrete prijs
zichtbaar.

Grenswaarden per categorie (alleen categorieën met een expliciet
vastgestelde indeling; overige categorieën blijven report-only totdat hun
grenzen bewust zijn vastgesteld):

    keramische koekenpannen ("koekenpannen"):
        < €25            → €
        €25 – < €50      → €€
        €50 – < €90      → €€€
        ≥ €90            → €€€€

    hapjespannen ("hapjespannen"):
        < €40            → €
        €40 – < €70      → €€
        €70 – < €110     → €€€
        ≥ €110           → €€€€

Grenzen zijn categoriegebonden (prijspeil verschilt per producttype);
bedragen worden met Decimal vergeleken en een prijs exact op een grens
valt altijd in de volgende categorie. Een nieuwe categorie toevoegen =
één entry in PRICE_RANGE_THRESHOLDS; onbekende categorieën blijven
bewust zonder niveau (geen stille fallback naar andermans grenzen).
"""

from decimal import Decimal, InvalidOperation

#: Per categorie: geordende (bovengrens-exclusief, niveau)-tupels; ``None``
#: als bovengrens betekent "en hoger". Gebruik de bestaande categoriekeys.
PRICE_RANGE_THRESHOLDS = {
    "koekenpannen": (
        (Decimal("25"), "€"),
        (Decimal("50"), "€€"),
        (Decimal("90"), "€€€"),
        (None, "€€€€"),
    ),
    "hapjespannen": (
        (Decimal("40"), "€"),
        (Decimal("70"), "€€"),
        (Decimal("110"), "€€€"),
        (None, "€€€€"),
    ),
}


def has_price_range_config(category):
    """True wanneer voor deze categorie definitieve prijsgrenzen bestaan."""
    return category in PRICE_RANGE_THRESHOLDS


def get_price_range(price, category="koekenpannen"):
    """Leid het prijsniveau af uit een numerieke prijs.

    - ``None``, ongeldige of negatieve prijzen geven ``None``;
    - grenswaarden zijn exact (25.00 → "€€", 89.99 → "€€€", 90.00 → "€€€€");
    - accepteert int, float, Decimal en numerieke strings;
    - een onbekende categorie geeft ``None`` (geen aannames over grenzen);
    - geeft alleen een niveau terug, nooit een concrete prijs.
    """
    thresholds = PRICE_RANGE_THRESHOLDS.get(category)
    if thresholds is None or price is None:
        return None
    try:
        normalized = Decimal(str(price))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if normalized.is_nan() or normalized < Decimal("0"):
        return None
    for upper, level in thresholds:
        if upper is None or normalized < upper:
            return level
    return None
