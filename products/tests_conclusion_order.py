"""Conclusions belong between the comparison and tips, including selectors."""

import re
from unittest.mock import patch

from django.shortcuts import render
from django.test import TestCase
from django.utils.html import escape


CATEGORY_PATHS = (
    "/koekenpannen/",
    "/rvs-koekenpannen/",
    "/koolstofstalen-koekenpannen/",
    "/gietijzeren-koekenpannen/",
    "/hapjespannen/",
    "/wokpannen/",
    "/snijplanken/",
    "/airfryers/",
    "/airfryers/xl/",
    "/airfryers/dual/",
)


class ConclusionOrderTests(TestCase):
    def heading_matches(self, html, title):
        return list(re.finditer(
            r"<h2(?:\s[^>]*)?>\s*" + re.escape(str(escape(title)))
            + r"\s*</h2>",
            html,
        ))

    def assert_page_order(self, response):
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        content = response.context["content"]
        conclusion = response.context.get("conclusie")
        tips = self.heading_matches(html, content["tips"]["title"])
        faq = self.heading_matches(html, content["faq"]["title"])
        self.assertEqual(len(tips), 1)
        self.assertEqual(len(faq), 1)
        self.assertLess(tips[0].start(), faq[0].start())

        if not conclusion:
            self.assertNotRegex(html, r"<h2[^>]*>\s*Conclusie\b")
            return

        conclusions = self.heading_matches(html, conclusion["title"])
        self.assertEqual(len(conclusions), 1)
        self.assertLess(conclusions[0].start(), tips[0].start())
        self.assertRegex(
            html, r"<p>\s*" + re.escape(conclusion["text"]) + r"\s*</p>"
        )
        # These complete sections must remain adjacent; no added summary,
        # empty conclusion or intervening content.
        between = html[conclusions[0].end():tips[0].start()]
        self.assertEqual(between.count("<section"), 1)
        self.assertEqual(between.count("</section>"), 1)
        self.assertEqual(between.count(conclusion["text"]), 1)

        comparison_title = (
            response.context.get("comparison_title")
            or content.get("products_section", {}).get("comparison_title")
        )
        if comparison_title and response.context["products"]:
            comparisons = self.heading_matches(html, comparison_title)
            self.assertEqual(len(comparisons), 1)
            self.assertLess(comparisons[0].start(), conclusions[0].start())

        for bullet in content["tips"].get("bullets", []):
            self.assertIn(bullet, html)
        self.assertNotRegex(html, r"<h2[^>]*>\s*</h2>")

    def test_all_categories_and_available_sizes(self):
        for path in CATEGORY_PATHS:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assert_page_order(response)
                for size in response.context.get("available_sizes", []):
                    with self.subTest(path=path, size=size):
                        self.assert_page_order(
                            self.client.get(path, {"size": str(size)})
                        )

    def test_named_and_combination_sets(self):
        cases = (
            ("/koekenpannen/", "24_28"),
            ("/rvs-koekenpannen/", "24_28"),
            ("/koolstofstalen-koekenpannen/", "24_28"),
            ("/koolstofstalen-koekenpannen/", "20_24_28"),
            ("/gietijzeren-koekenpannen/", "Pannensets"),
        )
        for path, size in cases:
            with self.subTest(path=path, size=size):
                response = self.client.get(path, {"size": size})
                self.assertEqual(response.context["selected_size"], size)
                self.assert_page_order(response)

    def test_storage_already_has_the_correct_order(self):
        for group in ("enkel", "3-delig", "5-delig"):
            for size in ("alle", "klein", "middel", "groot"):
                with self.subTest(group=group, size=size):
                    self.assert_page_order(self.client.get(
                        "/vershoudcontainers/",
                        {"uitvoering": group, "formaat": size},
                    ))

    def test_no_conclusion_keeps_tips_and_faq_without_an_empty_section(self):
        def render_without_conclusion(request, template, context):
            return render(request, template, {**context, "conclusie": {}})

        for path in CATEGORY_PATHS:
            with self.subTest(path=path), patch(
                "products.views.render", side_effect=render_without_conclusion,
            ):
                response = self.client.get(path)
                self.assert_page_order(response)
                self.assertNotRegex(
                    response.content.decode(), r"<h2[^>]*>\s*</h2>"
                )
