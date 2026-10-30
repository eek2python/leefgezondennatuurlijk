"""Hubs and set comparisons using the existing product display pipeline."""
import copy
import json

from django.shortcuts import render
from django.urls import reverse

from LeefNatuurlijkenGezond.site_urls import absolute_site_url
from .pan_catalogue import MATERIALS, SET_CATEGORIES, frying_pan_set_keys, pan_breadcrumbs
from .views import (
    _build_breadcrumb_ld, _build_faq_ld, _build_itemlist_ld,
    _enrich_products, _enrich_rvs_products, _format_content,
)


def _page_context(meta, url_name, breadcrumbs):
    canonical = absolute_site_url(reverse(url_name))
    return {
        "meta": meta,
        "canonical_url": canonical,
        "social_image": absolute_site_url("/static/images/thumbnails/koekenpan.webp"),
        "breadcrumbs": breadcrumbs,
        "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
        "collection_ld": json.dumps({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": meta["title"], "description": meta["description"],
            "url": canonical,
        }),
    }


def _set_cards():
    return [
        {
            "label": "Koekenpannensets", "url_name": "koekenpannensets",
            "text": "Meerdere koekenpannen, meestal in verschillende diameters. Vergelijk keramisch, RVS, koolstofstaal en gietijzer.",
        },
        {
            "label": "Bak- & braadsets", "url_name": "bak_en_braad_sets",
            "text": "Verschillende typen bakpannen samen, zoals een koekenpan met een hapjespan of wokpan.",
        },
        {
            "label": "Kookpannensets", "url_name": "kookpannensets",
            "text": "Hoofdzakelijk kookpannen en steelpannen, eventueel met een soeppan of stoominzet, voor water, sauzen en soepen.",
        },
        {
            "label": "Complete pannensets", "url_name": "complete_pannensets",
            "text": "Kookpannen en bak- of braadpannen samen, voor wie meerdere pannentypen tegelijk wil aanschaffen.",
        },
    ]


def pannen(request):
    context = _page_context({
        "title": "Pannen: soorten, materialen en sets | Leef Natuurlijk & Gezond",
        "description": "Welke pan past bij jou? Vergelijk keramisch, RVS, koolstofstaal en gietijzer, hapjespannen, wokpannen en vier soorten pannensets.",
    }, "pannen", [{"label": "Pannen", "url": reverse("pannen")}])
    context.update(hub_kind="pannen", set_cards=_set_cards())
    return render(request, "pan_hub.html", context)


def pannensets(request):
    context = _page_context({
        "title": "Pannensets: kies het juiste type set | Leef Natuurlijk & Gezond",
        "description": "Kies tussen koekenpannensets, bak- & braadsets, kookpannensets en complete pannensets. Ontdek welke samenstelling aansluit op jouw keuken.",
    }, "pannensets", [
        {"label": "Pannen", "url": reverse("pannen")},
        {"label": "Pannensets", "url": reverse("pannensets")},
    ])
    context.update(hub_kind="pannensets", set_cards=_set_cards())
    return render(request, "pan_hub.html", context)


def set_category(request, category):
    config = SET_CATEGORIES[category]
    # Rankings and content stay in their existing modules. Unranked products
    # remain reachable as detail pages but are not silently added to rankings.
    products = [copy.deepcopy(config["products"][key]) for key in config["rankings"]]
    _enrich_products(products, category=category)
    content = _format_content(config["content"], product_count=len(products))
    context = _page_context(content["meta"], config["url_name"], pan_breadcrumbs(category))
    context.update({
        "products": products, "product_count": len(products), "content": content,
        "hero_h1": content["hero"]["h1"],
        "products_h2": content["products_section"]["h2"],
        "comparison_title": content["products_section"]["comparison_title"],
        "conclusie": content["conclusies"]["default"],
        "faq_ld": _build_faq_ld(content["faq"]["items"]),
        "itemlist_ld": _build_itemlist_ld(
            request, content["meta"]["title"], content["meta"]["description"], products,
        ),
    })
    return render(request, "pan_set_list.html", context)


def koekenpannensets(request):
    selected = request.GET.get("materiaal", "alle")
    if selected not in MATERIALS:
        selected = "alle"
    groups = []
    products = []
    for key, material in MATERIALS.items():
        if selected != "alle" and selected != key:
            continue
        items = [copy.deepcopy(material["products"][key]) for key in frying_pan_set_keys(material)]
        # Reuse exactly the enrichment of the source material page.
        if key == "rvs":
            _enrich_rvs_products(items)
        else:
            _enrich_products(items, category=material["category"])
        groups.append({**material, "products": items})
        products.extend(items)
    meta = {
        "title": "Koekenpannensets: keramisch, RVS, koolstofstaal en gietijzer",
        "description": "Vergelijk koekenpannensets uit vier materialen. Bekijk verschillende maten samen en kies keramisch, RVS, koolstofstaal of gietijzer.",
    }
    context = _page_context(meta, "koekenpannensets", pan_breadcrumbs("koekenpannensets"))
    context.update({
        "hero_h1": "Koekenpannensets: meerdere maten, één materiaal",
        "products_h2": "Vergelijk koekenpannensets",
        "comparison_title": "Koekenpannensets in één overzicht",
        "groups": groups, "products": products, "product_count": len(products),
        "materials": MATERIALS, "selected_material": selected,
        "itemlist_ld": _build_itemlist_ld(request, meta["title"], meta["description"], products),
        "content": {"hero": {"paragraphs": [
            "Een koekenpannenset bestaat uit meerdere koekenpannen, meestal in verschillende diameters. Kies het materiaal en de maten die passen bij wat je bakt en bij je kookplaat.",
            "Hier staan de bestaande sets uit onze vier materiaalvergelijkingen bij elkaar. De volgorde en eventuele badges komen uit die materiaal- en formaatgroepen; dit is geen nieuwe ranglijst over alle materialen heen.",
        ]}},
    })
    return render(request, "pan_set_list.html", context)
