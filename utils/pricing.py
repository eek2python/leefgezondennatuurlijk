"""Centrale prijsniveaubepaling: ``price`` → ``price_range``.

``price`` is de interne numerieke bron; ``price_range`` (€/€€/€€€/€€€€) is
uitsluitend een afgeleide presentatiewaarde. De afleiding loopt altijd in
één richting (price → price_range) en maakt nooit een concrete prijs
zichtbaar.

Grenswaarden per categorie (alleen categorieën met een expliciet
vastgestelde indeling; overige categorieën blijven report-only totdat hun
grenzen bewust zijn vastgesteld):

    keramische koekenpannen ("koekenpannen"):
        formaat- en setgebonden grenzen; bovengrenzen zijn inclusief.
        Dezelfde grenzen voeden de prijsuitleg, productweergave en audits.

    hapjespannen ("hapjespannen"):
        < €40            → €
        €40 – < €70      → €€
        €70 – < €110     → €€€
        ≥ €110           → €€€€

Grenzen zijn categoriegebonden (prijspeil verschilt per producttype);
bedragen worden met Decimal vergeleken. Behalve bij keramische koekenpannen
valt een prijs exact op een grens in de volgende categorie. Een nieuwe categorie toevoegen =
één entry in PRICE_RANGE_THRESHOLDS; onbekende categorieën blijven
bewust zonder niveau (geen stille fallback naar andermans grenzen).
"""

from decimal import Decimal, InvalidOperation

#: Per categorie: geordende (bovengrens-exclusief, niveau)-tupels; ``None``
#: als bovengrens betekent "en hoger". Gebruik de bestaande categoriekeys.
PRICE_RANGE_THRESHOLDS = {
    "hapjespannen": (
        (Decimal("40"), "€"),
        (Decimal("70"), "€€"),
        (Decimal("110"), "€€€"),
        (None, "€€€€"),
    ),
    "airfryers_compact": (
        (Decimal("75"), "€"),
        (Decimal("110"), "€€"),
        (Decimal("150"), "€€€"),
        (None, "€€€€"),
    ),

    "airfryers_xl": (
        (Decimal("90"), "€"),
        (Decimal("130"), "€€"),
        (Decimal("180"), "€€€"),
        (None, "€€€€"),
    ),

    "airfryers_dual": (
        (Decimal("110"), "€"),
        (Decimal("170"), "€€"),
        (Decimal("250"), "€€€"),
        (None, "€€€€"),
    ),
}

KERAMISCHE_KOEKENPANNEN_PRICE_RANGES = {
    20: ((Decimal("25"), "€"), (Decimal("50"), "€€"), (Decimal("90"), "€€€"), (None, "€€€€")),
    24: ((Decimal("30"), "€"), (Decimal("60"), "€€"), (Decimal("100"), "€€€"), (None, "€€€€")),
    26: ((Decimal("35"), "€"), (Decimal("65"), "€€"), (Decimal("105"), "€€€"), (None, "€€€€")),
    28: ((Decimal("40"), "€"), (Decimal("70"), "€€"), (Decimal("110"), "€€€"), (None, "€€€€")),
    30: ((Decimal("45"), "€"), (Decimal("75"), "€€"), (Decimal("120"), "€€€"), (None, "€€€€")),
    32: ((Decimal("50"), "€"), (Decimal("85"), "€€"), (Decimal("130"), "€€€"), (None, "€€€€")),
}

KERAMISCHE_KOEKENPANNENSETS_PRICE_RANGES = {
    (20, 24): ((Decimal("50"), "€"), (Decimal("80"), "€€"), (Decimal("125"), "€€€"), (None, "€€€€")),
    (20, 28): ((Decimal("50"), "€"), (Decimal("75"), "€€"), (Decimal("110"), "€€€"), (None, "€€€€")),
    (24, 28): ((Decimal("60"), "€"), (Decimal("100"), "€€"), (Decimal("175"), "€€€"), (None, "€€€€")),
    (20, 24, 28): ((Decimal("75"), "€"), (Decimal("120"), "€€"), (Decimal("175"), "€€€"), (None, "€€€€")),
}

RVS_KOEKENPANNEN_PRICE_RANGES = {
    20: ((Decimal("50"), "€"), (Decimal("90"), "€€"), (Decimal("140"), "€€€"), (None, "€€€€")),
    24: ((Decimal("60"), "€"), (Decimal("100"), "€€"), (Decimal("150"), "€€€"), (None, "€€€€")),
    26: ((Decimal("60"), "€"), (Decimal("100"), "€€"), (Decimal("150"), "€€€"), (None, "€€€€")),
    28: ((Decimal("65"), "€"), (Decimal("110"), "€€"), (Decimal("175"), "€€€"), (None, "€€€€")),
    30: ((Decimal("70"), "€"), (Decimal("120"), "€€"), (Decimal("180"), "€€€"), (None, "€€€€")),
    32: ((Decimal("90"), "€"), (Decimal("150"), "€€"), (Decimal("220"), "€€€"), (None, "€€€€")),
}

RVS_KOEKENPANNENSETS_PRICE_RANGES = {
(20, 28): ((Decimal("140"), "€"), (Decimal("180"), "€€"), (Decimal("240"), "€€€"), (None, "€€€€")),
(24, 28): ((Decimal("140"), "€"), (Decimal("190"), "€€"), (Decimal("260"), "€€€"), (None, "€€€€")),
(20, 24, 28): ((Decimal("150"), "€"), (Decimal("250"), "€€"), (Decimal("350"), "€€€"), (None, "€€€€")),
}
# Keramische grenzen worden gedeeld door de openbare pagina en de audit.
# De overige formaatgebonden panconfiguratie blijft audit-only.
# Andere pannencategorieën kunnen hier eigen diameter- en setgrenzen registreren.
PAN_AUDIT_PRICE_RANGES = {
    "koekenpannen": {
        "single": KERAMISCHE_KOEKENPANNEN_PRICE_RANGES,
        "sets": KERAMISCHE_KOEKENPANNENSETS_PRICE_RANGES,
    },
    "rvs-koekenpannen": {
        "single": RVS_KOEKENPANNEN_PRICE_RANGES,
        "sets": RVS_KOEKENPANNENSETS_PRICE_RANGES,
    }
}


def get_audit_price_thresholds(category, product):
    """Selecteer auditgrenzen op productformaat; geen fallback bij onbekend formaat.

    ``diameters`` markeert een set en heeft voorrang boven ``diameter``.
    De volgorde van setdiameters maakt niet uit; dubbele maten blijven behouden.
    Categorieën zonder formaatconfig gebruiken hun bestaande categoriegrenzen.
    """
    config = PAN_AUDIT_PRICE_RANGES.get(category)
    if config is None:
        return PRICE_RANGE_THRESHOLDS.get(category)
    if "diameters" in product:
        diameters = product["diameters"]
        if not isinstance(diameters, (list, tuple)) or not diameters:
            return None
        if any(isinstance(d, bool) or not isinstance(d, (int, float, Decimal))
               for d in diameters):
            return None
        return config.get("sets", {}).get(tuple(sorted(diameters)))
    diameter = product.get("diameter")
    if isinstance(diameter, bool) or not isinstance(diameter, (int, float, Decimal)):
        return None
    return config.get("single", {}).get(diameter)


def has_price_range_config(category):
    """True wanneer voor deze categorie definitieve prijsgrenzen bestaan."""
    return category == "koekenpannen" or category in PRICE_RANGE_THRESHOLDS


def get_price_range(price, category="koekenpannen", *, product=None):
    """Leid het prijsniveau af uit een numerieke prijs.

    - ``None``, ongeldige of negatieve prijzen geven ``None``;
    - keramische koekenpannen vereisen productformaat; bovengrenzen zijn inclusief;
    - accepteert int, float, Decimal en numerieke strings;
    - een onbekende categorie geeft ``None`` (geen aannames over grenzen);
    - geeft alleen een niveau terug, nooit een concrete prijs.
    """
    thresholds = (
        get_audit_price_thresholds(category, product or {})
        if category == "koekenpannen"
        else PRICE_RANGE_THRESHOLDS.get(category)
    )
    return get_price_range_from_thresholds(
        price, thresholds, inclusive=category == "koekenpannen",
    )


def get_price_range_from_thresholds(price, thresholds, *, inclusive=False):
    """Bereken met expliciet gekozen grenzen (gedeeld door rendering en audit)."""
    if thresholds is None or price is None:
        return None
    try:
        normalized = Decimal(str(price))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not normalized.is_finite() or normalized < Decimal("0"):
        return None
    for upper, level in thresholds:
        if upper is None or (normalized <= upper if inclusive else normalized < upper):
            return level
    return None


def get_regular_price(source, *, family=None):
    """Eigen referentieprijs, optioneel de gedeelde kleurreferentie, dan eigen prijs.

    ``family`` wordt alleen expliciet meegegeven voor kleurvarianten van
    keramische koekenpannen. Een actuele familie- of andere variantprijs is
    nooit een fallback; de brondata wordt niet aangepast.
    """
    reference = source.get("reference_price")
    if reference not in (None, ""):
        return reference
    if family is not None:
        reference = family.get("reference_price")
        if reference not in (None, ""):
            return reference
    return source.get("price")


def get_price_guide(selection):
    """Vier zichtbare niveaus uit dezelfde keramische formaat- of setconfiguratie."""
    if isinstance(selection, str):
        try:
            parts = tuple(int(part) for part in selection.split("_"))
        except ValueError:
            return []
        selection = parts[0] if len(parts) == 1 else parts
    if isinstance(selection, (tuple, list)):
        product = {"diameters": selection}
    else:
        product = {"diameter": selection}
    thresholds = get_audit_price_thresholds("koekenpannen", product)
    if not thresholds:
        return []

    def amount(value):
        # Grensbedragen zijn meestal heel; cents worden uitsluitend getoond
        # waar nodig om de inclusieve intervallen zonder overlap te beschrijven.
        return format(value, ".2f").rstrip("0").rstrip(".").replace(".", ",")

    rows = []
    previous = None
    for upper, label in thresholds:
        if previous is None:
            description = f"Tot en met €{amount(upper)}"
        elif upper is None:
            description = f"Meer dan €{amount(previous)}"
        else:
            lower = previous + Decimal("0.01")
            description = f"€{amount(lower)}–€{amount(upper)}"
        rows.append({"label": label, "description": description})
        previous = upper
    return rows
