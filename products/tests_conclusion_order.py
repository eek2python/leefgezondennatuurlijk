"""Conclusions immediately follow comparisons, before explanatory sections."""

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
    "/pannensets/koekenpannensets/",
    "/kookpannensets/",
    "/complete-pannensets/",
    "/bak-braadsets/",
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
        tips = self.heading_matches(html, content["tips"]["title"]) if content.get("tips") else []
        faq = self.heading_matches(html, content["faq"]["title"]) if content.get("faq") else []
        if content.get("tips"):
            self.assertEqual(len(tips), 1)
        if content.get("faq"):
            self.assertEqual(len(faq), 1)
        if tips and faq:
            self.assertLess(tips[0].start(), faq[0].start())

        if not conclusion:
            self.assertNotRegex(html, r"<h2[^>]*>\s*Conclusie\b")
            return

        conclusions = self.heading_matches(html, conclusion["title"])
        self.assertEqual(len(conclusions), 1)
        if tips:
            self.assertLess(conclusions[0].start(), tips[0].start())
        self.assertRegex(
            html, r"<p>\s*" + re.escape(conclusion["text"]) + r"\s*</p>"
        )
        comparison_title = (
            response.context.get("comparison_title")
            or content.get("products_section", {}).get("comparison_title")
        )
        if comparison_title and response.context["products"]:
            comparisons = self.heading_matches(html, comparison_title)
            self.assertEqual(len(comparisons), 1)
            self.assertLess(comparisons[0].start(), conclusions[0].start())
            table_end = html.index("</table>", comparisons[0].end()) + len("</table>")
            # Only closing layout wrappers may separate the table and conclusion.
            between = html[table_end:conclusions[0].start()]
            self.assertNotRegex(between, r"<(?:h[1-6]|p|details|ul)\b")
            remaining = re.sub(r"<!--.*?-->|<[^>]+>", "", between, flags=re.S)
            self.assertEqual(remaining.strip(), "")
            after = html[conclusions[0].end():]
            self.assertEqual(after.count(conclusion["text"]), 1)

        for bullet in content.get("tips", {}).get("bullets", []):
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
            view_module = "products.pan_views" if path in CATEGORY_PATHS[-4:] else "products.views"
            with self.subTest(path=path), patch(
                view_module + ".render", side_effect=render_without_conclusion,
            ):
                response = self.client.get(path)
                self.assert_page_order(response)
                self.assertNotRegex(
                    response.content.decode(), r"<h2[^>]*>\s*</h2>"
                )

    def test_gourmet_conclusion_immediately_follows_comparison(self):
        response = self.client.get("/gourmetsets/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        conclusion = response.context["content"]["conclusion"]
        matches = self.heading_matches(html, conclusion["title"])
        self.assertEqual(len(matches), 1)
        table_end = html.index("</table>") + len("</table>")
        between = html[table_end:matches[0].start()]
        self.assertNotRegex(between, r"<(?:h[1-6]|p|details|ul)\b")
        self.assertEqual(re.sub(r"<[^>]+>", "", between).strip(), "")
        self.assertIn(conclusion["text"], html[matches[0].end():])
