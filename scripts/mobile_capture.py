"""Capture responsive baselines/results; run with MOBILE_CAPTURE_STAGE=before|after."""
import json
import os
import subprocess
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("generated-artifacts/mobile-ux")
OUT.mkdir(parents=True, exist_ok=True)
CHROME = next(Path("/nix/store").glob("*playwright-chromium-*/chrome-linux/chrome"), None)
if not CHROME:
    CHROME = next(Path("/nix/store").glob("*playwright-chromium-*/chrome-linux64/chrome"))
BASE = "https://" + os.environ["REPLIT_DEV_DOMAIN"]

def snapshot(page):
    return page.evaluate("""() => ({
      width: innerWidth, overflow: document.documentElement.scrollWidth > innerWidth,
      bodyFont: getComputedStyle(document.body).fontSize,
      heroHeight: document.querySelector('.hero-banner')?.getBoundingClientRect().height,
      text: document.querySelector('#main').innerText,
      links: Array.from(document.querySelectorAll('#main a')).map(a=>[a.textContent.trim(),a.getAttribute('href')]),
      seo: Array.from(document.querySelectorAll('head meta:not([name="viewport"]),head link[rel="canonical"],script[type="application/ld+json"]')).map(e=>e.outerHTML),
      productCount: document.querySelectorAll('.product-block').length,
      tableCells: Array.from(document.querySelectorAll('.product-table tr')).map(row=>Array.from(row.children).map(cell=>cell.textContent.trim().replace(/\\s+/g,' '))),
      productMediaFloat: document.querySelector('.product-block .product-media,.product-block .image.right') ?
        getComputedStyle(document.querySelector('.product-block .product-media,.product-block .image.right')).cssFloat : null,
      sidebarWidth: document.querySelector('#sidebar').getBoundingClientRect().width
    })""")

if __name__ == "__main__":
    stage = os.environ.get("MOBILE_CAPTURE_STAGE", "before")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        page = browser.new_page()
        if stage == "before":
            original_css = subprocess.check_output(["git", "show", "HEAD:static/assets/css/main.css"])
            page.route("**/assets/css/main.css*", lambda route: route.fulfill(body=original_css, content_type="text/css"))
            original_js = subprocess.check_output(["git", "show", "HEAD:static/assets/js/main.js"])
            page.route("**/assets/js/main.js*", lambda route: route.fulfill(body=original_js, content_type="text/javascript"))
            page.route("**/assets/js/mobile-accessibility.js*", lambda route: route.fulfill(body="", content_type="text/javascript"))
            def original_document(route):
                response = route.fetch()
                html = response.text().replace('initial-scale=1"', 'initial-scale=1, user-scalable=no"')
                html = html.replace('<button type="button" class="opener" aria-expanded="false" aria-controls="menu-pannen">Koekenpannen</button>', '<span class="opener">Koekenpannen</span>')
                html = html.replace('<ul id="menu-pannen" inert>', '<ul>')
                route.fulfill(response=response, body=html)
            page.route("**/*", lambda route: original_document(route) if route.request.resource_type == "document" else route.fallback())
        cards_only = "--cards-only" in sys.argv
        result = json.loads((OUT / f"{stage}.json").read_text()) if cards_only else {}
        paths = ["/", "/koekenpannen/", "/vershoudcontainers/", "/airfryers/", "/blogs/"]
        for width in (390, 1440):
            page.set_viewport_size({"width": width, "height": 844 if width == 390 else 1000})
            for index, path in enumerate(paths):
                if cards_only and index not in (1, 2):
                    continue
                page.goto(BASE + path)
                page.wait_for_timeout(2800)
                key = f"{width}-{index}"
                result[key] = snapshot(page)
                page.screenshot(path=str(OUT / f"{stage}-{key}.jpg"))
                if index in (1, 2):
                    for _ in range(2):
                        page.locator(".product-block").first.evaluate("""e=>{
                          const bars=[...document.querySelectorAll('.format-sticky.is-visible:not(.is-too-tall),.storage-filters-sticky:not(.is-too-tall)')];
                          const height=Math.max(0,...bars.map(b=>b.getBoundingClientRect().height));
                          const menu=innerWidth<=1280?56:0;
                          scrollTo(0,e.getBoundingClientRect().top+scrollY-height-menu-12);
                        }""")
                        page.wait_for_timeout(350)
                    page.screenshot(path=str(OUT / f"{stage}-{key}-card.jpg"))
                if width == 390 and index == 1:
                    page.locator("#sidebar .toggle").click()
                    page.wait_for_timeout(550)
                    result[key]["menuExpanded"] = page.locator("#sidebar .toggle").get_attribute("aria-expanded")
                    result[key]["hiddenMenuInert"] = page.locator("#sidebar > .inner").evaluate("(e)=>e.inert")
                    page.screenshot(path=str(OUT / f"{stage}-menu.jpg"))
                    page.locator("#sidebar .toggle").click()
        (OUT / f"{stage}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
        browser.close()
