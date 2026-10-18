"""Browser icon, social-image and production-static regression checks."""

import ast
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from urllib.parse import urlsplit
import struct

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase, override_settings


class HeadParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.metadata = {}
        self.static_paths = set()
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link":
            self.links.append(attrs)
        if tag == "meta":
            self.metadata[attrs.get("property") or attrs.get("name")] = attrs.get("content")
        for name in ("src", "href"):
            value = attrs.get(name, "")
            path = urlsplit(value).path
            if path.startswith("/static/"):
                self.static_paths.add(path)


@override_settings(DEBUG=False, WHITENOISE_USE_FINDERS=True)
class BrowserAssetsTests(TestCase):
    def test_homepage_has_one_favicon_and_one_apple_icon(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        head = HeadParser(response.content.decode())
        icons = [link for link in head.links if link.get("rel") == "icon"]
        apple = [link for link in head.links if link.get("rel") == "apple-touch-icon"]
        self.assertEqual(len(icons), 1)
        self.assertEqual(icons[0]["href"], "/static/favicon.ico")
        self.assertEqual(len(apple), 1)
        self.assertEqual(apple[0]["href"], "/static/apple-touch-icon.png")
        self.assertEqual(apple[0]["sizes"], "180x180")
        for path in head.static_paths:
            with self.subTest(path=path):
                self.assertIsNotNone(finders.find(path.removeprefix("/static/")))

    def test_rvs_social_images_use_the_existing_category_thumbnail(self):
        response = self.client.get("/rvs-koekenpannen/")
        self.assertEqual(response.status_code, 200)
        metadata = HeadParser(response.content.decode()).metadata
        expected = settings.SITE_URL + "/static/images/thumbnails/rvs-koekenpannen.webp"
        self.assertEqual(metadata["og:image"], expected)
        self.assertEqual(metadata["twitter:image"], expected)
        self.assertIsNotNone(finders.find(urlsplit(expected).path.removeprefix("/static/")))
        self.assertNotIn("rvs-koekenpannen.jpg", response.content.decode())

    def test_important_pages_and_real_404_are_preserved(self):
        for path in (
            "/", "/koekenpannen/", "/rvs-koekenpannen/", "/koolstofstalen-koekenpannen/",
            "/gietijzeren-koekenpannen/", "/hapjespannen/", "/wokpannen/",
            "/snijplanken/", "/airfryers/", "/airfryers/xl/", "/airfryers/dual/",
            "/vershoudcontainers/", "/over-ons/", "/hoe-wij-beoordelen/",
            "/privacy/", "/blogs/", "/sitemap.xml", "/robots.txt",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        response = self.client.get("/this-page-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("Location", response)
        self.assertNotIn(b"Using the URLconf", response.content)

    def test_unknown_host_is_rejected(self):
        with self.assertLogs("django.security.DisallowedHost", level="ERROR"):
            response = self.client.get("/", HTTP_HOST="untrusted.example")
        self.assertEqual(response.status_code, 400)


@override_settings(
    DEBUG=False, WHITENOISE_USE_FINDERS=False, WHITENOISE_AUTOREFRESH=False,
)
class ProductionStaticTests(SimpleTestCase):
    def test_collected_assets_and_root_icons_without_redirects(self):
        # Exercise real collectstatic and cached production WhiteNoise, not
        # Django's development static-file handler or a static finder fallback.
        with TemporaryDirectory() as directory, override_settings(STATIC_ROOT=directory):
            call_command("collectstatic", interactive=False, verbosity=0)
            client = Client()
            contents = {}
            for path in (
                "/favicon.ico", "/apple-touch-icon.png",
                "/apple-touch-icon-precomposed.png",
                "/static/favicon.ico", "/static/apple-touch-icon.png",
                "/static/images/thumbnails/rvs-koekenpannen.webp",
            ):
                with self.subTest(path=path):
                    response = client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertNotIn("Location", response)
                    self.assertTrue(response["Content-Type"].startswith("image/"))
                    contents[path] = b"".join(response.streaming_content)
                    response.close()
            self.assertEqual(contents["/favicon.ico"], contents["/static/favicon.ico"])
            self.assertTrue(contents["/favicon.ico"].startswith(b"\x00\x00\x01\x00"))
            png = contents["/apple-touch-icon.png"]
            self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertEqual(struct.unpack(">II", png[16:24]), (180, 180))
            self.assertEqual(png, contents["/apple-touch-icon-precomposed.png"])
            self.assertEqual(png, contents["/static/apple-touch-icon.png"])

            head = HeadParser(client.get("/").content.decode())
            for path in head.static_paths:
                with self.subTest(homepage_asset=path):
                    response = client.get(path)
                    self.assertEqual(response.status_code, 200)
                    response.close()
            for path in ("/this-page-does-not-exist/", "/.env", "/.git/config"):
                with self.subTest(path=path):
                    self.assertEqual(client.get(path).status_code, 404)

    def test_public_root_contains_only_expected_icon_aliases(self):
        root = Path(settings.WHITENOISE_ROOT)
        targets = {
            "favicon.ico": "favicon.ico",
            "apple-touch-icon.png": "apple-touch-icon.png",
            "apple-touch-icon-precomposed.png": "apple-touch-icon.png",
        }
        self.assertEqual({path.name for path in root.iterdir()}, set(targets))
        for name, target in targets.items():
            with self.subTest(name=name):
                path = root / name
                self.assertTrue(path.is_symlink())
                self.assertEqual(path.resolve(), (settings.BASE_DIR / "static" / target).resolve())


class ProductionDefaultsTests(SimpleTestCase):
    def runtime_config(self, environment):
        # Evaluate only the real DEBUG/host settings, without reading dotenv,
        # credentials, database configuration or changing the process environment.
        tree = ast.parse((settings.BASE_DIR / "LeefNatuurlijkenGezond/settings.py").read_text())
        nodes = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id in {"DEBUG", "ALLOWED_HOSTS"}
                for target in node.targets
            ):
                nodes.append(node)
            elif isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == "_host":
                nodes.append(node)
        namespace = {"os": SimpleNamespace(getenv=environment.get)}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "<runtime config>", "exec"), namespace)
        return namespace

    def test_debug_is_false_when_missing_or_not_explicitly_enabled(self):
        for value in (None, "", "false", "False", "0", "no", "off", "unexpected"):
            with self.subTest(value=value):
                environment = {} if value is None else {"DEBUG": value}
                self.assertIs(self.runtime_config(environment)["DEBUG"], False)

    def test_local_debug_can_be_explicitly_enabled(self):
        for value in ("true", "True", " TRUE ", "1", "yes", "on"):
            with self.subTest(value=value):
                self.assertIs(self.runtime_config({"DEBUG": value})["DEBUG"], True)

    def test_hosts_cover_production_and_explicit_preview_hosts_without_wildcard(self):
        hosts = self.runtime_config({
            "REPLIT_DEV_DOMAIN": "example.replit.dev",
            "RENDER_EXTERNAL_HOSTNAME": "example.onrender.com",
            "ALLOWED_HOSTS": " extra.example.com, leefnatuurlijkengezond.nl, ",
        })["ALLOWED_HOSTS"]
        for host in (
            "leefnatuurlijkengezond.nl", "www.leefnatuurlijkengezond.nl",
            "localhost", "127.0.0.1", "[::1]",
            "example.replit.dev", "example.onrender.com", "extra.example.com",
        ):
            self.assertIn(host, hosts)
        self.assertNotIn("*", hosts)
        self.assertNotIn("", hosts)
        self.assertEqual(len(hosts), len(set(hosts)))
