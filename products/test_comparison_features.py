"""Feature cells must never silently prepend material information."""
from pathlib import Path
import re

from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.utils.html import escape


class ComparisonFeaturesTests(SimpleTestCase):
    def test_comparison_features_take_priority_with_escaping(self):
        html = render_to_string("partials/comparison_features.html", {
            "comparison_features": ["Belangrijk", "<kort>"],
            "features": ["Uitgebreide lijst"],
        }).strip()
        self.assertEqual(html, "Belangrijk · &lt;kort&gt;")

    def test_empty_comparison_features_fall_back_to_features(self):
        for value in (None, [], ""):
            with self.subTest(comparison_features=value):
                html = render_to_string("partials/comparison_features.html", {
                    "comparison_features": value,
                    "features": ["Inductie", "Ovenbestendig"],
                }).strip()
                self.assertEqual(html, "Inductie · Ovenbestendig")

    def test_comparison_features_work_without_general_features(self):
        html = render_to_string("partials/comparison_features.html", {
            "comparison_features": ["Compact"],
        }).strip()
        self.assertEqual(html, "Compact")

    def test_features_only_with_escaping(self):
        html = render_to_string("partials/comparison_features.html", {
            "features": ["Inductie", "Oven tot 220 °C", "<script>"],
            "material": "Niet toevoegen",
        }).strip()
        self.assertEqual(html, "Inductie · Oven tot 220 °C · &lt;script&gt;")

    def test_missing_features_do_not_fall_back_to_material(self):
        for features in (None, [], ""):
            with self.subTest(features=features):
                self.assertEqual(render_to_string("partials/comparison_features.html", {
                    "features": features, "material": "Aluminium",
                }).strip(), "—")

    def test_all_affected_templates_use_shared_features_only_cell(self):
        root = Path(__file__).resolve().parent.parent / "templates"
        names = (
            "koekenpannen.html", "hapjespannen.html", "wokpannen.html",
            "rvs-koekenpannen.html", "koolstofstaal-koekenpannen.html",
            "gietijzeren-koekenpannen.html", "airfryers.html",
            "snijplanken.html", "vershoudcontainers.html",
            "partials/pan_set_comparison.html",
        )
        for name in names:
            with self.subTest(template=name):
                source = (root / name).read_text()
                self.assertIn('"partials/comparison_features.html"', source)
                self.assertIn("comparison_features=", source)
                self.assertNotIn("product.material", source)


class ComparisonPageTests(TestCase):
    def test_rendered_feature_cells_match_source_without_material_prefix(self):
        paths = (
            "/koekenpannen/", "/hapjespannen/", "/wokpannen/",
            "/rvs-koekenpannen/", "/koolstofstalen-koekenpannen/",
            "/gietijzeren-koekenpannen/", "/snijplanken/",
            "/airfryers/", "/airfryers/xl/", "/airfryers/dual/",
            "/vershoudcontainers/", "/vershoudcontainers/?uitvoering=3-delig",
            "/pannensets/koekenpannensets/", "/kookpannensets/",
            "/complete-pannensets/", "/bak-braadsets/",
        )
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                table = re.search(
                    r'<table\b[^>]*class="[^"]*product-table[^"]*"[^>]*>(.*?)</table>',
                    html, re.S,
                )
                self.assertIsNotNone(table)
                self.assertIn("Kenmerken</th>", table[1])
                products = response.context["products"]
                if path.startswith("/vershoudcontainers/"):
                    products = [row["product"] for row in response.context["comparison_rows"]]
                for product in products:
                    selected = product.get("comparison_features") or product.get("features") or []
                    expected = str(escape(" · ".join(selected) or "—"))
                    self.assertRegex(table[1], r"<td>\s*" + re.escape(expected) + r"\s*</td>")
