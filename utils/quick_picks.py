"""Compacte navigatie naar bestaande awardproducten, zonder nieuwe aanbevelingen."""

AWARD_ORDER = {
    "🏆 Beste keuze": 1,
    "💰 Budget keuze": 2,
    "💎 Premium keuze": 3,
}


def _quick_reason(product):
    reason = product.get("quick_reason")
    if isinstance(reason, str) and reason.strip():
        return reason.strip()
    features = product.get("comparison_features")
    if not isinstance(features, (list, tuple)):
        return ""
    selected = [
        feature.strip() for feature in features
        if isinstance(feature, str) and feature.strip()
    ][:2]
    return " · ".join(selected)


def build_quick_picks(products):
    """Behoud dezelfde productobjecten; alleen erkende awards in vaste volgorde.

    Redenen zijn uitsluitend bestaande tekst. Ontbrekende badges of redenen
    worden niet aangevuld met andere producten of verzonnen claims.
    """
    awarded = [
        product for product in products
        if product.get("award") in AWARD_ORDER
    ]
    return [
        {"product": product, "reason": _quick_reason(product)}
        for product in sorted(awarded, key=lambda product: AWARD_ORDER[product["award"]])
    ]
