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
        response = self.client.get("/vershoudcontainers/?uitvoering=3-delig")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertEqual(html.count("data-shape-card"), 2)
        self.assertIn('aria-pressed="true"', html)
        self.assertIn(">Rond</button>", html)
        self.assertIn(">Vierkant</button>", html)
        self.assertIn("Geselecteerd: Rond", html)

    def test_igluu_is_one_row_in_comparison_table(self):
        import re

        response = self.client.get("/vershoudcontainers/?uitvoering=3-delig")
        html = response.content.decode()
        table = re.search(r"<tbody>(.*?)</tbody>", html, re.S).group(1)
        self.assertEqual(table.count("Igluu Meal Prep"), 1)
        self.assertIn("Afhankelijk van uitvoering", table)

    def test_structured_data_uses_default_variant_offer(self):
        import re

        response = self.client.get("/vershoudcontainers/?uitvoering=3-delig")
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

class StorageTypeSelectorTests(TestCase):
    def test_selector_shows_three_options(self):
        response = self.client.get("/vershoudcontainers/")
        html = response.content.decode()
        self.assertEqual(html.count("data-storage-type-selector"), 1)
        self.assertIn("Enkel", html)
        self.assertIn("3-delig", html)
        self.assertIn("5-delig", html)
        self.assertIn('?uitvoering=enkel', html)
        self.assertIn('?uitvoering=3-delig', html)
        self.assertIn('?uitvoering=5-delig', html)

    def test_default_selection_is_single(self):
        response = self.client.get("/vershoudcontainers/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Beste losse glazen vershoudbakjes", html)
        self.assertIn("Pyrex Cook &amp; Store", html)
        self.assertNotIn("Mepal EasyClip Glas – 3-delige", html)

    def test_each_uitvoering_selects_correct_group(self):
        cases = {
            "enkel": ("Beste losse glazen vershoudbakjes", "Ikea 365+"),
            "3-delig": ("Beste 3-delige glazen vershoudsets", "Glasslock"),
            "5-delig": ("Beste 5-delige glazen vershoudsets", "KitchenBrothers"),
        }
        for slug, (heading, product) in cases.items():
            response = self.client.get(f"/vershoudcontainers/?uitvoering={slug}")
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertIn(heading, html)
            self.assertIn(product, html)
            self.assertIn('aria-current="page"', html)

    def test_invalid_value_falls_back_to_single(self):
        for bad in ("bogus", "", "999", "<script>"):
            response = self.client.get("/vershoudcontainers/", {"uitvoering": bad})
            self.assertEqual(response.status_code, 200)
            self.assertIn("Beste losse glazen vershoudbakjes", response.content.decode())

    def test_only_selected_group_products_shown(self):
        response = self.client.get("/vershoudcontainers/?uitvoering=5-delig")
        html = response.content.decode()
        self.assertIn("Pyrex Cook &amp; Heat – 5-delige", html)
        self.assertNotIn("enkele schaal", html)
        self.assertNotIn("Mepal EasyClip Glas \u2013 3-delige set", html)

    def test_comparison_table_total_column_for_sets_only(self):
        single = self.client.get("/vershoudcontainers/?uitvoering=enkel").content.decode()
        sets = self.client.get("/vershoudcontainers/?uitvoering=5-delig").content.decode()
        self.assertNotIn("<th>Totale inhoud</th>", single)
        self.assertIn("<th>Totale inhoud</th>", sets)

    def test_itemlist_ld_matches_selected_group(self):
        import re
        response = self.client.get("/vershoudcontainers/?uitvoering=5-delig")
        html = response.content.decode()
        blocks = re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S
        )
        itemlist = next(json.loads(b) for b in blocks if '"ItemList"' in b)
        names = [e["item"]["name"] for e in itemlist["itemListElement"]]
        self.assertEqual(len(names), 5)
        self.assertTrue(all("5-delige" in n or "6-delig" in n or "5 " in n or "set" in n.lower() for n in names))
        positions = [e["position"] for e in itemlist["itemListElement"]]
        self.assertEqual(positions, list(range(1, len(names) + 1)))

    def test_faq_ld_present(self):
        import re
        response = self.client.get("/vershoudcontainers/?uitvoering=enkel")
        html = response.content.decode()
        blocks = re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S
        )
        faq = next(json.loads(b) for b in blocks if '"FAQPage"' in b)
        self.assertGreater(len(faq["mainEntity"]), 0)
        self.assertIn("Veelgestelde vragen", html)

    def test_no_none_rendered(self):
        for slug in ("enkel", "3-delig", "5-delig"):
            html = self.client.get(f"/vershoudcontainers/?uitvoering={slug}").content.decode()
            self.assertNotIn(">None<", html)
            self.assertNotIn(">0 ml<", html)

    def test_single_capacity_formatting(self):
        html = self.client.get("/vershoudcontainers/?uitvoering=enkel").content.decode()
        self.assertIn("800 ml", html)

    def test_shape_variant_selector_still_works_alongside_page_selector(self):
        html = self.client.get("/vershoudcontainers/?uitvoering=3-delig").content.decode()
        self.assertEqual(html.count("data-storage-type-selector"), 1)
        self.assertIn("data-shape-option", html)
        self.assertIn(">Rond</button>", html)
        self.assertIn(">Vierkant</button>", html)

    def test_award_validation_rejects_duplicates(self):
        from .views import _ALLOWED_VERSHOUDBAKJES_AWARDS
        self.assertEqual(len(_ALLOWED_VERSHOUDBAKJES_AWARDS), 3)

    def test_other_category_pages_unchanged(self):
        for url in ("/koekenpannen/", "/snijplanken/", "/airfryers/"):
            self.assertEqual(self.client.get(url).status_code, 200)


class StorageSizeClassificationTests(TestCase):
    """Unit tests for the formaat classification helpers."""

    def test_small_boundary(self):
        from utils.product_helpers import classify_storage_size
        self.assertEqual(classify_storage_size([600]), "small")
        self.assertEqual(classify_storage_size([601]), "medium")

    def test_medium_boundary(self):
        from utils.product_helpers import classify_storage_size
        self.assertEqual(classify_storage_size([1200]), "medium")
        self.assertEqual(classify_storage_size([1201]), "large")

    def test_uses_largest_not_total(self):
        from utils.product_helpers import classify_storage_size
        # total 2000 ml but largest 400 ml -> small
        self.assertEqual(classify_storage_size([400, 400, 400, 400, 400]), "small")
        # total 2600 ml, largest 1500 ml -> large
        self.assertEqual(classify_storage_size([400, 700, 1500]), "large")

    def test_single_value(self):
        from utils.product_helpers import classify_storage_size
        self.assertEqual(classify_storage_size([800]), "medium")

    def test_invalid_capacities(self):
        from utils.product_helpers import classify_storage_size
        self.assertIsNone(classify_storage_size([]))
        self.assertIsNone(classify_storage_size(None))
        self.assertIsNone(classify_storage_size(["800 ml"]))
        self.assertIsNone(classify_storage_size([0, -5]))

    def test_family_multiple_categories(self):
        from utils.product_helpers import get_product_size_categories
        product = {
            "shape_variants": [
                {"capacities": [450]},
                {"capacities": [1000]},
                {"capacities": [1800]},
            ]
        }
        self.assertEqual(get_product_size_categories(product), ["small", "medium", "large"])

    def test_family_skips_invalid_variants(self):
        from utils.product_helpers import get_product_size_categories
        product = {"shape_variants": [{"capacities": []}, {"capacities": [700]}]}
        self.assertEqual(get_product_size_categories(product), ["medium"])

    def test_falls_back_to_product_level(self):
        from utils.product_helpers import get_product_size_categories
        self.assertEqual(get_product_size_categories({"capacities": [500]}), ["small"])
        self.assertEqual(get_product_size_categories({"capacity": 1500}), ["large"])
        self.assertEqual(get_product_size_categories({}), [])

    def test_filter_preserves_order_and_all(self):
        from utils.product_helpers import filter_products_by_storage_size
        products = [
            {"slug": "a", "size_categories": ["small"]},
            {"slug": "b", "size_categories": []},
            {"slug": "c", "size_categories": ["small", "large"]},
        ]
        self.assertEqual([p["slug"] for p in filter_products_by_storage_size(products, "all")], ["a", "b", "c"])
        self.assertEqual([p["slug"] for p in filter_products_by_storage_size(products, "small")], ["a", "c"])
        self.assertEqual([p["slug"] for p in filter_products_by_storage_size(products, "large")], ["c"])
        # unclassified product only under "all"
        self.assertNotIn("b", [p["slug"] for p in filter_products_by_storage_size(products, "small")])


class StorageSizeFilterPageTests(TestCase):
    """Integration tests for the ?formaat= page filter."""

    def _get(self, query):
        return self.client.get(f"/vershoudcontainers/?{query}")

    def test_alle_shows_all_products_of_type(self):
        html = self._get("uitvoering=enkel&formaat=alle").content.decode()
        self.assertIn("6 producten gevonden", html)

    def test_size_filter_reduces_products(self):
        html = self._get("uitvoering=enkel&formaat=klein").content.decode()
        self.assertIn("3 producten gevonden", html)

    def test_invalid_formaat_falls_back_to_alle(self):
        full = self._get("uitvoering=enkel&formaat=alle").content.decode()
        invalid = self._get("uitvoering=enkel&formaat=onzin").content.decode()
        self.assertIn("6 producten gevonden", invalid)
        self.assertEqual(full.count("product-block"), invalid.count("product-block"))

    def test_invalid_uitvoering_falls_back_to_enkel(self):
        response = self._get("uitvoering=nonsens&formaat=klein")
        self.assertEqual(response.status_code, 200)
        self.assertIn("losse", response.content.decode().lower())

    def test_both_params_preserved_in_links(self):
        html = self._get("uitvoering=3-delig&formaat=groot").content.decode()
        self.assertIn("?uitvoering=5-delig&amp;formaat=groot", html)
        self.assertIn("?uitvoering=3-delig&amp;formaat=middel", html)

    def test_empty_result_shows_message_and_reset_link(self):
        html = self._get("uitvoering=enkel&formaat=groot").content.decode()
        self.assertIn("Binnen deze combinatie zijn momenteel geen producten beschikbaar", html)
        self.assertIn("?uitvoering=enkel&amp;formaat=alle", html)
        self.assertNotIn("<table", html)

    def test_ranking_order_preserved(self):
        import re
        full = self._get("uitvoering=enkel&formaat=alle").content.decode()
        filtered = self._get("uitvoering=enkel&formaat=middel").content.decode()

        def slugs(html):
            return re.findall(r'href="/product/([^"]+)/"', html)

        full_order = []
        for s in slugs(full):
            if s not in full_order:
                full_order.append(s)
        filtered_order = []
        for s in slugs(filtered):
            if s not in filtered_order:
                filtered_order.append(s)
        # filtered order must be a subsequence of the full ranking order
        it = iter(full_order)
        self.assertTrue(all(s in it for s in filtered_order))

    def test_itemlist_ld_only_visible_products_positions_from_1(self):
        import re
        html = self._get("uitvoering=enkel&formaat=klein").content.decode()
        blocks = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S)
        itemlist = next(json.loads(b) for b in blocks if '"ItemList"' in b)
        elements = itemlist["itemListElement"]
        self.assertEqual(len(elements), 3)
        self.assertEqual([e["position"] for e in elements], [1, 2, 3])

    def test_comparison_table_only_visible_products(self):
        html = self._get("uitvoering=enkel&formaat=klein").content.decode()
        self.assertEqual(html.count("<tr>"), 4)  # 1 header row + 3 visible products

    def test_selector_and_filter_render_with_aria_current(self):
        html = self._get("uitvoering=enkel&formaat=klein").content.decode()
        self.assertIn("data-storage-size-filter", html)
        self.assertIn("Filter op formaat", html)
        self.assertGreaterEqual(html.count('aria-current="page"'), 2)

    def test_shape_variant_selector_still_renders_with_filter(self):
        html = self._get("uitvoering=3-delig&formaat=middel").content.decode()
        self.assertIn("data-shape-card", html)
        self.assertIn("data-shape-option", html)

    def test_default_variant_used_at_alle(self):
        from products.views import prepare_storage_product
        variants = [
            {"id": "s", "capacities": [450], "image": "s.jpg"},
            {"id": "l", "capacities": [1800], "image": "l.jpg"},
        ]
        product = {"shape_variants": variants, "default_variant": variants[0]}
        prepare_storage_product(product, "all")
        self.assertEqual(product["default_variant"]["id"], "s")

    def test_matching_variant_selected_under_active_filter(self):
        from products.views import prepare_storage_product
        variants = [
            {"id": "s", "capacities": [450], "image": "s.jpg"},
            {"id": "l", "capacities": [1800], "image": "l.jpg", "affiliate_url": "https://x"},
        ]
        product = {"shape_variants": variants, "default_variant": variants[0]}
        prepare_storage_product(product, "large")
        self.assertEqual(product["default_variant"]["id"], "l")
        self.assertEqual(product["image"], "l.jpg")
        self.assertEqual(product["affiliate_url"], "https://x")

    def test_default_kept_when_it_matches_filter(self):
        from products.views import prepare_storage_product
        variants = [
            {"id": "m1", "capacities": [700]},
            {"id": "m2", "capacities": [900]},
        ]
        product = {"shape_variants": variants, "default_variant": variants[1]}
        prepare_storage_product(product, "medium")
        self.assertEqual(product["default_variant"]["id"], "m2")

    def test_no_size_classification_without_capacity(self):
        from products.views import prepare_storage_product
        product = {"slug": "x", "capacity": "800 ml tekst"}
        prepare_storage_product(product, "all")
        self.assertEqual(product["size_categories"], [])
        self.assertEqual(product["size_label"], "")

    def test_formatted_capacity_recomputed_after_variant_swap(self):
        from products.views import prepare_storage_product
        variants = [
            {"id": "s", "capacities": [450]},
            {"id": "l", "capacities": [1500, 1800]},
        ]
        product = {
            "shape_variants": variants,
            "default_variant": variants[0],
            "capacities": [450],
            "formatted_capacity": "450 ml",
            "formatted_total_capacity": "",
        }
        prepare_storage_product(product, "large")
        self.assertEqual(product["default_variant"]["id"], "l")
        self.assertEqual(product["formatted_capacity"], "1,5 L + 1,8 L")
        self.assertEqual(product["formatted_total_capacity"], "3,3 L")
        self.assertEqual(product["size_label"], "Groot")


class LockNLockCapacityVariantTests(TestCase):
    """Inhoudselector (630 ml / 740 ml / 1 L) op het Lock&Lock-productblok."""

    def _get_html(self, url="/vershoudcontainers/"):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def _product(self):
        from products.products_vershoudcontainers import PRODUCTS as VERSHOUDCONTAINERS_PRODUCTS
        import copy as _copy
        product = _copy.deepcopy(VERSHOUDCONTAINERS_PRODUCTS["locknlock_enkel"])
        prepare_product_variants(product)
        return product

    def test_one_ranked_product(self):
        from products.rankings_vershoudcontainers import RANKINGS as VERSHOUDCONTAINERS_RANKINGS
        self.assertEqual(
            VERSHOUDCONTAINERS_RANKINGS["single"].count("locknlock_enkel"), 1
        )

    def test_card_shows_three_capacity_options_with_exact_labels(self):
        html = self._get_html()
        self.assertIn(">630 ml</button>", html)
        self.assertIn(">740 ml</button>", html)
        self.assertIn(">1 L</button>", html)
        self.assertIn("Inhoud", html)

    def test_variant_ids_unique_and_one_default(self):
        product = self._product()
        ids = [v["id"] for v in product["shape_variants"]]
        self.assertEqual(len(ids), len(set(ids)))
        defaults = [v for v in product["shape_variants"] if v.get("is_default")]
        self.assertEqual(len(defaults), 1)
        self.assertEqual(defaults[0]["id"], "740-ml")

    def test_default_variant_commercial_data_copied_to_product(self):
        product = self._product()
        self.assertEqual(product["capacities"], [740])
        self.assertEqual(product["price"], 12.95)
        self.assertIn("740-ml", product["affiliate_url"])
        self.assertEqual(product["image"], "locknlock-enkel.jpg")

    def test_capacity_formatting(self):
        product = self._product()
        v630, v740, v1000 = product["shape_variants"]
        self.assertEqual(v630["formatted_capacity"], "630 ml")
        self.assertEqual(v740["formatted_capacity"], "740 ml")
        self.assertEqual(v1000["formatted_capacity"], "1 L")

    def test_selected_summary_no_duplicate_capacity(self):
        product = self._product()
        v740 = product["shape_variants"][1]
        self.assertEqual(v740["selected_summary"], "Geselecteerd: 740 ml")

    def test_all_variants_classified_medium(self):
        from utils.product_helpers import classify_storage_size, get_product_size_categories
        product = self._product()
        for v in product["shape_variants"]:
            self.assertEqual(classify_storage_size(v["capacities"]), "medium")
        self.assertEqual(get_product_size_categories(product), ["medium"])

    def test_visible_under_alle_and_middel_not_klein_groot(self):
        for formaat, expected in (
            ("alle", True), ("middel", True), ("klein", False), ("groot", False)
        ):
            html = self._get_html(f"/vershoudcontainers/?formaat={formaat}")
            self.assertEqual(
                "locknlock-enkel" in html, expected,
                f"formaat={formaat}",
            )

    def test_missing_variant_data_not_rendered_as_zero_or_none(self):
        product = self._product()
        v630 = product["shape_variants"][0]
        self.assertIsNone(v630["price"])
        self.assertEqual(v630["affiliate_url"], "")
        self.assertEqual(v630["image_url"], "")
        html = self._get_html()
        self.assertNotIn("€0", html)
        self.assertNotIn(">None<", html)

    def test_missing_affiliate_does_not_fall_back_to_other_variant(self):
        html = self._get_html()
        import re
        card = re.search(
            r'data-product-slug="locknlock-enkel".*?</div>\s*</div>', html, re.S
        ).group(0)
        buttons = re.findall(r'<button[^>]*data-shape-option[^>]*>', card)
        self.assertEqual(len(buttons), 3)
        for b in buttons:
            if 'data-variant-id="630-ml"' in b or 'data-variant-id="1000-ml"' in b:
                self.assertIn('data-affiliate=""', b)

    def test_default_renders_serverside_without_js(self):
        html = self._get_html()
        self.assertIn("Geselecteerd: 740 ml", html)
        self.assertIn('aria-pressed="true"', html)

    def test_one_row_in_comparison_table(self):
        import re
        html = self._get_html()
        table = re.search(r"<tbody>(.*?)</tbody>", html, re.S).group(1)
        self.assertEqual(table.count("Lock&amp;Lock"), 1)
        self.assertIn("Afhankelijk van uitvoering", table)

    def test_itemlist_ld_contains_locknlock_once_with_default_offer(self):
        import re
        html = self._get_html()
        blocks = re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S
        )
        itemlist = next(json.loads(b) for b in blocks if '"ItemList"' in b)
        entries = [
            e["item"] for e in itemlist["itemListElement"]
            if "Lock&Lock" in e["item"]["name"]
        ]
        self.assertEqual(len(entries), 1)
        offer = entries[0]["offers"]
        self.assertEqual(offer["price"], 12.95)
        self.assertIn("740-ml", offer["url"])
        positions = [e["position"] for e in itemlist["itemListElement"]]
        self.assertEqual(len(positions), len(set(positions)))

    def test_detail_page_uses_default_variant(self):
        response = self.client.get("/product/locknlock-enkel/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("740 ml", html)

    def test_other_selectors_unaffected(self):
        html = self._get_html("/vershoudcontainers/?uitvoering=3-delig")
        self.assertIn(">Rond</button>", html)
        self.assertIn(">Vierkant</button>", html)
        html = self._get_html()
        self.assertEqual(html.count("data-storage-type-selector"), 1)
        self.assertEqual(html.count("data-storage-size-filter"), 1)
