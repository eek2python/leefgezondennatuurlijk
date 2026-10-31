"""Check both storage filters beside the mobile menu, including navigation."""
from pathlib import Path

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright


def run():
    out = Path("generated-artifacts/storage-toolbar")
    out.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        page = browser.new_page(reduced_motion="reduce")
        page.on("pageerror", lambda error: errors.append(str(error)))
        for width, height in ((320, 740), (390, 844), (844, 390), (932, 430), (1024, 768), (1440, 1000)):
            page.set_viewport_size({"width": width, "height": height})
            assert page.goto(BASE + "/vershoudcontainers/?uitvoering=enkel&formaat=groot").status == 200
            page.wait_for_timeout(350)
            bar = page.locator(".storage-filters-sticky")
            sentinel = page.locator(".storage-filters-sentinel")
            assert not bar.evaluate("e=>e.classList.contains('is-stuck')")
            assert bar.locator(".label").first.is_visible()
            assert not bar.locator(".format-scroll-button").first.is_visible()
            sentinel.evaluate("e=>scrollTo(0,e.getBoundingClientRect().top+scrollY+120)")
            page.wait_for_timeout(450)
            assert bar.evaluate("e=>e.classList.contains('is-stuck')")
            if width <= 1280:
                assert abs(bar.bounding_box()["y"]) < 1, bar.bounding_box()
                assert bar.bounding_box()["height"] <= 116
                assert not bar.evaluate("e=>e.classList.contains('is-too-tall')")
                toggle_box = page.locator("#sidebar .toggle").bounding_box()
                for row in bar.locator(".storage-filter-row").all():
                    assert row.bounding_box()["x"] >= toggle_box["x"] + toggle_box["width"]
                    selected = row.locator('[aria-current="page"]')
                    assert selected.evaluate("""e=>{
                        const r=e.getBoundingClientRect(), p=e.parentElement.getBoundingClientRect();
                        return r.left>=p.left-1 && r.right<=p.right+1;
                    }"""), (width, selected.inner_text())
                    for chip in row.locator(".format-pill").all():
                        assert chip.bounding_box()["height"] >= 44
                        assert chip.evaluate("e=>getComputedStyle(e).color") == (
                            "rgb(255, 255, 255)" if chip.get_attribute("aria-current") else "rgb(61, 68, 73)"
                        )
                    arrows = row.locator(".format-scroll-button")
                    if arrows.first.is_visible():
                        options = row.locator("div").first
                        options.evaluate("e=>e.scrollLeft=0")
                        page.wait_for_timeout(100)
                        assert arrows.first.is_disabled()
                        assert arrows.last.is_enabled()
                        arrows.last.focus()
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(100)
                        assert options.evaluate("e=>e.scrollLeft") > 0
                        options.evaluate("e=>e.scrollLeft=e.scrollWidth")
                        page.wait_for_timeout(100)
                        assert arrows.last.is_disabled()
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
                offset = page.evaluate("parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sticky-filter-height'))")
                assert abs(offset - bar.bounding_box()["height"]) <= 1
                page.screenshot(path=str(out / f"toolbar-{width}x{height}.jpg"))
                page.locator("#sidebar .toggle").click()
                page.wait_for_timeout(550)
                assert not bar.is_visible()
                page.keyboard.press("Escape")
                page.wait_for_timeout(550)
                assert bar.is_visible()
                assert abs(bar.bounding_box()["y"]) < 1
            else:
                assert bar.evaluate("e=>getComputedStyle(e).position") == "sticky"
                assert bar.locator(".format-scroll-button").first.is_hidden()
            page.evaluate("scrollTo(0,0)")
            page.wait_for_timeout(400)
            assert not bar.evaluate("e=>e.classList.contains('is-stuck')")
            assert sentinel.bounding_box()["height"] == 0
            print(f"{width}x{height}: positioning, overflow, menu, arrows and scroll restoration passed")

        # Follow the real URLs: changing execution preserves the size selection.
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(BASE + "/vershoudcontainers/?uitvoering=enkel&formaat=groot")
        sentinel.evaluate("e=>scrollTo(0,e.getBoundingClientRect().top+scrollY+120)")
        page.wait_for_timeout(350)
        link = page.locator("[data-storage-type-selector] a").filter(has_text="3-delig")
        expected = link.get_attribute("href")
        link.click()
        page.wait_for_url("**/" + expected)
        assert "uitvoering=3-delig" in page.url and "formaat=groot" in page.url
        assert page.locator('[data-storage-type-selector] [aria-current="page"]').inner_text().strip() == "3-delig"
        sentinel.evaluate("e=>scrollTo(0,e.getBoundingClientRect().top+scrollY+120)")
        page.wait_for_timeout(350)
        link = page.locator("[data-storage-size-filter] a").filter(has_text="Klein")
        expected = link.get_attribute("href")
        link.click()
        page.wait_for_url("**/" + expected)
        assert "uitvoering=3-delig" in page.url and "formaat=klein" in page.url
        assert page.locator('[data-storage-size-filter] [aria-current="page"]').inner_text().strip() == "Klein"
        assert page.locator(".storage-empty-state").is_visible()
        reset = page.locator(".storage-empty-state a")
        reset_url = reset.get_attribute("href")
        reset.click()
        page.wait_for_url("**/" + reset_url)
        assert "uitvoering=3-delig" in page.url and "formaat=alle" in page.url
        assert page.locator(".product-block").count() > 0
        print("Both real filters work and preserve the other selection.")
        browser.close()
    assert not errors, errors


if __name__ == "__main__":
    run()
