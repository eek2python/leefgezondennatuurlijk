"""Airfryer-prijsaudit: groepen uit rankings, grenzen uit centrale config."""

import copy
from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase

from audits.checks.variants import audit_price_levels, run_price_level_check
from utils.pricing import get_price_range


class AirfryerPricingTests(SimpleTestCase):
    def test_threshold_boundaries(self):
        for group, boundaries in (
            ("compact", (75, 110, 150)),
            ("xl", (90, 130, 180)),
            ("dual", (110, 170, 250)),
        ):
            for index, amount in enumerate(boundaries):
                with self.subTest(group=group, amount=amount):
                    key = f"airfryers_{group}"
                    self.assertEqual(
                        get_price_range(Decimal(amount) - Decimal("0.01"), key),
                        "€" * (index + 1),
                    )
                    self.assertEqual(get_price_range(amount, key), "€" * (index + 2))

    def test_group_is_from_rankings_and_variants_use_same_group(self):
        products = {
            "name_xl_but_compact": {"price": 75, "price_range": "€"},
            "large": {"variants": [
                {"name": "Groen", "price": 130, "price_range": "€"},
                {"name": "Blauw", "price": None},
            ]},
            "double": {"variants": [
                {"id": "default", "price": 250, "price_range": "€€€€"},
            ]},
        }
        before = copy.deepcopy(products)
        rankings = {
            "compact": ["name_xl_but_compact"],
            "xl": ["large"],
            "dual": ["double"],
        }
        with patch("audits.checks.variants._load_products", return_value=products), \
                patch("products.rankings_airfryers.RANKINGS", rankings):
            errors, warnings, rows = audit_price_levels("airfryers", "unused")
        self.assertEqual(errors, [])
        self.assertEqual([row[-1] for row in rows], ["€€", "€€€", "—", "€€€€"])
        mismatches = [w for w in warnings if w[0] == "price_range_mismatch"]
        self.assertEqual({w[2] for w in mismatches}, {"name_xl_but_compact", "large"})
        self.assertIn("missing_price", {w[0] for w in warnings})
        self.assertEqual(products, before)

    def test_unknown_and_ambiguous_groups_have_no_fallback(self):
        products = {
            "unranked": {"price": 100},
            "ambiguous": {"price": 100},
        }
        rankings = {"compact": ["ambiguous"], "xl": ["ambiguous"], "dual": []}
        with patch("audits.checks.variants._load_products", return_value=products), \
                patch("products.rankings_airfryers.RANKINGS", rankings):
            _, warnings, rows = audit_price_levels("airfryers", "unused")
        self.assertTrue(all(row[-1] == "—" for row in rows))
        self.assertEqual(
            [w[0] for w in warnings],
            ["airfryer_pricing_group_unknown"] * 2,
        )

    def test_shared_runner_returns_computed_airfryer_price_table(self):
        from products.rankings_airfryers import RANKINGS

        _, metadata = run_price_level_check(category="airfryers")
        rows = metadata["price_table"]
        self.assertTrue(rows)
        expected_groups = {
            product: group for group, products in RANKINGS.items() for product in products
        }
        for row in rows:
            with self.subTest(product=row["product"], variant=row["variant"]):
                group = expected_groups.get(row["product"])
                expected = get_price_range(
                    row["price"], f"airfryers_{group}"
                ) if group else None
                self.assertEqual(row["computed"], expected or "—")
        self.assertTrue(any(row["computed"] != "—" for row in rows))
