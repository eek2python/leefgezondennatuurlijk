"""Regression checks for readable mobile comparison tables."""
import json
from pathlib import Path

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright


OUT = Path("generated-artifacts/comparison-tables")
PATHS = [
    "/gietijzeren-koekenpannen/?size=Pannensets",
    "/koekenpannen/", "/rvs-koekenpannen/", "/koolstofstalen-koekenpannen/",
    "/hapjespannen/", "/wokpannen/", "/snijplanken/", "/airfryers/",
    "/vershoudcontainers/", "/pannensets/koekenpannensets/",
    "/bak-braadsets/", "/kookpannensets/", "/complete-pannensets/",
]


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {"pages": [], "page_errors": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        page = browser.new_page()
        page.on("pageerror", lambda error: results["page_errors"].append(str(error)))
        for width in (320, 390, 430, 736, 768, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            for path in PATHS:
                assert page.goto(BASE + path).status == 200
                page.wait_for_timeout(150)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), (width, path)
                table = page.locator(".table-wrapper table.product-table").first
                assert table.count() == 1, path
                if width <= 736:
                    assert table.evaluate("e => e.getBoundingClientRect().width >= 959")
                    cells = table.locator("tbody tr").first.locator("td, th")
                    assert cells.first.evaluate("e => e.getBoundingClientRect().width >= 180")
                    assert cells.last.evaluate("e => e.getBoundingClientRect().width >= 220")
                    buttons = table.locator(".button")
                    assert buttons.evaluate_all("""ls => ls.every(e => {
                        const r = e.getBoundingClientRect(), s = getComputedStyle(e);
                        return r.width >= 180 && r.height >= 44 &&
                            s.overflowWrap === 'normal' && s.wordBreak === 'normal' &&
                            e.scrollWidth <= e.clientWidth + 1 && r.height < 130;
                    })"""), (width, path, "unreadable button")
                    # Verify each word occupies a single text line (not broken into letters).
                    assert buttons.evaluate_all("""ls => ls.every(e => {
                        const walker = document.createTreeWalker(e, NodeFilter.SHOW_TEXT);
                        let node;
                        while ((node = walker.nextNode())) {
                            const words = node.textContent.matchAll(/\\S+/g);
                            for (const word of words) {
                                const range = document.createRange();
                                range.setStart(node, word.index);
                                range.setEnd(node, word.index + word[0].length);
                                if (range.getClientRects().length > 1) return false;
                            }
                        }
                        return true;
                    })"""), (width, path, "split word")
                    if width <= 480:
                        assert cells.first.evaluate("e => getComputedStyle(e).position === 'static'")
                        wrapper = table.locator("..")
                        wrapper.evaluate("e => e.scrollLeft = e.scrollWidth")
                        assert cells.last.evaluate("""e => {
                            const c = e.getBoundingClientRect();
                            const w = e.closest('.table-wrapper').getBoundingClientRect();
                            return c.left >= w.left - 1 && c.right <= w.right + 1;
                        }"""), (width, path, "action column obscured")
                        if width == 390 and path == PATHS[0]:
                            table.scroll_into_view_if_needed()
                            page.screenshot(path=str(OUT / "phone-actions.jpg"))
                            wrapper.evaluate("e => e.scrollLeft = 0")
                            page.screenshot(path=str(OUT / "phone-products.jpg"))
                results["pages"].append([width, path, "pass"])
            print(f"{width}px: {len(PATHS)} comparison tables passed", flush=True)

        # Increased text size must not make buttons break words or widen the page.
        page.set_viewport_size({"width": 390, "height": 900})
        page.goto(BASE + PATHS[0])
        page.add_style_tag(content="html { font-size: 200% !important; }")
        # Let responsive label fitting settle after the text-size change.
        page.wait_for_timeout(250)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        assert page.locator("table.product-table .button").evaluate_all(
            "ls => ls.every(e => e.scrollWidth <= e.clientWidth + 1)"
        )
        results["large_text"] = "pass"
        browser.close()
    assert not results["page_errors"]
    (OUT / "results.json").write_text(json.dumps(results, indent=2))
    print(f"{len(results['pages'])} page checks passed; no JavaScript errors")


if __name__ == "__main__":
    run()
