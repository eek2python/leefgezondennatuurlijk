"""Browser checks for Pannen navigation; uses optional requirements-browser.txt."""
import json
from pathlib import Path

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright


OUT = Path("generated-artifacts/pannen")
OUT.mkdir(parents=True, exist_ok=True)
PATHS = [
    "/pannen/", "/pannensets/", "/pannensets/koekenpannensets/",
    "/bak-braadsets/", "/kookpannensets/", "/complete-pannensets/",
]


def run():
    results = {"matrix": [], "menu": [], "interactions": [], "page_errors": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        page = browser.new_page()
        page.on("pageerror", lambda e: results["page_errors"].append(str(e)))

        def ready(path):
            response = page.goto(BASE + path)
            assert response.status == 200, (path, response.status)
            page.wait_for_timeout(180)

        for width in (320, 360, 390, 430, 768, 1024, 1440, 1920):
            page.set_viewport_size({"width": width, "height": 844 if width < 768 else 1000})
            for path in PATHS:
                ready(path)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), (width, path)
                assert page.locator("head link[rel=canonical]").count() == 1
                assert page.locator("h1").count() == 1
                assert page.locator("#main img").evaluate_all(
                    "imgs => imgs.every(i => !i.complete || i.naturalWidth > 0)"
                ), ("broken image", path)
                results["matrix"].append([width, path, "pass"])

            ready("/pannen/")
            toggle = page.locator("#sidebar .toggle")
            if width <= 1280:
                toggle.focus()
                page.keyboard.press("Enter")
                assert page.locator("#main").evaluate("e=>e.inert")
            opener = page.locator("#menu .opener")
            opener.focus()
            page.keyboard.press("Space")
            assert opener.get_attribute("aria-expanded") == "true"
            assert not page.locator("#menu-pannen").evaluate("e=>e.inert")
            assert page.locator("#menu-pannen .opener").count() == 0
            # Every submenu destination must be visible/reachable, never off-screen.
            for link in page.locator("#menu-pannen a").all():
                link.focus()
                link.scroll_into_view_if_needed()
                bounds = link.bounding_box()
                assert bounds["x"] >= -1 and bounds["x"] + bounds["width"] <= width + 1, (width, bounds)
                assert bounds["height"] >= 43.9, (width, "small target", bounds)
                assert bounds["y"] >= -1 and bounds["y"] + bounds["height"] <= page.viewport_size["height"] + 1, (width, "unreachable", bounds)
            page.screenshot(path=str(OUT / f"menu-{width}.jpg"))
            opener.focus()
            page.keyboard.press("Enter")
            assert opener.get_attribute("aria-expanded") == "false"
            assert page.locator("#menu-pannen").evaluate("e=>e.inert")
            page.keyboard.press("Enter")
            if width <= 1280:
                for _ in range(28):
                    page.keyboard.press("Tab")
                    assert page.evaluate("document.querySelector('#sidebar').contains(document.activeElement)")
                page.keyboard.press("Escape")
                assert toggle.get_attribute("aria-expanded") == "false"
                assert toggle.evaluate("e=>document.activeElement===e")
                toggle.click()
            # Real link navigation, not just a rendered href.
            page.locator("#menu-pannen a[href='/pannensets/']").click()
            page.wait_for_url("**/pannensets/")
            results["menu"].append([width, "keyboard, reachable links, collapse, navigation: pass"])
            print(f"{width}px: six pages and shared menu passed", flush=True)

        page.set_viewport_size({"width": 390, "height": 844})
        ready("/pannensets/koekenpannensets/")
        count_all = page.locator(".product-block").count()
        assert count_all == 44
        for key, count in (("keramisch", 18), ("rvs", 13), ("koolstofstaal", 8), ("gietijzer", 5)):
            page.locator(f".pan-material-selector a[href$='materiaal={key}']").click()
            page.wait_for_url(f"**/?materiaal={key}")
            assert page.locator(".product-block").count() == count
            assert page.locator(".pan-material-selector [aria-current=true]").count() == 1
            assert page.locator("head link[rel=canonical]").get_attribute("href").endswith("/pannensets/koekenpannensets/")
        page.locator(".pan-material-selector a").first.click()
        assert page.locator(".product-block").count() == count_all
        results["interactions"].append("all four server-rendered material filters, selected states and canonical: pass")

        ready("/bak-braadsets/")
        page.locator(".product-block h3 a").first.click()
        page.wait_for_url("**/product/**")
        assert page.locator(".breadcrumbs").inner_text().startswith("Home")
        assert "Pannensets" in page.locator(".breadcrumbs").inner_text()
        assert page.locator(".product-photo-notice").is_visible()
        results["interactions"].append("set card opens original detail, hierarchy and missing photo notice: pass")

        # Landscape and 200% text enlargement are separate from real-device tests.
        for viewport in ({"width": 844, "height": 390}, {"width": 390, "height": 844}):
            page.set_viewport_size(viewport)
            ready("/pannen/")
            page.add_style_tag(content="body { font-size: 200% !important; }")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            page.screenshot(path=str(OUT / f"large-text-{viewport['width']}.jpg"))
        results["interactions"].append("landscape and 200% body text enlargement: no page overflow")
        for path, name in (("/pannen/", "hub-mobile"), ("/pannensets/", "sets-mobile")):
            ready(path)
            page.screenshot(path=str(OUT / f"{name}.jpg"))
        browser.close()
    assert not results["page_errors"], results["page_errors"]
    (OUT / "browser-results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps({k: len(v) for k, v in results.items()}, indent=2))


if __name__ == "__main__":
    run()
