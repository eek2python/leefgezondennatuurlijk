import json
import re
from urllib.parse import urlparse
from xml.etree import ElementTree

from django.test import TestCase
from django.contrib.staticfiles import finders

from blogs.views import BLOG_ARTICLE_META, BLOG_TITLES


class KoolstofstaalVsGietijzerBlogTests(TestCase):
    slug = "koolstofstaal-vs-gietijzer-koekenpan"
    path = f"/blogs/{slug}/"

    def test_blog_page_renders_with_seo_and_internal_links(self):
        response = self.client.get(self.path)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Koolstofstaal vs gietijzer: welke koekenpan past het beste bij jou?",
        )
        self.assertContains(
            response,
            f'<link rel="canonical" href="https://leefnatuurlijkengezond.nl{self.path}">',
            html=True,
        )
        self.assertContains(response, '"@type": "Article"')
        self.assertContains(response, "/koolstofstalen-koekenpannen/")
        self.assertContains(response, "/gietijzeren-koekenpannen/")

    def test_blog_is_linked_from_overview_and_category_articles(self):
        overview = self.client.get("/blogs/")
        carbon_steel = self.client.get("/koolstofstalen-koekenpannen/")

        self.assertContains(overview, self.path)
        self.assertContains(
            overview,
            "images/thumbnails/koolstofstaal-vs-gietijzer-koekenpan.webp",
        )
        self.assertContains(carbon_steel, self.path)

    def test_blog_is_in_sitemap(self):
        response = self.client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f"https://leefnatuurlijkengezond.nl{self.path}",
        )

    def test_blog_images_exist(self):
        self.assertIsNotNone(
            finders.find(
                "images/blogs/koolstofstaal-vs-gietijzer-koekenpan.webp"
            )
        )
        self.assertIsNotNone(
            finders.find(
                "images/thumbnails/koolstofstaal-vs-gietijzer-koekenpan.webp"
            )
        )


class AllBlogSeoTests(TestCase):
    def test_every_blog_has_complete_unique_seo_markup(self):
        for slug in BLOG_TITLES:
            with self.subTest(slug=slug):
                path = f"/blogs/{slug}/"
                response = self.client.get(path)
                html = response.content.decode()

                self.assertEqual(response.status_code, 200)
                self.assertEqual(html.count("<h1"), 1)
                self.assertEqual(html.count('name="description"'), 1)
                self.assertEqual(html.count('rel="canonical"'), 1)
                self.assertIn(
                    f'<link rel="canonical" href="https://leefnatuurlijkengezond.nl{path}">',
                    html,
                )
                self.assertEqual(html.count('"@type": "Article"'), 1)
                self.assertEqual(html.count('"@type": "BreadcrumbList"'), 1)
                self.assertEqual(html.count('property="og:title"'), 1)
                self.assertEqual(html.count('name="twitter:title"'), 1)

                schemas = re.findall(
                    r'<script type="application/ld\+json">(.*?)</script>',
                    html,
                    flags=re.DOTALL,
                )
                parsed_schemas = [json.loads(schema) for schema in schemas]
                article_schema = next(
                    schema
                    for schema in parsed_schemas
                    if schema.get("@type") == "Article"
                )
                canonical = f"https://leefnatuurlijkengezond.nl{path}"
                self.assertEqual(article_schema["mainEntityOfPage"], canonical)
                self.assertEqual(
                    article_schema["image"],
                    (
                        "https://leefnatuurlijkengezond.nl"
                        f"{BLOG_ARTICLE_META[slug]['image']}"
                    ),
                )
                self.assertTrue(
                    any(
                        schema.get("@type") == "BreadcrumbList"
                        for schema in parsed_schemas
                    )
                )

    def test_every_blog_is_linked_from_overview_and_sitemap(self):
        overview = self.client.get("/blogs/").content.decode()
        sitemap_response = self.client.get("/sitemap.xml")
        sitemap = sitemap_response.content.decode()

        for slug in BLOG_TITLES:
            with self.subTest(slug=slug):
                path = f"/blogs/{slug}/"
                self.assertIn(path, overview)
                self.assertEqual(
                    sitemap.count(
                        f"https://leefnatuurlijkengezond.nl{path}"
                    ),
                    1,
                )

        root = ElementTree.fromstring(sitemap_response.content)
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        blog_urls = [
            loc.text
            for loc in root.findall("sm:url/sm:loc", namespace)
            if "/blogs/" in loc.text and not loc.text.endswith("/blogs/")
        ]
        expected_urls = [
            f"https://leefnatuurlijkengezond.nl/blogs/{slug}/"
            for slug in BLOG_TITLES
        ]
        self.assertCountEqual(blog_urls, expected_urls)
        for url in blog_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(urlparse(url).path).status_code, 200)

    def test_internal_blog_links_resolve(self):
        linked_slugs = set()
        for slug in BLOG_TITLES:
            response = self.client.get(f"/blogs/{slug}/")
            linked_slugs.update(
                re.findall(r'href="/blogs/([^"/]+)/"', response.content.decode())
            )

        self.assertTrue(linked_slugs)
        self.assertEqual(linked_slugs - set(BLOG_TITLES), set())
        for slug in linked_slugs:
            with self.subTest(slug=slug):
                self.assertEqual(self.client.get(f"/blogs/{slug}/").status_code, 200)

    def test_article_social_images_exist(self):
        for slug, meta in BLOG_ARTICLE_META.items():
            with self.subTest(slug=slug):
                self.assertIsNotNone(finders.find(meta["image"].removeprefix("/static/")))

    def test_unknown_blog_slug_is_404(self):
        self.assertEqual(
            self.client.get("/blogs/dit-artikel-bestaat-niet/").status_code,
            404,
        )
