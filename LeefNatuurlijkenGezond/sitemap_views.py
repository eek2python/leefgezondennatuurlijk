import os
from django.http import HttpResponse
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from datetime import datetime


STATIC_URLS = [
    {"name": "homepage",           "loc_name": "homepage",          "changefreq": "weekly",  "priority": "1.0"},
    {"name": "koekenpannen",       "loc_name": "koekenpannen",      "changefreq": "monthly", "priority": "0.9"},
    {"name": "hapjespannen",       "loc_name": "hapjespannen",      "changefreq": "monthly", "priority": "0.9"},
    {"name": "wokpannen",          "loc_name": "wokpannen",         "changefreq": "monthly", "priority": "0.9"},
    {"name": "snijplanken",        "loc_name": "snijplanken",       "changefreq": "monthly", "priority": "0.9"},
    {"name": "airfryers",          "loc_name": "airfryers",         "changefreq": "monthly", "priority": "0.9"},
    {"name": "vershoudcontainers", "loc_name": "vershoudcontainers","changefreq": "monthly", "priority": "0.9"},
    {"name": "blogs_overview",     "loc_name": "blogs_overview",    "changefreq": "weekly",  "priority": "0.8"},
    {"name": "over_ons",           "loc_name": "over_ons",          "changefreq": "yearly",  "priority": "0.5"},
    {"name": "hoe_wij_beoordelen", "loc_name": "hoe_wij_beoordelen","changefreq": "yearly",  "priority": "0.5"},
    {"name": "privacy",            "loc_name": "privacy",           "changefreq": "yearly",  "priority": "0.3"},
]

BASE_URL = "https://leefnatuurlijkengezond.nl"


def sitemap_xml(request):
    static_urls = []
    for entry in STATIC_URLS:
        static_urls.append({
            "loc": BASE_URL + reverse(entry["loc_name"]),
            "changefreq": entry["changefreq"],
            "priority": entry["priority"],
        })

    blog_templates_path = os.path.join(settings.BASE_DIR, "blogs", "templates", "blogs")
    blog_urls = []
    if os.path.isdir(blog_templates_path):
        for filename in sorted(os.listdir(blog_templates_path)):
            if filename.endswith(".html") and filename != "blogoverzicht.html":
                slug = filename.replace(".html", "")
                file_path = os.path.join(blog_templates_path, filename)
                blog_urls.append({
                    "loc": f"{BASE_URL}/blogs/{slug}/",
                    "lastmod": datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).strftime("%Y-%m-%d"),
                })

    from products.views import ALL_PRODUCTS_BY_SLUG
    product_urls = []
    for slug in sorted(ALL_PRODUCTS_BY_SLUG):
        product_urls.append({
            "loc": BASE_URL + reverse("product_detail", kwargs={"slug": slug}),
            "changefreq": "monthly",
            "priority": "0.6",
        })

    xml = render_to_string("sitemap_template.xml", {
        "static_urls": static_urls,
        "blog_urls": blog_urls,
        "product_urls": product_urls,
    })
    return HttpResponse(xml, content_type="application/xml")
