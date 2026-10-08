"""Comparison pages describe lists without claiming Product rich results."""

import copy
import json
import re
from urllib.parse import urlsplit

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from LeefNatuurlijkenGezond.site_urls import absolute_site_url
from products.views import _build_itemlist_ld


def json_ld_blocks(response):
    return [
        json.loads(block)
        for block in re.findall(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            response.content.decode(), re.S,
        )
    ]


class ItemListHelperTests(SimpleTestCase):
    def test_minimal_products_need_no_commercial_or_review_fields(self):
        products = [{"slug": "first", "name": "First"},
                    {"slug": "second", "name": "Second"}]
        before = copy.deepcopy(products)
        with self.settings(SITE_URL="https://canonical.example"):
            data = json.loads(_build_itemlist_ld(
                None, "Comparison", "Description", products,
            ))
        self.assertEqual(data["numberOfItems"], 2)
        self.assertEqual(data["itemListElement"], [
            {"@type": "ListItem", "position": 1, "name": "First",
             "url": "https://canonical.example/product/first/"},
            {"@type": "ListItem", "position": 2, "name": "Second",
             "url": "https://canonical.example/product/second/"},
        ])
        self.assertEqual(products, before)

    def test_empty_list_is_valid(self):
        data = json.loads(_build_itemlist_ld(None, "Empty", "", []))
        self.assertEqual(data["numberOfItems"], 0)
        self.assertEqual(data["itemListElement"], [])


class CategoryStructuredDataTests(TestCase):
    def assert_list_matches_visible_products(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, path)
        blocks = json_ld_blocks(response)
        lists = [block for block in blocks if block.get("@type") == "ItemList"]
        self.assertEqual(len(lists), 1, path)
        data = lists[0]
        products = response.context["products"]
        self.assertEqual(data["numberOfItems"], len(products), path)
        self.assertEqual(data["itemListElement"], [
            {
                "@type": "ListItem", "position": position, "name": p["name"],
                "url": absolute_site_url(
                    reverse("product_detail", kwargs={"slug": p["slug"]})
                ),
            }
            for position, p in enumerate(products, 1)
        ], path)
        serialized = json.dumps(blocks)
        for forbidden in (
            '"@type": "Product"', '"@type": "Offer"', '"offers"',
            '"review"', '"aggregateRating"',
        ):
            self.assertNotIn(forbidden, serialized, path)
        self.assertTrue(any(
            block.get("@type") == "BreadcrumbList" for block in blocks
        ), path)
        return response, data

    def test_all_category_lists_and_size_filters(self):
        paths = [
            "/koekenpannen/", "/rvs-koekenpannen/",
            "/koolstofstalen-koekenpannen/", "/gietijzeren-koekenpannen/",
            "/hapjespannen/", "/wokpannen/", "/snijplanken/",
            "/vershoudcontainers/", "/airfryers/",
            "/airfryers/xl/", "/airfryers/dual/",
        ]
        for path in paths:
            with self.subTest(path=path):
                response, data = self.assert_list_matches_visible_products(path)
                for entry in data["itemListElement"]:
                    detail = self.client.get(urlsplit(entry["url"]).path)
                    self.assertEqual(detail.status_code, 200, entry["url"])
                for size in response.context.get("available_sizes", []):
                    self.assert_list_matches_visible_products(f"{path}?size={size}")

    def test_storage_filters(self):
        for query in (
            "uitvoering=3-delig", "uitvoering=5-delig",
            "uitvoering=enkel&formaat=klein",
        ):
            with self.subTest(query=query):
                self.assert_list_matches_visible_products(
                    f"/vershoudcontainers/?{query}"
                )

    def test_skeppshult_remains_in_list_without_product_markup(self):
        response, data = self.assert_list_matches_visible_products(
            "/gietijzeren-koekenpannen/?size=28"
        )
        entries = [entry for entry in data["itemListElement"]
                   if entry["name"] == "Skeppshult Traditional"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0]["url"],
            absolute_site_url("/product/skeppshult-traditional-28/"),
        )
        self.assertContains(response, "Skeppshult Traditional")
