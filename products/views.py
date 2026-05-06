import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from .models import Product, Click
import json
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


def _enrich_products(products):
    for p in products:
        p["rating_class"] = str(p["rating"]).replace(".", "-")
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
                "item": {
                    "@type": "Product",
                    "name": p["name"],
                    "description": p["description"],
                    "image": request.build_absolute_uri(
                        f"/static/{p['image_path']}/{p['image']}"
                    ),
                    "brand": {"@type": "Brand", "name": p["brand"]},
                    "material": p["material"],
                    "aggregateRating": {
                        "@type": "AggregateRating",
                        "ratingValue": p["rating"],
                        "reviewCount": p["rating_count"],
                    },
                    "offers": {
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
                    },
                },
            }
            for i, p in enumerate(products)
        ],
    })


def snijplanken(request):
    products = [dict(SNIJPLANKEN_PRODUCTS[k]) for k in SNIJPLANKEN_RANKINGS]
    _enrich_products(products)
    product_count = len(products)
    content = SNIJPLANKEN_CONTENT
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
    products = [dict(KOEKENPANNEN_PRODUCTS[k]) for k in keys if k in KOEKENPANNEN_PRODUCTS]
    _enrich_products(products)
    product_count = len(products)

    conclusie = content["conclusies"].get(size, {})
    hero_h1 = content["hero"]["h1"].format(product_count=product_count, selected_size=size)
    products_h2 = content["products_section"]["h2"].format(product_count=product_count, selected_size=size)
    comparison_title = content["products_section"]["comparison_title"].format(
        product_count=product_count, selected_size=size
    )
    faq_ld = _build_faq_ld(content["faq"]["items"])
    json_ld = _build_itemlist_ld(
        request,
        f"Top {product_count} PFAS-vrije Koekenpannen {size} cm",
        f"Top {product_count} PFAS-vrije koekenpannen van {size}\u00a0cm \u2013 duurzaam, gezond en zonder schadelijke stoffen.",
        products,
    )
    breadcrumbs = [{"label": "Koekenpannen", "url": "/koekenpannen/"}]
    return render(request, "koekenpannen.html", {
        "products": products,
        "top_picks": _build_top_picks(products),
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
    products = [dict(HAPJESPANNEN_PRODUCTS[k]) for k in keys if k in HAPJESPANNEN_PRODUCTS]
    _enrich_products(products)
    product_count = len(products)

    conclusie = content["conclusies"].get(size, {})
    hero_h1 = content["hero"]["h1"].format(product_count=product_count, selected_size=size)
    products_h2 = content["products_section"]["h2"].format(product_count=product_count, selected_size=size)
    comparison_title = content["products_section"]["comparison_title"].format(
        product_count=product_count, selected_size=size
    )
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
    products = [dict(WOKPANNEN_PRODUCTS[k]) for k in keys if k in WOKPANNEN_PRODUCTS]
    _enrich_products(products)
    product_count = len(products)

    conclusie = content["conclusies"].get(size, {})
    hero_h1 = content["hero"]["h1"].format(product_count=product_count, selected_size=size)
    products_h2 = content["products_section"]["h2"].format(product_count=product_count, selected_size=size)
    comparison_title = content["products_section"]["comparison_title"].format(
        product_count=product_count, selected_size=size
    )
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


def airfryers(request):
    content = AIRFRYERS_CONTENT
    products = [dict(AIRFRYERS_PRODUCTS[k]) for k in AIRFRYERS_RANKINGS]
    _enrich_products(products)
    product_count = len(products)
    conclusie = content["conclusies"]["default"]
    faq_ld = _build_faq_ld(content["faq"]["items"])
    json_ld = _build_itemlist_ld(
        request,
        "Top 6 PFAS-vrije Airfryers van 2026",
        "De 6 beste PFAS-vrije airfryers van 2026 \u2013 gezond, duurzaam en zonder schadelijke stoffen.",
        products,
    )
    breadcrumbs = [{"label": "Airfryers", "url": "/airfryers/"}]
    return render(request, "airfryers.html", {
        "products": products,
        "top_picks": _build_top_picks(products),
        "product_count": product_count,
        "content": content,
        "conclusie": conclusie,
        "json_ld": json_ld,
        "faq_ld": faq_ld,
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
    })


def vershoudcontainers(request):
    content = VERSHOUDCONTAINERS_CONTENT
    products = [dict(VERSHOUDCONTAINERS_PRODUCTS[k]) for k in VERSHOUDCONTAINERS_RANKINGS]
    _enrich_products(products)
    product_count = len(products)
    conclusie = content["conclusies"]["default"]
    faq_ld = _build_faq_ld(content["faq"]["items"])
    json_ld = _build_itemlist_ld(
        request,
        "Top 5 PFAS-vrije Vershoudcontainers van 2026",
        "De 5 beste glazen vershoudcontainers van 2026 \u2013 voedselveilig, duurzaam en PFAS-vrij.",
        products,
    )
    breadcrumbs = [{"label": "Vershoudbakjes", "url": "/vershoudcontainers/"}]
    return render(request, "vershoudcontainers.html", {
        "products": products,
        "top_picks": _build_top_picks(products),
        "product_count": product_count,
        "content": content,
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
    _enrich_products(products)


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
    products = [dict(RVS_KOEKENPANNEN_PRODUCTS[k]) for k in keys if k in RVS_KOEKENPANNEN_PRODUCTS]
    _enrich_rvs_products(products)
    product_count = len(products)
    conclusie = content["conclusies"]["default"]
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
        product = dict(entry["data"])
        cat_key = entry["category"]
        cat_info = CATEGORY_MAP[cat_key]
        _enrich_products([product])
        if cat_key == "rvs-koekenpannen":
            product["image_path"] = "images/rvs-koekenpannen"
            product["image"] = (product.get("image") or "").split("/")[-1]
            if (product.get("affiliate_url") or "").startswith("TODO"):
                product["affiliate_url"] = None
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
