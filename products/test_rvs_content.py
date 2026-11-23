"""RVS content integration for single pans and sets, without editing source data."""
import copy
import json
import re
from unittest.mock import patch

from django.test import TestCase
from django.utils.html import escape

from products.content_rvs_koekenpannen import CONTENT
from products.products_rvs_koekenpannen import PRODUCTS
from products.rankings_rvs_koekenpannen import RANKINGS
from utils.quick_picks import AWARD_ORDER, build_quick_picks


class RvsContentTests(TestCase):
    def test_all_formats_render_every_supplied_text_and_unique_quick_pick_targets(self):
        products_before, content_before = copy.deepcopy(PRODUCTS), copy.deepcopy(CONTENT)

        def check_strings(value, html):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key != "ranges_by_size":
                        check_strings(child, html)
            elif isinstance(value, list):
                for child in value:
                    check_strings(child, html)
            elif isinstance(value, str):
                self.assertTrue(value in html or str(escape(value)) in html, value)

        for size, keys in RANKINGS.items():
            with self.subTest(size=size):
                response = self.client.get("/rvs-koekenpannen/", {"size": str(size)})
                self.assertEqual(response.status_code, 200)
                context, html = response.context, response.content.decode()
                self.assertEqual(html.count("<h1>"), 1)
                self.assertNotRegex(html, r"<h[1-6][^>]*>\s*</h[1-6]>")
                self.assertNotContains(response, "{selected_size}")
                self.assertNotContains(response, "{product_count}")
                for section, value in context["content"].items():
                    if section not in ("meta", "related_categories"):
                        check_strings(value, html)
                self.assertContains(response, f'<title>{CONTENT["meta"]["title"]} | Leef Natuurlijk &amp; Gezond</title>', html=True)
                self.assertContains(response, f'<meta name="description" content="{CONTENT["meta"]["description"]}">', html=True)
                self.assertEqual(context["conclusie"], {})
                products = context["products"]
                self.assertEqual([p["slug"] for p in products], [PRODUCTS[k]["slug"] for k in keys])
                for product, key in zip(products, keys):
                    for field in ("rating", "award", "price", "reference_price", "price_range",
                                  "pros", "cons", "verdict", "affiliate_url", "retailer_url"):
                        self.assertEqual(product.get(field), PRODUCTS[key].get(field), (key, field))
                self.assertEqual(context["quick_picks"], build_quick_picks(products))
                for pick in context["quick_picks"]:
                    product = pick["product"]
                    self.assertTrue(any(product is p for p in products))
                    self.assertEqual(html.count(f'id="product-{product["slug"]}"'), 1)
                    self.assertRegex(html, 'id="product-' + re.escape(product["slug"]) + r'" tabindex="-1"')
                    self.assertIn(f'href="#product-{product["slug"]}"', html)
                itemlist = json.loads(context["itemlist_ld"])
                self.assertEqual(itemlist["numberOfItems"], len(products))
                self.assertEqual(itemlist["name"], CONTENT["meta"]["title"])
                self.assertEqual(len(json.loads(context["faq_ld"])["mainEntity"]), len(CONTENT["faq"]["items"]))
                titles = [context["content"][key]["title"] for key in
                          ("price_guide", "how_we_assess", "awards", "size_guide", "why_choose", "tips", "faq")]
                positions = [html.index(title) for title in titles]
                self.assertEqual(positions, sorted(positions))
                self.assertLess(html.index("</table>"), positions[0])
                self.assertNotRegex(html, r"\(&#x27;(?:title|intro|bullets|outro)&#x27;,")
        self.assertEqual(PRODUCTS, products_before)
        self.assertEqual(CONTENT, content_before)

    def test_zero_to_three_awards_do_not_create_placeholder_cards(self):
        for count in range(4):
            products = copy.deepcopy(PRODUCTS)
            for index, key in enumerate(RANKINGS[28]):
                products[key]["award"] = list(AWARD_ORDER)[index] if index < count else ""
            with self.subTest(count=count), patch("products.views.RVS_KOEKENPANNEN_PRODUCTS", products):
                response = self.client.get("/rvs-koekenpannen/")
                self.assertContains(response, 'class="ceramic-quick-pick"', count=count)
                self.assertEqual(bool(response.context["quick_picks"]), bool(count))
                if not count:
                    self.assertNotContains(response, 'id="snel-kiezen"')

    def test_price_guide_only_shows_the_four_ranges_for_the_selected_format(self):
        for size in RANKINGS:
            with self.subTest(size=size):
                response = self.client.get("/rvs-koekenpannen/", {"size": str(size)})
                expected = CONTENT["price_guide"]["ranges_by_size"][str(size)]
                self.assertEqual(response.context["content"]["price_guide"]["ranges"], expected)
                section = re.search(r'<details id="prijsniveaus".*?</details>',
                                    response.content.decode(), re.S).group()
                self.assertEqual(section.count("<li>"), 4)
                for level in expected:
                    self.assertIn(f'<strong>{level["label"]}</strong>: {level["description"]}', section)
                for other_ranges in CONTENT["price_guide"]["ranges_by_size"].values():
                    for level in other_ranges:
                        if level["description"] not in [row["description"] for row in expected]:
                            self.assertNotIn(level["description"], section)

    def test_invalid_format_uses_default_price_ranges(self):
        response = self.client.get("/rvs-koekenpannen/?size=invalid")
        self.assertEqual(response.context["selected_size"], 28)
        self.assertEqual(response.context["content"]["price_guide"]["ranges"],
                         CONTENT["price_guide"]["ranges_by_size"]["28"])

    def test_missing_price_configuration_does_not_borrow_another_format(self):
        content = copy.deepcopy(CONTENT)
        del content["price_guide"]["ranges_by_size"]["28"]
        with patch("products.views.RVS_KOEKENPANNEN_CONTENT", content):
            response = self.client.get("/rvs-koekenpannen/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["content"]["price_guide"]["ranges"], [])

