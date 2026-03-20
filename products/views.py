from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Click
import json
from .data_koekenpannen import KOEKENPANNEN_TOP10_BY_SIZE
from .data_conclusies_koekenpannen import KOEKENPANNEN_CONCLUSIES_BY_SIZE
from .data_hapjespannen import HAPJESPANNEN_TOP10_BY_SIZE
from .data_conclusies_hapjespannen import HAPJESPANNEN_CONCLUSIES_BY_SIZE
from .data_wokpannen import WOKPANNEN_TOP10_BY_SIZE
from .data_conclusies_wokpannen import WOKPANNEN_CONCLUSIES_BY_SIZE
from .data_snijplanken import SNIJPLANKEN_PRODUCTS
from .data_conclusies_snijplanken import SNIJPLANKEN_CONCLUSIE
from .data_airfryers import AIRFRYERS_PRODUCTS
from .data_conclusies_airfryers import AIRFRYERS_CONCLUSIE
from .data_vershoudcontainers import VERSHOUDCONTAINERS_PRODUCTS
from .data_conclusies_vershoudcontainers import VERSHOUDCONTAINERS_CONCLUSIE


def homepage(request):
    return render(request, "index.html")


def _enrich_products(products):
    for p in products:
        p["rating_class"] = str(p["rating"]).replace(".", "-")
        award = p.get("award", "").lower()
        if "beste keuze" in award:
            p["award_class"] = "best-choice"
        elif "budget" in award:
            p["award_class"] = "budget-choice"
        elif "premium" in award:
            p["award_class"] = "premium-choice"
        elif "betaalbare" in award:
            p["award_class"] = "value-choice"
        else:
            p["award_class"] = ""


def snijplanken(request):
    products = [dict(p) for p in SNIJPLANKEN_PRODUCTS]
    _enrich_products(products)
    product_count = len(products)

    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Top 10 Houten Snijplanken zonder Plastic (PFAS-vrij)",
        "description": "De 10 beste houten snijplanken van 2026 – duurzaam, voedselveilig en PFAS-vrij.",
        "itemListOrder": "ItemListOrderDescending",
        "numberOfItems": product_count,
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
                    },
                },
            }
            for i, p in enumerate(products)
        ],
    })
    return render(request, "snijplanken.html", {
        "products": products,
        "product_count": product_count,
        "conclusie": SNIJPLANKEN_CONCLUSIE,
        "json_ld": json_ld,
    })


def koekenpannen(request):
    available_sizes = sorted(KOEKENPANNEN_TOP10_BY_SIZE.keys())
    size = request.GET.get("size")
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = available_sizes[0]

    koekenpannen = KOEKENPANNEN_TOP10_BY_SIZE.get(size, [])
    product_count = len(koekenpannen)

    for p in koekenpannen:
        p["rating_class"] = str(p["rating"]).replace(".", "-")
        award = p.get("award", "").lower()
        if "beste keuze" in award:
            p["award_class"] = "best-choice"
        elif "budget" in award:
            p["award_class"] = "budget-choice"
        elif "premium" in award:
            p["award_class"] = "premium-choice"
        elif "betaalbare" in award:
            p["award_class"] = "value-choice"
        else:
            p["award_class"] = ""

    conclusie = KOEKENPANNEN_CONCLUSIES_BY_SIZE.get(size)

    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Top 10 PFAS-vrije Koekenpannen {size} cm",
        "description": f"Top 10 PFAS-vrije koekenpannen van {size} cm – duurzaam, gezond en zonder schadelijke stoffen.",
        "itemListOrder": "ItemListOrderDescending",
        "numberOfItems": len(koekenpannen),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {
                    "@type": "Product",
                    "name": p["name"],
                    "description": p["description"],
                    "image": request.build_absolute_uri(
                        f"/static/images/{p['image']}"
                    ),
                    "brand": {
                        "@type": "Brand",
                        "name": p["brand"]
                    },
                    "material": p["material"],
                    "aggregateRating": {
                        "@type": "AggregateRating",
                        "ratingValue": p["rating"],
                        "reviewCount": p["rating_count"]
                    },
                    "offers": {
                        "@type": "Offer",
                        "url": p["affiliate_url"],
                        "price": p["price"],
                        "priceCurrency": p["currency"],
                        "availability": f"https://schema.org/{p['availability']}"
                    }
                }
            }
            for i, p in enumerate(koekenpannen)
        ]
    })
    return render(
        request,
        "koekenpannen.html",
        {
            "available_sizes": available_sizes,
            "selected_size": size,
            "koekenpannen": koekenpannen,
            "product_count": product_count,
            "conclusie": conclusie,
            "json_ld": json_ld,
        }
    )


def hapjespannen(request):
    available_sizes = sorted(HAPJESPANNEN_TOP10_BY_SIZE.keys())
    size = request.GET.get("size")
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = available_sizes[0]

    hapjespannen = HAPJESPANNEN_TOP10_BY_SIZE.get(size, [])
    product_count = len(hapjespannen)

    for p in hapjespannen:
        p["rating_class"] = str(p["rating"]).replace(".", "-")
        award = p.get("award", "").lower()
        if "beste keuze" in award:
            p["award_class"] = "best-choice"
        elif "budget" in award:
            p["award_class"] = "budget-choice"
        elif "premium" in award:
            p["award_class"] = "premium-choice"
        elif "betaalbare" in award:
            p["award_class"] = "value-choice"
        else:
            p["award_class"] = ""

    conclusie = HAPJESPANNEN_CONCLUSIES_BY_SIZE.get(size)

    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Top 10 PFAS-vrije Hapjespannen {size} cm",
        "description": f"Top 10 PFAS-vrije hapjespannen van {size} cm – duurzaam, gezond en zonder schadelijke stoffen.",
        "itemListOrder": "ItemListOrderDescending",
        "numberOfItems": len(hapjespannen),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {
                    "@type": "Product",
                    "name": p["name"],
                    "description": p["description"],
                    "image": request.build_absolute_uri(
                        f"/static/images/hapjespannen/{p['image']}"
                    ),
                    "brand": {
                        "@type": "Brand",
                        "name": p["brand"]
                    },
                    "material": p["material"],
                    "aggregateRating": {
                        "@type": "AggregateRating",
                        "ratingValue": p["rating"],
                        "reviewCount": p["rating_count"]
                    },
                    "offers": {
                        "@type": "Offer",
                        "url": p["affiliate_url"],
                        "price": p["price"],
                        "priceCurrency": p["currency"],
                        "availability": f"https://schema.org/{p['availability']}"
                    }
                }
            }
            for i, p in enumerate(hapjespannen)
        ]
    })
    return render(
        request,
        "hapjespannen.html",
        {
            "available_sizes": available_sizes,
            "selected_size": size,
            "hapjespannen": hapjespannen,
            "product_count": product_count,
            "conclusie": conclusie,
            "json_ld": json_ld,
        }
    )

def wokpannen(request):
    available_sizes = sorted(WOKPANNEN_TOP10_BY_SIZE.keys())
    size = request.GET.get("size")
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = available_sizes[0]

    wokpannen = WOKPANNEN_TOP10_BY_SIZE.get(size, [])
    product_count = len(wokpannen)

    for p in wokpannen:
        p["rating_class"] = str(p["rating"]).replace(".", "-")
        award = p.get("award", "").lower()
        if "beste keuze" in award:
            p["award_class"] = "best-choice"
        elif "budget" in award:
            p["award_class"] = "budget-choice"
        elif "premium" in award:
            p["award_class"] = "premium-choice"
        elif "betaalbare" in award:
            p["award_class"] = "value-choice"
        else:
            p["award_class"] = ""

    conclusie = WOKPANNEN_CONCLUSIES_BY_SIZE.get(size)

    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Top 10 PFAS-vrije Wokpannen {size} cm",
        "description": f"Top 10 PFAS-vrije Wokpannen van {size} cm – duurzaam, gezond en zonder schadelijke stoffen.",
        "itemListOrder": "ItemListOrderDescending",
        "numberOfItems": len(wokpannen),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {
                    "@type": "Product",
                    "name": p["name"],
                    "description": p["description"],
                    "image": request.build_absolute_uri(
                        f"/static/images/wokpannen/{p['image']}"
                    ),
                    "brand": {
                        "@type": "Brand",
                        "name": p["brand"]
                    },
                    "material": p["material"],
                    "aggregateRating": {
                        "@type": "AggregateRating",
                        "ratingValue": p["rating"],
                        "reviewCount": p["rating_count"]
                    },
                    "offers": {
                        "@type": "Offer",
                        "url": p["affiliate_url"],
                        "price": p["price"],
                        "priceCurrency": p["currency"],
                        "availability": f"https://schema.org/{p['availability']}"
                    }
                }
            }
            for i, p in enumerate(wokpannen)
        ]
    })
    return render(
        request,
        "wokpannen.html",
        {
            "available_sizes": available_sizes,
            "selected_size": size,
            "wokpannen": wokpannen,
            "product_count": product_count,
            "conclusie": conclusie,
            "json_ld": json_ld,
        }
    )


def airfryers(request):
    products = [dict(p) for p in AIRFRYERS_PRODUCTS]
    _enrich_products(products)
    product_count = len(products)

    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Top 6 PFAS-vrije Airfryers van 2026",
        "description": "De 6 beste PFAS-vrije airfryers van 2026 – gezond, duurzaam en zonder schadelijke stoffen.",
        "itemListOrder": "ItemListOrderDescending",
        "numberOfItems": product_count,
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
                    },
                },
            }
            for i, p in enumerate(products)
        ],
    })
    return render(request, "airfryers.html", {
        "products": products,
        "product_count": product_count,
        "conclusie": AIRFRYERS_CONCLUSIE,
        "json_ld": json_ld,
    })


def vershoudcontainers(request):
    products = [dict(p) for p in VERSHOUDCONTAINERS_PRODUCTS]
    _enrich_products(products)
    product_count = len(products)

    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Top 5 PFAS-vrije Vershoudcontainers van 2026",
        "description": "De 5 beste glazen vershoudcontainers van 2026 – voedselveilig, duurzaam en PFAS-vrij.",
        "itemListOrder": "ItemListOrderDescending",
        "numberOfItems": product_count,
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
                    },
                },
            }
            for i, p in enumerate(products)
        ],
    })
    return render(request, "vershoudcontainers.html", {
        "products": products,
        "product_count": product_count,
        "conclusie": VERSHOUDCONTAINERS_CONCLUSIE,
        "json_ld": json_ld,
    })


def blogs(request):
    return render(request, "blogs.html")


def blog01(request):
    return render(request, "blog-pfas-in-huis.html")


def product_list(request):
    products = Product.objects.filter(is_active=True)
    return render(request, "products/product_list.html", {"products": products})


def product_detail(request, slug):
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
