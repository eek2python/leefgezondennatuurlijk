"""Named cast-iron set selection alongside existing centimetre sizes."""

import copy
import json
import re
from unittest.mock import patch

from django.test import TestCase

from products.content_gietijzeren_koekenpannen import CONTENT
from products.products_gietijzeren_koekenpannen import PRODUCTS
from products.rankings_gietijzeren_koekenpannen import RANKINGS


class GietijzerPannensetsTests(TestCase):
    path = "/gietijzeren-koekenpannen/"

    def test_selector_shows_named_option_without_cm(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_size"], 28)
        self.assertEqual(
            response.context["available_sizes"],
            [20, 24, 26, 28, 30, "Pannensets"],
        )
        self.assertContains(response, 'href="?size=Pannensets"', count=2)
        self.assertContains(response, "Pannensets")
        self.assertNotContains(response, "Pannensets cm")
        for size in (20, 24, 26, 28, 30):
            self.assertContains(response, f"{size} cm")

    def test_sets_and_conclusion_for_upper_and_lower_case(self):
        before = copy.deepcopy(PRODUCTS)
        for query in ("Pannensets", "pannensets"):
            with self.subTest(query=query):
                response = self.client.get(self.path, {"size": query})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["selected_size"], "Pannensets")
                keys = RANKINGS["Pannensets"]
                self.assertEqual(response.context["product_count"], len(keys))
                self.assertEqual(
                    [p["slug"] for p in response.context["products"]],
                    [PRODUCTS[key]["slug"] for key in keys],
                )
                conclusion = CONTENT["conclusies"]["Pannensets"]
                self.assertEqual(response.context["conclusie"], conclusion)
                self.assertContains(response, conclusion["title"])
                self.assertContains(response, conclusion["text"])
                selected_links = re.findall(
                    r'<a\b[^>]*href="\?size=Pannensets"[^>]*aria-current="page"[^>]*>',
                    response.content.decode(),
                )
                self.assertEqual(len(selected_links), 2)
                self.assertContains(response, "Beste gietijzeren pannensets (2026)")
                self.assertNotContains(response, "Pannensets cm")
        self.assertEqual(PRODUCTS, before)

    def test_single_sizes_keep_their_conclusions(self):
        for size in (20, 24, 26, 28, 30):
            with self.subTest(size=size):
                response = self.client.get(self.path, {"size": size})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["selected_size"], size)
                self.assertContains(response, CONTENT["conclusies"][size]["text"])

    def test_unknown_format_uses_default(self):
        response = self.client.get(self.path, {"size": "unknown"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_size"], 28)

    def test_set_links_and_metadata(self):
        response = self.client.get(self.path, {"size": "Pannensets"})
        self.assertContains(
            response,
            '<link rel="canonical" href="https://leefnatuurlijkengezond.nl/gietijzeren-koekenpannen/">',
            html=True,
        )
        blocks = [
            json.loads(block) for block in re.findall(
                r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                response.content.decode(), re.S,
            )
        ]
        itemlist = next(b for b in blocks if b.get("@type") == "ItemList")
        self.assertEqual(itemlist["name"], "Beste gietijzeren pannensets")
        self.assertEqual(itemlist["numberOfItems"], len(RANKINGS["Pannensets"]))
        self.assertNotIn('"@type": "Product"', json.dumps(blocks))
        for entry in itemlist["itemListElement"]:
            path = entry["url"].split("https://leefnatuurlijkengezond.nl", 1)[1]
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_missing_named_conclusion_does_not_show_single_pan_default(self):
        content = copy.deepcopy(CONTENT)
        del content["conclusies"]["Pannensets"]
        with patch("products.views.GIETIJZEREN_KOEKENPANNEN_CONTENT", content):
            response = self.client.get(self.path, {"size": "Pannensets"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["conclusie"], {})
        self.assertNotContains(response, content["conclusies"]["default"]["text"])
