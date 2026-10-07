"""Read-only SEO checks against the public origin declared in Django settings.

Run from the project root: python scripts/check_live_seo.py
Does not start Django, access a database, or change deployment settings.
"""

import ast
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT / "LeefNatuurlijkenGezond/settings.py").read_text())
ORIGIN = next(
    ast.literal_eval(node.value)
    for node in tree.body
    if isinstance(node, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "SITE_URL" for t in node.targets)
).rstrip("/")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect())


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "LiveSEOAudit/1.0"})
    try:
        response = OPENER.open(request, timeout=45)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.code, dict(response.headers.items()), response.read().decode("utf-8")


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.og_url = []
        self.robots = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonical.append(attrs.get("href"))
        if tag == "meta":
            if attrs.get("property", "").lower() == "og:url":
                self.og_url.append(attrs.get("content"))
            if attrs.get("name", "").lower() in {"robots", "googlebot", "bingbot"}:
                self.robots.append(attrs.get("content", ""))


def headers_lower(headers):
    return {key.lower(): value for key, value in headers.items()}


def check_page(url):
    try:
        status, headers, body = fetch(url)
        metadata = Metadata()
        metadata.feed(body)
        headers = headers_lower(headers)
        directives = metadata.robots + [headers.get("x-robots-tag", "")]
        issues = []
        if status != 200:
            issues.append(f"HTTP {status}")
        if metadata.canonical != [url]:
            issues.append("Canonical count/value mismatch")
        if metadata.og_url != [url]:
            issues.append("og:url count/value mismatch")
        if any(re.search(r"\b(noindex|none)\b", value.lower())
               for value in directives):
            issues.append("Indexing blocked by directive")
        return {"url": url, "status": status, "canonical": metadata.canonical,
                "og_url": metadata.og_url, "robots_meta": metadata.robots,
                "x_robots_tag": headers.get("x-robots-tag"), "issues": issues}
    except Exception as error:
        return {"url": url, "issues": [str(error)]}


def redirect_chain(url):
    hops = []
    seen = set()
    for _ in range(6):
        if url in seen:
            return {"hops": hops, "error": "Redirect loop"}
        seen.add(url)
        try:
            status, headers, _ = fetch(url)
        except Exception as error:
            return {"hops": hops, "error": str(error)}
        location = headers_lower(headers).get("location")
        hops.append({"url": url, "status": status, "location": location})
        if status not in {301, 302, 303, 307, 308} or not location:
            return {"hops": hops}
        url = urljoin(url, location)
    return {"hops": hops, "error": "Too many redirects"}


def main():
    sitemap_status, sitemap_headers, sitemap_body = fetch(ORIGIN + "/sitemap.xml")
    xml = ET.fromstring(sitemap_body)
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    urls = [node.text for node in xml.findall(f"{namespace}url/{namespace}loc")]
    counts = Counter(urls)
    robots_status, _, robots_body = fetch(ORIGIN + "/robots.txt")
    robots = RobotFileParser()
    robots.parse(robots_body.splitlines())
    product_urls = [url for url in urls if urlsplit(url).path.startswith("/product/")]
    if not product_urls:
        raise RuntimeError("No /product/ URLs in sitemap; inspect actual product routes")
    selected = [url for url in urls if url not in product_urls] + product_urls[:1]
    with ThreadPoolExecutor(max_workers=3) as pool:
        pages = list(pool.map(check_page, selected))
    for page in pages:
        page["robots_allowed"] = {
            agent: robots.can_fetch(agent, page["url"])
            for agent in ("*", "Googlebot", "Bingbot")
        }
        if not all(page["robots_allowed"].values()):
            page["issues"].append("Blocked by robots.txt")
    host = urlsplit(ORIGIN).netloc
    redirect_tests = []
    for path in ("/", "/wokpannen/?seo_audit=1&bron=live%20test"):
        for scheme, hostname in (("https", host), ("https", "www." + host),
                                 ("http", host), ("http", "www." + host)):
            url = f"{scheme}://{hostname}{path}"
            chain = redirect_chain(url)
            hops = chain["hops"]
            chain.update({"input": url, "expected_final": ORIGIN + path,
                          "passed": not chain.get("error") and bool(hops)
                          and hops[-1]["url"] == ORIGIN + path
                          and hops[-1]["status"] == 200
                          and all(h["status"] in {301, 308} for h in hops[:-1])})
            redirect_tests.append(chain)
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "origin": ORIGIN,
        "scope": "All non-product sitemap pages and one product; not all products fetched",
        "sitemap": {
            "status": sitemap_status,
            "content_type": headers_lower(sitemap_headers).get("content-type"),
            "valid_urlset": xml.tag == namespace + "urlset",
            "count": len(urls), "product_count": len(product_urls),
            "duplicates": [url for url, count in counts.items() if count > 1],
            "invalid_origin_or_query": [
                url for url in urls
                if not url.startswith(ORIGIN + "/")
                or urlsplit(url).query or urlsplit(url).fragment
            ],
        },
        "robots": {"status": robots_status, "body": robots_body,
                   "sitemaps": robots.site_maps()},
        "pages": pages, "redirects": redirect_tests,
        "trailing_slash": redirect_chain(ORIGIN + "/wokpannen"),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    passed = (
        sitemap_status == 200
        and report["sitemap"]["valid_urlset"]
        and bool(urls)
        and not report["sitemap"]["duplicates"]
        and not report["sitemap"]["invalid_origin_or_query"]
        and robots_status == 200
        and robots.site_maps() == [ORIGIN + "/sitemap.xml"]
        and all(not page["issues"] for page in pages)
        and all(chain["passed"] for chain in redirect_tests)
    )
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
