import datetime
import logging
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.db.utils import OperationalError
from django.test import SimpleTestCase, TestCase, override_settings

from products.models import AffiliateProductState
from products.views import ALL_PRODUCTS_BY_SLUG


@override_settings(DEBUG=False)
class ProductionCatalogueRegressionTests(TestCase):
    DETAIL_CASES = {
        # Reported production failure; a representative flat product.
        "greenpan-barcelona-pro-hapjespan-28": "flat",
        # Airfryer added in the deployment after maintenance support.
        "ninja-crispi-4-in-1": "swatch",
        # A second swatch family used on category and detail pages.
        "greenpan-bistro-xxl-7-2l": "swatch",
        # Button/shape variants project a selected variant to product level.
        "ikea-365-plus-enkel": "button",
    }

    def _assert_source_shape(self, slug, expected_shape):
        data = ALL_PRODUCTS_BY_SLUG[slug]["data"]
        variants = data.get("variants") or []
        if expected_shape == "flat":
            self.assertFalse(variants)
        elif expected_shape == "swatch":
            self.assertTrue(variants)
            self.assertTrue(all(not variant.get("id") for variant in variants))
        elif expected_shape == "button":
            self.assertTrue(variants)
            self.assertTrue(all(variant.get("id") for variant in variants))

    def test_representative_detail_shapes_render_without_overrides(self):
        for slug, shape in self.DETAIL_CASES.items():
            with self.subTest(slug=slug, shape=shape):
                self._assert_source_shape(slug, shape)
                response = self.client.get(f"/product/{slug}/")
                self.assertEqual(response.status_code, 200)

    def test_representative_detail_shapes_render_with_database_overrides(self):
        for slug in self.DETAIL_CASES:
            AffiliateProductState.objects.create(
                slug=slug,
                price=Decimal("199.99"),
                availability="OutOfStock",
                price_last_checked=datetime.date(2026, 8, 19),
            )

        for slug, shape in self.DETAIL_CASES.items():
            with self.subTest(slug=slug, shape=shape):
                response = self.client.get(f"/product/{slug}/")
                self.assertEqual(response.status_code, 200)

    def test_representative_categories_render_with_database_dates(self):
        AffiliateProductState.objects.create(
            slug="greenpan-barcelona-pro-hapjespan-28",
            price=Decimal("149.90"),
            availability="InStock",
            price_last_checked=datetime.date(2026, 8, 19),
        )
        AffiliateProductState.objects.create(
            slug="ninja-crispi-4-in-1",
            price=Decimal("179.99"),
            availability="InStock",
            price_last_checked=datetime.date(2026, 8, 19),
        )

        for url in (
            "/hapjespannen/?size=28",
            "/airfryers/",
            "/airfryers/xl/",
            "/airfryers/dual/",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_missing_maintenance_table_remains_visible_as_request_error(self):
        self.client.raise_request_exception = False
        error = OperationalError(
            "no such table: products_affiliateproductstate"
        )

        with patch.object(
            AffiliateProductState.objects,
            "in_bulk",
            side_effect=error,
        ), self.assertLogs("django.request", level=logging.ERROR) as captured:
            response = self.client.get(
                "/product/greenpan-barcelona-pro-hapjespan-28/"
            )

        log_output = "\n".join(captured.output)
        self.assertEqual(response.status_code, 500)
        self.assertIn("OperationalError", log_output)
        self.assertIn("products_affiliateproductstate", log_output)
        self.assertNotContains(response, "OperationalError", status_code=500)
        self.assertNotContains(
            response,
            "products_affiliateproductstate",
            status_code=500,
        )


@override_settings(DEBUG=False, ROOT_URLCONF="products.test_urls")
class ProductionRequestLoggingTests(SimpleTestCase):
    def test_django_request_logger_has_explicit_stderr_handler(self):
        handler_name = settings.LOGGING["loggers"]["django.request"][
            "handlers"
        ][0]
        handler = settings.LOGGING["handlers"][handler_name]

        self.assertEqual(handler["class"], "logging.StreamHandler")
        self.assertEqual(handler["stream"], "ext://sys.stderr")
        self.assertEqual(handler["level"], "ERROR")
        self.assertFalse(
            settings.LOGGING["loggers"]["django.request"]["propagate"]
        )
        self.assertFalse(settings.LOGGING["disable_existing_loggers"])

    def test_unhandled_exception_logs_traceback_but_returns_safe_500(self):
        self.client.raise_request_exception = False

        with self.assertLogs(
            "django.request", level=logging.ERROR
        ) as captured:
            response = self.client.get("/_test/unhandled-exception/")

        log_output = "\n".join(captured.output)
        self.assertEqual(response.status_code, 500)
        self.assertIn("Traceback", log_output)
        self.assertIn("RuntimeError: production logging sentinel", log_output)
        self.assertNotContains(response, "Traceback", status_code=500)
        self.assertNotContains(
            response,
            "production logging sentinel",
            status_code=500,
        )