"""Keep the cutting-board page wired to the editor's current content structure."""
import copy
import json
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.utils.html import escape

from LeefNatuurlijkenGezond.site_urls import absolute_site_url
from products.content_snijplanken import CONTENT
from products.products_snijplanken import PRODUCTS
from products.rankings_snijplanken import RANKINGS


class SnijplankenContentTests(TestCase):
    def test_page_loads_without_a_conclusion_and_has_one_current_heading(self):
        response = self.client.get("/snijplanken/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["conclusie"])
        html = response.content.decode()
        self.assertEqual(html.count("<h1>"), 1)
        self.assertContains(response, f'<h1>{CONTENT["page_meta"]["h1"]}</h1>', html=True)
        self.assertNotRegex(html, r"<h[1-6][^>]*>\s*</h[1-6]>")

    def test_every_supplied_information_text_is_rendered(self):
        response = self.client.get("/snijplanken/")
        html = response.content.decode()

        def check_strings(value):
            if isinstance(value, dict):
                for child in value.values():
                    check_strings(child)
            elif isinstance(value, list):
                for child in value:
                    check_strings(child)
            elif isinstance(value, str):
                self.assertTrue(value in html or str(escape(value)) in html, value)

        for key in ("hero", "products_section", "why_choose", "why_wood", "size_guide",
                    "price_guide", "how_we_assess", "tips", "faq"):
            with self.subTest(section=key):
                check_strings(response.context["content"][key])
        self.assertContains(response, "→ Lees meer over onze beoordelingsmethode")
        self.assertNotContains(response, "{product_count}")

    def test_metadata_and_structured_data_use_the_current_editorial_text(self):
        response = self.client.get("/snijplanken/")
        meta = response.context["content"]["page_meta"]
        for markup in (
            f'<title>{meta["meta_title"]}</title>',
            f'<meta name="description" content="{meta["meta_description"]}">',
            f'<meta property="og:title" content="{meta["og_title"]}">',
            f'<meta property="og:description" content="{meta["og_description"]}">',
            f'<meta name="twitter:title" content="{meta["og_title"]}">',
            f'<meta name="twitter:description" content="{meta["og_description"]}">',
            f'<link rel="canonical" href="{absolute_site_url(meta["canonical_path"])}">',
        ):
            self.assertContains(response, markup, html=True)
        structured = json.loads(response.context["json_ld"])
        self.assertEqual(structured["@type"], "ItemList")
        self.assertEqual(structured["name"], meta["itemlist_name"])
        self.assertEqual(structured["description"], meta["itemlist_description"])
        self.assertEqual(structured["numberOfItems"], len(RANKINGS))
        self.assertNotIn("PFAS-vrij", structured["description"])
        faq = json.loads(response.context["faq_ld"])
        self.assertEqual(len(faq["mainEntity"]), len(CONTENT["faq"]["items"]))

    def test_product_order_values_and_source_content_remain_unchanged(self):
        products_before, content_before = copy.deepcopy(PRODUCTS), copy.deepcopy(CONTENT)
        response = self.client.get("/snijplanken/")
        actual = response.context["products"]
        self.assertEqual([p["slug"] for p in actual], [PRODUCTS[key]["slug"] for key in RANKINGS])
        for product, key in zip(actual, RANKINGS):
            for field in ("rating", "award", "price", "reference_price", "pros", "cons",
                          "verdict", "affiliate_url", "retailer_url"):
                self.assertEqual(product.get(field), PRODUCTS[key].get(field), (key, field))
        self.assertEqual(PRODUCTS, products_before)
        self.assertEqual(CONTENT, content_before)

    def test_optional_conclusion_still_precedes_information_if_supplied(self):
        content = copy.deepcopy(CONTENT)
        content["conclusion"] = {"title": "Een bestaande conclusie", "text": "Bestaande tekst."}
        with patch("products.views.SNIJPLANKEN_CONTENT", content):
            response = self.client.get("/snijplanken/")
        html = response.content.decode()
        self.assertLess(html.index("</table>"), html.index("Een bestaande conclusie"))
        self.assertLess(html.index("Een bestaande conclusie"), html.index('id="keuzehulp"'))


class OptionalInformationSectionTests(SimpleTestCase):
    def test_missing_items_never_renders_dictionary_method_results(self):
        for section in (
            {"title": "Testtitel", "intro": "Testintro", "bullets": ["Eerste punt"]},
            {"title": "Testtitel", "intro": "Testintro"},
        ):
            html = render_to_string("partials/category_information_section.html", {"section": section})
            self.assertNotIn("(&#x27;", html)
            self.assertNotIn("('title'", html)
            self.assertIn("<h2>Testtitel</h2>", html)
            self.assertEqual(html.count("<li>"), len(section.get("bullets", [])))

    def test_explicit_items_are_still_rendered(self):
        section = {"title": "Badges", "items": ["<strong>Beste keuze</strong>", "Budget keuze"]}
        html = render_to_string("partials/category_information_section.html", {"section": section})
        self.assertEqual(html.count("<li>"), 2)
        self.assertIn("<strong>Beste keuze</strong>", html)

    def test_missing_optional_sections_do_not_render_empty_headings(self):
        for section in (None, {}):
            html = render_to_string("partials/category_information_section.html", {"section": section})
            self.assertEqual(html.strip(), "")
