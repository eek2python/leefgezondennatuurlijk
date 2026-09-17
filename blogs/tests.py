from django.test import TestCase
from django.contrib.staticfiles import finders


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
            f'<link rel="canonical" href="https://www.leefnatuurlijkengezond.nl{self.path}">',
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
            f"https://www.leefnatuurlijkengezond.nl{self.path}",
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
