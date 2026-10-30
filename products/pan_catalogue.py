"""Pan navigation and read-only collections over the existing catalogues.

Never store a second copy of a frying-pan set here. Rankings contain source
keys; enriched display dictionaries are created per request by the views.
"""
from django.urls import reverse

from .products_koekenpannen import PRODUCTS as CERAMIC
from .rankings_koekenpannen import RANKINGS as CERAMIC_RANKINGS
from .products_rvs_koekenpannen import PRODUCTS as STAINLESS
from .rankings_rvs_koekenpannen import RANKINGS as STAINLESS_RANKINGS
from .products_koolstofstaal_koekenpannen import PRODUCTS as CARBON
from .rankings_koolstofstaal_koekenpannen import RANKINGS as CARBON_RANKINGS
from .products_gietijzeren_koekenpannen import PRODUCTS as CAST_IRON
from .rankings_gietijzeren_koekenpannen import RANKINGS as CAST_IRON_RANKINGS
from .products_bak_en_braad_sets import PRODUCTS as BAK_PRODUCTS
from .rankings_bak_en_braad_sets import RANKINGS as BAK_RANKINGS
from .content_bak_en_braad_sets import CONTENT as BAK_CONTENT
from .products_kookpannensets import PRODUCTS as KOOK_PRODUCTS
from .rankings_kookpannensets import RANKINGS as KOOK_RANKINGS
from .content_kookpannensets import CONTENT as KOOK_CONTENT
from .products_complete_pannensets import PRODUCTS as COMPLETE_PRODUCTS
from .rankings_complete_pannensets import RANKINGS as COMPLETE_RANKINGS
from .content_complete_pannensets import CONTENT as COMPLETE_CONTENT


MATERIALS = {
    "keramisch": {
        "label": "Keramisch", "category": "koekenpannen",
        "url_name": "koekenpannen", "products": CERAMIC, "rankings": CERAMIC_RANKINGS,
    },
    "rvs": {
        "label": "RVS", "category": "rvs-koekenpannen",
        "url_name": "rvs_koekenpannen", "products": STAINLESS, "rankings": STAINLESS_RANKINGS,
    },
    "koolstofstaal": {
        "label": "Koolstofstaal", "category": "koolstofstalen-koekenpannen",
        "url_name": "koolstofstalen_koekenpannen", "products": CARBON, "rankings": CARBON_RANKINGS,
    },
    "gietijzer": {
        "label": "Gietijzer", "category": "gietijzeren-koekenpannen",
        "url_name": "gietijzeren_koekenpannen", "products": CAST_IRON, "rankings": CAST_IRON_RANKINGS,
    },
}

SET_CATEGORIES = {
    "bak-braadsets": {
        "label": "Bak- & braadsets", "url_name": "bak_en_braad_sets",
        "products": BAK_PRODUCTS, "rankings": BAK_RANKINGS, "content": BAK_CONTENT,
    },
    "kookpannensets": {
        "label": "Kookpannensets", "url_name": "kookpannensets",
        "products": KOOK_PRODUCTS, "rankings": KOOK_RANKINGS, "content": KOOK_CONTENT,
    },
    "complete-pannensets": {
        "label": "Complete pannensets", "url_name": "complete_pannensets",
        "products": COMPLETE_PRODUCTS, "rankings": COMPLETE_RANKINGS, "content": COMPLETE_CONTENT,
    },
}


def frying_pan_set_keys(material):
    """Select sets without inferring product type from names or multi-size pans.

    Three catalogues have explicit set_type. Cast iron already has a dedicated
    ranked Pannensets group. Keep the existing order within each size group and
    append any explicitly typed but not yet ranked sets in source order.
    """
    source = material["products"]
    existing_group = set(material["rankings"].get("Pannensets", []))
    selected = {
        key for key, product in source.items()
        if (product.get("set_type") or "").casefold() == "koekenpannenset"
        or key in existing_group
    }
    ordered = dict.fromkeys(
        key for group in material["rankings"].values()
        for key in group if key in selected
    )
    ordered.update(dict.fromkeys(key for key in source if key in selected))
    return list(ordered)


def pan_breadcrumbs(category):
    """The same hierarchy for visible crumbs and BreadcrumbList JSON-LD."""
    root = [{"label": "Pannen", "url": reverse("pannen")}]
    for material in MATERIALS.values():
        if category == material["category"]:
            return root + [
                {"label": "Koekenpannen", "url": reverse("pannen") + "#koekenpannen"},
                {"label": material["label"], "url": reverse(material["url_name"])},
            ]
    if category in SET_CATEGORIES or category == "koekenpannensets":
        info = SET_CATEGORIES.get(category, {
            "label": "Koekenpannensets", "url_name": "koekenpannensets",
        })
        return root + [
            {"label": "Pannensets", "url": reverse("pannensets")},
            {"label": info["label"], "url": reverse(info["url_name"])},
        ]
    if category in ("hapjespannen", "wokpannen"):
        return root + [{"label": category.capitalize(), "url": reverse(category)}]
    raise ValueError(f"Unknown pan category: {category}")
