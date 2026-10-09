"""Carbon-steel set selectors show ranked products and matching conclusions."""

import copy
import json
import re
from unittest.mock import patch

from django.test import TestCase

from products.content_koolstofstaal_koekenpannen import CONTENT
from products.products_koolstofstaal_koekenpannen import PRODUCTS
from products.rankings_koolstofstaal_koekenpannen import RANKINGS


class KoolstofstaalSetSelectorTests(TestCase):
    path = "/koolstofstalen-koekenpannen/"

    def test_selector_includes_both_sets_after_single_pans(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_size"], 28)
        self.assertEqual(
            response.context["available_sizes"],
            [20, 24, 28, 30, 32, "24_28", "20_24_28"],
        )
        for key, label in (("24_28", "24 + 28"), ("20_24_28", "20 + 24 + 28")):
            self.assertContains(response, f'href="?size={key}"', count=2)
            self.assertContains(response, f"{label} cm")

    def test_sets_load_ranked_products_and_selected_state(self):
        before = copy.deepcopy(PRODUCTS)
        for key in ("24_28", "20_24_28"):
            with self.subTest(size=key):
                response = self.client.get(self.path, {"size": key})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["selected_size"], key)
                self.assertEqual(response.context["product_count"], len(RANKINGS[key]))
                self.assertEqual(
                    [p["slug"] for p in response.context["products"]],
                    [PRODUCTS[k]["slug"] for k in RANKINGS[key]],
                )
                selected_links = re.findall(
                    r'<a\b[^>]*href="\?size=' + re.escape(key)
                    + r'"[^>]*aria-current="page"[^>]*>',
                    response.content.decode(),
                )
                self.assertEqual(len(selected_links), 2)
                self.assertContains(response, f"{' + '.join(key.split('_'))} cm")
                self.assertNotContains(response, f"{key} cm")
        self.assertEqual(PRODUCTS, before)

    def test_every_size_shows_its_authored_conclusion(self):
        for key in RANKINGS:
            with self.subTest(size=key):
                response = self.client.get(self.path, {"size": str(key)})
                conclusion = CONTENT["conclusies"][key]
                self.assertEqual(response.context["conclusie"], conclusion)
                self.assertContains(response, conclusion["title"])
                self.assertContains(response, conclusion["text"])

    def test_sets_keep_canonical_and_plain_itemlist(self):
        for key in ("24_28", "20_24_28"):
            with self.subTest(size=key):
                response = self.client.get(self.path, {"size": key})
                self.assertContains(
                    response,
                    '<link rel="canonical" href="https://leefnatuurlijkengezond.nl/koolstofstalen-koekenpannen/">',
                    html=True,
                )
                blocks = [
                    json.loads(block) for block in re.findall(
                        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                        response.content.decode(), re.S,
                    )
                ]
                itemlist = next(b for b in blocks if b.get("@type") == "ItemList")
                self.assertEqual(itemlist["numberOfItems"], len(RANKINGS[key]))
                self.assertIn(" + ".join(key.split("_")), itemlist["name"])
                self.assertTrue(all(
                    e["@type"] == "ListItem" for e in itemlist["itemListElement"]
                ))
                self.assertNotIn('"@type": "Product"', json.dumps(blocks))

    def test_invalid_size_falls_back_to_28(self):
        for size in ("18_22", "unknown", "2428", ""):
            with self.subTest(size=size):
                response = self.client.get(self.path, {"size": size})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["selected_size"], 28)
                self.assertEqual(response.context["conclusie"], CONTENT["conclusies"][28])

    def test_missing_set_conclusion_never_shows_single_pan_default(self):
        content = copy.deepcopy(CONTENT)
        del content["conclusies"]["24_28"]
        with patch("products.views.KOOLSTOFSTALEN_KOEKENPANNEN_CONTENT", content):
            response = self.client.get(self.path, {"size": "24_28"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["conclusie"], {})
        self.assertNotContains(response, content["conclusies"]["default"]["text"])
