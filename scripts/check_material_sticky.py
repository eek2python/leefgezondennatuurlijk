"""Verify the pan-set material selector reuses the shared sticky toolbar."""
import json
from pathlib import Path

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright

OUT = Path("generated-artifacts/material-sticky")
PATH = "/pannensets/koekenpannensets/"


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        page = browser.new_page(reduced_motion="reduce")
        page.on("pageerror", lambda error: errors.append(str(error)))
        for width, height in ((320, 844), (375, 844), (390, 844), (430, 844),
                              (844, 390), (768, 1024), (1440, 900)):
            page.set_viewport_size({"width": width, "height": height})
            assert page.goto(BASE + PATH).status == 200
            source = page.locator("[data-material-selector]")
            sticky = page.locator("[data-material-sticky]")
            assert sticky.get_attribute("inert") is not None
            assert "is-visible" not in sticky.get_attribute("class")
            assert sticky.locator("a").all_text_contents() == source.locator("a").all_text_contents()
            assert sticky.locator("a").evaluate_all("es=>es.map(e=>e.getAttribute('href').split('#')[0])") == source.locator("a").evaluate_all("es=>es.map(e=>e.getAttribute('href'))")
            page.evaluate("""()=>{
                const source=document.querySelector('[data-material-selector]');
                scrollTo(0,source.getBoundingClientRect().bottom+scrollY+100);
            }""")
            page.wait_for_timeout(300)
            assert "is-visible" in sticky.get_attribute("class")
            assert sticky.get_attribute("inert") is None
            assert abs(sticky.bounding_box()["y"]) < 1
            assert sticky.bounding_box()["height"] < 80
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
            assert page.locator(".format-sticky-chips").evaluate("e=>e.getBoundingClientRect().left>=56") if width <= 1280 else True
            chips = sticky.locator(".format-sticky-chips")
            more = sticky.get_by_role("button", name="Meer materialen")
            if chips.evaluate("e=>e.scrollWidth>e.clientWidth+1"):
                assert more.is_visible()
                more.click()
                assert chips.evaluate("e=>e.scrollLeft>0")
            if width in (390, 1440):
                page.screenshot(path=str(OUT / f"sticky-{width}.jpg"))
            page.evaluate("scrollTo(0,0)")
            page.wait_for_timeout(250)
            assert "is-visible" not in sticky.get_attribute("class")
            print(f"{width}x{height}: sticky visibility, menu space, scrolling and overflow passed")

        # Exercise an actual material selection from the pinned bar and history.
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(BASE + PATH)
        page.locator("#productlijst").evaluate("e=>e.scrollIntoView({block:'start'})")
        page.wait_for_timeout(300)
        rvs = page.locator('[data-material-sticky] a').filter(has_text="RVS")
        href = rvs.get_attribute("href")
        rvs.focus()
        page.keyboard.press("Enter")
        page.wait_for_url("**" + href)
        page.wait_for_timeout(500)
        assert page.locator('[data-material-selector] [aria-current]').inner_text() == "RVS"
        assert page.locator('[data-material-sticky] [aria-current]').inner_text() == "RVS"
        assert page.locator("#productlijst").bounding_box()["y"] >= page.locator("[data-material-sticky]").bounding_box()["height"]
        assert page.locator(".product-block").count() > 0
        page.go_back()
        page.wait_for_timeout(350)
        assert page.locator('[data-material-selector] [aria-current]').inner_text() == "Alle materialen"
        page.go_forward()
        page.wait_for_timeout(350)
        assert page.locator('[data-material-selector] [aria-current]').inner_text() == "RVS"

        # No material toolbar on other set lists; existing selectors still pin.
        for path, selector in (("/kookpannensets/", None), ("/koekenpannen/", "[data-size-sticky]"),
                               ("/airfryers/", "[data-format-sticky]")):
            page.goto(BASE + path)
            assert not page.locator("[data-material-sticky]").count()
            if selector:
                page.evaluate("scrollTo(0,5000)")
                page.wait_for_timeout(250)
                assert "is-visible" in page.locator(selector).get_attribute("class")
        plain = browser.new_context(java_script_enabled=False, viewport={"width": 390, "height": 844})
        nojs = plain.new_page()
        nojs.goto(BASE + PATH)
        nojs.locator("[data-material-selector] a").filter(has_text="RVS").click()
        assert nojs.locator('[data-material-selector] [aria-current]').inner_text() == "RVS"
        plain.close()
        browser.close()
    assert not errors, errors
    (OUT / "results.json").write_text(json.dumps({"layouts": 7, "javascriptErrors": errors}))
    print("Material filtering, keyboard, history, no-JS and existing selectors passed")


if __name__ == "__main__":
    run()
