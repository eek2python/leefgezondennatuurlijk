import copy
import json

from django.test import SimpleTestCase, TestCase

from utils.variant_helpers import prepare_product_variants
from utils.product_helpers import (
    calculate_total_capacity,
    format_capacities,
    format_total_capacity,
    get_capacity_display,
)


class FormatCapacitiesTests(SimpleTestCase):
    def test_single_ml(self):
        self.assertEqual(format_capacities([800]), "800 ml")

    def test_single_liter(self):
        self.assertEqual(format_capacities([1500]), "1,5 L")

    def test_exact_liter(self):
        self.assertEqual(format_capacities([1000]), "1 L")

    def test_two_decimals(self):
        self.assertEqual(format_capacities([1250]), "1,25 L")

    def test_grouped_equal(self):
        self.assertEqual(format_capacities([1000, 1000, 1000]), "3 × 1 L")

    def test_mixed_set(self):
        self.assertEqual(format_capacities([700, 700, 1500]), "2 × 700 ml + 1,5 L")

    def test_large_mixed_set(self):
        self.assertEqual(
            format_capacities([370, 370, 640, 1040]),
            "2 × 370 ml + 640 ml + 1,04 L",
        )

    def test_unsorted_input_is_sorted(self):
        self.assertEqual(format_capacities([1500, 700, 700]), "2 × 700 ml + 1,5 L")

    def test_empty_list(self):
        self.assertEqual(format_capacities([]), "")

    def test_none(self):
        self.assertEqual(format_capacities(None), "")

    def test_strings_ignored(self):
        self.assertEqual(format_capacities(["700"]), "")

    def test_negative_ignored(self):
        self.assertEqual(format_capacities([-100, 700]), "700 ml")

    def test_zero_and_none_entries_ignored(self):
        self.assertEqual(format_capacities([0, None, 800]), "800 ml")

    def test_float_liter_value(self):
        self.assertEqual(format_capacities([1000.0]), "1 L")

    def test_float_ml_value(self):
        self.assertEqual(format_capacities([999.5]), "999,5 ml")

    def test_large_value(self):
        self.assertEqual(format_capacities([12500]), "12,5 L")


class CalculateTotalCapacityTests(SimpleTestCase):
    def test_mixed_set(self):
        self.assertEqual(calculate_total_capacity([700, 700, 1500]), 2900)

    def test_equal_set(self):
        self.assertEqual(calculate_total_capacity([1000, 1000, 1000]), 3000)

    def test_invalid_entries(self):
        self.assertEqual(calculate_total_capacity([-100, "700", None, 700]), 700)

    def test_empty(self):
        self.assertEqual(calculate_total_capacity([]), 0)
        self.assertEqual(calculate_total_capacity(None), 0)


class FormatTotalCapacityTests(SimpleTestCase):
    def test_ml(self):
        self.assertEqual(format_total_capacity(800), "800 ml")

    def test_liters(self):
        self.assertEqual(format_total_capacity(1500), "1,5 L")
        self.assertEqual(format_total_capacity(2900), "2,9 L")
        self.assertEqual(format_total_capacity(2420), "2,42 L")
        self.assertEqual(format_total_capacity(3000), "3 L")

    def test_invalid(self):
        self.assertEqual(format_total_capacity(0), "")
        self.assertEqual(format_total_capacity(-5), "")
        self.assertEqual(format_total_capacity(None), "")
        self.assertEqual(format_total_capacity("2900"), "")


class GetCapacityDisplayTests(SimpleTestCase):
    def test_single_container_no_total(self):
        formatted, total = get_capacity_display({"capacities": [800]})
        self.assertEqual(formatted, "800 ml")
        self.assertEqual(total, "")

    def test_multi_container_with_total(self):
        formatted, total = get_capacity_display({"capacities": [700, 700, 1500]})
        self.assertEqual(formatted, "2 × 700 ml + 1,5 L")
        self.assertEqual(total, "2,9 L")

    def test_large_set_total(self):
        formatted, total = get_capacity_display({"capacities": [370, 370, 640, 1040]})
        self.assertEqual(formatted, "2 × 370 ml + 640 ml + 1,04 L")
        self.assertEqual(total, "2,42 L")

    def test_legacy_capacity_field(self):
        formatted, total = get_capacity_display({"capacity": [1500]})
        self.assertEqual(formatted, "1,5 L")
        self.assertEqual(total, "")

    def test_legacy_scalar_capacity(self):
        formatted, total = get_capacity_display({"capacity": 800})
        self.assertEqual(formatted, "800 ml")
        self.assertEqual(total, "")

    def test_capacities_take_priority(self):
        formatted, _ = get_capacity_display({"capacities": [800], "capacity": [1500]})
        self.assertEqual(formatted, "800 ml")

    def test_product_without_capacity(self):
        formatted, total = get_capacity_display({"name": "Koekenpan"})
        self.assertEqual(formatted, "")
        self.assertEqual(total, "")


class PrepareProductVariantsTests(TestCase):
    def _sample_product(self):
        return {
            "slug": "test-set",
            "name": "Test Set",
            "image_path": "images/vershoudbakjes",
            "price_range": "€",
            "variant_label": "Vorm",
            "variants": [
                {
                    "id": "round",
                    "label": "Rond",
                    "shape": "Rond",
                    "capacities": [700, 700, 1500],
                    "image": "test-rond.jpg",
                    "price": 24.95,
                    "currency": "EUR",
                    "availability": "InStock",
                    "affiliate_url": "https://example.com/rond",
                    "is_default": True,
                },
                {
                    "id": "square",
                    "label": "Vierkant",
                    "shape": "Vierkant",
                    "capacities": [],
                    "image": "",
                    "price": None,
                    "currency": "EUR",
                    "availability": "",
                    "affiliate_url": "",
                    "is_default": False,
                },
            ],
        }

    def test_two_unique_valid_variants(self):
        product = self._sample_product()
        prepare_product_variants(product)
        self.assertEqual(len(product["shape_variants"]), 2)
        ids = [v["id"] for v in product["shape_variants"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_exactly_one_default_selected(self):
        product = self._sample_product()
        prepare_product_variants(product)
        self.assertEqual(product["default_variant"]["id"], "round")

    def test_default_fallback_to_first(self):
        product = self._sample_product()
        for v in product["variants"]:
            v["is_default"] = False
        prepare_product_variants(product)
        self.assertEqual(product["default_variant"]["id"], "round")

    def test_default_data_copied_to_product_level(self):
        product = self._sample_product()
        prepare_product_variants(product)
        self.assertEqual(product["image"], "test-rond.jpg")
        self.assertEqual(product["capacities"], [700, 700, 1500])
        self.assertEqual(product["price"], 24.95)
        self.assertEqual(product["affiliate_url"], "https://example.com/rond")
        self.assertEqual(product["availability"], "InStock")

    def test_capacity_formatting_per_variant(self):
        product = self._sample_product()
        prepare_product_variants(product)
        round_v, square_v = product["shape_variants"]
        self.assertEqual(round_v["formatted_capacity"], "2 × 700 ml + 1,5 L")
        self.assertEqual(round_v["formatted_total_capacity"], "2,9 L")
        self.assertEqual(round_v["total_capacity_ml"], 2900)
        self.assertEqual(round_v["container_count"], 3)
        self.assertEqual(square_v["formatted_capacity"], "")
        self.assertEqual(square_v["formatted_total_capacity"], "")
        self.assertEqual(square_v["container_count"], 0)

    def test_selected_summary(self):
        product = self._sample_product()
        prepare_product_variants(product)
        round_v, square_v = product["shape_variants"]
        self.assertEqual(
            round_v["selected_summary"], "Geselecteerd: Rond · 2 × 700 ml + 1,5 L"
        )
        self.assertEqual(square_v["selected_summary"], "Geselecteerd: Vierkant")

    def test_missing_price_stays_none_not_zero(self):
        product = self._sample_product()
        prepare_product_variants(product)
        self.assertIsNone(product["shape_variants"][1]["price"])
        self.assertNotEqual(product["shape_variants"][1]["price"], 0)

    def test_missing_affiliate_url_is_empty_string(self):
        product = self._sample_product()
        prepare_product_variants(product)
        self.assertEqual(product["shape_variants"][1]["affiliate_url"], "")

    def test_duplicate_variant_ids_raise(self):
        product = self._sample_product()
        product["variants"][1]["id"] = "round"
        with self.assertRaises(ValueError):
            prepare_product_variants(product)

    def test_capacity_summary_differs(self):
        product = self._sample_product()
        prepare_product_variants(product)
        self.assertEqual(product["capacity_summary"], "Afhankelijk van uitvoering")

    def test_capacity_summary_equal_variants(self):
        product = self._sample_product()
        product["variants"][1]["capacities"] = [700, 700, 1500]
        prepare_product_variants(product)
        self.assertEqual(product["capacity_summary"], "2 × 700 ml + 1,5 L")

    def test_product_without_variants_untouched(self):
        product = {"slug": "plain", "name": "Plain", "capacities": [800]}
        before = copy.deepcopy(product)
        prepare_product_variants(product)
        self.assertEqual(product, before)

    def test_color_swatch_variants_ignored(self):
        product = {
            "slug": "airfryer",
            "name": "Airfryer",
            "variants": [
                {"name": "Groen", "image": "g.jpg", "hex": "#0f0"},
                {"name": "Crème", "image": "c.jpg", "hex": "#eee"},
            ],
        }
        prepare_product_variants(product)
        self.assertNotIn("shape_variants", product)
        self.assertNotIn("default_variant", product)


class VariantPageTests(TestCase):
    def test_category_page_renders_selector_once(self):
        response = self.client.get("/vershoudcontainers/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertEqual(html.count("data-shape-card"), 1)
        self.assertIn('aria-pressed="true"', html)
        self.assertIn(">Rond</button>", html)
        self.assertIn(">Vierkant</button>", html)
        self.assertIn("Geselecteerd: Rond", html)

    def test_igluu_is_one_row_in_comparison_table(self):
        import re

        response = self.client.get("/vershoudcontainers/")
        html = response.content.decode()
        table = re.search(r"<tbody>(.*?)</tbody>", html, re.S).group(1)
        self.assertEqual(table.count("Igluu Meal Prep"), 1)
        self.assertIn("Afhankelijk van uitvoering", table)

    def test_structured_data_uses_default_variant_offer(self):
        import re

        response = self.client.get("/vershoudcontainers/")
        html = response.content.decode()
        blocks = re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S
        )
        itemlist = next(
            json.loads(b) for b in blocks if '"ItemList"' in b
        )
        igluu = [
            e["item"]
            for e in itemlist["itemListElement"]
            if "Igluu" in e["item"]["name"]
        ]
        self.assertEqual(len(igluu), 1)  # one Product entity, not one per shape
        offer = igluu[0]["offers"]
        self.assertEqual(offer["url"], "https://www.amazon.nl/dp/B08DYF9GXP/?th=1")
        self.assertEqual(offer["price"], 24.95)
        self.assertEqual(offer["availability"], "https://schema.org/InStock")

    def test_igluu_detail_page_uses_default_variant(self):
        response = self.client.get("/product/igluu-meal-prep-3delig/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("400 ml + 650 ml + 950 ml", html)
        self.assertIn("2 L", html)  # total 2000 ml

    def test_products_without_variants_render_normally(self):
        response = self.client.get("/product/pyrex-cook-store-enkel/")
        self.assertEqual(response.status_code, 200)
