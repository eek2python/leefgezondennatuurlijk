"""Canonical, sitemap, social and structured-data consistency across the site."""

import json
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit
from xml.etree import ElementTree

from django.test import TestCase

from .site_urls import absolute_site_url


ORIGIN = "https://leefnatuurlijkengezond.nl"
LEGACY_HOST = "www.leefnatuurlijkengezond.nl"


class HeadMetadata(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.canonicals = []
        self.metadata = {}
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "canonical" in attrs.get("rel", "").split():
            self.canonicals.append(attrs.get("href"))
        if tag == "meta":
            key = attrs.get("property", attrs.get("name", "")).lower()
            self.metadata.setdefault(key, []).append(attrs.get("content", ""))
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])


class CanonicalURLTests(TestCase):
    def assert_canonical_page(self, path, canonical_path=None, host=None):
        response = self.client.get(
            path, secure=True, HTTP_HOST=host or "leefnatuurlijkengezond.nl"
        )
        self.assertEqual(response.status_code, 200, path)
        html = response.content.decode()
        head = HeadMetadata(html)
        expected = ORIGIN + (canonical_path or urlsplit(path).path)
        self.assertEqual(head.canonicals, [expected], path)
        self.assertEqual(head.metadata.get("og:url"), [expected], path)
        self.assertNotIn(LEGACY_HOST, html, path)
        self.assertNotIn("noindex", response.get("X-Robots-Tag", "").lower(), path)
        for robot_type in ("robots", "googlebot"):
            self.assertTrue(all(
                "noindex" not in value.lower()
                for value in head.metadata.get(robot_type, [])
            ), path)
        for image_key in ("og:image", "twitter:image"):
            for value in head.metadata.get(image_key, []):
                self.assertTrue(value.startswith(ORIGIN + "/"), (path, value))
        for link in head.links:
            if link.startswith(ORIGIN):
                link_path = urlsplit(link).path
                self.assertTrue(link_path.endswith("/") or "." in link_path,
                                (path, link))
        # Parse each JSON-LD block, including nested Product/Article/Breadcrumb URLs.
        for block in re.findall(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html, flags=re.S | re.I,
        ):
            data = json.loads(block)
            self.assertNotIn(LEGACY_HOST, json.dumps(data))
            self.assertNotIn("testserver", json.dumps(data))
            self.assertNotIn("preview.example", json.dumps(data))
        return response

    def test_representative_pages(self):
        for path in (
            "/", "/wokpannen/", "/koekenpannen/", "/rvs-koekenpannen/",
            "/koolstofstalen-koekenpannen/", "/gietijzeren-koekenpannen/",
            "/hapjespannen/", "/blogs/",
            "/blogs/koken-zonder-schadelijke-stoffen/",
            "/airfryers/", "/airfryers/xl/", "/airfryers/dual/",
        ):
            with self.subTest(path=path):
                self.assert_canonical_page(path)

    def test_filter_queries_keep_existing_base_canonical(self):
        for path, canonical in (
            ("/koekenpannen/?size=28", "/koekenpannen/"),
            ("/rvs-koekenpannen/?size=20_28", "/rvs-koekenpannen/"),
            ("/vershoudcontainers/?uitvoering=3-delig&formaat=klein",
             "/vershoudcontainers/"),
        ):
            with self.subTest(path=path):
                self.assert_canonical_page(path, canonical)

    def test_preview_and_www_request_hosts_do_not_change_public_metadata(self):
        for host in ("preview.example", LEGACY_HOST):
            with self.subTest(host=host):
                self.assert_canonical_page("/koekenpannen/", host=host)
                self.assert_canonical_page(
                    "/blogs/koken-zonder-schadelijke-stoffen/", host=host
                )
                response = self.client.get("/sitemap.xml", HTTP_HOST=host)
                self.assertNotIn(host, response.content.decode())

    def test_sitemap_is_unique_canonical_and_every_entry_is_indexable(self):
        response = self.client.get("/sitemap.xml", secure=True,
                                   HTTP_HOST="leefnatuurlijkengezond.nl")
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/xml", response["Content-Type"])
        root = ElementTree.fromstring(response.content)
        self.assertEqual(root.tag, "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")
        urls = [node.text for node in root.findall(".//{*}loc")]
        self.assertTrue(urls)
        self.assertEqual(len(urls), len(set(urls)))
        for path in (
            "/koekenpannen/", "/rvs-koekenpannen/",
            "/koolstofstalen-koekenpannen/", "/gietijzeren-koekenpannen/",
            "/wokpannen/", "/hapjespannen/", "/blogs/",
            "/snijplanken/", "/vershoudcontainers/", "/airfryers/",
            "/airfryers/xl/", "/airfryers/dual/",
        ):
            self.assertIn(ORIGIN + path, urls)
        from blogs.views import BLOG_TITLES
        for slug in BLOG_TITLES:
            self.assertIn(f"{ORIGIN}/blogs/{slug}/", urls)
        for url in urls:
            with self.subTest(url=url):
                parsed = urlsplit(url)
                self.assertEqual(parsed.scheme, "https")
                self.assertEqual(parsed.netloc, "leefnatuurlijkengezond.nl")
                self.assertFalse(parsed.query or parsed.fragment)
                self.assertTrue(parsed.path.endswith("/"))
                self.assertFalse(parsed.path.startswith("/admin/"))
                self.assert_canonical_page(parsed.path)

    def test_robots_sitemap_and_trailing_slash(self):
        response = self.client.get("/robots.txt", secure=True)
        self.assertEqual(response.status_code, 200)
        text = response.content.decode()
        self.assertIn("Allow: /", text)
        self.assertNotIn("Disallow:", text)
        self.assertIn(f"Sitemap: {ORIGIN}/sitemap.xml", text)
        self.assertNotIn(LEGACY_HOST, text)
        response = self.client.get("/wokpannen", secure=True)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/wokpannen/")

    def test_helper_and_templates_follow_single_configuration(self):
        with self.settings(SITE_URL="https://canonical.example"):
            self.assertEqual(absolute_site_url("/wokpannen/"),
                             "https://canonical.example/wokpannen/")
            response = self.client.get("/wokpannen/")
            self.assertEqual(HeadMetadata(response.content.decode()).canonicals,
                             ["https://canonical.example/wokpannen/"])
            response = self.client.get("/sitemap.xml")
            self.assertNotIn(ORIGIN, response.content.decode())
            self.assertIn("https://canonical.example/", response.content.decode())
        self.assertEqual(absolute_site_url("https://cdn.example/image.webp"),
                         "https://cdn.example/image.webp")
