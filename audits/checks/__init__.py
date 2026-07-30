"""Registratie van alle beschikbare productaudits.

Alleen audits met een bestaande, betrouwbare implementatie worden
geregistreerd (spec: geen speculatieve audits). Netwerkafhankelijke
controles (live affiliate-linkbereikbaarheid via scripts/monitor_products.py)
worden bewust NIET als admin-runner geregistreerd; daarvoor toont het
dashboard een commandline-instructie.
"""

from audits.registry import (
    SPEED_NETWORK,
    SPEED_QUICK,
    SPEED_STANDARD,
    register_audit,
)
from audits.checks.variants import (
    AUDIT_CATEGORIES,
    run_price_level_check,
    run_variant_check,
)
from audits.checks.links import run_product_link_check
from audits.checks.product_data import run_product_data_check
from audits.checks.rankings import run_brand_diversity_check

register_audit(
    key="product_variants",
    title="Productvarianten",
    description=(
        "Variantdata, displayvarianten, commerciële velden, template- en "
        "JS-wisbranches, brondatamutatie en JSON-LD-consistentie."
    ),
    runner=run_variant_check,
    supports_category=True,
    uses_network=False,
    speed=SPEED_STANDARD,
    categories=AUDIT_CATEGORIES,
)

register_audit(
    key="price_levels",
    title="Prijzen en prijsniveaus",
    description=(
        "Geldigheid van interne prijzen en vergelijking van handmatige "
        "prijsniveaus met het uit price berekende niveau "
        "(alleen keramische koekenpannen heeft definitieve grenzen)."
    ),
    runner=run_price_level_check,
    supports_category=True,
    uses_network=False,
    speed=SPEED_QUICK,
    categories=AUDIT_CATEGORIES,
)

register_audit(
    key="product_links",
    title="Productlinks (affiliate/retailer/fabrikant)",
    description=(
        "Onderscheid tussen affiliate_url, retailer_url en official_url: "
        "prioriteit, rel-attributen, labels, variantveiligheid, "
        "trackingparameters en handmatige-reviewlijst voor onbevestigde "
        "affiliatelinks."
    ),
    runner=run_product_link_check,
    supports_category=True,
    uses_network=False,
    speed=SPEED_STANDARD,
    categories=AUDIT_CATEGORIES,
)

register_audit(
    key="product_data",
    title="Productdata",
    description=(
        "Veldconsistentie per categorie: verplichte velden, types, "
        "ratings, afbeeldingspaden en placeholderdetectie "
        "(services/product_normalization.py)."
    ),
    runner=run_product_data_check,
    supports_category=True,
    uses_network=False,
    speed=SPEED_STANDARD,
    categories=AUDIT_CATEGORIES,
)

register_audit(
    key="brand_diversity",
    title="Rankings en merkdiversiteit",
    description=(
        "Maximaal aantal producten per merk per ranking "
        "(services/product_validation.py)."
    ),
    runner=run_brand_diversity_check,
    supports_category=True,
    uses_network=False,
    speed=SPEED_QUICK,
    categories=AUDIT_CATEGORIES,
)

register_audit(
    key="live_links",
    title="Live affiliate-links (netwerk)",
    description=(
        "HTTP-bereikbaarheid van affiliate-URL's. Netwerkafhankelijk en "
        "potentieel traag; niet uitvoerbaar vanuit admin."
    ),
    runner=None,
    supports_category=True,
    uses_network=True,
    speed=SPEED_NETWORK,
    cli_hint="python scripts/monitor_products.py  (of --no-live voor droge run)",
    categories=AUDIT_CATEGORIES,
)
