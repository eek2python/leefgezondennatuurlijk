from django.test import SimpleTestCase

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
