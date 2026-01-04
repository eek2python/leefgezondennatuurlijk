from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Click
import json
from .data_koekenpannen import KOEKENPANNEN_TOP10_BY_SIZE
from .data_conclusies_koekenpannen import KOEKENPANNEN_CONCLUSIES_BY_SIZE
from .data_hapjespannen import HAPJESPANNEN_TOP10_BY_SIZE
from .data_conclusies_hapjespannen import HAPJESPANNEN_CONCLUSIES_BY_SIZE


def homepage(request):
    return render(request, "index.html")


def snijplanken(request):
    return render(request, "snijplanken.html")


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
    return render(request, "wokpannen.html")


def airfryers(request):
    return render(request, "airfryers.html")


def vershoudcontainers(request):
    return render(request, "vershoudcontainers.html")


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
