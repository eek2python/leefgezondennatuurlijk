import re
from unittest.mock import patch

from django.test import TestCase

from products import views


class RvsSetFormatTests(TestCase):
    def test_each_set_format_is_selectable_even_when_empty(self):
        rankings = {28: [], "20_28": [], "24_28": [], "20_24_28": []}
        with patch.dict(views.RVS_KOEKENPANNEN_RANKINGS, rankings, clear=True):
            for size, label in (
                ("20_28", "20 + 28"),
                ("24_28", "24 + 28"),
                ("20_24_28", "20 + 24 + 28"),
            ):
                with self.subTest(size=size):
                    response = self.client.get("/rvs-koekenpannen/", {"size": size})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context["selected_size"], size)
                    self.assertContains(response, f"{label} cm")
                    self.assertContains(response, "nog geen RVS-koekenpannen toegevoegd")
                    active_links = re.findall(
                        rf'<a href="\?size={size}"[^>]*aria-current="page"',
                        response.content.decode(),
                    )
                    self.assertEqual(len(active_links), 2)
                    self.assertEqual(response.context["product_count"], 0)
                    self.assertEqual(response.context["conclusie"], {})

    def test_set_products_follow_the_selected_ranking(self):
        key = "demeyere_essential_5_set_24_28"
        rankings = {28: [], "20_28": [], "24_28": [key], "20_24_28": []}
        with patch.dict(views.RVS_KOEKENPANNEN_RANKINGS, rankings, clear=True):
            response = self.client.get("/rvs-koekenpannen/?size=24_28")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["product_count"], 1)
        self.assertContains(response, views.RVS_KOEKENPANNEN_PRODUCTS[key]["name"])
        self.assertNotContains(response, "nog geen RVS-koekenpannen toegevoegd")

    def test_single_sizes_and_invalid_values_keep_the_existing_default(self):
        for raw_size, expected in ((None, 28), ("24", 24), ("unknown", 28), ("99", 28)):
            with self.subTest(size=raw_size):
                params = {} if raw_size is None else {"size": raw_size}
                response = self.client.get("/rvs-koekenpannen/", params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["selected_size"], expected)

    def test_selector_orders_single_pans_before_sets(self):
        response = self.client.get("/rvs-koekenpannen/")
        self.assertEqual(
            response.context["available_sizes"],
            [20, 24, 26, 28, 30, 32, "20_28", "24_28", "20_24_28"],
        )