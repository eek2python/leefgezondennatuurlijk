"""Appliance hub and gourmet comparison, using the existing category pipeline."""
import copy

from django.contrib.staticfiles import finders
from django.shortcuts import render
from django.urls import reverse

from LeefNatuurlijkenGezond.site_urls import absolute_site_url
from .appliance_catalogue import APPLIANCE_CATEGORIES
from .content_gourmetsets import CONTENT
from .products_gourmetsets import PRODUCTS
from .rankings_gourmetsets import RANKINGS
from .views import (
    _build_breadcrumb_ld, _build_faq_ld, _build_itemlist_ld,
    _enrich_products, _format_content,
)


def keukenapparatuur(request):
    canonical = absolute_site_url(reverse("keukenapparatuur"))
    breadcrumbs = [{"label": "Keukenapparatuur", "url": reverse("keukenapparatuur")}]
    categories = [dict(category) for category in APPLIANCE_CATEGORIES]
    # Use a real supplied photo when one becomes available, not an invented one.
    for category in categories:
        if category["key"] == "gourmetsets":
            for product in PRODUCTS.values():
                filename = product.get("image")
                image = f"{product['image_path']}/{filename}" if filename else ""
                if image and finders.find(image):
                    category["image"] = image
                    break
    return render(request, "keukenapparatuur.html", {
        "meta": {
            "title": "Keukenapparatuur voor bewust koken | Leef Natuurlijk & Gezond",
            "description": "Vergelijk airfryers en gourmetsets op prestaties, materialen, coatings, reiniging en duurzaamheid. Lees per onderdeel wat bekend is over PFAS.",
        },
        "canonical_url": canonical,
        "social_image": absolute_site_url("/static/images/airfryers.jpg"),
        "appliance_categories": categories,
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
    })


def gourmetsets(request):
    # Keep the supplied ranking order, even where scores or awards differ.
    products = [copy.deepcopy(PRODUCTS[key]) for key in RANKINGS]
    _enrich_products(products, category="gourmetsets")
    content = _format_content(CONTENT, product_count=len(products))
    page_meta = content["page_meta"]
    breadcrumbs = [
        {"label": "Keukenapparatuur", "url": reverse("keukenapparatuur")},
        {"label": "Gourmetsets", "url": reverse("gourmetsets")},
    ]
    return render(request, "gourmetsets.html", {
        "meta": {
            "title": page_meta["meta_title"],
            "description": page_meta["meta_description"],
            "og_title": page_meta["og_title"],
            "og_description": page_meta["og_description"],
        },
        "canonical_url": absolute_site_url(reverse("gourmetsets")),
        "social_image": absolute_site_url("/static/images/logo.jpg"),
        "hero_h1": page_meta["h1"],
        "products": products,
        "product_count": len(products),
        "content": content,
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
        "faq_ld": _build_faq_ld(content["faq"]["items"]),
        "itemlist_ld": _build_itemlist_ld(
            request, page_meta["itemlist_name"], page_meta["itemlist_description"], products
        ),
    })
