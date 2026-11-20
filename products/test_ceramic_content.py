"""Keramische contentopbouw en centrale prijsgrenzen, zonder productmutaties."""
import copy
import json
import re
from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.utils.html import escape

from products.content_koekenpannen import CONTENT
from products.products_koekenpannen import PRODUCTS
from products.rankings_koekenpannen import RANKINGS
from products.templatetags.product_formatting import format_size_label
from utils.pricing import (
    get_audit_price_thresholds, get_price_guide, get_price_range, get_regular_price,
)


SELECTIONS = (20, 24, 26, 28, 30, 32, "20_28", "24_28", "20_24_28")


class CeramicPriceGuideTests(SimpleTestCase):
    def test_all_boundaries_are_inclusive_and_shared_with_guide(self):
        for selection in SELECTIONS:
            product = (
                {"diameters": [int(x) for x in selection.split("_")]}
                if isinstance(selection, str) else {"diameter": selection}
            )
            thresholds = get_audit_price_thresholds("koekenpannen", product)
            guide = get_price_guide(selection)
            self.assertEqual([row["label"] for row in guide], [x[1] for x in thresholds])
            for index, (upper, label) in enumerate(thresholds[:-1]):
                with self.subTest(selection=selection, upper=upper):
                    self.assertEqual(get_price_range(
                        upper, product=product,
                    ), label)
                    self.assertEqual(get_price_range(
                        upper + Decimal("0.01"), product=product,
                    ), thresholds[index + 1][1])

    def test_guide_matches_requested_inclusive_wording(self):
        self.assertEqual(get_price_guide(28), [
            {"label": "€", "description": "Tot en met €40"},
            {"label": "€€", "description": "€40,01–€70"},
            {"label": "€€€", "description": "€70,01–€110"},
            {"label": "€€€€", "description": "Meer dan €110"},
        ])

    def test_sets_accept_tuples_and_underscores_without_using_largest_pan(self):
        self.assertEqual(get_price_guide((28, 20)), get_price_guide("20_28"))
        self.assertEqual(get_price_guide("24_28")[2]["description"], "€100,01–€175")
        self.assertNotEqual(get_price_guide("24_28"), get_price_guide(28))

    def test_configuration_change_reaches_both_rendering_and_guide(self):
        thresholds = ((Decimal("42"), "€"), (Decimal("80"), "€€"),
                      (Decimal("125"), "€€€"), (None, "€€€€"))
        with patch.dict("utils.pricing.KERAMISCHE_KOEKENPANNEN_PRICE_RANGES", {28: thresholds}):
            self.assertEqual(get_price_guide(28)[0]["description"], "Tot en met €42")
            self.assertEqual(get_price_range(42, product={"diameter": 28}), "€")

    def test_regular_price_and_variant_isolation(self):
        from products.views import _derive_price_levels
        product = {
            "diameter": 28, "price": 20, "reference_price": 120,
            "variants": [
                {"price": 20, "reference_price": 70},
                {"price": 20},
                {},
            ],
        }
        _derive_price_levels(product, "koekenpannen")
        self.assertEqual(product["display_price_range"], "€€")
        self.assertEqual(
            [v["display_price_range"] for v in product["variants"]], ["€€", "€", ""],
        )
        self.assertEqual(get_regular_price({"price": 10, "reference_price": 50}), 50)
        self.assertEqual(get_regular_price({"price": 10}), 10)

    def test_unknown_format_does_not_borrow_a_price_model(self):
        for selection in ("onbekend", 22, (), True):
            self.assertEqual(get_price_guide(selection), [])
        self.assertIsNone(get_price_range(40, product={"diameter": 22}))
        self.assertIsNone(get_price_range("Infinity", product={"diameter": 28}))
        self.assertIsNone(get_price_range("NaN", product={"diameter": 28}))

    def test_shape_variant_does_not_inherit_the_family_reference_price(self):
        from products.views import _derive_price_levels
        product = {
            "diameter": 28, "price": 20, "reference_price": 120,
            "shape_variants": [{"id": "a", "price": 20}],
            "default_variant": {"id": "a", "price": 20},
        }
        _derive_price_levels(product, "koekenpannen")
        self.assertEqual(product["display_price_range"], "€")

    def test_audit_uses_the_same_regular_price_and_inclusive_rule(self):
        from audits.checks.variants import audit_price_levels
        products = {"test": {"diameter": 28, "price": 10, "reference_price": 70,
                             "price_range": "€€"}}
        with patch("audits.checks.variants._load_products", return_value=products):
            errors, warnings, rows = audit_price_levels("koekenpannen", "unused")
        self.assertEqual((errors, warnings), ([], []))
        self.assertEqual(rows[0][-1], "€€")


class CeramicContentPageTests(TestCase):
    def test_nine_selections_keep_products_and_follow_requested_order(self):
        original_products = copy.deepcopy(PRODUCTS)
        original_rankings = copy.deepcopy(RANKINGS)
        for selection in SELECTIONS:
            with self.subTest(selection=selection):
                response = self.client.get("/koekenpannen/", {"size": str(selection)})
                self.assertEqual(response.status_code, 200)
                context = response.context
                # Existing view excludes stale ranking keys; this content-only
                # change must not invent products or rewrite the user's selection.
                expected_products = [
                    PRODUCTS[key] for key in RANKINGS[selection] if key in PRODUCTS
                ]
                label = format_size_label(selection)
                html = response.content.decode()
                self.assertEqual(context["selected_size"], selection)
                self.assertEqual(context["product_count"], len(expected_products))
                self.assertEqual(
                    [p["slug"] for p in context["products"]],
                    [p["slug"] for p in expected_products],
                )
                self.assertIn(
                    f"De {len(expected_products)} beste PFAS-vrije keramische "
                    f"koekenpannen van {label} cm (2026)", html,
                )
                headings = [
                    context["hero_h1"], context["products_h2"], context["comparison_title"],
                    CONTENT["price_guide"]["title"], CONTENT["how_we_assess"]["title"],
                    CONTENT["awards"]["title"], CONTENT["size_guide"]["title"],
                    CONTENT["why_choose"]["title"], CONTENT["tips"]["title"],
                    CONTENT["faq"]["title"],
                ]
                positions = [html.index(str(escape(title))) for title in headings]
                self.assertEqual(positions, sorted(positions))
                self.assertNotIn("Conclusie voor", html)
                self.assertNotIn('class="top-pick-card', html)
                self.assertNotIn("conclusie", context)
                self.assertIn('id="productlijst"', html)
                self.assertIn('id="vergelijking"', html)
                self.assertEqual(context["price_guide"], get_price_guide(selection))
                for row in context["price_guide"]:
                    self.assertIn(str(escape(row["description"])), html)
                # Enrichment may add display fields, never change editorial data.
                for rendered, source in zip(context["products"], expected_products):
                    for field in ("rating", "award", "price", "pros", "cons", "verdict",
                                  "comparison_features", "affiliate_url"):
                        self.assertEqual(rendered.get(field), source.get(field), field)
        self.assertEqual(PRODUCTS, original_products)
        self.assertEqual(RANKINGS, original_rankings)

    def test_assessment_weights_and_faq_remain_consistent_with_schema(self):
        self.assertEqual(sum(
            int(item["weight"].rstrip("%"))
            for item in CONTENT["how_we_assess"]["score_weights"]
        ), 100)
        questions = [item["q"] for item in CONTENT["faq"]["items"]]
        self.assertEqual(len(questions), len(set(questions)))
        response = self.client.get("/koekenpannen/")
        html = response.content.decode()
        for field in ("intro", "criteria_intro", "evidence", "score_explanation",
                      "review_note", "sets_note", "testing_note", "outro"):
            self.assertIn(str(escape(CONTENT["how_we_assess"][field])), html)
        blocks = [json.loads(value) for value in re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S,
        )]
        faq = next(block for block in blocks if block.get("@type") == "FAQPage")
        self.assertEqual([item["name"] for item in faq["mainEntity"]], questions)
        itemlist = next(block for block in blocks if block.get("@type") == "ItemList")
        self.assertEqual(len(itemlist["itemListElement"]), response.context["product_count"])
        self.assertNotIn("how_we_test", CONTENT)
        self.assertNotIn("conclusies", CONTENT)

    def test_metadata_is_dynamic_and_displays_the_selected_set(self):
        response = self.client.get("/koekenpannen/", {"size": "24_28"})
        html = response.content.decode()
        title = re.search(r"<title>(.*?)</title>", html, re.S)[1]
        description = re.search(
            r'<meta\s+name="description"\s+content="([^"]+)"', html, re.S,
        )[1]
        self.assertIn("24 + 28", title)
        self.assertIn("24 + 28", description)
        self.assertIn(str(response.context["product_count"]), description)

    def test_price_guide_and_assessment_can_be_rendered_without_javascript(self):
        html = self.client.get("/koekenpannen/").content.decode()
        self.assertIn("Tot en met €40", html)
        self.assertIn("25%", html)
        self.assertIn("PFAS-status is een toelatingsvoorwaarde", html)
        self.assertIn("Winkelgemiddelden vormen niet onze sterrenbeoordeling", html)
