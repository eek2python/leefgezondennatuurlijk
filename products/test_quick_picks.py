"""Quick picks are navigation to existing awarded products, never a second ranking."""
import copy
import re
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase

from products.products_koekenpannen import PRODUCTS
from products.rankings_koekenpannen import RANKINGS
from utils.quick_picks import AWARD_ORDER, build_quick_picks


def example_product(award="🏆 Beste keuze"):
    return {
        "slug": "test-pan", "name": "Testpan", "award": award,
        "award_class": "best-choice", "rating": 4.5, "rating_class": "4-5",
        "rating_display": "4,5", "comparison_features": ["Constructie", "Oven", "Garantie"],
    }


class QuickPickSelectionTests(SimpleTestCase):
    def test_awards_are_sorted_without_copying_or_mutating_products(self):
        products = [example_product(award) for award in reversed(AWARD_ORDER)]
        products.append(example_product("Andere aanbeveling"))
        original = copy.deepcopy(products)
        picks = build_quick_picks(products)
        self.assertEqual([pick["product"]["award"] for pick in picks], list(AWARD_ORDER))
        self.assertIs(picks[0]["product"], products[2])
        self.assertEqual(products, original)

    def test_zero_one_two_and_three_awards_without_placeholders(self):
        for count in range(4):
            with self.subTest(count=count):
                picks = build_quick_picks([
                    example_product(award) for award in list(AWARD_ORDER)[:count]
                ])
                html = render_to_string("partials/ceramic_quick_picks.html", {
                    "quick_picks": picks,
                })
                self.assertEqual(html.count('class="ceramic-quick-pick"'), count)
                self.assertEqual("Snel kiezen: onze aanbevelingen" in html, bool(count))
                if not count:
                    self.assertEqual(html.strip(), "")

    def test_quick_reason_precedes_features_without_generated_claims(self):
        product = example_product()
        product["quick_reason"] = "  Bestaande korte reden  "
        self.assertEqual(build_quick_picks([product])[0]["reason"], "Bestaande korte reden")
        product["quick_reason"] = ""
        self.assertEqual(build_quick_picks([product])[0]["reason"], "Constructie · Oven")

    def test_no_reason_when_only_unapproved_sources_are_available(self):
        product = example_product()
        product.pop("comparison_features")
        product.update(features=["Niet gebruiken"], pros=["Ook niet"], verdict="Niet overnemen")
        self.assertEqual(build_quick_picks([product])[0]["reason"], "")

    def test_empty_or_invalid_features_are_not_rendered_as_claims(self):
        product = example_product()
        for features in (None, "", "Geen lijst", [], [None, "", "A", 5, "B", "C"]):
            with self.subTest(features=features):
                product["comparison_features"] = features
                expected = "A · B" if isinstance(features, list) and features else ""
                self.assertEqual(build_quick_picks([product])[0]["reason"], expected)

    def test_partial_only_shows_editorial_fields_and_internal_links(self):
        product = example_product()
        product.update({
            "quick_reason": "<script>onveilig</script>",
            "price": "GEHEIME PRIJS", "reference_price": "OUDE PRIJS",
            "description": "LANGE BESCHRIJVING", "pros": ["UITGEBREIDE PRO"],
            "cons": ["UITGEBREIDE CON"], "verdict": "VOLLEDIG VERDICT",
            "affiliate_url": "https://retailer.invalid/affiliate", "rating_count": 9999,
            "image": "verboden-foto.jpg", "retailer_url": "https://retailer.invalid/",
        })
        html = render_to_string("partials/ceramic_quick_picks.html", {
            "quick_picks": build_quick_picks([product]),
        })
        self.assertIn('href="#product-test-pan"', html)
        self.assertIn("Bekijk beoordeling", html)
        self.assertIn("4,5", html)
        self.assertIn("&lt;script&gt;", html)
        for forbidden in ("GEHEIME PRIJS", "OUDE PRIJS", "LANGE BESCHRIJVING",
                          "UITGEBREIDE PRO", "UITGEBREIDE CON", "VOLLEDIG VERDICT",
                          "retailer.invalid", "9999", "verboden-foto.jpg", "<script>"):
            self.assertNotIn(forbidden, html)

    def test_changing_an_award_changes_selection_without_separate_configuration(self):
        product = example_product()
        self.assertEqual(len(build_quick_picks([product])), 1)
        product["award"] = ""
        self.assertEqual(build_quick_picks([product]), [])


class QuickPickPageTests(TestCase):
    def test_all_nine_selections_link_to_unique_focusable_product_cards(self):
        before = copy.deepcopy(PRODUCTS)
        for size in (20, 24, 26, 28, 30, 32, "20_28", "24_28", "20_24_28"):
            with self.subTest(size=size):
                response = self.client.get("/koekenpannen/", {"size": str(size)})
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                expected = build_quick_picks(response.context["products"])
                self.assertEqual(response.context["quick_picks"], expected)
                for pick in expected:
                    product = pick["product"]
                    self.assertIn(f'href="#product-{product["slug"]}"', html)
                    self.assertEqual(html.count(f'id="product-{product["slug"]}"'), 1)
                    self.assertRegex(html, r'id="product-' + re.escape(product["slug"])
                                     + r'" tabindex="-1"')
                    self.assertTrue(any(
                        product is full for full in response.context["products"]
                    ))
                self.assertLess(html.index('id="snel-kiezen"'), html.index('id="productlijst"'))
                self.assertEqual(response.context["product_count"],
                                 sum(key in PRODUCTS for key in RANKINGS[size]))
        self.assertEqual(PRODUCTS, before)

    def test_full_page_omits_empty_section_when_no_awards_exist(self):
        product = copy.deepcopy(PRODUCTS[next(iter(PRODUCTS))])
        product["award"] = ""
        with patch("products.views.KOEKENPANNEN_PRODUCTS", {"test": product}), \
                patch("products.views.KOEKENPANNEN_RANKINGS", {28: ["test"]}):
            response = self.client.get("/koekenpannen/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="snel-kiezen"')
        self.assertNotContains(response, "Snel kiezen: onze aanbevelingen")
        self.assertContains(response, 'id="productlijst"')

    def test_other_categories_keep_their_existing_recommendation_component(self):
        response = self.client.get("/rvs-koekenpannen/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="snel-kiezen"')
        self.assertNotContains(response, 'id="product-')
