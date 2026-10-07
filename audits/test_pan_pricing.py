"""Formaatgebonden panprijzen blijven audit-only en delen dezelfde runner."""

import copy
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from audits.checks.variants import audit_price_levels
from audits.models import ProductAuditRun
from utils.pricing import (
    get_audit_price_thresholds,
    get_price_range,
    get_price_range_from_thresholds,
)


class PanPricingTests(SimpleTestCase):
    def test_real_rvs_boundaries_through_audit(self):
        # Alleen de productbron vervangen, niet de echte prijsconfiguratie.
        cases = [
            ({"diameter": 20}, (50, 90, 140)),
            ({"diameter": 24}, (60, 100, 150)),
            ({"diameter": 26}, (60, 100, 150)),
            ({"diameter": 28}, (65, 110, 175)),
            ({"diameter": 30}, (70, 120, 180)),
            ({"diameter": 32}, (90, 150, 220)),
            ({"diameter": 28, "diameters": [28, 20]}, (140, 180, 240)),
            ({"diameters": [28, 24]}, (140, 190, 260)),
            ({"diameters": [28, 20, 24]}, (150, 250, 350)),
        ]
        for product, amounts in cases:
            for index, amount in enumerate(amounts):
                for price, expected in (
                    (Decimal(amount) - Decimal("0.01"), "€" * (index + 1)),
                    (Decimal(amount), "€" * (index + 2)),
                ):
                    for manual in (expected, "verkeerd"):
                        with self.subTest(product=product, price=price, manual=manual):
                            products = {"pan": {
                                **product, "price": price, "price_range": manual,
                            }}
                            before = copy.deepcopy(products)
                            with patch("audits.checks.variants._load_products",
                                       return_value=products):
                                errors, warnings, rows = audit_price_levels(
                                    "rvs-koekenpannen", "unused"
                                )
                            self.assertEqual(errors, [])
                            self.assertEqual(rows, [
                                ("rvs-koekenpannen", "pan", "", price, manual, expected),
                            ])
                            self.assertEqual(
                                [w[0] for w in warnings],
                                [] if manual == expected else ["price_range_mismatch"],
                            )
                            self.assertEqual(products, before)

    def test_all_requested_boundaries(self):
        cases = [
            ({"diameter": 20}, (25, 50, 90)),
            ({"diameter": 24}, (30, 60, 100)),
            ({"diameter": 26}, (35, 65, 105)),
            ({"diameter": 28}, (40, 70, 110)),
            ({"diameter": 30}, (45, 75, 120)),
            ({"diameter": 32}, (50, 85, 130)),
            ({"diameters": [20, 24]}, (50, 80, 125)),
            ({"diameters": [20, 28]}, (50, 75, 110)),
            ({"diameters": [24, 28]}, (60, 100, 175)),
            ({"diameters": [20, 24, 28]}, (75, 120, 175)),
        ]
        for product, amounts in cases:
            thresholds = get_audit_price_thresholds("koekenpannen", product)
            self.assertIsNotNone(thresholds)
            for index, amount in enumerate(amounts):
                with self.subTest(product=product, amount=amount):
                    self.assertEqual(
                        get_price_range_from_thresholds(
                            Decimal(amount) - Decimal("0.01"), thresholds
                        ), "€" * (index + 1),
                    )
                    self.assertEqual(
                        get_price_range_from_thresholds(amount, thresholds),
                        "€" * (index + 2),
                    )

    def test_set_takes_precedence_and_order_is_irrelevant(self):
        thresholds = get_audit_price_thresholds(
            "koekenpannen", {"diameter": 28, "diameters": [28, 20]}
        )
        self.assertEqual(get_price_range_from_thresholds(110, thresholds), "€€€€")
        self.assertEqual(get_price_range_from_thresholds(110, get_audit_price_thresholds(
            "koekenpannen", {"diameter": 28}
        )), "€€€€")
        self.assertEqual(get_price_range_from_thresholds(45, thresholds), "€")
        self.assertEqual(get_price_range_from_thresholds(45, get_audit_price_thresholds(
            "koekenpannen", {"diameter": 28}
        )), "€€")

    def test_missing_or_unconfigured_formats_have_no_fallback(self):
        for product in (
            {}, {"diameter": 22}, {"diameter": "28"}, {"diameter": True},
            {"diameter": 28, "diameters": []},
            {"diameter": 28, "diameters": [20, 32]},
            {"diameters": "20_28"}, {"diameters": [20, "28"]},
        ):
            with self.subTest(product=product):
                self.assertIsNone(get_audit_price_thresholds("koekenpannen", product))
                with patch("audits.checks.variants._load_products",
                           return_value={"pan": {**product, "price": 55}}):
                    _, warnings, rows = audit_price_levels("koekenpannen", "unused")
                self.assertEqual(rows[0][-1], "—")
                self.assertIn("pan_pricing_format_unknown", {w[0] for w in warnings})

    def test_real_rvs_unknown_formats_have_no_fallback(self):
        # 20+24 is wel keramisch geconfigureerd, maar geen bestaande RVS-setgrens.
        for product in (
            {}, {"diameter": 22}, {"diameter": "28"}, {"diameter": True},
            {"diameter": 28, "diameters": []},
            {"diameter": 28, "diameters": [20, 24]},
            {"diameters": [20, 32]}, {"diameters": [20, 20, 28]},
            {"diameters": "20_28"}, {"diameters": [20, "28"]},
        ):
            with self.subTest(product=product):
                self.assertIsNone(get_audit_price_thresholds("rvs-koekenpannen", product))
                with patch("audits.checks.variants._load_products", return_value={
                    "pan": {**product, "price": 150, "price_range": "€€"},
                }):
                    errors, warnings, rows = audit_price_levels("rvs-koekenpannen", "unused")
                self.assertEqual(errors, [])
                self.assertEqual(rows[0][-1], "—")
                self.assertEqual([w[0] for w in warnings], ["pan_pricing_format_unknown"])

    def test_variant_format_overrides_family_format_without_mutation(self):
        products = {"pan": {
            "diameter": 20,
            "variants": [
                {"id": "small", "diameter": 20, "price": 55, "price_range": "€€€"},
                {"id": "large", "diameter": 28, "price": 55, "price_range": "€€"},
            ],
        }}
        before = copy.deepcopy(products)
        with patch("audits.checks.variants._load_products", return_value=products):
            errors, warnings, rows = audit_price_levels("koekenpannen", "unused")
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual([row[-1] for row in rows], ["€€€", "€€"])
        self.assertEqual(products, before)

    def test_other_categories_can_register_own_formats(self):
        custom = ((Decimal("200"), "€"), (None, "€€"))
        with patch.dict("utils.pricing.PAN_AUDIT_PRICE_RANGES", {
            "test-pannen": {"single": {24: custom}, "sets": {(20, 28): custom}},
        }):
            self.assertEqual(get_audit_price_thresholds(
                "test-pannen", {"diameter": 24}
            ), custom)
            self.assertEqual(get_audit_price_thresholds(
                "test-pannen", {"diameters": [28, 20]}
            ), custom)
            self.assertIsNone(get_audit_price_thresholds(
                "test-pannen", {"diameter": 28}
            ))

    def test_public_levels_and_unconfigured_categories_unchanged(self):
        self.assertEqual(get_price_range(55, "koekenpannen"), "€€€")
        self.assertEqual(get_price_range_from_thresholds(
            55, get_audit_price_thresholds("koekenpannen", {"diameter": 28})
        ), "€€")
        self.assertEqual(get_price_range_from_thresholds(
            55, get_audit_price_thresholds("hapjespannen", {})
        ), "€€")
        self.assertIsNone(get_audit_price_thresholds("rvs-koekenpannen", {}))
        for price in (49.99, 60, 110, 150, 240, 350):
            with self.subTest(price=price):
                self.assertIsNone(get_price_range(price, "rvs-koekenpannen"))


class PanPricingEntryPointTests(TestCase):
    products = {"pan": {"diameter": 28, "price": 55, "price_range": "€€€"}}
    rvs_products = {
        "single": {"diameter": 28, "price": 150, "price_range": "€"},
        "set": {"diameter": 28, "diameters": [28, 20],
                "price": 150, "price_range": "€"},
        "unknown-set": {"diameter": 24, "diameters": [20, 24],
                        "price": 150, "price_range": "€"},
    }

    def assert_rvs_run_saved(self, run):
        self.assertEqual(run.status, "completed")
        self.assertEqual(run.category, "rvs-koekenpannen")
        self.assertEqual(run.error_count, 0)
        self.assertEqual(run.warning_count, 3)
        self.assertEqual(run.issue_count, 3)
        self.assertCountEqual(run.metadata["price_table"], [
            {
                "category": "rvs-koekenpannen",
                "product": slug,
                "variant": "—",
                "price": 150.0,
                "manual": "€",
                "computed": computed,
            }
            for slug, computed in (
                ("single", "€€€"), ("set", "€€"), ("unknown-set", "—"),
            )
        ])
        self.assertCountEqual(
            list(run.issues.values_list(
                "code", "severity", "category", "product_slug",
            )),
            [
                ("price_range_mismatch", "warning", "rvs-koekenpannen", "single"),
                ("price_range_mismatch", "warning", "rvs-koekenpannen", "set"),
                ("pan_pricing_format_unknown", "warning",
                 "rvs-koekenpannen", "unknown-set"),
            ],
        )

    def test_management_command_saves_rvs_levels_and_unknown_format(self):
        # Alleen de productbron vervangen: de RVS-grenzen blijven echt.
        with patch("audits.checks.variants._load_products",
                   return_value=self.rvs_products):
            with self.assertRaises(CommandError):
                call_command("audit_products", audit="price_levels",
                             category="rvs-koekenpannen", strict=True,
                             stdout=StringIO())
        run = ProductAuditRun.objects.get(audit_key="price_levels")
        self.assert_rvs_run_saved(run)

    def test_admin_run_saves_rvs_levels_and_unknown_format(self):
        user = User.objects.create_superuser(username="audit-test", password="test-only")
        self.client.force_login(user)
        with patch("audits.checks.variants._load_products",
                   return_value=self.rvs_products):
            response = self.client.post(
                reverse("audit_run"),
                {"audit_key": "price_levels", "category": "rvs-koekenpannen"},
                follow=True,
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Interne prijstabel")
        run = ProductAuditRun.objects.get(audit_key="price_levels")
        self.assert_rvs_run_saved(run)
        self.assertCountEqual(
            response.context["price_table"], run.metadata["price_table"],
        )

    def test_management_command_saves_new_computed_levels(self):
        with patch("audits.checks.variants._load_products", return_value=self.products):
            with self.assertRaises(CommandError):
                call_command("audit_products", audit="price_levels",
                             category="koekenpannen", strict=True, stdout=StringIO())
        run = ProductAuditRun.objects.get(audit_key="price_levels")
        self.assertEqual(run.status, "completed")
        self.assertEqual(run.metadata["price_table"][0]["computed"], "€€")
        self.assertTrue(run.issues.filter(code="price_range_mismatch").exists())

    def test_admin_run_shows_new_computed_price_table(self):
        user = User.objects.create_superuser(username="audit-test", password="test-only")
        self.client.force_login(user)
        with patch("audits.checks.variants._load_products", return_value=self.products):
            response = self.client.post(
                reverse("audit_run"),
                {"audit_key": "price_levels", "category": "koekenpannen"},
                follow=True,
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Interne prijstabel")
        self.assertEqual(response.context["price_table"][0]["computed"], "€€")
