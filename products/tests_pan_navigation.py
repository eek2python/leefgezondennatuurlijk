"""Regression coverage for the Pannen IA and reference-only set collection."""
import copy
import json
import re
from html import unescape
from xml.etree import ElementTree

from django.test import TestCase
from django.urls import resolve, reverse

from .pan_catalogue import MATERIALS, SET_CATEGORIES, frying_pan_set_keys
from .views import ALL_PRODUCTS_BY_SLUG


NEW_ROUTES = {
    "pannen": "/pannen/",
    "pannensets": "/pannensets/",
    "koekenpannensets": "/pannensets/koekenpannensets/",
    "bak_en_braad_sets": "/bak-braadsets/",
    "kookpannensets": "/kookpannensets/",
    "complete_pannensets": "/complete-pannensets/",
}
OLD_ROUTES = {
    "koekenpannen": "/koekenpannen/",
    "rvs_koekenpannen": "/rvs-koekenpannen/",
    "koolstofstalen_koekenpannen": "/koolstofstalen-koekenpannen/",
    "gietijzeren_koekenpannen": "/gietijzeren-koekenpannen/",
    "hapjespannen": "/hapjespannen/",
    "wokpannen": "/wokpannen/",
    "blogs_overview": "/blogs/",
}


def ld_objects(response):
    return [
        json.loads(text) for text in re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
            response.content.decode(), re.S,
        )
    ]


class PanNavigationTests(TestCase):
    def test_routes_and_unique_canonical(self):
        for name, path in {**OLD_ROUTES, **NEW_ROUTES}.items():
            with self.subTest(name=name):
                self.assertEqual(reverse(name), path)
                self.assertEqual(resolve(path).url_name, name)
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                canonical = re.findall(
                    r'<link\s+rel="canonical"\s+href="([^"]+)"',
                    response.content.decode(),
                )
                self.assertEqual(canonical, ["https://leefnatuurlijkengezond.nl" + path])

    def test_new_metadata_and_structured_data(self):
        titles = set()
        for name, path in NEW_ROUTES.items():
            response = self.client.get(path)
            html = response.content.decode()
            title = re.search(r"<title>(.*?)</title>", html).group(1)
            self.assertNotIn(title, titles)
            titles.add(title)
            for tag in ('name="description"', 'property="og:title"',
                        'property="og:url"', 'name="twitter:title"'):
                self.assertIn(tag, html)
            self.assertContains(response, f'property="og:url" content="https://leefnatuurlijkengezond.nl{path}"')
            objects = ld_objects(response)
            self.assertEqual(sum(o["@type"] == "CollectionPage" for o in objects), 1)
            # List pages must not invent product reviews or offers.
            for obj in objects:
                if obj["@type"] == "ItemList":
                    self.assertTrue(all(item["@type"] == "ListItem" for item in obj["itemListElement"]))
                    self.assertNotIn('"offers"', json.dumps(obj))
                    self.assertNotIn('"aggregateRating"', json.dumps(obj))

    def test_single_menu_group_with_working_named_links(self):
        response = self.client.get(reverse("pannen"))
        html = response.content.decode()
        menu = re.search(r'<nav id="menu">(.*?)</nav>', html, re.S).group(1)
        self.assertEqual(menu.count('class="opener"'), 1)
        self.assertIn('aria-expanded="false" aria-controls="menu-pannen">Pannen</button>', menu)
        self.assertIn('<ul id="menu-pannen" inert>', menu)
        for name in (*NEW_ROUTES, *OLD_ROUTES):
            if name == "blogs_overview":
                continue
            self.assertEqual(menu.count(f'href="{reverse(name)}"'), 1, name)
        for href in re.findall(r'href="([^"]+)"', menu):
            self.assertEqual(self.client.get(unescape(href)).status_code, 200)

    def test_breadcrumbs_match_json_ld(self):
        for name, path in {**NEW_ROUTES, **OLD_ROUTES}.items():
            if name == "blogs_overview":
                continue
            response = self.client.get(path)
            crumbs = response.context["breadcrumbs"]
            self.assertEqual(crumbs[0]["label"], "Pannen")
            ld = next(obj for obj in ld_objects(response) if obj["@type"] == "BreadcrumbList")
            self.assertEqual([c["name"] for c in ld["itemListElement"]], ["Home"] + [c["label"] for c in crumbs])
            visible = re.search(r'<nav class="breadcrumbs".*?</nav>', response.content.decode(), re.S).group(0)
            for crumb in crumbs[:-1]:
                self.assertIn(f'href="{crumb["url"]}"', visible)
                self.assertEqual(self.client.get(crumb["url"].split("#")[0]).status_code, 200)
            for item in ld["itemListElement"]:
                if "item" in item:
                    self.assertTrue(item["item"].startswith("https://leefnatuurlijkengezond.nl/"))

    def test_sitemap_includes_old_new_and_each_product_only_once(self):
        response = self.client.get(reverse("sitemap"))
        self.assertEqual(response.status_code, 200)
        xml = ElementTree.fromstring(response.content)
        locations = [e.text for e in xml.findall("{*}url/{*}loc")]
        self.assertEqual(len(locations), len(set(locations)))
        for path in (*NEW_ROUTES.values(), *OLD_ROUTES.values()):
            self.assertIn("https://leefnatuurlijkengezond.nl" + path, locations)
        self.assertTrue(all(loc.startswith("https://leefnatuurlijkengezond.nl/") for loc in locations))
        for config in SET_CATEGORIES.values():
            for product in config["products"].values():
                self.assertIn("https://leefnatuurlijkengezond.nl" + reverse("product_detail", args=[product["slug"]]), locations)

    def test_hubs_only_link_existing_relevant_blogs(self):
        from blogs.views import BLOG_ARTICLE_META
        for path in ("/pannen/", "/pannensets/"):
            response = self.client.get(path)
            content = response.content.decode().split('<!-- Sidebar -->')[0]
            slugs = re.findall(r'href="/blogs/([^/]+)/"', content)
            self.assertGreater(len(slugs), 0)
            for slug in slugs:
                self.assertIn(slug, BLOG_ARTICLE_META)
                self.assertEqual(self.client.get(reverse("blogs_detail", args=[slug])).status_code, 200)


class FryingPanCollectionTests(TestCase):
    def test_collection_uses_every_existing_set_exactly_once(self):
        response = self.client.get(reverse("koekenpannensets"))
        actual = [p["slug"] for p in response.context["products"]]
        expected = []
        for material in MATERIALS.values():
            for key in frying_pan_set_keys(material):
                original = material["products"][key]
                expected.append(original["slug"])
                self.assertIs(ALL_PRODUCTS_BY_SLUG[original["slug"]]["data"], original)
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual([len(g["products"]) for g in response.context["groups"]], [18, 13, 8, 5])

    def test_selection_does_not_mistake_a_multi_size_single_pan_for_a_set(self):
        material = {"products": {
            "single": {"slug": "single", "diameters": [24, 28]},
            "explicit": {"slug": "explicit", "set_type": "Koekenpannenset"},
            "cast": {"slug": "cast"},
        }, "rankings": {28: ["single", "explicit"], "Pannensets": ["cast", "explicit"]}}
        self.assertEqual(frying_pan_set_keys(material), ["explicit", "cast"])

    def test_filters_are_server_side_and_canonical_stays_unfiltered(self):
        for key, material in MATERIALS.items():
            response = self.client.get(reverse("koekenpannensets"), {"materiaal": key})
            self.assertEqual(response.context["selected_material"], key)
            self.assertEqual([p["slug"] for p in response.context["products"]],
                             [material["products"][k]["slug"] for k in frying_pan_set_keys(material)])
            self.assertContains(response, 'rel="canonical" href="https://leefnatuurlijkengezond.nl/pannensets/koekenpannensets/"', count=1)
            self.assertContains(response, f'href="{reverse(material["url_name"])}"')
        response = self.client.get(reverse("koekenpannensets"), {"materiaal": "invalid"})
        self.assertEqual(response.context["selected_material"], "alle")
        self.assertEqual(len(response.context["groups"]), 4)

    def test_material_set_filters_and_enrichment_are_unchanged(self):
        for material_key, material in MATERIALS.items():
            for size, keys in material["rankings"].items():
                expected = [key for key in keys if key in frying_pan_set_keys(material)]
                if not expected:
                    continue
                response = self.client.get(reverse(material["url_name"]), {"size": size})
                actual = response.context["products"]
                self.assertEqual([p["slug"] for p in actual],
                                 [material["products"][key]["slug"] for key in keys])
                central = self.client.get(reverse("koekenpannensets"), {"materiaal": material_key})
                lookup = {p["slug"]: p for p in central.context["products"]}
                for p in actual:
                    for field in ("display_price_range", "award", "award_class", "resolved_link", "rating_display"):
                        self.assertEqual(p.get(field), lookup[p["slug"]].get(field), (p["slug"], field))

    def test_no_source_mutation_after_any_listing_or_detail(self):
        configs = list(MATERIALS.values()) + list(SET_CATEGORIES.values())
        before = [copy.deepcopy(c["products"]) for c in configs]
        self.client.get(reverse("koekenpannensets"))
        for key in MATERIALS:
            self.client.get(reverse("koekenpannensets"), {"materiaal": key})
        for category, config in SET_CATEGORIES.items():
            self.client.get(reverse(config["url_name"]))
            for product in config["products"].values():
                self.client.get(reverse("product_detail", args=[product["slug"]]))
        for config, original in zip(configs, before):
            self.assertEqual(config["products"], original)

    def test_new_set_categories_keep_rankings_and_source_references(self):
        for key, config in SET_CATEGORIES.items():
            response = self.client.get(reverse(config["url_name"]))
            self.assertEqual([p["slug"] for p in response.context["products"]],
                             [config["products"][k]["slug"] for k in config["rankings"]])
            for product in config["products"].values():
                entry = ALL_PRODUCTS_BY_SLUG[product["slug"]]
                self.assertIs(entry["data"], product)
                self.assertEqual(entry["category"], key)
                detail = self.client.get(reverse("product_detail", args=[product["slug"]]))
                self.assertEqual(detail.status_code, 200)
                self.assertEqual(detail.context["breadcrumbs"][1]["label"], "Pannensets")

    def test_unknown_products_remain_real_404(self):
        self.assertEqual(self.client.get("/product/nonexistent-pan-set/").status_code, 404)

    def test_missing_photo_never_renders_broken_product_image(self):
        for config in SET_CATEGORIES.values():
            response = self.client.get(reverse(config["url_name"]))
            for product in response.context["products"]:
                if product["image_unavailable"]:
                    self.assertNotContains(response, f'/static/{product["image_path"]}/{product["image"]}')
                    self.assertContains(response, "Productfoto nog niet beschikbaar.")
