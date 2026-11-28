"""Render the current wok content without changing editorial product data."""
import copy
import json
import re
from unittest.mock import patch

from django.test import TestCase
from django.utils.html import escape

from products.content_wokpannen import CONTENT
from products.products_wokpannen import PRODUCTS
from products.rankings_wokpannen import RANKINGS
from utils.quick_picks import AWARD_ORDER, build_quick_picks


class WokContentTests(TestCase):
    def test_formats_show_all_supplied_text_in_the_requested_order(self):
        before = copy.deepcopy((CONTENT, PRODUCTS, RANKINGS))

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
                response = self.client.get("/wokpannen/", {"size": size})
                self.assertEqual(response.status_code, 200)
                html, context = response.content.decode(), response.context
                self.assertEqual(html.count("<h1>"), 1)
                self.assertEqual(context["conclusie"], {})
                self.assertNotContains(response, "{selected_size}")
                self.assertNotContains(response, "{product_count}")
                self.assertNotRegex(html, r"<h[1-6][^>]*>\s*</h[1-6]>")
                self.assertNotRegex(html, r"\(&#x27;(?:title|intro|bullets|outro)&#x27;,")
                for value in context["content"].values():
                    check_strings(value, html)
                section_keys = ("price_guide", "how_we_assess", "awards",
                                "size_guide", "why_choose", "tips", "faq")
                positions = [
                    re.search(r"<h2[^>]*>\s*" + re.escape(str(escape(context["content"][key]["title"]))) + r"\s*</h2>", html).start()
                    for key in section_keys
                ]
                self.assertEqual(positions, sorted(positions))
                self.assertLess(html.index("</table>"), positions[0])
                products = context["products"]
                self.assertEqual([p["slug"] for p in products], [PRODUCTS[k]["slug"] for k in keys])
                for product, key in zip(products, keys):
                    for field in ("name", "rating", "award", "price", "reference_price",
                                  "price_range", "pros", "cons", "verdict",
                                  "affiliate_url", "retailer_url", "comparison_features"):
                        self.assertEqual(product.get(field), PRODUCTS[key].get(field), (key, field))
                self.assertEqual(context["quick_picks"], build_quick_picks(products))
                for pick in context["quick_picks"]:
                    product = pick["product"]
                    self.assertTrue(any(product is p for p in products))
                    self.assertContains(response, f'href="#product-{product["slug"]}"', count=1)
                    self.assertContains(response, f'id="product-{product["slug"]}" tabindex="-1"', count=1)
                self.assertEqual(json.loads(context["json_ld"])["numberOfItems"], len(products))
                self.assertEqual(len(json.loads(context["faq_ld"])["mainEntity"]),
                                 len(CONTENT["faq"]["items"]))
        self.assertEqual((CONTENT, PRODUCTS, RANKINGS), before)

    def test_price_explanation_uses_only_selected_format(self):
        for size in RANKINGS:
            with self.subTest(size=size):
                response = self.client.get("/wokpannen/", {"size": size})
                expected = CONTENT["price_guide"]["ranges_by_size"][str(size)]
                self.assertEqual(response.context["content"]["price_guide"]["ranges"], expected)
                section = re.search(r'<details id="prijsniveaus".*?</details>',
                                    response.content.decode(), re.S).group()
                self.assertEqual(section.count("<li>"), 4)
                for level in expected:
                    self.assertIn(f'<strong>{level["label"]}</strong>: {level["description"]}', section)
                for levels in CONTENT["price_guide"]["ranges_by_size"].values():
                    for level in levels:
                        if level["description"] not in [row["description"] for row in expected]:
                            self.assertNotIn(level["description"], section)

    def test_invalid_sizes_keep_default_content_and_price_explanation(self):
        for value in (None, "onbekend", "99", "24_28"):
            with self.subTest(value=value):
                response = self.client.get("/wokpannen/", {} if value is None else {"size": value})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["selected_size"], 28)
                self.assertEqual(response.context["content"]["price_guide"]["ranges"],
                                 CONTENT["price_guide"]["ranges_by_size"]["28"])

    def test_missing_format_price_explanation_is_not_borrowed(self):
        content = copy.deepcopy(CONTENT)
        del content["price_guide"]["ranges_by_size"]["28"]
        with patch("products.views.WOKPANNEN_CONTENT", content):
            response = self.client.get("/wokpannen/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["content"]["price_guide"]["ranges"], [])

    def test_zero_to_three_awards_do_not_add_placeholder_recommendations(self):
        for count in range(4):
            products = copy.deepcopy(PRODUCTS)
            for index, key in enumerate(RANKINGS[28]):
                products[key]["award"] = list(AWARD_ORDER)[index] if index < count else ""
            with self.subTest(count=count), patch("products.views.WOKPANNEN_PRODUCTS", products):
                response = self.client.get("/wokpannen/")
                self.assertContains(response, 'class="ceramic-quick-pick"', count=count)
                if not count:
                    self.assertNotContains(response, 'id="snel-kiezen"')
