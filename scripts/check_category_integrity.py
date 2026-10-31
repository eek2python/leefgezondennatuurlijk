"""Compare category responses with the checked-in templates before UI changes."""
import collections
import copy
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LeefNatuurlijkenGezond.settings")
import django
django.setup()
from django.conf import settings
from django.test import Client, override_settings


class Extract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.meta, self.links, self.scripts, self.h1, self.ids = [], [], [], [], [], []
        self.script, self.in_heading = None, False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "meta" or tag == "link" and attrs.get("rel") == "canonical":
            self.meta.append((tag, sorted(attrs.items())))
        if tag == "a":
            self.links.append(attrs.get("href", "").split("#")[0])
        if tag == "h1":
            self.in_heading = True
        if tag == "script":
            self.script = [] if attrs.get("type") == "application/ld+json" else False

    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_heading = False
        if tag == "script":
            if isinstance(self.script, list):
                self.scripts.append(json.loads("".join(self.script)))
            self.script = None

    def handle_data(self, data):
        if self.script is not None:
            if isinstance(self.script, list):
                self.script.append(data)
            return
        text = " ".join(data.split())
        if text:
            self.parts.append(text)
        if self.in_heading:
            self.h1.append(text)


def run():
    paths = [
        "/koekenpannen/", "/rvs-koekenpannen/?size=24",
        "/koolstofstalen-koekenpannen/", "/gietijzeren-koekenpannen/",
        "/hapjespannen/", "/wokpannen/", "/snijplanken/", "/airfryers/",
        "/airfryers/xl/", "/airfryers/dual/", "/vershoudcontainers/",
        "/vershoudcontainers/?uitvoering=3-delig&formaat=klein",
        "/pannensets/koekenpannensets/",
    ]
    original_templates = {}
    for name in subprocess.check_output(["git", "ls-files", "templates"], text=True).splitlines():
        if name.endswith(".html"):
            original_templates[name.removeprefix("templates/")] = subprocess.check_output(
                ["git", "show", "HEAD:" + name], text=True)
    config = copy.deepcopy(settings.TEMPLATES)
    config[0]["APP_DIRS"] = False
    config[0]["OPTIONS"]["loaders"] = [
        ("django.template.loaders.locmem.Loader", original_templates),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    client = Client(HTTP_HOST=os.environ["REPLIT_DEV_DOMAIN"])
    listing = client.get("/vershoudcontainers/").content.decode()
    detail = re.search(r'href="(/product/[^"]+/)"', listing)
    if detail:
        paths.append(detail.group(1))
    for path in paths:
        with override_settings(TEMPLATES=config):
            before = client.get(path)
        after = client.get(path)
        assert before.status_code == after.status_code == 200, path
        old, new = Extract(), Extract()
        old.feed(before.content.decode())
        new.feed(after.content.decode())
        assert old.h1 == new.h1, (path, "H1 changed")
        assert old.meta == new.meta, (path, "metadata changed")
        assert old.scripts == new.scripts, (path, "structured data changed")
        assert collections.Counter(old.links) == collections.Counter(new.links), (path, "links changed")
        missing = collections.Counter(t for t in old.parts if len(t) > 24) - collections.Counter(new.parts)
        assert not missing, (path, "missing editorial text", missing)
        assert len(new.ids) == len(set(new.ids)), (path, "duplicate IDs")
        if not path.startswith("/product/"):
            assert "productlijst" in new.ids, path
        print(path, ": H1, metadata, structured data, links and editorial text preserved")


if __name__ == "__main__":
    run()
