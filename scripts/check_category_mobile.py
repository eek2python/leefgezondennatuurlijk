"""Browser checks for category layout, progressive enhancement and URL history."""
import json
import sys
from pathlib import Path

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright

OUT = Path("generated-artifacts/category-mobile")
PATHS = (
    "/koekenpannen/", "/snijplanken/", "/airfryers/", "/vershoudcontainers/",
    "/pannensets/koekenpannensets/",
)


def pin_at_products(page):
    page.locator("#productlijst").evaluate("e=>e.scrollIntoView()")
    page.wait_for_timeout(350)
    # The first jump enables the compact bar; account for its final height.
    page.locator("#productlijst").evaluate("e=>e.scrollIntoView()")
    page.wait_for_timeout(150)


def check_page(page, width, path):
    assert page.goto(BASE + path).status == 200
    page.wait_for_timeout(300)
    assert page.locator("h1").count() == 1
    assert page.locator("#productlijst").count() == 1
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), (width, path, "overflow")
    assert page.locator(".category-help").count()
    supplemental = page.locator(".category-help:not(.category-intro-more)")
    if supplemental.count():
        assert supplemental.first.evaluate(
            "e=>e.compareDocumentPosition(document.getElementById('productlijst'))&Node.DOCUMENT_POSITION_PRECEDING"
        ), (width, path, "explanation precedes products")
    assert page.locator(".category-help").evaluate_all(
        "es=>es.every(e=>e.open===" + ("false" if width <= 736 else "true") + ")"
    )
    cards = page.locator(".comparison-cards")
    assert cards.count(), (width, path, "comparison cards absent")
    for group in cards.all():
        assert group.is_visible() == (width <= 736)
        wrapper = group.locator("xpath=preceding-sibling::*[1]")
        assert wrapper.is_visible() == (width > 736)
        assert group.evaluate("""e=>{
            const rows=[...e.previousElementSibling.querySelectorAll('tbody > tr')];
            const cards=[...e.children];
            const text=n=>n.textContent.trim().replace(/\\s+/g,' ');
            return rows.length===cards.length && rows.every((row,i)=>{
                const card=cards[i];
                return text(row.children[0])===text(card.querySelector('h3')) &&
                    JSON.stringify([...row.querySelectorAll('a')].map(a=>[a.getAttribute('href'),a.rel,a.getAttribute('aria-label')]))===
                    JSON.stringify([...card.querySelectorAll('a')].map(a=>[a.getAttribute('href'),a.rel,a.getAttribute('aria-label')]));
            });
        }"""), (width, path, "card data or link mismatch")
    assert page.evaluate("""()=>{
        const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
        return ids.length===new Set(ids).size;
    }"""), (width, path, "duplicate IDs")
    pin_at_products(page)
    geometry = page.evaluate("""()=>{
        const bars=[...document.querySelectorAll('.format-sticky.is-visible,.storage-filters-sticky.is-stuck')];
        const bottom=Math.max(0,...bars.filter(e=>getComputedStyle(e).visibility!=='hidden').map(e=>e.getBoundingClientRect().bottom));
        return {top:document.getElementById('productlijst').getBoundingClientRect().top,bottom};
    }""")
    assert geometry["top"] >= geometry["bottom"] - 1, (width, path, geometry)
    if width <= 736 and supplemental.count():
        summary = page.locator(".category-help:not(.category-intro-more) > summary").first
        summary.focus()
        page.keyboard.press("Enter")
        assert summary.evaluate("e=>e.parentElement.open")
        page.keyboard.press("Enter")
        assert not summary.evaluate("e=>e.parentElement.open")
    if width in (320, 390, 1440):
        page.locator(".comparison-cards" if width <= 736 else ".table-wrapper").first.scroll_into_view_if_needed()
        page.screenshot(path=str(OUT / f"{width}-{path.strip('/').replace('/', '-')}.jpg"))


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        page = browser.new_page(reduced_motion="reduce")
        page.on("pageerror", lambda error: errors.append(str(error)))
        count = 0
        interactions_only = "--interactions-only" in sys.argv
        for width in (() if interactions_only else (320, 375, 390, 430, 768, 1024, 1440)):
            page.set_viewport_size({"width": width, "height": 844 if width < 737 else 1000})
            for path in PATHS:
                check_page(page, width, path)
                count += 1
            print(f"{width}px: five category layouts, help panels and comparisons passed", flush=True)
        for width in (() if interactions_only else (390, 1440)):
            page.set_viewport_size({"width": width, "height": 844})
            for path in ("/rvs-koekenpannen/", "/koolstofstalen-koekenpannen/",
                         "/gietijzeren-koekenpannen/", "/hapjespannen/", "/wokpannen/"):
                check_page(page, width, path)
                count += 1
        # Real navigation, not mocked URLs or synthetic history entries.
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(BASE + "/koekenpannen/?size=28#productlijst")
        page.wait_for_timeout(550)
        pin_at_products(page)
        link = page.locator('.format-sticky a[href="?size=24#productlijst"]')
        link.click()
        page.wait_for_url("**/?size=24#productlijst")
        page.wait_for_timeout(550)
        assert page.locator('[data-size-selector] [aria-current="page"]').inner_text().strip() == "24 cm"
        assert page.locator(".product-block").count() > 0
        assert "24" in page.locator("#productlijst").inner_text()
        assert page.locator("#productlijst").bounding_box()["y"] >= 56
        page.go_back()
        page.wait_for_timeout(400)
        assert "?size=28#productlijst" in page.url
        assert page.locator('[data-size-selector] [aria-current="page"]').inner_text().strip() == "28 cm"
        page.go_forward()
        page.wait_for_timeout(400)
        assert "?size=24#productlijst" in page.url
        assert page.locator('[data-size-selector] [aria-current="page"]').inner_text().strip() == "24 cm"
        # Existing product-detail links and variant controls must still function.
        page.goto(BASE + "/vershoudcontainers/")
        detail_url = page.locator('.product-block a[href^="/product/"]').first.get_attribute("href")
        page.goto(BASE + detail_url)
        assert page.locator("h1").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
        variant = page.locator("[data-variant-option]:visible").last
        if variant.count():
            variant.click()
            assert variant.get_attribute("aria-pressed") == "true"
        # No-JS keeps all editorial HTML, table and ordinary selection links usable.
        nojs = browser.new_context(java_script_enabled=False, viewport={"width": 390, "height": 844})
        plain = nojs.new_page()
        plain.goto(BASE + "/koekenpannen/")
        assert plain.locator(".category-help").first.get_attribute("open") is not None
        assert plain.locator(".product-table").first.is_visible()
        plain.locator('[data-size-selector] a[href="?size=24#productlijst"]').click()
        plain.wait_for_url("**/?size=24#productlijst")
        assert plain.locator('[data-size-selector] [aria-current="page"]').inner_text().strip() == "24 cm"
        assert plain.locator("#productlijst").is_visible()
        nojs.close()
        browser.close()
    assert not errors, errors
    (OUT / "results.json").write_text(json.dumps({"layouts": count, "javascriptErrors": errors}))
    print(f"{count} layouts; URL selection, history, product detail, keyboard and no-JS checks passed")


if __name__ == "__main__":
    run()
