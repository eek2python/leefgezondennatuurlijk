import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from .models import Product, Click
import logging
from utils.product_helpers import (
    get_capacity_display,
    classify_storage_size,
    get_product_size_categories,
    filter_products_by_storage_size,
    format_total_capacity,
    STORAGE_SIZE_LABELS,
    STORAGE_SIZE_THRESHOLDS,
)
from utils.usage_helpers import build_usage_display
from utils.pricing import get_price_range, has_price_range_config
from utils.variant_helpers import (
    apply_resolved_link,
    prepare_product_variants,
    resolve_availability_label,
    resolve_commercial_fields,
    resolve_product_link,
    set_display_variant,
)
import copy
import json

logger = logging.getLogger(__name__)
from .products_koekenpannen import PRODUCTS as KOEKENPANNEN_PRODUCTS
from .rankings_koekenpannen import RANKINGS as KOEKENPANNEN_RANKINGS
from .content_koekenpannen import CONTENT as KOEKENPANNEN_CONTENT
from .products_hapjespannen import PRODUCTS as HAPJESPANNEN_PRODUCTS
from .rankings_hapjespannen import RANKINGS as HAPJESPANNEN_RANKINGS
from .content_hapjespannen import CONTENT as HAPJESPANNEN_CONTENT
from .products_wokpannen import PRODUCTS as WOKPANNEN_PRODUCTS
from .rankings_wokpannen import RANKINGS as WOKPANNEN_RANKINGS
from .content_wokpannen import CONTENT as WOKPANNEN_CONTENT
from .products_snijplanken import PRODUCTS as SNIJPLANKEN_PRODUCTS
from .rankings_snijplanken import RANKINGS as SNIJPLANKEN_RANKINGS
from .content_snijplanken import CONTENT as SNIJPLANKEN_CONTENT
from .products_airfryers import PRODUCTS as AIRFRYERS_PRODUCTS
from .rankings_airfryers import RANKINGS as AIRFRYERS_RANKINGS
from .content_airfryers import CONTENT as AIRFRYERS_CONTENT
from .products_vershoudcontainers import PRODUCTS as VERSHOUDCONTAINERS_PRODUCTS
from .rankings_vershoudcontainers import RANKINGS as VERSHOUDCONTAINERS_RANKINGS
from .content_vershoudcontainers import CONTENT as VERSHOUDCONTAINERS_CONTENT
from .products_rvs_koekenpannen import PRODUCTS as RVS_KOEKENPANNEN_PRODUCTS
from .rankings_rvs_koekenpannen import RANKINGS as RVS_KOEKENPANNEN_RANKINGS
from .content_rvs_koekenpannen import CONTENT as RVS_KOEKENPANNEN_CONTENT
from .slug_redirects import SLUG_REDIRECTS


CATEGORY_MAP = {
    "koekenpannen": {"products": KOEKENPANNEN_PRODUCTS, "label": "Koekenpannen", "url_name": "koekenpannen"},
    "rvs-koekenpannen": {"products": RVS_KOEKENPANNEN_PRODUCTS, "label": "RVS Koekenpannen", "url_name": "rvs_koekenpannen"},
    "hapjespannen": {"products": HAPJESPANNEN_PRODUCTS, "label": "Hapjespannen", "url_name": "hapjespannen"},
    "wokpannen": {"products": WOKPANNEN_PRODUCTS, "label": "Wokpannen", "url_name": "wokpannen"},
    "snijplanken": {"products": SNIJPLANKEN_PRODUCTS, "label": "Snijplanken", "url_name": "snijplanken"},
    "airfryers": {"products": AIRFRYERS_PRODUCTS, "label": "Airfryers", "url_name": "airfryers"},
    "vershoudcontainers": {"products": VERSHOUDCONTAINERS_PRODUCTS, "label": "Vershoudbakjes", "url_name": "vershoudcontainers"},
}

ALL_PRODUCTS_BY_SLUG = {}
for cat_key, cat_info in CATEGORY_MAP.items():
    for prod_key, prod_data in cat_info["products"].items():
        slug = prod_data.get("slug", prod_key)
        if slug in ALL_PRODUCTS_BY_SLUG:
            raise ValueError(f"Duplicate product slug '{slug}' in category '{cat_key}' — slugs must be globally unique")
        ALL_PRODUCTS_BY_SLUG[slug] = {"data": prod_data, "category": cat_key}


def _build_breadcrumb_ld(breadcrumbs):
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.leefnatuurlijkengezond.nl/"}]
    for i, crumb in enumerate(breadcrumbs, start=2):
        entry = {"@type": "ListItem", "position": i, "name": crumb["label"]}
        if crumb.get("url"):
            entry["item"] = f"https://www.leefnatuurlijkengezond.nl{crumb['url']}"
        items.append(entry)
    return json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items})


def homepage(request):
    return render(request, "index.html")


def over_ons(request):
    breadcrumbs = [{"label": "Over ons", "url": "/over-ons/"}]
    return render(request, "over_ons.html", {
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
    })


def hoe_wij_beoordelen(request):
    breadcrumbs = [{"label": "Hoe wij beoordelen", "url": "/hoe-wij-beoordelen/"}]
    return render(request, "hoe_wij_beoordelen.html", {
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
    })


def privacy(request):
    breadcrumbs = [{"label": "Privacyverklaring", "url": "/privacy/"}]
    return render(request, "privacy.html", {
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
    })


def _derive_price_levels(p, category):
    """Zet ``display_price_range`` op product- (en swatchvariant-)niveau.

    - Categorieën met definitieve prijsgrenzen (zie utils/pricing.py) leiden
      het niveau strikt af uit het numerieke ``price``-veld van de getoonde
      displayvariant: geen fallback naar een andere variant of naar een
      handmatig niveau; ontbrekende prijs → leeg niveau.
    - Overige categorieën gebruiken de bestaande handmatige
      ``price_range``-velden ongewijzigd (report-only in de audit).
    Concrete prijzen worden hierdoor nooit zichtbaar gemaakt.
    """
    variants = p.get("variants")
    is_swatch = bool(variants) and not p.get("shape_variants")
    if has_price_range_config(category):
        p["price_range_is_derived"] = True
        if is_swatch:
            # Kleurswatches: strikt het niveau van de eigen variantprijs.
            for v in variants:
                v["display_price_range"] = get_price_range(v.get("price"), category) or ""
            p["display_price_range"] = variants[0]["display_price_range"]
        elif p.get("shape_variants"):
            # Knopvarianten: prepare_product_variants projecteerde de
            # commerciële velden van de displayvariant al strikt (set-or-clear).
            p["display_price_range"] = get_price_range(p.get("price"), category) or ""
        else:
            computed = get_price_range(p.get("price"), category)
            if computed:
                p["display_price_range"] = computed
            elif p.get("price") in (None, ""):
                # Zonder numerieke prijs blijft het handmatige niveau de
                # enige (backward-compatible) bron.
                p["display_price_range"] = p.get("price_range") or ""
            else:
                p["display_price_range"] = ""
    else:
        p["price_range_is_derived"] = False
        if is_swatch:
            first = variants[0]
            p["display_price_range"] = first.get("price_range") or p.get("price_range") or ""
        else:
            p["display_price_range"] = p.get("price_range") or ""


def _enrich_products(products, category=None):
    for p in products:
        prepare_product_variants(p)
        # Centrale linkresolutie: producten met button-varianten kregen hun
        # resolved_link al in prepare_product_variants (displayvariant);
        # alle overige producten resolven hier op productniveau.
        if "resolved_link" not in p:
            apply_resolved_link(p)
        _derive_price_levels(p, category)
        if "usage_display" not in p:
            p["usage_display"] = build_usage_display(p.get("usage"))
        p["formatted_capacity"], p["formatted_total_capacity"] = get_capacity_display(p)
        p["rating_class"] = str(p["rating"]).replace(".", "-")
        # Nederlandse displaywaarde (komma); numerieke rating blijft ongewijzigd.
        p["rating_display"] = str(p["rating"]).replace(".", ",") if p.get("rating") else ""
        award = (p.get("award") or "").lower()
        if "beste keuze" in award:
            p["award_class"] = "best-choice"
        elif "budget" in award:
            p["award_class"] = "budget-choice"
        elif "premium" in award:
            p["award_class"] = "premium-choice"
        elif "betaalbare" in award:
            p["award_class"] = "value-choice"
        elif "meest gekozen" in award:
            p["award_class"] = "popular-choice"
        elif "eco keuze" in award:
            p["award_class"] = "eco-choice"
        elif "meest duurzaam" in award:
            p["award_class"] = "eco-choice"
        elif "chef" in award:
            p["award_class"] = "chef-choice"
        elif "stilste" in award:
            p["award_class"] = "feature-choice"
        elif "inductie" in award:
            p["award_class"] = "feature-choice"
        else:
            p["award_class"] = ""


def _build_top_picks(products):
    picks = {"beste": None, "budget": None, "premium": None}
    for p in products:
        award = (p.get("award") or "").lower()
        if "beste keuze" in award and not picks["beste"]:
            picks["beste"] = p
        elif "budget" in award and not picks["budget"]:
            picks["budget"] = p
        elif "premium" in award and not picks["premium"]:
            picks["premium"] = p
    if not picks["beste"] and products:
        picks["beste"] = products[0]
    return picks


def _build_in_het_kort(products, content):
    picks = _build_top_picks(products)
    return {
        "beste": picks.get("beste"),
        "budget": picks.get("budget"),
        "premium": picks.get("premium"),
        "use_cases": content.get("in_het_kort", {}).get("use_cases", []),
    }


def _format_content(content, **fmt):
    def _walk(node):
        if isinstance(node, str):
            try:
                return node.format(**fmt)
            except (KeyError, IndexError, ValueError):
                return node
        if isinstance(node, list):
            return [_walk(x) for x in node]
        if isinstance(node, dict):
            return {k: _walk(v) for k, v in node.items()}
        return node
    return _walk(content)


def _build_faq_ld(faq_items):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["q"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["a"],
                },
            }
            for item in faq_items
        ],
    })


def _build_product_ld(request, p):
    product_ld = {
        "@type": "Product",
        "name": p["name"],
        "description": p["description"],
        "image": request.build_absolute_uri(
            f"/static/{p['image_path']}/{p['image']}"
        ),
        "brand": {"@type": "Brand", "name": p["brand"]},
        "material": p["material"],
    }
    # Only emit aggregateRating when a real review/rating count exists.
    # Schema.org requires ratingCount or reviewCount; emitting a null count
    # produces invalid structured data (Google Rich Results error).
    if p.get("rating_count"):
        product_ld["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": p["rating"],
            "reviewCount": p["rating_count"],
        }
    offer = _build_offer_ld(p)
    if offer is not None:
        product_ld["offers"] = offer
    return product_ld


def _build_offer_ld(p):
    # Nooit een Offer zonder geldige prijs én URL (en munteenheid /
    # beschikbaarheid): een displayvariant zonder eigen commerciële data
    # levert géén Offer op — er wordt niet teruggevallen op een andere
    # variant.
    if (
        not p.get("affiliate_url")
        or p.get("price") in (None, "")
        or not p.get("currency")
        or not p.get("availability")
    ):
        return None
    return {
                        "@type": "Offer",
                        "url": p["affiliate_url"],
                        "price": p["price"],
                        "priceCurrency": p["currency"],
                        "availability": f"https://schema.org/{p['availability']}",
                        "hasMerchantReturnPolicy": {
                            "@type": "MerchantReturnPolicy",
                            "applicableCountry": "NL",
                            "returnPolicyCountry": "NL",
                            "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
                            "merchantReturnDays": 14,
                            "returnMethod": "https://schema.org/ReturnByMail",
                            "returnFees": "https://schema.org/FreeReturn",
                        },
                        "shippingDetails": {
                            "@type": "OfferShippingDetails",
                            "shippingDestination": {
                                "@type": "DefinedRegion",
                                "addressCountry": "NL",
                            },
                            "shippingRate": {
                                "@type": "MonetaryAmount",
                                "value": "0.00",
                                "currency": p["currency"],
                            },
                            "deliveryTime": {
                                "@type": "ShippingDeliveryTime",
                                "handlingTime": {
                                    "@type": "QuantitativeValue",
                                    "minValue": 0,
                                    "maxValue": 1,
                                    "unitCode": "DAY",
                                },
                                "transitTime": {
                                    "@type": "QuantitativeValue",
                                    "minValue": 1,
                                    "maxValue": 2,
                                    "unitCode": "DAY",
                                },
                            },
                        },
                    }


def _build_itemlist_ld(request, name, description, products):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "description": description,
        "itemListOrder": "ItemListOrderDescending",
        "numberOfItems": len(products),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": _build_product_ld(request, p),
            }
            for i, p in enumerate(products)
        ],
    })


def snijplanken(request):
    products = [copy.deepcopy(SNIJPLANKEN_PRODUCTS[k]) for k in SNIJPLANKEN_RANKINGS]
    content = SNIJPLANKEN_CONTENT
    _enrich_products(products, category="snijplanken")
    product_count = len(products)
    conclusie = content["conclusies"]["default"]
    faq_ld = _build_faq_ld(content["faq"]["items"])
    json_ld = _build_itemlist_ld(
        request,
        "Top 10 Houten Snijplanken zonder Plastic (PFAS-vrij)",
        "De 10 beste houten snijplanken van 2026 \u2013 duurzaam, voedselveilig en PFAS-vrij.",
        products,
    )
    breadcrumbs = [{"label": "Snijplanken", "url": "/snijplanken/"}]
    return render(request, "snijplanken.html", {
        "products": products,
        "top_picks": _build_top_picks(products),
        "in_het_kort": _build_in_het_kort(products, content),
        "product_count": product_count,
        "content": content,
        "conclusie": conclusie,
        "json_ld": json_ld,
        "faq_ld": faq_ld,
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
    })


def koekenpannen(request):
    content = KOEKENPANNEN_CONTENT
    available_sizes = sorted(KOEKENPANNEN_RANKINGS.keys())
    size = request.GET.get("size")
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = 28 if 28 in available_sizes else available_sizes[0]
    if size not in KOEKENPANNEN_RANKINGS:
        size = 28 if 28 in available_sizes else available_sizes[0]

    keys = KOEKENPANNEN_RANKINGS[size]
    # Deep copies: prijsniveau-afleiding zet velden op geneste variant-dicts
    # en mag de brondata in PRODUCTS nooit muteren.
    products = [copy.deepcopy(KOEKENPANNEN_PRODUCTS[k]) for k in keys if k in KOEKENPANNEN_PRODUCTS]
    _enrich_products(products, category="koekenpannen")
    product_count = len(products)

    conclusie = content["conclusies"].get(size, {})
    hero_h1 = content["hero"]["h1"].format(product_count=product_count, selected_size=size)
    products_h2 = content["products_section"]["h2"].format(product_count=product_count, selected_size=size)
    comparison_title = content["products_section"]["comparison_title"].format(
        product_count=product_count, selected_size=size
    )
    content = _format_content(content, product_count=product_count, selected_size=size)
    faq_ld = _build_faq_ld(content["faq"]["items"])
    json_ld = _build_itemlist_ld(
        request,
        f"Top {product_count} PFAS-vrije Koekenpannen {size} cm",
        f"Top {product_count} PFAS-vrije koekenpannen van {size}\u00a0cm \u2013 duurzaam, gezond en zonder schadelijke stoffen.",
        products,
    )
    breadcrumbs = [
        {"label": "Koekenpannen", "url": "/koekenpannen/"},
        {"label": "Keramisch", "url": None},
    ]
    return render(request, "koekenpannen.html", {
        "products": products,
        "top_picks": _build_top_picks(products),
        "in_het_kort": _build_in_het_kort(products, content),
        "available_sizes": available_sizes,
        "selected_size": size,
        "product_count": product_count,
        "content": content,
        "hero_h1": hero_h1,
        "products_h2": products_h2,
        "comparison_title": comparison_title,
        "conclusie": conclusie,
        "json_ld": json_ld,
        "faq_ld": faq_ld,
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
    })


def hapjespannen(request):
    content = HAPJESPANNEN_CONTENT
    available_sizes = sorted(HAPJESPANNEN_RANKINGS.keys())
    size = request.GET.get("size")
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = 28 if 28 in available_sizes else available_sizes[0]
    if size not in HAPJESPANNEN_RANKINGS:
        size = 28 if 28 in available_sizes else available_sizes[0]

    keys = HAPJESPANNEN_RANKINGS[size]
    products = [copy.deepcopy(HAPJESPANNEN_PRODUCTS[k]) for k in keys if k in HAPJESPANNEN_PRODUCTS]
    _enrich_products(products, category="hapjespannen")
    product_count = len(products)

    conclusie = content["conclusies"].get(size, {})
    hero_h1 = content["hero"]["h1"].format(product_count=product_count, selected_size=size)
    products_h2 = content["products_section"]["h2"].format(product_count=product_count, selected_size=size)
    comparison_title = content["products_section"]["comparison_title"].format(
        product_count=product_count, selected_size=size
    )
    content = _format_content(content, product_count=product_count, selected_size=size)
    faq_ld = _build_faq_ld(content["faq"]["items"])
    json_ld = _build_itemlist_ld(
        request,
        f"Top {product_count} PFAS-vrije Hapjespannen {size} cm",
        f"Top {product_count} PFAS-vrije hapjespannen van {size}\u00a0cm \u2013 duurzaam, gezond en zonder schadelijke stoffen.",
        products,
    )
    breadcrumbs = [{"label": "Hapjespannen", "url": "/hapjespannen/"}]
    return render(request, "hapjespannen.html", {
        "products": products,
        "top_picks": _build_top_picks(products),
        "in_het_kort": _build_in_het_kort(products, content),
        "available_sizes": available_sizes,
        "selected_size": size,
        "product_count": product_count,
        "content": content,
        "hero_h1": hero_h1,
        "products_h2": products_h2,
        "comparison_title": comparison_title,
        "conclusie": conclusie,
        "json_ld": json_ld,
        "faq_ld": faq_ld,
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
    })


def wokpannen(request):
    content = WOKPANNEN_CONTENT
    available_sizes = sorted(WOKPANNEN_RANKINGS.keys())
    size = request.GET.get("size")
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = 28 if 28 in available_sizes else available_sizes[0]
    if size not in WOKPANNEN_RANKINGS:
        size = 28 if 28 in available_sizes else available_sizes[0]

    keys = WOKPANNEN_RANKINGS[size]
    products = [copy.deepcopy(WOKPANNEN_PRODUCTS[k]) for k in keys if k in WOKPANNEN_PRODUCTS]
    _enrich_products(products, category="wokpannen")
    product_count = len(products)

    conclusie = content["conclusies"].get(size, {})
    hero_h1 = content["hero"]["h1"].format(product_count=product_count, selected_size=size)
    products_h2 = content["products_section"]["h2"].format(product_count=product_count, selected_size=size)
    comparison_title = content["products_section"]["comparison_title"].format(
        product_count=product_count, selected_size=size
    )
    content = _format_content(content, product_count=product_count, selected_size=size)
    faq_ld = _build_faq_ld(content["faq"]["items"])
    json_ld = _build_itemlist_ld(
        request,
        f"Top {product_count} PFAS-vrije Wokpannen {size} cm",
        f"Top {product_count} PFAS-vrije wokpannen van {size}\u00a0cm \u2013 duurzaam, gezond en zonder schadelijke stoffen.",
        products,
    )
    breadcrumbs = [{"label": "Wokpannen", "url": "/wokpannen/"}]
    return render(request, "wokpannen.html", {
        "products": products,
        "top_picks": _build_top_picks(products),
        "in_het_kort": _build_in_het_kort(products, content),
        "available_sizes": available_sizes,
        "selected_size": size,
        "product_count": product_count,
        "content": content,
        "hero_h1": hero_h1,
        "products_h2": products_h2,
        "comparison_title": comparison_title,
        "conclusie": conclusie,
        "json_ld": json_ld,
        "faq_ld": faq_ld,
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
    })


AIRFRYER_FORMATS = ["compact", "xl", "dual"]
AIRFRYER_BASE_URL = "https://www.leefnatuurlijkengezond.nl"


def airfryers(request, fmt=None):
    if fmt == "compact":
        return redirect("airfryers", permanent=True)

    selected_format = fmt or "compact"
    if selected_format not in AIRFRYERS_RANKINGS:
        raise Http404("Onbekend airfryer-formaat")

    keys = AIRFRYERS_RANKINGS[selected_format]
    products = [copy.deepcopy(AIRFRYERS_PRODUCTS[k]) for k in keys if k in AIRFRYERS_PRODUCTS]
    _enrich_products(products, category="airfryers")
    product_count = len(products)

    raw = AIRFRYERS_CONTENT
    fmt_label = raw["formats"][selected_format]["label"]
    content = _format_content(raw, product_count=product_count, selected_format=fmt_label)
    fmt_meta = content["formats"][selected_format]

    canonical_path = "/airfryers/" if selected_format == "compact" else f"/airfryers/{selected_format}/"
    canonical_url = AIRFRYER_BASE_URL + canonical_path

    hero_h1 = fmt_meta["h1"]
    products_h2 = content["products_section"]["h2"]
    comparison_title = content["products_section"]["comparison_title"]
    conclusie = content["conclusies"].get(selected_format, {})

    faq_ld = _build_faq_ld(content["faq"]["items"])
    json_ld = _build_itemlist_ld(
        request,
        fmt_meta["itemlist_name"],
        fmt_meta["itemlist_description"],
        products,
    )

    format_links = [
        {
            "key": k,
            "label": raw["formats"][k]["label"],
            "url": "/airfryers/" if k == "compact" else f"/airfryers/{k}/",
        }
        for k in AIRFRYER_FORMATS
    ]

    breadcrumbs = [{"label": "Airfryers", "url": "/airfryers/"}]
    if selected_format != "compact":
        breadcrumbs.append({"label": fmt_label, "url": None})

    return render(request, "airfryers.html", {
        "products": products,
        "top_picks": _build_top_picks(products),
        "in_het_kort": _build_in_het_kort(products, content),
        "product_count": product_count,
        "content": content,
        "selected_format": selected_format,
        "format_links": format_links,
        "hero_h1": hero_h1,
        "products_h2": products_h2,
        "comparison_title": comparison_title,
        "conclusie": conclusie,
        "intro_extra": fmt_meta["intro_extra"],
        "meta_title": fmt_meta["meta_title"],
        "meta_description": fmt_meta["meta_description"],
        "og_title": fmt_meta["og_title"],
        "og_description": fmt_meta["og_description"],
        "canonical_url": canonical_url,
        "json_ld": json_ld,
        "faq_ld": faq_ld,
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
    })


VERSHOUDBAKJES_TYPES = [
    {"key": "single", "slug": "enkel", "label": "Enkel", "heading": "Beste losse glazen vershoudbakjes"},
    {"key": "set_3", "slug": "3-delig", "label": "3-delig", "heading": "Beste 3-delige glazen vershoudsets"},
    {"key": "set_5", "slug": "5-delig", "label": "5-delig", "heading": "Beste 5-delige glazen vershoudsets"},
]

_VERSHOUDBAKJES_SLUG_TO_TYPE = {t["slug"]: t for t in VERSHOUDBAKJES_TYPES}

_ALLOWED_VERSHOUDBAKJES_AWARDS = {"🏆 Beste keuze", "💰 Budget keuze", "💎 Premium keuze"}


def _validate_vershoudbakjes_awards():
    for type_key, keys in VERSHOUDCONTAINERS_RANKINGS.items():
        seen = {}
        for k in keys:
            product = VERSHOUDCONTAINERS_PRODUCTS.get(k)
            if product is None:
                raise ValueError(f"Vershoudbakjes ranking '{type_key}' verwijst naar onbekende product key '{k}'")
            award = product.get("award") or ""
            if not award:
                continue
            if award not in _ALLOWED_VERSHOUDBAKJES_AWARDS:
                raise ValueError(f"Onbekend awardlabel '{award}' bij product '{k}' (uitvoering '{type_key}')")
            if award in seen:
                raise ValueError(
                    f"Award '{award}' komt meerdere keren voor in uitvoering '{type_key}': '{seen[award]}' en '{k}'"
                )
            seen[award] = k


_validate_vershoudbakjes_awards()

from products.validators_vershoudbakjes import validate_vershoudbakjes  # noqa: E402

VERSHOUDBAKJES_AUDIT_WARNINGS = validate_vershoudbakjes(
    VERSHOUDCONTAINERS_PRODUCTS, VERSHOUDCONTAINERS_RANKINGS
)


SIZE_FILTERS = [
    {"key": "all", "slug": "alle", "label": "Alle"},
    {"key": "small", "slug": "klein", "label": "Klein"},
    {"key": "medium", "slug": "middel", "label": "Middel"},
    {"key": "large", "slug": "groot", "label": "Groot"},
]

_SIZE_FILTER_SLUG_TO_FILTER = {f["slug"]: f for f in SIZE_FILTERS}


def get_selected_storage_type(request):
    slug = request.GET.get("uitvoering", "enkel")
    return _VERSHOUDBAKJES_SLUG_TO_TYPE.get(slug, VERSHOUDBAKJES_TYPES[0])


def get_selected_storage_size(request):
    slug = request.GET.get("formaat", "alle")
    return _SIZE_FILTER_SLUG_TO_FILTER.get(slug, SIZE_FILTERS[0])


def prepare_storage_product(product, selected_size):
    """Attach size-classification fields and, when a size filter is active,
    pick a matching display variant for shape-variant families."""
    product["size_categories"] = get_product_size_categories(product)
    own_category = classify_storage_size(
        product.get("capacities") if product.get("capacities") is not None else product.get("capacity")
    )
    product["size_category"] = own_category
    product["size_label"] = STORAGE_SIZE_LABELS.get(own_category, "")
    product["size_labels"] = [STORAGE_SIZE_LABELS[c] for c in product["size_categories"]]
    if not product["size_categories"]:
        logger.warning(
            "Vershoudbakjes product '%s' heeft geen bruikbare capaciteit; alleen zichtbaar bij formaat 'Alle'",
            product.get("slug"),
        )

    variants = product.get("shape_variants") or []
    if selected_size != "all" and variants:
        matching = [
            v for v in variants
            if classify_storage_size(v.get("capacities")) == selected_size
        ]
        if matching:
            current_default = product.get("default_variant")
            display = current_default if current_default in matching else matching[0]
            if display is not current_default:
                set_display_variant(product, display)
                product["formatted_capacity"], product["formatted_total_capacity"] = get_capacity_display(product)
                display_category = classify_storage_size(display.get("capacities"))
                product["size_category"] = display_category
                product["size_label"] = STORAGE_SIZE_LABELS.get(display_category, "")
    return product


def vershoudcontainers(request):
    content = VERSHOUDCONTAINERS_CONTENT
    selected_type = get_selected_storage_type(request)
    type_key = selected_type["key"]
    type_content = content["types"][type_key]
    selected_size_filter = get_selected_storage_size(request)
    size_key = selected_size_filter["key"]

    keys = VERSHOUDCONTAINERS_RANKINGS.get(type_key, [])
    # Deep copies: voorbereiden/variantselectie mag de brondata in PRODUCTS
    # (inclusief geneste variant-dicts) nooit muteren.
    all_ranked_products = [copy.deepcopy(VERSHOUDCONTAINERS_PRODUCTS[k]) for k in keys if k in VERSHOUDCONTAINERS_PRODUCTS]
    _enrich_products(all_ranked_products, category="vershoudcontainers")
    for p in all_ranked_products:
        prepare_storage_product(p, size_key)
    products = filter_products_by_storage_size(all_ranked_products, size_key)
    product_count = len(products)

    is_set_type = type_key != "single"
    comparison_rows = []
    for p in products:
        capacity_display = p.get("capacity_summary") or p.get("formatted_capacity") or ""
        total_display = p.get("formatted_total_capacity") or "" if is_set_type else ""
        display_variant = p.get("default_variant") if p.get("shape_variants") else None
        commercial = resolve_commercial_fields(p, display_variant)
        comparison_rows.append({
            "product": p,
            "display_variant": display_variant,
            "display_variant_id": display_variant.get("id") if display_variant else None,
            "affiliate_url": commercial["affiliate_url"],
            # Dezelfde centrale resolver als de productkaart; geen
            # afwijkende linkprioriteit in de vergelijkingstabel.
            "resolved_link": resolve_product_link(p, display_variant),
            "availability_label": resolve_availability_label(p, display_variant),
            "price": commercial["price"],
            "availability": commercial["availability"],
            # Prijsniveau expliciet per rij (zelfde bron als de productkaart).
            "price_range": p.get("display_price_range") or "",
            "rating": p.get("rating"),
            "rating_class": p.get("rating_class"),
            "rating_display": p.get("rating_display"),
            "capacity_display": capacity_display,
            "total_display": total_display,
            "size_display": ", ".join(p.get("size_labels") or []) or "—",
        })

    available_types = [
        {
            "key": t["key"],
            "slug": t["slug"],
            "label": t["label"],
            "url": f"?uitvoering={t['slug']}&formaat={selected_size_filter['slug']}",
            "is_active": t["key"] == type_key,
        }
        for t in VERSHOUDBAKJES_TYPES
    ]

    available_size_filters = [
        {
            "key": f["key"],
            "slug": f["slug"],
            "label": f["label"],
            "url": f"?uitvoering={selected_type['slug']}&formaat={f['slug']}",
            "is_active": f["key"] == size_key,
        }
        for f in SIZE_FILTERS
    ]
    size_filter_reset_url = f"?uitvoering={selected_type['slug']}&formaat=alle"
    size_filter_help = (
        "Het formaat is gebaseerd op de inhoud van het grootste bakje: "
        f"Klein tot en met {STORAGE_SIZE_THRESHOLDS['small_max_ml']} ml, "
        f"Middel tot en met {format_total_capacity(STORAGE_SIZE_THRESHOLDS['medium_max_ml'])}, "
        f"Groot daarboven."
    )

    conclusie = type_content.get("conclusie")
    faq_ld = _build_faq_ld(content["faq"]["items"])
    json_ld = _build_itemlist_ld(
        request,
        type_content["itemlist_name"],
        type_content["itemlist_description"],
        products,
    )
    breadcrumbs = [{"label": "Vershoudbakjes", "url": "/vershoudcontainers/"}]
    return render(request, "vershoudcontainers.html", {
        "products": products,
        "top_picks": _build_top_picks(products),
        "in_het_kort": _build_in_het_kort(products, content),
        "product_count": product_count,
        "content": content,
        "available_types": available_types,
        "selected_type": selected_type,
        "selected_type_key": type_key,
        "selected_type_label": selected_type["label"],
        "type_heading": type_content["heading"],
        "type_intro": type_content.get("intro"),
        "comparison_title": type_content["comparison_title"],
        "show_total_column": is_set_type,
        "comparison_rows": comparison_rows,
        "available_size_filters": available_size_filters,
        "selected_size_filter": selected_size_filter,
        "selected_size_key": size_key,
        "size_filter_help": size_filter_help,
        "size_filter_reset_url": size_filter_reset_url,
        "visible_product_count": product_count,
        "conclusie": conclusie,
        "json_ld": json_ld,
        "faq_ld": faq_ld,
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
    })


def _enrich_rvs_products(products):
    for p in products:
        p["image_path"] = "images/rvs-koekenpannen"
        p["image"] = (p.get("image") or "").split("/")[-1]
        if (p.get("affiliate_url") or "").startswith("TODO"):
            p["affiliate_url"] = None
    _enrich_products(products, category="rvs-koekenpannen")


def rvs_koekenpannen(request):
    content = RVS_KOEKENPANNEN_CONTENT
    available_sizes = sorted(RVS_KOEKENPANNEN_RANKINGS.keys())
    size = request.GET.get("size")
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = 28 if 28 in available_sizes else available_sizes[0]
    if size not in RVS_KOEKENPANNEN_RANKINGS:
        size = 28 if 28 in available_sizes else available_sizes[0]

    keys = RVS_KOEKENPANNEN_RANKINGS[size]
    products = [copy.deepcopy(RVS_KOEKENPANNEN_PRODUCTS[k]) for k in keys if k in RVS_KOEKENPANNEN_PRODUCTS]
    _enrich_rvs_products(products)
    product_count = len(products)
    conclusie = content["conclusies"].get(size, content["conclusies"]["default"])
    faq_ld = _build_faq_ld(content["faq"]["items"])
    real_products = [p for p in products if p["affiliate_url"]]
    itemlist_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": content["meta"]["title"],
        "description": content["meta"]["description"],
        "itemListOrder": "ItemListOrderDescending",
        "numberOfItems": len(real_products),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": p["name"],
                "url": p["affiliate_url"],
            }
            for i, p in enumerate(real_products)
        ],
    })
    meta = content["meta"]
    breadcrumbs = [{"label": "Koekenpannen", "url": "/koekenpannen/"}, {"label": "RVS", "url": "/rvs-koekenpannen/"}]
    return render(request, "rvs-koekenpannen.html", {
        "products": products,
        "top_picks": _build_top_picks(products),
        "in_het_kort": _build_in_het_kort(products, content),
        "available_sizes": available_sizes,
        "selected_size": size,
        "product_count": product_count,
        "content": content,
        "conclusie": conclusie,
        "faq_ld": faq_ld,
        "itemlist_ld": itemlist_ld,
        "meta": meta,
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
    })


def blogs(request):
    return render(request, "blogs.html")


def blog01(request):
    return render(request, "blog-pfas-in-huis.html")


def product_list(request):
    products = Product.objects.filter(is_active=True)
    return render(request, "products/product_list.html", {"products": products})


def product_detail(request, slug):
    if slug in SLUG_REDIRECTS:
        new_slug = SLUG_REDIRECTS[slug]
        if new_slug != slug and new_slug in ALL_PRODUCTS_BY_SLUG:
            return redirect("product_detail", slug=new_slug, permanent=True)
    entry = ALL_PRODUCTS_BY_SLUG.get(slug)
    if entry:
        # Deep copy: verrijking/variantnormalisatie mag de brondata nooit muteren.
        product = copy.deepcopy(entry["data"])
        cat_key = entry["category"]
        cat_info = CATEGORY_MAP[cat_key]
        _enrich_products([product], category=cat_key)
        if cat_key == "rvs-koekenpannen":
            product["image_path"] = "images/rvs-koekenpannen"
            product["image"] = (product.get("image") or "").split("/")[-1]
            if (product.get("affiliate_url") or "").startswith("TODO"):
                product["affiliate_url"] = None
                # affiliate_url is na verrijking gewijzigd: resolved link
                # opnieuw bepalen via de centrale resolver.
                apply_resolved_link(product)
        from django.urls import reverse
        category_url = reverse(cat_info["url_name"])
        breadcrumbs = [
            {"label": cat_info["label"], "url": category_url},
            {"label": product["name"], "url": None},
        ]
        return render(request, "product_detail.html", {
            "product": product,
            "category_label": cat_info["label"],
            "category_url": category_url,
            "breadcrumbs": breadcrumbs,
            "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
        })
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "products/product_detail.html", {"product": product})


def track_and_redirect(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    Click.objects.create(
        product=product,
        ip=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT"),
    )
    return redirect(product.affiliate_url)
