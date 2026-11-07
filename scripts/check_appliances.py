"""Responsive browser checks for the existing menus and appliance integration."""
import json
from pathlib import Path

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright

OUT = Path("generated-artifacts/appliances")
PATHS = ("/keukenapparatuur/", "/airfryers/", "/gourmetsets/")


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    errors, checks = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        page = browser.new_page(reduced_motion="reduce")
        page.on("pageerror", lambda error: errors.append(str(error)))
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            for path in PATHS:
                assert page.goto(BASE + path).status == 200
                page.wait_for_timeout(250)
                assert page.locator("h1").count() == 1
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), (width, path)
                assert page.locator('link[rel="canonical"]').get_attribute("href") == "https://leefnatuurlijkengezond.nl" + path
                if path == "/gourmetsets/":
                    assert page.locator(".product-block").count() == 6
                    specs = page.locator(".product-specifications").first
                    specs.locator("summary").focus()
                    page.keyboard.press("Enter")
                    assert specs.get_attribute("open") is not None
                    assert "PFAS-vrij: bakplaat" in specs.inner_text()
                    assert "PFAS-vrij: pannetjes" in specs.inner_text()
                    specs.locator("summary").press("Enter")
                    assert page.locator(".product-block .product-badge").count() == 3
                    comparison = page.locator(".compact-comparison-scroll")
                    source = page.locator(".table-wrapper")
                    assert comparison.is_visible() == (width <= 736)
                    assert source.is_visible() == (width > 736)
                    if width <= 736:
                        assert comparison.locator("tbody tr").count() == 6
                        assert comparison.locator("thead th").all_text_contents() == [
                            "Product", "Oordeel", "Prijs", "Pannetjes", "Vermogen",
                            "Type plaat", "Temperatuurregeling",
                            "PFAS-vrij: bakplaat", "PFAS-vrij: pannetjes",
                        ]
                        # Additional mobile cells must match the desktop source exactly.
                        assert comparison.locator("table").evaluate("""mobile => {
                            const source = document.querySelector('.product-table');
                            const clean = e => e.textContent.replace(/\\s+/g, ' ').trim();
                            const headers = [...source.tHead.rows[0].cells].map(clean);
                            return [...mobile.tBodies[0].rows].every((row, i) =>
                                [...mobile.tHead.rows[0].cells].slice(5).every((header, j) =>
                                    clean(row.cells[j + 5]) === clean(
                                        source.tBodies[0].rows[i].cells[headers.indexOf(clean(header))])));
                        }""")
                        assert "niet van toepassing" in comparison.inner_text()
                        assert page.locator(".compact-comparison-hint").is_visible()
                        assert not comparison.locator(".button,button,[rel~='sponsored']").count()
                        comparison.scroll_into_view_if_needed()
                        first = comparison.locator("tbody th").first
                        x = first.bounding_box()["x"]
                        comparison.evaluate("e=>e.scrollLeft=e.scrollWidth")
                        assert abs(first.bounding_box()["x"] - x) < 1
                        comparison.evaluate("e=>e.scrollLeft=0")
                    page.evaluate("scrollTo(0,0)")
                    page.screenshot(path=str(OUT / f"gourmet-{width}.jpg"))
                if path == "/keukenapparatuur/":
                    assert page.locator(".category-card").count() == 2
                    page.screenshot(path=str(OUT / f"hub-{width}.jpg"))
                checks.append([width, path, "pass"])
            # Reuse the site's existing mobile overlay / desktop sidebar.
            toggle = page.locator("#sidebar .toggle")
            if toggle.is_visible() and toggle.get_attribute("aria-expanded") != "true":
                toggle.click()
                page.wait_for_timeout(300)
            pans = page.locator('[aria-controls="menu-pannen"]')
            appliances = page.locator('[aria-controls="menu-keukenapparatuur"]')
            if pans.get_attribute("aria-expanded") != "true":
                pans.click()
            assert page.locator("#menu-pannen a").count() == 13
            assert pans.get_attribute("aria-expanded") == "true"
            appliances.focus()
            page.keyboard.press("Enter")
            assert appliances.get_attribute("aria-expanded") == "true"
            assert pans.get_attribute("aria-expanded") == "false"
            assert not page.locator("#menu-pannen").is_visible()
            menu = page.locator("#menu-keukenapparatuur")
            assert menu.is_visible() and menu.get_attribute("inert") is None
            assert menu.locator("a").all_text_contents() == ["Alle keukenapparatuur", "Airfryers", "Gourmetsets"]
            assert page.locator('#menu a[href="/airfryers/"]').count() == 1
            assert not menu.locator("ul").count()
            assert menu.evaluate("""e=>{
                const r=e.getBoundingClientRect();
                return r.left>=0 && r.right<=innerWidth+1;
            }""")
            assert menu.locator("a").evaluate_all("es=>es.every(e=>e.getBoundingClientRect().height>=44)")
            page.screenshot(path=str(OUT / f"menu-{width}.jpg"))
            appliances.focus()
            page.keyboard.press("Tab")
            assert page.evaluate("document.activeElement.getAttribute('href')") == "/keukenapparatuur/"
            page.keyboard.press("Enter")
            page.wait_for_url("**/keukenapparatuur/")
            # Actual card navigation, not a synthetic request.
            page.locator('.category-card[href="/gourmetsets/"]').click()
            page.wait_for_url("**/gourmetsets/")
            assert page.locator(".product-block").count() == 6
            print(f"{width}px: hub, airfryers, gourmet data, menu and navigation passed", flush=True)
        browser.close()
    assert not errors, errors
    (OUT / "results.json").write_text(json.dumps({"layouts": checks, "javascriptErrors": errors}, indent=2))


if __name__ == "__main__":
    run()
