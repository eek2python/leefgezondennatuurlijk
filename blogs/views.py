import json
from django.shortcuts import render
from django.http import Http404


def _build_breadcrumb_ld(breadcrumbs):
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.leefnatuurlijkengezond.nl/"}]
    for i, crumb in enumerate(breadcrumbs, start=2):
        entry = {"@type": "ListItem", "position": i, "name": crumb["label"]}
        if crumb.get("url"):
            entry["item"] = f"https://www.leefnatuurlijkengezond.nl{crumb['url']}"
        items.append(entry)
    return json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items})


BLOG_TITLES = {
    "koken-zonder-schadelijke-stoffen": "Koken zonder Schadelijke Stoffen",
    "pfas-in-huis": "PFAS in Huis",
}


def blogs_overview(request):
   breadcrumbs = [{"label": "Blogs", "url": "/blogs/"}]
   return render(request, "blogs/blogoverzicht.html", {
       "breadcrumbs": breadcrumbs,
       "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
   })

def blogs_detail(request, slug):
   template_name = f"blogs/{slug}.html"
   title = BLOG_TITLES.get(slug, slug.replace("-", " ").title())
   breadcrumbs = [
       {"label": "Blogs", "url": "/blogs/"},
       {"label": title, "url": f"/blogs/{slug}/"},
   ]
   try:
       return render(request, template_name, {
           "breadcrumbs": breadcrumbs,
           "breadcrumb_ld": _build_breadcrumb_ld(breadcrumbs),
       })
   except:
       raise Http404("Pagina niet gevonden")

