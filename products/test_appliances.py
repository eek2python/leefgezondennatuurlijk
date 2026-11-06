import copy
import json
import re
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .appliance_catalogue import APPLIANCE_CATEGORIES, gourmet_specifications
from .products_gourmetsets import PRODUCTS
from .rankings_gourmetsets import RANKINGS


class ApplianceIntegrationTests(TestCase):
    def get_page(self, name, **kwargs):
        response = self.client.get(reverse(name, kwargs=kwargs or None))
        self.assertEqual(response.status_code, 200)
        return response, response.content.decode()

    def test_routes_metadata_and_breadcrumbs(self):
        for name in ("keukenapparatuur", "airfryers", "gourmetsets"):
            with self.subTest(name=name):
                response, html = self.get_page(name)
                canonical = "https://leefnatuurlijkengezond.nl" + reverse(name)
                self.assertIn(f'<link rel="canonical" href="{canonical}">', html)
                self.assertIn(f'<meta property="og:url" content="{canonical}">', html)
                for field in ('name="description"', 'property="og:title"', 'name="twitter:description"'):
                    self.assertRegex(html, "<meta " + field + r' content="[^"]+">')
                self.assertEqual(len(re.findall(r"<h1(?:\s|>)", html)), 1)
                self.assertNotIn('name="robots" content="noindex', html)
                expected = ["Home", "Keukenapparatuur"]
                if name != "keukenapparatuur":
                    expected.append(name.capitalize())
                schema = json.loads(response.context["breadcrumb_ld"])
                self.assertEqual([x["name"] for x in schema["itemListElement"]], expected)
                self.assertTrue(all("www." not in x.get("item", "") for x in schema["itemListElement"]))

    def test_menu_structure_and_hub_categories(self):
        _, html = self.get_page("keukenapparatuur")
        menu = html.split('<nav id="menu">', 1)[1].split("</nav>", 1)[0]
        submenu = menu.split('<ul id="menu-keukenapparatuur" inert>', 1)[1].split("</ul>", 1)[0]
        self.assertEqual(re.findall(r'<a href="[^"]+">([^<]+)</a>', submenu),
                         ["Alle keukenapparatuur", "Airfryers", "Gourmetsets"])
        self.assertEqual(menu.count('href="/airfryers/"'), 1)
        self.assertNotIn("<ul", submenu)
        cards = re.findall(r'<a href="([^"]+)" class="category-card">', html)
        self.assertEqual(cards, [reverse(c["url_name"]) for c in APPLIANCE_CATEGORIES])
        pans = menu.split('<ul id="menu-pannen" inert>', 1)[1].split("</ul>", 1)[0]
        self.assertEqual(len(re.findall(r"<a ", pans)), 13)

    def test_products_ranking_awards_prices_and_links_are_preserved(self):
        snapshot = copy.deepcopy(PRODUCTS)
        response, html = self.get_page("gourmetsets")
        rendered = response.context["products"]
        self.assertEqual([p["slug"] for p in rendered], [PRODUCTS[key]["slug"] for key in RANKINGS])
        self.assertEqual(html.count('class="product-block"'), 6)
        for product, key in zip(rendered, RANKINGS):
            source = PRODUCTS[key]
            self.assertEqual(product["rating"], source["rating"])
            self.assertEqual(product["award"], source["award"])
            self.assertEqual(product["display_price_range"], source["price_range"])
            self.assertEqual(product["resolved_link"].url, source["affiliate_url"] or source["retailer_url"])
            self.assertTrue(product["image_unavailable"])
            if source["affiliate_url"]:
                self.assertIn("sponsored", product["resolved_link"].rel)
            else:
                self.assertNotIn("sponsored", product["resolved_link"].rel)
        self.assertEqual(PRODUCTS, snapshot)
        self.assertEqual(html.count('class="product-specifications"'), 6)
        self.assertNotRegex(html, r'<img[^>]+src="[^"]*gourmetsets')
        self.assertIn("niet van toepassing", html)
        schema = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S)]
        self.assertTrue(any(x.get("@type") == "ItemList" for x in schema))
        self.assertTrue(any(x.get("@type") == "FAQPage" for x in schema))
        self.assertNotIn('"@type": "AggregateRating"', html)

    def test_missing_scores_awards_and_component_claims(self):
        products = copy.deepcopy(PRODUCTS)
        for product in products.values():
            product.pop("rating", None)
            product["award"] = None
        with patch("products.appliance_views.PRODUCTS", products):
            _, html = self.get_page("gourmetsets")
            self.assertEqual(html.count('class="product-block"'), 6)
            self.assertNotIn('class="product-badge', html)
            self.assertNotIn("None/5", html)
        changed = copy.deepcopy(next(iter(PRODUCTS.values())))
        changed["pfas_claim"] = {"grill_plate": "bevestigd", "pans": "onbekend"}
        facts = {row["label"]: row["value"] for row in gourmet_specifications(changed)}
        self.assertEqual(facts["PFAS-vrij: bakplaat"], "bevestigd")
        self.assertEqual(facts["PFAS-vrij: pannetjes"], "onbekend")
        changed["number_of_pans"] = 0
        self.assertIn({"label": "Aantal pannetjes", "value": 0}, gourmet_specifications(changed))

    def test_product_links_resolve_and_sitemap(self):
        for product in PRODUCTS.values():
            _, html = self.get_page("product_detail", slug=product["slug"])
            self.assertIn(product["slug"], html)
            self.assertEqual(html.count('class="product-specifications"'), 1)
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        xml = response.content.decode()
        for name in ("keukenapparatuur", "gourmetsets", "airfryers"):
            self.assertIn("<loc>https://leefnatuurlijkengezond.nl" + reverse(name) + "</loc>", xml)
        self.assertNotIn("https://www.", xml)

    def test_airfryer_formats_still_work(self):
        for fmt in ("xl", "dual"):
            response, html = self.get_page("airfryers_format", fmt=fmt)
            self.assertGreater(len(response.context["products"]), 0)
            self.assertIn("Keukenapparatuur", html)
