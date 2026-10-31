"""Check single-line, readable mobile action buttons without page overflow."""
import json
from pathlib import Path

from mobile_capture import BASE, CHROME
from check_comparison_tables import PATHS
from playwright.sync_api import sync_playwright


OUT = Path("generated-artifacts/mobile-buttons")


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {"pages": [], "errors": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        page = browser.new_page()
        page.on("pageerror", lambda error: results["errors"].append(str(error)))
        for width in (320, 390, 430, 736):
            page.set_viewport_size({"width": width, "height": 900})
            for path in ["/", "/pannen/", "/pannensets/", "/koekenpannen/?size=30", *PATHS]:
                assert page.goto(BASE + path).status == 200
                page.wait_for_timeout(180)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), (width, path)
                bad = page.locator("#main .button, #main button").evaluate_all("""ls => ls.filter(e => {
                    if (!e.getClientRects().length) return false;
                    const s = getComputedStyle(e), r = e.getBoundingClientRect();
                    const range = document.createRange();
                    range.selectNodeContents(e);
                    const lines = new Set(Array.from(range.getClientRects())
                        .filter(r => r.width > 0).map(r => Math.round(r.top)));
                    return s.whiteSpace !== 'nowrap' || e.scrollWidth > e.clientWidth + 1 ||
                        r.height < 44 || lines.size > 1;
                }).map(e => e.textContent.trim())""")
                assert not bad, (width, path, bad)
                results["pages"].append([width, path, "pass"])
                if width == 390 and path == "/koekenpannen/?size=30":
                    button = page.locator(".product-block a.button").first
                    button.scroll_into_view_if_needed()
                    page.screenshot(path=str(OUT / "product-button-phone.jpg"))
            print(f"{width}px: all action buttons single-line, no overflow", flush=True)
        page.set_viewport_size({"width": 390, "height": 900})
        page.goto(BASE + "/gietijzeren-koekenpannen/?size=Pannensets")
        page.add_style_tag(content="html { font-size: 200% !important; }")
        page.wait_for_timeout(300)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        assert page.locator("#main .button").evaluate_all(
            "ls=>ls.filter(e=>e.getClientRects().length).every(e=>e.scrollWidth<=e.clientWidth+1)"
        )
        action = page.locator(".product-block a.button").first
        assert action.text_content().strip() == "Bekijk prijs →"
        href, aria = action.get_attribute("href"), action.get_attribute("aria-label")
        # Variant controllers replace textContent and link classification.
        action.evaluate("""e => {
            e.textContent = 'Bekijk productspecificaties →';
            e.setAttribute('data-link-type', 'official');
        }""")
        page.wait_for_timeout(150)
        assert action.text_content().strip() in ("Specificaties →", "Productinformatie →")
        assert action.get_attribute("href") == href
        assert action.get_attribute("aria-label") == aria
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.wait_for_timeout(400)
        assert action.text_content().strip() == "Bekijk productspecificaties →"
        results["enlarged_text_and_dynamic_labels"] = "pass"
        browser.close()
    assert not results["errors"]
    (OUT / "results.json").write_text(json.dumps(results, indent=2))
    print(f"{len(results['pages'])} page checks passed")


if __name__ == "__main__":
    run()
