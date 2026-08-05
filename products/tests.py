import copy
import json
import re

from django.test import SimpleTestCase, TestCase

from utils.variant_helpers import (
    prepare_product_variants,
    resolve_commercial_fields,
    resolve_product_link,
    set_display_variant,
)
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
        self.assertEqual(table.count("<strong>Igluu Meal Prep"), 1)
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
        # Beleid: affiliate_url → retailer_url als fallback. Igluu heeft
        # retailer_url (amazon.nl), dus krijgt wél een Offer.
        self.assertIn("offers", igluu[0])
        self.assertEqual(igluu[0]["offers"]["@type"], "Offer")
        self.assertIn("amazon.nl", igluu[0]["offers"]["url"])

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
        self.assertNotIn(">Totale inhoud</th>", single)
        self.assertIn(">Totale inhoud</th>", sets)

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
        self.assertIn("data-variant-option", html)
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
        self.assertRegex(html, r"6\s+producten\s+gevonden")

    def test_size_filter_reduces_products(self):
        html = self._get("uitvoering=enkel&formaat=klein").content.decode()
        self.assertRegex(html, r"4\s+producten\s+gevonden")

    def test_invalid_formaat_falls_back_to_alle(self):
        full = self._get("uitvoering=enkel&formaat=alle").content.decode()
        invalid = self._get("uitvoering=enkel&formaat=onzin").content.decode()
        self.assertRegex(invalid, r"6\s+producten\s+gevonden")
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
        html = self._get("uitvoering=3-delig&formaat=klein").content.decode()
        self.assertIn("Binnen deze combinatie zijn momenteel geen producten beschikbaar", html)
        self.assertIn("?uitvoering=3-delig&amp;formaat=alle", html)
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
        self.assertEqual(len(elements), 4)
        self.assertEqual([e["position"] for e in elements], [1, 2, 3, 4])

    def test_comparison_table_only_visible_products(self):
        html = self._get("uitvoering=enkel&formaat=klein").content.decode()
        self.assertEqual(html.count("<tr>"), 5)  # 1 header row + 4 visible products

    def test_selector_and_filter_render_with_aria_current(self):
        html = self._get("uitvoering=enkel&formaat=klein").content.decode()
        self.assertIn("data-storage-size-filter", html)
        self.assertIn("Filter op formaat", html)
        self.assertGreaterEqual(html.count('aria-current="page"'), 2)

    def test_shape_variant_selector_still_renders_with_filter(self):
        html = self._get("uitvoering=3-delig&formaat=middel").content.decode()
        self.assertIn("data-shape-card", html)
        self.assertIn("data-variant-option", html)

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


class DisplayVariantHardeningTests(TestCase):
    """Variantafhankelijke velden worden bij iedere variantselectie
    expliciet gezet of gewist — nooit stil een waarde van een eerdere
    variant behouden."""

    def _make_product(self):
        return {
            "slug": "hardening-test",
            "name": "Hardening Test",
            "image": "family.webp",
            "image_path": "images/vershoudbakjes",
            "affiliate_url": "https://example.com/family",
            "price": 1.0,
            "currency": "EUR",
            "availability": "InStock",
            "price_last_checked": "2026-07-01",
            "variant_label": "Inhoud",
            "variants": [
                {
                    "id": "a",
                    "label": "500 ml",
                    "capacities": [500],
                    "image": "a.webp",
                    "price": 9.99,
                    "currency": "EUR",
                    "availability": "InStock",
                    "affiliate_url": "https://example.com/a",
                    "price_last_checked": "2026-07-10",
                    "usage": {"oven": {"container": True}},
                    "is_default": True,
                },
                {
                    "id": "b",
                    "label": "1 L",
                    "capacities": [1000],
                    # géén commerciële data, geen afbeelding, geen usage
                },
            ],
        }

    def _prepared(self):
        product = self._make_product()
        prepare_product_variants(product)
        return product

    def _variant(self, product, vid):
        return next(v for v in product["shape_variants"] if v["id"] == vid)

    def test_variant_without_url_never_inherits_url(self):
        from utils.variant_helpers import set_display_variant
        product = self._prepared()
        set_display_variant(product, self._variant(product, "b"))
        self.assertEqual(product["affiliate_url"], "")

    def test_variant_without_price_never_inherits_price(self):
        from utils.variant_helpers import set_display_variant
        product = self._prepared()
        set_display_variant(product, self._variant(product, "b"))
        self.assertIsNone(product["price"])
        self.assertIsNone(product["currency"])
        self.assertIsNone(product["price_last_checked"])

    def test_variant_without_availability_never_inherits_availability(self):
        from utils.variant_helpers import set_display_variant
        product = self._prepared()
        set_display_variant(product, self._variant(product, "b"))
        self.assertEqual(product["availability"], "")

    def test_variant_with_unknown_usage_clears_previous_usage(self):
        from utils.variant_helpers import set_display_variant
        product = self._prepared()
        self.assertTrue(product["usage_display"])  # variant A heeft usage
        set_display_variant(product, self._variant(product, "b"))
        self.assertEqual(product["usage_display"], [])

    def test_variant_images_selected_correctly_with_family_fallback(self):
        from utils.variant_helpers import set_display_variant
        product = self._prepared()
        self.assertEqual(product["image"], "a.webp")
        set_display_variant(product, self._variant(product, "b"))
        # variant B heeft geen eigen afbeelding → expliciete familie-fallback
        self.assertEqual(product["image"], "family.webp")
        set_display_variant(product, self._variant(product, "a"))
        self.assertEqual(product["image"], "a.webp")

    def test_prepared_products_do_not_affect_each_other(self):
        import copy as _copy
        from utils.variant_helpers import set_display_variant
        p1 = self._make_product()
        p2 = _copy.deepcopy(p1)
        prepare_product_variants(p1)
        prepare_product_variants(p2)
        set_display_variant(p1, self._variant(p1, "b"))
        self.assertEqual(p2["affiliate_url"], "https://example.com/a")
        self.assertEqual(p2["default_variant"]["id"], "a")

    def test_source_products_not_mutated_by_page_view(self):
        import copy as _copy
        from products.products_vershoudcontainers import PRODUCTS
        before = _copy.deepcopy(PRODUCTS)
        for query in ("", "?uitvoering=enkel&formaat=groot", "?uitvoering=3-delig"):
            self.client.get(f"/vershoudcontainers/{query}")
        self.assertEqual(PRODUCTS, before)

    def test_source_products_not_mutated_by_detail_page(self):
        import copy as _copy
        from products.products_vershoudcontainers import PRODUCTS
        before = _copy.deepcopy(PRODUCTS)
        self.client.get("/product/igluu-meal-prep-3delig/")
        self.client.get("/product/locknlock-enkel/")
        self.assertEqual(PRODUCTS, before)

    def test_product_without_variants_keeps_product_level_fields(self):
        product = {
            "slug": "plain",
            "name": "Plain",
            "affiliate_url": "https://example.com/p",
            "price": 4.5,
            "currency": "EUR",
            "availability": "InStock",
        }
        prepare_product_variants(product)
        self.assertEqual(product["affiliate_url"], "https://example.com/p")
        self.assertEqual(product["price"], 4.5)

    def test_offer_ld_omitted_without_price_or_url(self):
        from products.views import _build_offer_ld
        base = {
            "affiliate_url": "https://example.com/x",
            "price": 9.99,
            "currency": "EUR",
            "availability": "InStock",
        }
        self.assertIsNotNone(_build_offer_ld(base))

        # Zonder URL (affiliate én retailer leeg/afwezig) → geen Offer.
        no_url = dict(base)
        no_url["affiliate_url"] = None
        self.assertIsNone(_build_offer_ld(no_url), "affiliate_url only, no retailer_url")

        # Zonder prijs → geen Offer.
        no_price = dict(base)
        no_price["price"] = None
        self.assertIsNone(_build_offer_ld(no_price), "price")

        # currency is optioneel: ontbrekend → valt terug op EUR, Offer wordt wél aangemaakt.
        no_currency = dict(base)
        no_currency["currency"] = None
        offer = _build_offer_ld(no_currency)
        self.assertIsNotNone(offer, "currency defaults to EUR")
        self.assertEqual(offer["priceCurrency"], "EUR")

        # availability is optioneel: ontbrekend of onbekend → Offer zonder availability-veld.
        no_avail = dict(base)
        no_avail["availability"] = None
        offer_no_avail = _build_offer_ld(no_avail)
        self.assertIsNotNone(offer_no_avail, "availability is optional")
        self.assertNotIn("availability", offer_no_avail)

        # retailer_url als enige URL → Offer wordt wél aangemaakt.
        retailer_only = {
            "affiliate_url": "",
            "retailer_url": "https://example.com/retailer",
            "price": 9.99,
        }
        offer_retailer = _build_offer_ld(retailer_only)
        self.assertIsNotNone(offer_retailer, "retailer_url fallback")
        self.assertEqual(offer_retailer["url"], "https://example.com/retailer")


class EditorialRatingDisplayTests(TestCase):
    """Zichtbaar 'Onze beoordeling: X,X/5' naast de sterren."""

    def test_product_card_shows_label_and_dutch_score(self):
        response = self.client.get("/koekenpannen/")
        html = response.content.decode()
        self.assertIn("Onze beoordeling:", html)
        self.assertRegex(html, r'class="rating-value">\s*\d,?\d?/5')

    def test_comparison_table_shows_label(self):
        for url in ("/vershoudcontainers/", "/airfryers/", "/snijplanken/"):
            html = self.client.get(url).content.decode()
            self.assertIn("editorial-rating--compact", html, url)
            self.assertIn("Onze beoordeling:", html, url)

    def test_no_double_label(self):
        html = self.client.get("/koekenpannen/").content.decode()
        self.assertNotIn("Onze beoordeling: Onze beoordeling:", html)

    def test_dutch_comma_and_unchanged_numeric_rating(self):
        import copy as _copy
        from products.products_koekenpannen import PRODUCTS
        from products.views import _enrich_products
        before = _copy.deepcopy(PRODUCTS)
        products = [_copy.deepcopy(p) for p in PRODUCTS.values()]
        _enrich_products(products)
        for p in products:
            if p.get("rating"):
                self.assertNotIn(".", p["rating_display"])
                self.assertEqual(
                    p["rating_display"], str(p["rating"]).replace(".", ",")
                )
                self.assertIsInstance(p["rating"], (int, float))
        self.assertEqual(PRODUCTS, before)

    def test_jsonld_rating_stays_numeric(self):
        import json as _json
        import re as _re
        html = self.client.get("/koekenpannen/").content.decode()
        for ld in _re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, _re.S
        ):
            data = _json.loads(ld)
            if data.get("@type") != "ItemList":
                continue
            for element in data.get("itemListElement", []):
                agg = element.get("item", {}).get("aggregateRating")
                if agg:
                    self.assertIsInstance(agg["ratingValue"], (int, float))

    def test_stars_hidden_for_screenreaders(self):
        html = self.client.get("/koekenpannen/").content.decode()
        self.assertNotIn('role="img"', html)

    def test_customer_review_counts_not_labeled(self):
        # Reviewaantallen (externe klantdata) staan alleen in JSON-LD; het
        # label hoort uitsluitend bij de redactionele score.
        html = self.client.get("/koekenpannen/").content.decode()
        label_count = html.count("Onze beoordeling:")
        self.assertGreater(label_count, 0)
        self.assertNotIn("Klantbeoordeling: Onze beoordeling", html)

    def test_no_rating_block_without_rating(self):
        from django.template.loader import render_to_string
        product = {
            "slug": "x", "name": "X", "brand": "Y", "features": [],
            "pros": [], "cons": [], "rating": None, "rating_class": "",
            "rating_display": "", "image": "", "image_path": "images",
        }
        html = render_to_string(
            "partials/product_block.html", {"product": product}
        )
        self.assertNotIn("Onze beoordeling:", html)


class PriceRangeHelperTests(SimpleTestCase):
    """Centrale prijsniveauhelper: price → price_range (utils/pricing.py)."""

    def test_none_gives_none(self):
        from utils.pricing import get_price_range
        self.assertIsNone(get_price_range(None, "koekenpannen"))

    def test_invalid_text_gives_none(self):
        from utils.pricing import get_price_range
        self.assertIsNone(get_price_range("nvt", "koekenpannen"))
        self.assertIsNone(get_price_range("€42,99", "koekenpannen"))

    def test_negative_gives_none(self):
        from utils.pricing import get_price_range
        self.assertIsNone(get_price_range(-1, "koekenpannen"))

    def test_boundaries(self):
        from utils.pricing import get_price_range
        cases = [
            (0, "€"), (24.99, "€"), (25.00, "€€"), (49.99, "€€"),
            (50.00, "€€€"), (89.99, "€€€"), (90.00, "€€€€"),
        ]
        for price, expected in cases:
            self.assertEqual(get_price_range(price, "koekenpannen"), expected, price)

    def test_numeric_string_decimal_float(self):
        from decimal import Decimal
        from utils.pricing import get_price_range
        self.assertEqual(get_price_range("42.99", "koekenpannen"), "€€")
        self.assertEqual(get_price_range(Decimal("42.99"), "koekenpannen"), "€€")
        self.assertEqual(get_price_range(42.99, "koekenpannen"), "€€")

    def test_unknown_category_gives_none(self):
        from utils.pricing import get_price_range
        self.assertIsNone(get_price_range(42.99, "airfryers"))

    def test_hapjespannen_boundaries(self):
        from utils.pricing import get_price_range
        cases = [
            (None, None), (0, "€"), (39.99, "€"), (40.00, "€€"),
            (69.99, "€€"), (70.00, "€€€"), (109.99, "€€€"),
            (110.00, "€€€€"), (250.00, "€€€€"),
        ]
        for price, expected in cases:
            self.assertEqual(
                get_price_range(price, "hapjespannen"), expected, price
            )

    def test_hapjespannen_decimal_boundary_precision(self):
        from decimal import Decimal
        from utils.pricing import get_price_range
        # 39.999 mag niet door floatafronding als €€ worden ingedeeld.
        self.assertEqual(get_price_range(Decimal("39.999"), "hapjespannen"), "€")
        self.assertEqual(get_price_range("39.999", "hapjespannen"), "€")
        self.assertEqual(get_price_range(Decimal("109.999"), "hapjespannen"), "€€€")

    def test_koekenpannen_thresholds_unchanged(self):
        from decimal import Decimal
        from utils.pricing import PRICE_RANGE_THRESHOLDS
        self.assertEqual(
            [u for u, _ in PRICE_RANGE_THRESHOLDS["koekenpannen"]],
            [Decimal("25"), Decimal("50"), Decimal("90"), None],
        )

    def test_unknown_category_no_silent_fallback_to_koekenpannen(self):
        from utils.pricing import get_price_range, has_price_range_config
        self.assertFalse(has_price_range_config("wokpannen"))
        # €45 zou bij koekenpangrenzen "€€" zijn; onbekend blijft None.
        self.assertIsNone(get_price_range(45, "wokpannen"))
        self.assertTrue(has_price_range_config("hapjespannen"))


class NonVariantPriceRangeTests(TestCase):
    """Producten zonder varianten: productniveauprijs → berekend niveau."""

    def test_computed_level_overrides_manual(self):
        from products.views import _enrich_products
        product = {
            "name": "Test", "rating": 4.0, "price": 42.99,
            "price_range": "€€€€",  # verouderd handmatig niveau
        }
        _enrich_products([product], category="koekenpannen")
        self.assertEqual(product["display_price_range"], "€€")
        # Handmatig veld blijft ongewijzigd in de data (backward compat).
        self.assertEqual(product["price_range"], "€€€€")

    def test_manual_level_only_used_without_price(self):
        from products.views import _enrich_products
        product = {"name": "Test", "rating": 4.0, "price_range": "€€"}
        _enrich_products([product], category="koekenpannen")
        self.assertEqual(product["display_price_range"], "€€")

    def test_source_data_not_mutated(self):
        from products.products_koekenpannen import PRODUCTS
        before = copy.deepcopy(PRODUCTS)
        self.client.get("/koekenpannen/")
        self.assertEqual(PRODUCTS, before)

    def test_no_concrete_price_in_public_html(self):
        from products.products_koekenpannen import PRODUCTS
        html = self.client.get("/koekenpannen/").content.decode()
        for p in PRODUCTS.values():
            for source in [p] + list(p.get("variants") or []):
                price = source.get("price")
                if price is None:
                    continue
                formatted = f"{price:.2f}"
                self.assertNotIn(f"€{formatted}", html)
                self.assertNotIn(f"€ {formatted}", html)
                self.assertNotIn(formatted.replace(".", ","), html)

    def test_no_new_offer_added_for_unknown_category_passthrough(self):
        # Andere categorie: display is passthrough van handmatig niveau.
        from products.views import _enrich_products
        product = {"name": "Test", "rating": 4.0, "price": 42.99,
                   "price_range": "€€€"}
        _enrich_products([product], category="wokpannen")
        self.assertEqual(product["display_price_range"], "€€€")


class VariantPriceRangeTests(TestCase):
    """Variantproducten: strikt het niveau van de eigen variantprijs."""

    def _enriched(self, key):
        from products.products_koekenpannen import PRODUCTS
        from products.views import _enrich_products
        product = copy.deepcopy(PRODUCTS[key])
        _enrich_products([product], category="koekenpannen")
        return product

    def test_mayflower_variants(self):
        p = self._enriched("greenpan_mayflower_28")
        by_name = {v["name"]: v["display_price_range"] for v in p["variants"]}
        self.assertEqual(by_name["Blauw"], "€€")   # 42.99
        self.assertEqual(by_name["Grijs"], "€€€")  # 59.90
        # Kaartniveau = getoonde (eerste) swatch, niet handmatig "€€-€€€".
        self.assertEqual(p["display_price_range"],
                         p["variants"][0]["display_price_range"])

    def test_kochstar_variants(self):
        p = self._enriched("kochstar_essenz_24")
        for v in p["variants"]:
            self.assertEqual(v["display_price_range"], "€")

    def test_variant_without_price_gets_empty_level(self):
        from products.views import _enrich_products
        product = {
            "name": "Test", "rating": 4.0, "price_range": "€€",
            "variants": [
                {"name": "A", "price": 42.99},
                {"name": "B"},  # geen prijs: geen niveau, geen fallback
            ],
        }
        _enrich_products([product], category="koekenpannen")
        self.assertEqual(product["variants"][0]["display_price_range"], "€€")
        self.assertEqual(product["variants"][1]["display_price_range"], "")

    def test_swatch_data_price_always_emitted_when_derived(self):
        html = self.client.get("/koekenpannen/").content.decode()
        # Afgeleide niveaus als data-price op swatches (Mayflower).
        self.assertIn('data-price="€€€"', html)
        self.assertIn('data-price="€€"', html)
        # Geen productniveau-fallbackattribuut bij afgeleide niveaus.
        self.assertNotIn("data-base-price", html)

    def test_js_clears_and_never_falls_back_for_derived_levels(self):
        js = open("static/assets/js/variants.js", encoding="utf-8").read()
        self.assertIn('swatch.hasAttribute("data-price")', js)
        self.assertIn('priceEl.textContent = price || ""', js)
        self.assertIn("priceEl.hidden = !price", js)

    def test_cards_do_not_share_state(self):
        p1 = self._enriched("greenpan_mayflower_28")
        p2 = self._enriched("kochstar_essenz_24")
        self.assertNotEqual(p1["display_price_range"],
                            p2["display_price_range"])


class PriceRangeTemplateTests(TestCase):
    """Templates en JSON-LD tonen alleen prijsniveaus."""

    def test_comparison_table_uses_display_level(self):
        from products.products_koekenpannen import PRODUCTS
        from products.rankings_koekenpannen import RANKINGS
        from utils.pricing import get_price_range
        html = self.client.get("/koekenpannen/").content.decode()
        key = RANKINGS[28][0]
        p = PRODUCTS[key]
        source = (p.get("variants") or [p])[0]
        expected = get_price_range(source.get("price"), "koekenpannen")
        self.assertIn(f"<td>{expected}</td>", html)

    def test_vershoud_table_uses_row_level(self):
        html = self.client.get("/vershoudcontainers/").content.decode()
        self.assertIn("Prijsniveau", html)
        self.assertEqual(
            self.client.get("/vershoudcontainers/").status_code, 200)

    def test_price_range_never_in_jsonld_price_field(self):
        for url in ("/koekenpannen/", "/airfryers/", "/vershoudcontainers/"):
            html = self.client.get(url).content.decode()
            for ld in re.findall(
                r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
                html, re.S,
            ):
                data = json.loads(ld)
                text = json.dumps(data)
                self.assertNotIn('"price": "€', text)

    def test_jsonld_still_valid_and_no_new_offers(self):
        html = self.client.get("/koekenpannen/").content.decode()
        blocks = re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
            html, re.S,
        )
        self.assertTrue(blocks)
        for ld in blocks:
            json.loads(ld)  # geen exceptie: syntactisch geldig

    def test_all_category_pages_render(self):
        for url in ("/koekenpannen/", "/wokpannen/", "/hapjespannen/",
                    "/snijplanken/", "/airfryers/", "/rvs-koekenpannen/",
                    "/vershoudcontainers/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)


class VariantAuditCommandTests(TestCase):
    """Read-only auditcommand: python manage.py audit_product_variants."""

    def _run(self, *args):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("audit_product_variants", *args, stdout=out)
        return out.getvalue()

    def test_command_runs_without_errors(self):
        output = self._run()
        self.assertIn("Structurele fouten: 0", output)

    def test_command_reports_airfryer_swatch_category(self):
        # De eerder bekende inconsistent_jsonld_variant-melding is verdwenen
        # doordat de affiliate-URL's naar retailer_url zijn gemigreerd; de
        # audit moet de swatchcategorie nog steeds volledig rapporteren.
        output = self._run("--category", "airfryers")
        self.assertIn("Variantproducten (kleurswatches): 2", output)
        self.assertIn("greenpan_bistro_xxl_7_2l", output)

    def test_command_does_not_mutate_source_data(self):
        import copy as _copy
        from products.products_vershoudcontainers import PRODUCTS as P1
        from products.products_airfryers import PRODUCTS as P2
        before1, before2 = _copy.deepcopy(P1), _copy.deepcopy(P2)
        self._run()
        self.assertEqual(P1, before1)
        self.assertEqual(P2, before2)

    def test_strict_mode_fails_on_warnings(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            self._run("--strict")

    def test_no_unsafe_commercial_firstof_in_comparison_templates(self):
        output = self._run()
        self.assertNotIn("unsafe_template_firstof", output)


class ComparisonRowResolutionTests(TestCase):
    """Strikte resolutie van commerciële velden in comparison_rows."""

    def test_static_storage_filters_js_exists(self):
        from django.contrib.staticfiles import finders
        self.assertIsNotNone(finders.find("js/storage-filters.js"))

    def test_script_loaded_exactly_once(self):
        html = self.client.get("/vershoudcontainers/").content.decode()
        self.assertEqual(html.count("js/storage-filters.js"), 1)

    def test_resolver_product_without_variants_uses_product_level(self):
        from utils.variant_helpers import resolve_commercial_fields
        product = {
            "slug": "plain",
            "affiliate_url": "https://example.com/p",
            "price": 12.5,
            "availability": "InStock",
            "price_last_checked": "2026-07-01",
        }
        resolved = resolve_commercial_fields(product)
        self.assertEqual(resolved["affiliate_url"], "https://example.com/p")
        self.assertEqual(resolved["price"], 12.5)
        self.assertEqual(resolved["availability"], "InStock")

    def test_resolver_variant_product_uses_display_variant_only(self):
        from utils.variant_helpers import resolve_commercial_fields
        variant_a = {"id": "a", "affiliate_url": "https://example.com/a", "price": 5}
        variant_b = {"id": "b"}  # geen commerciële data
        product = {
            "slug": "fam",
            "affiliate_url": "https://example.com/stale-from-a",
            "price": 5,
            "shape_variants": [variant_a, variant_b],
            "default_variant": variant_a,
        }
        resolved = resolve_commercial_fields(product, variant_b)
        self.assertEqual(resolved["affiliate_url"], "")
        self.assertIsNone(resolved["price"])
        self.assertEqual(resolved["availability"], "")

    def test_rows_contain_explicit_fields(self):
        response = self.client.get("/vershoudcontainers/")
        rows = response.context["comparison_rows"]
        self.assertTrue(rows)
        for row in rows:
            for field in (
                "affiliate_url", "price", "availability",
                "rating", "rating_class", "display_variant_id",
            ):
                self.assertIn(field, row)

    def test_row_variant_matches_card_display_variant_under_size_filter(self):
        response = self.client.get("/vershoudcontainers/?uitvoering=enkel&formaat=groot")
        for row in response.context["comparison_rows"]:
            product = row["product"]
            if product.get("shape_variants"):
                self.assertEqual(
                    row["display_variant_id"],
                    product["default_variant"]["id"],
                )
                self.assertEqual(
                    row["affiliate_url"],
                    product["default_variant"].get("affiliate_url") or "",
                )

    def test_no_empty_href_rendered(self):
        for query in ("", "?uitvoering=enkel&formaat=klein", "?uitvoering=3-delig"):
            html = self.client.get(f"/vershoudcontainers/{query}").content.decode()
            self.assertNotIn('href=""', html)

    def test_rating_numeric_text_and_scope_preserved(self):
        html = self.client.get("/vershoudcontainers/").content.decode()
        self.assertIn('class="rating-value"', html)
        self.assertRegex(html, r"[0-9](?:\.[0-9])?/5")
        self.assertIn('<th scope="col">Product</th>', html)
        self.assertIn('<th scope="row">', html)


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
        self.assertEqual(defaults[0]["id"], "630-ml")

    def test_default_variant_commercial_data_copied_to_product(self):
        product = self._product()
        self.assertEqual(product["capacities"], [630])
        self.assertEqual(product["price"], 9.95)
        self.assertIn("630-ml", product["retailer_url"])
        self.assertEqual(product["affiliate_url"], "")
        self.assertEqual(product["image"], "locknlock-630ml-enkel.webp")

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

    def test_capacities_derived_from_options_capacity(self):
        product = {
            "slug": "test-derive",
            "name": "Test",
            "variant_selectors": [{"key": "capacity", "label": "Inhoud"}],
            "variants": [
                {
                    "id": "500-ml",
                    "options": {"capacity": 500},
                    "option_labels": {"capacity": "500 ml"},
                    "is_default": True,
                },
                {
                    "id": "1000-ml",
                    "options": {"capacity": 1000},
                    "option_labels": {"capacity": "1 L"},
                },
            ],
        }
        prepare_product_variants(product)
        caps = [v["capacities"] for v in product["shape_variants"]]
        self.assertEqual(caps, [[500], [1000]])
        self.assertEqual(
            [v["formatted_capacity"] for v in product["shape_variants"]],
            ["500 ml", "1 L"],
        )

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

    def test_no_zero_or_none_rendered(self):
        html = self._get_html()
        self.assertNotIn("€0", html)
        self.assertNotIn(">None<", html)

    def test_each_variant_keeps_own_link(self):
        product = self._product()
        urls = [v["resolved_link"].url for v in product["shape_variants"]]
        self.assertEqual(len(urls), len(set(urls)))
        json_data = product["variant_json_data"]
        self.assertEqual(
            [v["resolved_url"] for v in json_data["variants"]], urls
        )

    def test_default_renders_serverside_without_js(self):
        html = self._get_html()
        self.assertIn("Geselecteerd: 630 ml", html)
        self.assertIn('aria-pressed="true"', html)

    def test_one_row_in_comparison_table(self):
        import re
        html = self._get_html()
        table = re.search(r"<tbody>(.*?)</tbody>", html, re.S).group(1)
        self.assertEqual(table.count("<strong>Lock&amp;Lock"), 1)
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
        # Beleid: affiliate_url → retailer_url als fallback. Lock&Lock heeft
        # een retailer_url (locklock.nl), dus krijgt wél een Offer.
        self.assertIn("offers", entries[0])
        self.assertEqual(entries[0]["offers"]["@type"], "Offer")
        self.assertIn("locklock.nl", entries[0]["offers"]["url"])
        positions = [e["position"] for e in itemlist["itemListElement"]]
        self.assertEqual(len(positions), len(set(positions)))

    def test_detail_page_uses_default_variant(self):
        response = self.client.get("/product/locknlock-enkel/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("630 ml", html)

    def test_other_selectors_unaffected(self):
        html = self._get_html("/vershoudcontainers/?uitvoering=3-delig")
        self.assertIn(">Rond</button>", html)
        self.assertIn(">Vierkant</button>", html)
        html = self._get_html()
        self.assertEqual(html.count("data-storage-type-selector"), 1)
        self.assertEqual(html.count("data-storage-size-filter"), 1)


class MultiSelectorVariantTests(TestCase):
    """Generic multi-selector (Vorm + Inhoud) variant architecture."""

    def _dual_product(self):
        return {
            "slug": "dual-test",
            "name": "Dual Test",
            "image_path": "images/vershoudbakjes",
            "variant_selectors": [
                {"key": "shape", "label": "Vorm"},
                {"key": "capacity", "label": "Inhoud"},
            ],
            "variants": [
                {
                    "id": "round-630",
                    "options": {"shape": "round", "capacity": 630},
                    "option_labels": {"shape": "Rond", "capacity": "630 ml"},
                    "capacities": [630],
                    "image": "round-630.webp",
                    "price": 9.95,
                    "affiliate_url": "https://example.com/round-630",
                    "availability": "InStock",
                    "is_default": True,
                },
                {
                    "id": "round-750",
                    "options": {"shape": "round", "capacity": 750},
                    "option_labels": {"shape": "Rond", "capacity": "750 ml"},
                    "capacities": [750],
                    "image": "round-750.webp",
                    "price": 11.95,
                    "affiliate_url": "https://example.com/round-750",
                    "availability": "InStock",
                    "is_default": False,
                },
                {
                    "id": "rect-750",
                    "options": {"shape": "rectangular", "capacity": 750},
                    "option_labels": {"shape": "Rechthoekig", "capacity": "750 ml"},
                    "capacities": [750],
                    "image": "rect-750.webp",
                    "price": 12.95,
                    "affiliate_url": "https://example.com/rect-750",
                    "availability": "InStock",
                    "is_default": False,
                },
                {
                    "id": "rect-1500",
                    "options": {"shape": "rectangular", "capacity": 1500},
                    "option_labels": {"shape": "Rechthoekig", "capacity": "1,5 L"},
                    "capacities": [1500],
                    "image": "rect-1500.webp",
                    "price": None,
                    "affiliate_url": None,
                    "availability": None,
                    "is_default": False,
                },
            ],
        }

    def test_two_selectors_prepared(self):
        product = self._dual_product()
        prepare_product_variants(product)
        groups = product["variant_selector_groups"]
        self.assertEqual([g["key"] for g in groups], ["shape", "capacity"])
        self.assertEqual([g["label"] for g in groups], ["Vorm", "Inhoud"])
        self.assertTrue(all(g["show"] for g in groups))

    def test_capacity_options_numerically_sorted(self):
        product = self._dual_product()
        # deliberately shuffle
        product["variants"].reverse()
        prepare_product_variants(product)
        caps = [o["value"] for o in product["variant_selector_options"]["capacity"]]
        self.assertEqual(caps, [630, 750, 1500])

    def test_shape_options_keep_data_order(self):
        product = self._dual_product()
        prepare_product_variants(product)
        shapes = [o["value"] for o in product["variant_selector_options"]["shape"]]
        self.assertEqual(shapes, ["round", "rectangular"])

    def test_only_existing_combinations_available(self):
        product = self._dual_product()
        prepare_product_variants(product)
        shape_group, capacity_group = product["variant_selector_groups"]
        # default is round-630: for the capacity selector (later group), only
        # capacities that exist in the selected shape are shown; 1500 has no
        # round variant so it is hidden
        availability = {o["label"]: o["available"] for o in capacity_group["options"]}
        self.assertEqual(
            availability, {"630 ml": True, "750 ml": True, "1,5 L": False}
        )
        # the first (primary) selector always shows all its options so every
        # shape stays reachable
        shape_avail = {o["label"]: o["available"] for o in shape_group["options"]}
        self.assertEqual(shape_avail, {"Rond": True, "Rechthoekig": True})

    def test_exactly_one_active_option_per_selector(self):
        product = self._dual_product()
        prepare_product_variants(product)
        for group in product["variant_selector_groups"]:
            active = [o for o in group["options"] if o["active"]]
            self.assertEqual(len(active), 1)

    def test_default_variant_and_summary(self):
        product = self._dual_product()
        prepare_product_variants(product)
        self.assertEqual(product["default_variant"]["id"], "round-630")
        self.assertEqual(
            product["default_variant"]["selected_summary"],
            "Geselecteerd: Rond · 630 ml",
        )

    def test_duplicate_option_combination_raises(self):
        product = self._dual_product()
        product["variants"][1]["options"] = {"shape": "round", "capacity": 630}
        with self.assertRaises(ValueError):
            prepare_product_variants(product)

    def test_duplicate_ids_raise(self):
        product = self._dual_product()
        product["variants"][1]["id"] = "round-630"
        with self.assertRaises(ValueError):
            prepare_product_variants(product)

    def test_missing_option_value_raises(self):
        product = self._dual_product()
        del product["variants"][2]["options"]["capacity"]
        with self.assertRaises(ValueError):
            prepare_product_variants(product)

    def test_more_than_one_default_raises(self):
        product = self._dual_product()
        product["variants"][1]["is_default"] = True
        with self.assertRaises(ValueError):
            prepare_product_variants(product)

    def test_missing_commercial_data_is_safe(self):
        product = self._dual_product()
        prepare_product_variants(product)
        rect_1500 = product["shape_variants"][3]
        self.assertIsNone(rect_1500["price"])
        self.assertEqual(rect_1500["affiliate_url"], "")
        json_variant = product["variant_json_data"]["variants"][3]
        self.assertIsNone(json_variant["price"])
        self.assertEqual(json_variant["affiliate_url"], "")

    def test_variant_json_data_payload(self):
        product = self._dual_product()
        prepare_product_variants(product)
        data = product["variant_json_data"]
        self.assertEqual(data["default_id"], "round-630")
        self.assertEqual(len(data["variants"]), 4)
        self.assertEqual(
            [s["key"] for s in data["selectors"]], ["shape", "capacity"]
        )
        ids = [v["id"] for v in data["variants"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_set_display_variant_reinitialises_both_selectors(self):
        from utils.variant_helpers import set_display_variant

        product = self._dual_product()
        prepare_product_variants(product)
        rect_1500 = product["shape_variants"][3]
        set_display_variant(product, rect_1500)
        self.assertEqual(product["default_variant"]["id"], "rect-1500")
        self.assertEqual(product["variant_json_data"]["default_id"], "rect-1500")
        for group in product["variant_selector_groups"]:
            active = [o for o in group["options"] if o["active"]]
            self.assertEqual(len(active), 1)
        shape_group, capacity_group = product["variant_selector_groups"]
        self.assertEqual(
            [o["label"] for o in shape_group["options"] if o["active"]],
            ["Rechthoekig"],
        )
        self.assertEqual(
            [o["label"] for o in capacity_group["options"] if o["active"]],
            ["1,5 L"],
        )
        self.assertEqual(product["capacities"], [1500])
        self.assertEqual(product["matching_variant_id"], "rect-1500")

    def test_size_filter_large_opens_matching_variant(self):
        from products.views import prepare_storage_product

        product = self._dual_product()
        prepare_product_variants(product)
        prepare_storage_product(product, "large")
        self.assertEqual(product["default_variant"]["id"], "rect-1500")
        self.assertEqual(product["size_label"], "Groot")

    def test_size_filter_alle_keeps_normal_default(self):
        from products.views import prepare_storage_product

        product = self._dual_product()
        prepare_product_variants(product)
        prepare_storage_product(product, "all")
        self.assertEqual(product["default_variant"]["id"], "round-630")


class LegacyVariantNormalizationTests(TestCase):
    """Old ``variant_label`` products keep working via normalisation."""

    def test_legacy_capacity_label_becomes_capacity_selector(self):
        product = {
            "slug": "legacy-cap",
            "name": "Legacy Cap",
            "image_path": "images",
            "variant_label": "Inhoud",
            "variants": [
                {"id": "600-ml", "label": "600 ml", "capacities": [600],
                 "is_default": True},
                {"id": "1000-ml", "label": "1 L", "capacity_ml": 1000,
                 "capacities": [1000]},
            ],
        }
        prepare_product_variants(product)
        self.assertEqual(
            product["variant_selectors"], [{"key": "capacity", "label": "Inhoud"}]
        )
        v600, v1000 = product["shape_variants"]
        self.assertEqual(v600["options"], {"capacity": 600})
        self.assertEqual(v1000["options"], {"capacity": 1000})
        self.assertEqual(v1000["option_labels"], {"capacity": "1 L"})
        caps = [o["value"] for o in product["variant_selector_options"]["capacity"]]
        self.assertEqual(caps, [600, 1000])

    def test_legacy_shape_label_becomes_shape_selector(self):
        product = {
            "slug": "legacy-shape",
            "name": "Legacy Shape",
            "image_path": "images",
            "variant_label": "Vorm",
            "variants": [
                {"id": "round", "label": "Rond", "shape": "Rond",
                 "capacities": [400, 650], "is_default": True},
                {"id": "square", "label": "Vierkant", "shape": "Vierkant"},
            ],
        }
        prepare_product_variants(product)
        self.assertEqual(
            product["variant_selectors"], [{"key": "shape", "label": "Vorm"}]
        )
        self.assertEqual(
            product["shape_variants"][1]["options"], {"shape": "Vierkant"}
        )

    def test_existing_legacy_products_on_page_still_render(self):
        # Igluu (Vorm) and IKEA/Mepal (Inhoud) still use the legacy structure.
        response = self.client.get("/vershoudcontainers/?uitvoering=3-delig")
        html = response.content.decode()
        self.assertIn(">Rond</button>", html)
        self.assertIn(">Vierkant</button>", html)
        self.assertIn("Geselecteerd: Rond", html)
        response = self.client.get("/vershoudcontainers/")
        self.assertEqual(response.status_code, 200)

    def test_each_card_has_own_json_payload(self):
        html = self.client.get("/vershoudcontainers/").content.decode()
        self.assertIn('id="variant-data-locknlock-enkel"', html)
        self.assertIn('id="variant-data-mepal-easyclip-glass-enkel"', html)
        # ids unique
        import re
        ids = re.findall(r'id="(variant-data-[^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)))

    def test_lock_and_lock_shows_single_selector(self):
        html = self.client.get("/vershoudcontainers/").content.decode()
        import re
        card = re.search(
            r'data-product-slug="locknlock-enkel".*?<script', html, re.S
        ).group(0)
        self.assertEqual(card.count("data-product-variant-selector"), 1)
        self.assertIn(">630 ml</button>", card)
        self.assertIn(">740 ml</button>", card)
        self.assertIn(">1 L</button>", card)


class ProductLinkResolverTests(TestCase):
    """Tests voor de centrale linkresolver (affiliate → retailer →
    official → availability_label)."""

    def _variant_product(self, variant_extra):
        variant = {
            "id": "v1",
            "options": {"shape": "rond"},
            "option_labels": {"shape": "Rond"},
            "is_default": True,
        }
        variant.update(variant_extra)
        return {
            "slug": "test-product",
            "name": "Testproduct",
            "variant_selectors": [{"key": "shape", "label": "Vorm"}],
            "variants": [variant],
        }

    def test_affiliate_only_wins_with_sponsored_rel(self):
        link = resolve_product_link({"affiliate_url": "https://a.example/x"})
        self.assertEqual(link.link_type, "affiliate")
        self.assertEqual(link.url, "https://a.example/x")
        self.assertIn("sponsored", link.rel)
        self.assertIn("nofollow", link.rel)
        self.assertTrue(link.is_commercial)
        self.assertIn("prijs", link.label.lower())

    def test_retailer_only_no_sponsored(self):
        link = resolve_product_link({"retailer_url": "https://shop.example/x"})
        self.assertEqual(link.link_type, "retailer")
        self.assertNotIn("sponsored", link.rel)
        self.assertIn("nofollow", link.rel)
        self.assertTrue(link.is_commercial)

    def test_official_only_informative(self):
        link = resolve_product_link({"official_url": "https://brand.example/x"})
        self.assertEqual(link.link_type, "official")
        self.assertEqual(link.rel, "noopener")
        self.assertNotIn("sponsored", link.rel)
        self.assertIn("productspecificaties", link.label.lower())
        self.assertFalse(link.is_commercial)

    def test_priority_affiliate_beats_all(self):
        link = resolve_product_link({
            "affiliate_url": "https://a.example/x",
            "retailer_url": "https://shop.example/x",
            "official_url": "https://brand.example/x",
        })
        self.assertEqual(link.link_type, "affiliate")

    def test_priority_retailer_beats_official(self):
        link = resolve_product_link({
            "retailer_url": "https://shop.example/x",
            "official_url": "https://brand.example/x",
        })
        self.assertEqual(link.link_type, "retailer")

    def test_no_urls_returns_empty_link(self):
        link = resolve_product_link({})
        self.assertEqual(link.url, "")
        self.assertEqual(link.link_type, "none")
        link = resolve_product_link({
            "affiliate_url": None, "retailer_url": "", "official_url": "   ",
        })
        self.assertEqual(link.url, "")

    def test_selected_variant_own_affiliate_used(self):
        product = self._variant_product({"affiliate_url": "https://a.example/v1"})
        prepare_product_variants(product)
        link = resolve_product_link(product, product["default_variant"])
        self.assertEqual(link.url, "https://a.example/v1")
        self.assertEqual(link.link_type, "affiliate")

    def _two_variant_product(self, product_extra=None, v1_extra=None,
                             v2_extra=None):
        product = {
            "slug": "test-product",
            "name": "Testproduct",
            "variant_selectors": [{"key": "shape", "label": "Vorm"}],
            "variants": [
                {"id": "v1", "options": {"shape": "rond"},
                 "option_labels": {"shape": "Rond"}, "is_default": True,
                 **(v1_extra or {})},
                {"id": "v2", "options": {"shape": "vierkant"},
                 "option_labels": {"shape": "Vierkant"}, **(v2_extra or {})},
            ],
        }
        product.update(product_extra or {})
        prepare_product_variants(product)
        return product

    def test_variant_without_link_falls_back_to_family_affiliate(self):
        product = self._two_variant_product(
            product_extra={"affiliate_url": "https://a.example/family"},
            v1_extra={"affiliate_url": "https://a.example/v1"},
        )
        link = resolve_product_link(product, product["shape_variants"][1])
        self.assertEqual(link.url, "https://a.example/family")
        self.assertEqual(link.link_type, "affiliate")
        self.assertIn("sponsored", link.rel)

    def test_variant_without_link_falls_back_to_family_retailer(self):
        product = self._two_variant_product(
            product_extra={"retailer_url": "https://shop.example/family"},
            v1_extra={"affiliate_url": "https://a.example/v1"},
        )
        link = resolve_product_link(product, product["shape_variants"][1])
        self.assertEqual(link.url, "https://shop.example/family")
        self.assertEqual(link.link_type, "retailer")
        self.assertNotIn("sponsored", link.rel)

    def test_variant_without_link_falls_back_to_family_official(self):
        product = self._two_variant_product(
            product_extra={"official_url": "https://brand.example/family"},
        )
        link = resolve_product_link(product, product["shape_variants"][1])
        self.assertEqual(link.url, "https://brand.example/family")
        self.assertEqual(link.link_type, "official")
        self.assertEqual(link.rel, "noopener")

    def test_variant_own_retailer_beats_family_affiliate(self):
        """Eerst de volledige prioriteit binnen de variant zelf; pas
        daarna de familie-fallback."""
        product = self._two_variant_product(
            product_extra={"affiliate_url": "https://a.example/family"},
            v2_extra={"retailer_url": "https://shop.example/v2"},
        )
        link = resolve_product_link(product, product["shape_variants"][1])
        self.assertEqual(link.url, "https://shop.example/v2")
        self.assertEqual(link.link_type, "retailer")

    def test_variant_and_family_without_urls_gives_no_link(self):
        product = self._two_variant_product()
        link = resolve_product_link(product, product["shape_variants"][1])
        self.assertEqual(link.url, "")
        self.assertEqual(link.link_type, "none")

    def test_fallback_never_uses_other_variant_url(self):
        product = self._two_variant_product(
            v1_extra={"affiliate_url": "https://a.example/v1"},
        )
        link = resolve_product_link(product, product["shape_variants"][1])
        self.assertEqual(link.url, "")

    def test_family_fallback_ignores_empty_strings_and_none(self):
        product = self._two_variant_product(
            product_extra={
                "affiliate_url": None,
                "retailer_url": "  ",
                "official_url": "https://brand.example/family",
            },
        )
        link = resolve_product_link(product, product["shape_variants"][1])
        self.assertEqual(link.url, "https://brand.example/family")

    def test_variant_json_payload_uses_family_fallback(self):
        product = self._two_variant_product(
            product_extra={"retailer_url": "https://shop.example/family"},
            v1_extra={"affiliate_url": "https://a.example/v1"},
        )
        payloads = product["variant_json_data"]["variants"]
        self.assertEqual(payloads[0]["resolved_url"], "https://a.example/v1")
        self.assertEqual(payloads[0]["resolved_link_type"], "affiliate")
        self.assertEqual(payloads[1]["resolved_url"], "https://shop.example/family")
        self.assertEqual(payloads[1]["resolved_link_type"], "retailer")
        self.assertNotIn("sponsored", payloads[1]["resolved_rel"])

    def test_switching_variants_updates_resolved_link_types(self):
        product = self._two_variant_product(
            v1_extra={"retailer_url": "https://shop.example/v1"},
            v2_extra={"affiliate_url": "https://a.example/v2"},
        )
        self.assertEqual(product["resolved_link"].link_type, "retailer")
        set_display_variant(product, product["shape_variants"][1])
        self.assertEqual(product["resolved_link"].link_type, "affiliate")
        self.assertEqual(product["resolved_link"].url, "https://a.example/v2")
        set_display_variant(product, product["shape_variants"][0])
        self.assertEqual(product["resolved_link"].link_type, "retailer")

    def test_variant_retailer_url(self):
        product = self._variant_product({"retailer_url": "https://shop.example/v1"})
        prepare_product_variants(product)
        link = product["default_variant"]["resolved_link"]
        self.assertEqual(link.link_type, "retailer")
        self.assertNotIn("sponsored", link.rel)

    def test_variant_official_url(self):
        product = self._variant_product({"official_url": "https://brand.example/v1"})
        prepare_product_variants(product)
        link = product["default_variant"]["resolved_link"]
        self.assertEqual(link.link_type, "official")
        self.assertIn("productspecificaties", link.label.lower())

    # ---- bol.com-knoptekst (label bepaald op de daadwerkelijk gekozen URL) ----

    BOL = "https://www.bol.com/nl/nl/p/product/123/"

    def test_bol_affiliate_url_gets_bol_label(self):
        link = resolve_product_link({"affiliate_url": self.BOL})
        self.assertEqual(link.label, "Bekijk prijs en reviews bij bol →")
        self.assertEqual(link.link_type, "affiliate")
        self.assertIn("sponsored", link.rel)

    def test_bol_retailer_url_gets_bol_label(self):
        link = resolve_product_link({"retailer_url": self.BOL})
        self.assertEqual(link.label, "Bekijk prijs en reviews bij bol →")
        self.assertEqual(link.link_type, "retailer")
        self.assertNotIn("sponsored", link.rel)

    def test_non_bol_affiliate_and_retailer_keep_default_label(self):
        for field in ("affiliate_url", "retailer_url"):
            link = resolve_product_link({field: "https://shop.example/x"})
            self.assertEqual(link.label, "Bekijk prijs & reviews →")

    def test_bol_official_url_keeps_specs_label(self):
        link = resolve_product_link({"official_url": self.BOL})
        self.assertIn("productspecificaties", link.label.lower())
        self.assertNotIn("bij bol", link.label)

    def test_variant_bol_retailer_with_empty_affiliate_gets_bol_label(self):
        product = self._variant_product(
            {"affiliate_url": "", "retailer_url": self.BOL}
        )
        prepare_product_variants(product)
        self.assertEqual(
            product["resolved_link"].label, "Bekijk prijs en reviews bij bol →"
        )

    def test_variant_family_fallback_to_bol_gets_bol_label(self):
        product = self._variant_product({})
        product["affiliate_url"] = self.BOL
        prepare_product_variants(product)
        link = product["default_variant"]["resolved_link"]
        self.assertEqual(link.url, self.BOL)
        self.assertEqual(link.label, "Bekijk prijs en reviews bij bol →")

    def test_switching_between_bol_and_non_bol_updates_label(self):
        product = self._two_variant_product(
            v1_extra={"retailer_url": self.BOL},
            v2_extra={"retailer_url": "https://shop.example/v2"},
        )
        self.assertEqual(
            product["resolved_link"].label, "Bekijk prijs en reviews bij bol →"
        )
        set_display_variant(product, product["shape_variants"][1])
        self.assertEqual(product["resolved_link"].label, "Bekijk prijs & reviews →")
        set_display_variant(product, product["shape_variants"][0])
        self.assertEqual(
            product["resolved_link"].label, "Bekijk prijs en reviews bij bol →"
        )

    def test_is_bol_nl_url_detection(self):
        from utils.variant_helpers import is_bol_nl_url
        self.assertTrue(is_bol_nl_url("https://www.bol.com/nl/nl/p/x/1/"))
        self.assertTrue(is_bol_nl_url("https://bol.com/nl/nl/p/x/1/"))
        self.assertTrue(is_bol_nl_url("HTTPS://WWW.BOL.COM/nl/p/x/1/"))
        self.assertTrue(is_bol_nl_url("https://www.bol.com./nl/p/x/1/"))
        self.assertTrue(
            is_bol_nl_url("https://www.bol.com/nl/p/x/1/?utm_source=tracking")
        )
        self.assertFalse(is_bol_nl_url("https://bol.com.example.com/nl/x"))
        self.assertFalse(
            is_bol_nl_url("https://example.com/?url=https://www.bol.com/nl/")
        )
        self.assertFalse(is_bol_nl_url("https://www.bol.com/be/nl/p/x/1/"))
        self.assertFalse(is_bol_nl_url("https://www.bol.com/"))
        self.assertFalse(is_bol_nl_url(""))
        self.assertFalse(is_bol_nl_url(None))
        self.assertFalse(is_bol_nl_url(123))

    def test_variant_switch_clears_stale_link(self):
        product = {
            "slug": "test-product",
            "name": "Testproduct",
            "variant_selectors": [{"key": "shape", "label": "Vorm"}],
            "variants": [
                {"id": "v1", "options": {"shape": "rond"},
                 "option_labels": {"shape": "Rond"},
                 "affiliate_url": "https://a.example/v1", "is_default": True},
                {"id": "v2", "options": {"shape": "vierkant"},
                 "option_labels": {"shape": "Vierkant"},
                 "availability_label": "Nog niet algemeen verkrijgbaar"},
            ],
        }
        prepare_product_variants(product)
        self.assertEqual(product["resolved_link"].url, "https://a.example/v1")
        set_display_variant(product, product["shape_variants"][1])
        self.assertEqual(product["resolved_link"].url, "")
        self.assertEqual(product["affiliate_url"], "")
        self.assertEqual(
            product["availability_label"], "Nog niet algemeen verkrijgbaar"
        )

    def test_variant_json_payload_contains_resolved_fields(self):
        product = self._variant_product({"retailer_url": "https://shop.example/v1"})
        prepare_product_variants(product)
        payload = product["variant_json_data"]["variants"][0]
        self.assertEqual(payload["resolved_url"], "https://shop.example/v1")
        self.assertEqual(payload["resolved_link_type"], "retailer")
        self.assertNotIn("sponsored", payload["resolved_rel"])
        self.assertIn("retailer_url", payload)
        self.assertIn("official_url", payload)
        self.assertIn("availability_label", payload)

    def test_legacy_product_with_only_affiliate_url_keeps_working(self):
        commercial = resolve_commercial_fields(
            {"affiliate_url": "https://a.example/x", "price": 10}
        )
        self.assertEqual(commercial["affiliate_url"], "https://a.example/x")
        self.assertEqual(commercial["retailer_url"], "")
        self.assertEqual(commercial["official_url"], "")
        self.assertEqual(commercial["availability_label"], "")


class ProductLinkPartialTests(TestCase):
    """Rendering van templates/includes/product_link.html."""

    def _render(self, context):
        from django.template.loader import render_to_string
        return render_to_string("includes/product_link.html", context)

    def test_affiliate_rendering(self):
        html = self._render({
            "resolved_link": resolve_product_link(
                {"affiliate_url": "https://a.example/x"}
            ),
        })
        self.assertIn('rel="nofollow sponsored noopener"', html)
        self.assertIn('data-link-type="affiliate"', html)
        self.assertIn("button primary", html)

    def test_official_rendering_secondary_without_sponsored(self):
        html = self._render({
            "resolved_link": resolve_product_link(
                {"official_url": "https://brand.example/x"}
            ),
        })
        self.assertIn('rel="noopener"', html)
        self.assertNotIn("sponsored", html)
        self.assertNotIn("primary", html)
        self.assertIn("Bekijk productspecificaties", html)

    def test_availability_label_without_url(self):
        html = self._render({
            "resolved_link": resolve_product_link({}),
            "availability_label": "Nog niet algemeen verkrijgbaar",
        })
        self.assertNotIn("<a", html)
        self.assertNotIn("href", html)
        self.assertIn("Nog niet algemeen verkrijgbaar", html)

    def test_nothing_rendered_without_url_and_label(self):
        html = self._render({"resolved_link": resolve_product_link({})})
        self.assertNotIn("<a", html)
        self.assertNotIn("href=", html)
        self.assertNotIn("button", html)

    def test_official_only_product_gets_no_offer_jsonld(self):
        from products.views import _build_offer_ld
        self.assertIsNone(_build_offer_ld({
            "official_url": "https://brand.example/x",
            "price": 99, "currency": "EUR", "availability": "InStock",
        }))


class SwatchVariantLinkTests(TestCase):
    """Per-swatch resolved links (kleurswatch-systeem, variants zonder id)."""

    def _product(self, product_extra=None, swatches=None):
        from utils.variant_helpers import (
            apply_resolved_link, resolve_swatch_variant_links,
        )
        product = {
            "slug": "swatch-product",
            "name": "Swatchproduct",
            "variants": swatches or [],
        }
        product.update(product_extra or {})
        apply_resolved_link(product)
        resolve_swatch_variant_links(product)
        return product

    def test_swatch_retailer_url_used_without_sponsored(self):
        product = self._product(swatches=[
            {"name": "Zwart", "retailer_url": "https://shop.example/zwart"},
        ])
        link = product["variants"][0]["resolved_link"]
        self.assertEqual(link.url, "https://shop.example/zwart")
        self.assertEqual(link.link_type, "retailer")
        self.assertNotIn("sponsored", link.rel)
        self.assertTrue(product["swatch_has_any_link"])

    def test_swatch_priority_within_own_fields(self):
        product = self._product(swatches=[
            {"name": "Zwart",
             "affiliate_url": "https://a.example/zwart",
             "retailer_url": "https://shop.example/zwart"},
        ])
        link = product["variants"][0]["resolved_link"]
        self.assertEqual(link.link_type, "affiliate")
        self.assertIn("sponsored", link.rel)

    def test_swatch_without_url_falls_back_to_product_level(self):
        product = self._product(
            product_extra={"official_url": "https://brand.example/fam"},
            swatches=[
                {"name": "Zwart", "affiliate_url": "https://a.example/zwart"},
                {"name": "Beige"},
            ],
        )
        beige = product["variants"][1]["resolved_link"]
        self.assertEqual(beige.url, "https://brand.example/fam")
        self.assertEqual(beige.link_type, "official")
        self.assertEqual(beige.rel, "noopener")
        # Nooit de URL van een andere swatch.
        self.assertNotEqual(beige.url, "https://a.example/zwart")

    def test_swatch_and_product_without_urls(self):
        product = self._product(swatches=[{"name": "Zwart"}])
        self.assertEqual(product["variants"][0]["resolved_link"].url, "")
        self.assertFalse(product["swatch_has_any_link"])

    def test_airfryers_xl_page_renders_swatch_link_data(self):
        # De swatchproducten (GreenPan Bistro XXL, Bourgini Pure) staan in
        # het xl-formaat, niet in de compact-default.
        html = self.client.get("/airfryers/xl/").content.decode()
        self.assertIn("data-variant-swatch", html)
        self.assertIn('data-url="', html)
        # Swatches met retailer_url: resolved zonder sponsored-rel.
        self.assertIn('data-rel="nofollow noopener"', html)
        swatch_area = html[html.find("variant-swatches"):]
        self.assertIn('data-link-type="retailer"', swatch_area)


class SnijplankenCountTests(TestCase):
    """Dynamisch {product_count} op de snijplankenpagina (view + meta)."""

    def test_all_counts_match_ranking_length(self):
        from products.rankings_snijplanken import RANKINGS
        count = len(RANKINGS)
        html = self.client.get("/snijplanken/").content.decode()
        self.assertNotIn("{product_count}", html)
        self.assertIn(f"<h1>De {count} beste houten snijplanken van 2026</h1>", html)
        self.assertIn(f"Top {count} Houten Snijplanken", html)
        self.assertIn(f"Ontdek de {count} beste houten snijplanken", html)
        self.assertIn(f"Bekijk de {count} beste houten snijplanken", html)
        self.assertNotIn("10 beste houten snijplanken", html)
        self.assertNotIn("Top 10 Houten Snijplanken", html)
        self.assertIn(f"Top {count} Houten Snijplanken zonder Plastic", html)
