import json
from django.shortcuts import render
from django.http import Http404
from LeefNatuurlijkenGezond.site_urls import absolute_site_url


def _build_breadcrumb_ld(breadcrumbs):
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": absolute_site_url("/")}]
    for i, crumb in enumerate(breadcrumbs, start=2):
        entry = {"@type": "ListItem", "position": i, "name": crumb["label"]}
        if crumb.get("url"):
            entry["item"] = absolute_site_url(crumb["url"])
        items.append(entry)
    return json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items})


BLOG_TITLES = {
    "koken-zonder-schadelijke-stoffen": "Koken zonder Schadelijke Stoffen",
    "pfas-in-huis": "PFAS in Huis",
    "keramische-vs-rvs-koekenpan": "Keramische vs RVS koekenpan",
    "greenpan-barcelona-vs-demeyere-industry-5": "GreenPan Barcelona vs Demeyere Industry 5",
    "welke-maat-koekenpan": "Welke maat koekenpan",
    "is-keramische-coating-veilig": "Is keramische coating veilig?",
    "beste-koekenpan-inductie-pfas-vrij": "Beste koekenpan voor inductie (PFAS-vrij)",
    "rvs-pan-bakken-zonder-aanbakken": "Hoe bak je met een RVS pan zonder dat het aanbakt?",
    "koolstofstaal-vs-gietijzer-koekenpan": "Koolstofstaal vs gietijzer: welke koekenpan past bij jou?",
}

BLOG_ARTICLE_META = {
    "koken-zonder-schadelijke-stoffen": {
        "description": "Ontdek hoe je PFAS, BPA en andere ongewenste stoffen in de keuken beperkt met bewuste keuzes voor pannen, keukengerei en bewaarbakjes.",
        "image": "/static/images/blogs/blog-koken-zonder-schadelijke-stoffen-4x3.jpg",
    },
    "pfas-in-huis": {
        "description": "Lees waar PFAS in huis kunnen voorkomen en welke praktische stappen helpen om blootstelling via pannen, verpakkingen, textiel en cosmetica te beperken.",
        "image": "/static/images/blogs/blog-pfas-in-huis.jpg",
    },
    "keramische-vs-rvs-koekenpan": {
        "description": "Vergelijk keramische en RVS koekenpannen op gebruiksgemak, duurzaamheid, bakresultaat en koken zonder PFAS.",
        "image": "/static/images/thumbnails/keramische-vs-rvs-koekenpan.webp",
        "template": "blogs/internal/keramische-vs-rvs-koekenpan.html",
    },
    "greenpan-barcelona-vs-demeyere-industry-5": {
        "description": "Vergelijk de GreenPan Barcelona en Demeyere Industry 5 op materiaal, bakprestaties, onderhoud, duurzaamheid en gebruiksgemak.",
        "image": "/static/images/thumbnails/greenpan-barcelona-vs-demeyere-industry-5.webp",
    },
    "welke-maat-koekenpan": {
        "description": "Ontdek welke maat koekenpan past bij je huishouden, kookzone en gerechten, van compacte 20 cm-pan tot ruime 32 cm-pan.",
        "image": "/static/images/thumbnails/welke-maat-koekenpan.webp",
    },
    "is-keramische-coating-veilig": {
        "description": "Lees hoe een keramische antiaanbaklaag werkt, wat PFAS-vrij betekent en hoe je een keramische koekenpan veilig gebruikt en onderhoudt.",
        "image": "/static/images/thumbnails/is-keramische-coating-veilig.webp",
    },
    "beste-koekenpan-inductie-pfas-vrij": {
        "description": "Ontdek waarop je let bij een PFAS-vrije koekenpan voor inductie, zoals bodemopbouw, materiaal, warmteverdeling en onderhoud.",
        "image": "/static/images/thumbnails/beste-koekenpan-inductie-pfas-vrij.webp",
    },
    "rvs-pan-bakken-zonder-aanbakken": {
        "description": "Leer hoe je een RVS pan goed voorverwarmt en gebruikt, zodat ingrediënten mooi bakken en minder snel aan de bodem blijven kleven.",
        "image": "/static/images/thumbnails/rvs-pan-bakken-zonder-aanbakken.webp",
    },
    "koolstofstaal-vs-gietijzer-koekenpan": {
        "description": "Vergelijk koolstofstaal en gietijzer op gewicht, warmtebehoud, onderhoud en gebruiksgemak en kies de pan die bij je past.",
        "image": "/static/images/blogs/koolstofstaal-vs-gietijzer-koekenpan.webp",
    },
}


def _build_article_ld(slug):
    meta = BLOG_ARTICLE_META[slug]
    canonical = absolute_site_url(f"/blogs/{slug}/")
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": BLOG_TITLES[slug],
        "description": meta["description"],
        "image": absolute_site_url(meta["image"]),
        "mainEntityOfPage": canonical,
        "author": {"@type": "Organization", "name": "Leef Natuurlijk & Gezond"},
        "publisher": {"@type": "Organization", "name": "Leef Natuurlijk & Gezond"},
    }, ensure_ascii=False)


def blogs_overview(request):
   breadcrumbs = [{"label": "Blogs", "url": "/blogs/"}]
   return render(request, "blogs/blogoverzicht.html", {
       "breadcrumbs": breadcrumbs,
       "blog_breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
   })


def blogs_detail(request, slug):
   if slug not in BLOG_TITLES:
       raise Http404("Pagina niet gevonden")
   template_name = BLOG_ARTICLE_META[slug].get("template", f"blogs/{slug}.html")
   title = BLOG_TITLES[slug]
   breadcrumbs = [
       {"label": "Blogs", "url": "/blogs/"},
       {"label": title, "url": f"/blogs/{slug}/"},
   ]
   return render(request, template_name, {
       "breadcrumbs": breadcrumbs,
       "blog_breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
       "article_ld": _build_article_ld(slug),
   })

