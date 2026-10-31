"""Compact comparisons: source fidelity, sticky columns and unchanged product cards."""
import json
import subprocess
import sys
from pathlib import Path

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright

OUT = Path("generated-artifacts/compact-comparisons")
PATHS = (
    "/koekenpannen/", "/rvs-koekenpannen/", "/koolstofstalen-koekenpannen/",
    "/gietijzeren-koekenpannen/", "/hapjespannen/", "/wokpannen/",
    "/snijplanken/", "/airfryers/", "/airfryers/xl/", "/airfryers/dual/",
    "/vershoudcontainers/", "/vershoudcontainers/?uitvoering=3-delig",
    "/pannensets/koekenpannensets/",
)


def contract(page):
    return page.evaluate("""()=>({
        cards:[...document.querySelectorAll('.product-block')].map(e=>e.outerHTML),
        desktopTables:[...document.querySelectorAll('.table-wrapper table.product-table')].map(e=>e.outerHTML),
        intro:document.querySelector('#banner')?.outerHTML,
        recommendations:document.querySelector('.top-picks')?.outerHTML,
        metadata:[...document.querySelectorAll('meta, link[rel="canonical"], script[type="application/ld+json"]')].map(e=>e.outerHTML),
        h1:document.querySelector('h1').outerHTML,
        menu:document.querySelector('#menu').outerHTML
    })""")


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    previous_css = subprocess.run(
        ["git", "show", "HEAD:static/assets/css/comparison-cards.css"],
        text=True, capture_output=True)
    previous_js = subprocess.check_output(
        ["git", "show", "HEAD:static/assets/js/category-experience.js"], text=True)
    compare_old_cards = previous_css.returncode == 0 and "comparison-cards" in previous_js
    paths = ("/koekenpannen/", "/snijplanken/", "/vershoudcontainers/") if "--smoke" in sys.argv else PATHS
    widths = (320, 390, 1440) if "--smoke" in sys.argv else (320, 375, 390, 430, 1440)
    results = {"checks": [], "errors": [], "heightRatios": {}}
    baselines, old_heights = {}, {}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        old = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        if compare_old_cards:
            old.route("**/category-experience.js*", lambda r: r.fulfill(body=previous_js, content_type="application/javascript"))
            old.route("**/comparison-table.css*", lambda r: r.fulfill(body=previous_css.stdout, content_type="text/css"))
        for path in paths:
            assert old.goto(BASE + path).status == 200
            old.wait_for_timeout(250)
            baselines[path] = contract(old)
            if compare_old_cards:
                old_heights[path] = old.locator(".comparison-cards").first.bounding_box()["height"]
        old.close()
        page = browser.new_page(reduced_motion="reduce")
        page.on("pageerror", lambda error: results["errors"].append(str(error)))
        for width in widths:
            page.set_viewport_size({"width": width, "height": 900})
            for path in paths:
                assert page.goto(BASE + path).status == 200
                page.wait_for_timeout(250)
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), (width, path, "page overflow")
                assert not page.locator(".comparison-cards,.comparison-card").count()
                wrapper = page.locator(".compact-comparison-scroll").first
                source = page.locator(".table-wrapper table.product-table").first
                if width == 390:
                    assert contract(page) == baselines[path], (path, "content outside comparison or desktop table changed")
                    if compare_old_cards:
                        ratio = wrapper.bounding_box()["height"] / old_heights[path]
                        results["heightRatios"][path] = round(ratio, 3)
                        assert ratio < 0.5, (path, "table not substantially more compact", ratio)
                if width > 736:
                    assert source.is_visible()
                    assert not wrapper.is_visible()
                    assert source.evaluate("e=>e.outerHTML") == baselines[path]["desktopTables"][0]
                    continue
                assert wrapper.is_visible() and not source.is_visible()
                compact = wrapper.locator("table")
                assert compact.locator("tbody tr").count() == source.locator("tbody tr").count()
                assert compact.bounding_box()["height"] / compact.locator("tbody tr").count() < 150
                assert not compact.locator("a[target='_blank'],.button,button,[rel~='sponsored']").count()
                assert compact.locator("thead th").all_text_contents()[:3] == ["Product", "Oordeel", "Prijs"]
                assert compact.locator("tbody th[scope='row']").count() == compact.locator("tbody tr").count()
                assert compact.evaluate("""e=>{
                    const source=e.parentElement.previousElementSibling.previousElementSibling.querySelector('table');
                    const rows=[...source.tBodies[0].rows], compact=[...e.tBodies[0].rows];
                    const text=n=>n.textContent.trim().replace(/\\s+/g,' ');
                    const heads=[...source.tHead.rows[0].cells].map(text);
                    const score=heads.findIndex(s=>/beoordeling/i.test(s));
                    const price=heads.findIndex(s=>/prijs/i.test(s));
                    return rows.every((row,i)=>{
                        const next=compact[i];
                        const value=row.cells[score].querySelector('.rating-value');
                        return text(next.cells[0])===text(row.cells[0]) &&
                            text(next.cells[1])===(value?text(value):text(row.cells[score]).replace(/^Onze beoordeling:\\s*/i,'')) &&
                            text(next.cells[2])===text(row.cells[price]) &&
                            [...next.querySelectorAll('.product-badge')].every((badge,j)=>
                                badge.outerHTML===row.querySelectorAll('.product-badge')[j].outerHTML);
                    });
                }"""), (width, path, "mobile values differ from desktop data")
                row = compact.locator("tbody tr").first
                region = wrapper.bounding_box()
                for cell in row.locator("th,td").all()[:3]:
                    assert cell.bounding_box()["x"] + cell.bounding_box()["width"] <= region["x"] + region["width"] + 1, (width, path, "core columns offscreen")
                hint = wrapper.locator("xpath=preceding-sibling::*[1]")
                overflow = wrapper.evaluate("e=>e.scrollWidth>e.clientWidth+1")
                assert hint.is_visible() == overflow, (width, path, "incorrect overflow hint")
                if overflow:
                    before = row.locator("th").bounding_box()["x"]
                    wrapper.focus()
                    page.keyboard.press("ArrowRight")
                    assert wrapper.evaluate("e=>e.scrollLeft") > 0
                    wrapper.evaluate("e=>e.scrollLeft=e.scrollWidth")
                    assert abs(row.locator("th").bounding_box()["x"] - before) < 1
                    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
                    wrapper.evaluate("e=>e.scrollLeft=0")
                if width == 390 and path in ("/koekenpannen/", "/snijplanken/", "/vershoudcontainers/"):
                    wrapper.evaluate("e=>scrollTo(0,e.getBoundingClientRect().top+scrollY-130)")
                    page.wait_for_timeout(100)
                    page.screenshot(path=str(OUT / (path.strip("/") + ".jpg")))
                # Product names lead back to existing cards without changing their markup.
                link = compact.locator(".compact-comparison-product").first
                if link.count():
                    href = link.get_attribute("href")
                    assert href.startswith("/product/")
                    link.click()
                    assert page.evaluate("document.activeElement.getAttribute('href')") == href
                    assert "/product/" not in page.url
                results["checks"].append([width, path, "pass"])
            print(f"{width}px: {len(paths)} compact/desktop comparisons passed", flush=True)
        browser.close()
    assert not results["errors"], results["errors"]
    (OUT / ("smoke-results.json" if "--smoke" in sys.argv else "results.json")).write_text(json.dumps(results, indent=2))
    print("Desktop tables, product cards, intro, recommendations, menu and SEO unchanged.")
    print("Mobile tables use under half the height of the former cards:", results["heightRatios"])


if __name__ == "__main__":
    run()
