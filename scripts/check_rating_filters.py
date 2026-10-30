"""Focused visual-layout regressions for rating stars and storage-type choices."""
import json
from mobile_capture import BASE, CHROME, OUT
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
    page = browser.new_page()
    results = []
    for width in (320, 390, 768, 1440):
        page.set_viewport_size({"width": width, "height": 844})
        for path in ("/koekenpannen/", "/vershoudcontainers/", "/airfryers/"):
            assert page.goto(BASE + path).status == 200
            page.wait_for_timeout(300)
            assert page.locator(".stars").count()
            assert page.locator(".stars").evaluate_all("""stars=>stars.every(e=>{
                const style=getComputedStyle(e), fill=getComputedStyle(e,'::after');
                return style.whiteSpace==='nowrap' && style.flexShrink==='0' &&
                  parseFloat(fill.height)<=e.getBoundingClientRect().height+1;
            })"""), (width, path, "wrapped stars")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1")
            if path == "/vershoudcontainers/":
                assert page.locator("[data-storage-type-selector]").evaluate("""e=>{
                  const label=e.querySelector('.label').getBoundingClientRect();
                  return [...e.querySelectorAll('a')].every(a=>a.getBoundingClientRect().top>=label.bottom);
                }"""), (width, "choices beside label")
                if width == 390:
                    page.locator("[data-storage-type-selector] a").nth(1).click()
                    page.wait_for_timeout(350)
                    assert "uitvoering=3-delig" in page.url
                    assert page.locator("[data-storage-type-selector] [aria-current]").inner_text() == "3-delig"
                    # A fragment target gives a settled sticky-filter screenshot.
                    page.evaluate("location.hash='producten'")
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(OUT / "refinement-storage.jpg"))
            results.append([width, path, "pass"])
    page.set_viewport_size({"width": 320, "height": 844})
    page.goto(BASE + "/koekenpannen/")
    page.add_style_tag(content="html{font-size:200% !important}body{font-size:32px !important}")
    page.wait_for_timeout(300)
    assert page.locator(".stars").evaluate_all("""stars=>stars.every(e=>
      parseFloat(getComputedStyle(e,'::after').height)<=e.getBoundingClientRect().height+1)""")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1")
    browser.close()
    (OUT / "rating-filter-checks.json").write_text(json.dumps(results, indent=2))
    print(f"{len(results)} page/width checks and 200% text enlargement passed.")
