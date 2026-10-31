"""Check the mobile top-row size selector in portrait and landscape."""
import json
from pathlib import Path

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright


OUT = Path("generated-artifacts/format-toolbar")
PATHS = [
    "/koekenpannen/?size=30", "/rvs-koekenpannen/",
    "/koolstofstalen-koekenpannen/", "/gietijzeren-koekenpannen/",
    "/hapjespannen/", "/wokpannen/", "/airfryers/",
]


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {"matrix": [], "errors": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        page = browser.new_page(reduced_motion="reduce")
        page.on("pageerror", lambda error: results["errors"].append(str(error)))
        for width, height in ((320, 740), (390, 844), (844, 390), (932, 430), (1024, 768), (1440, 1000)):
            page.set_viewport_size({"width": width, "height": height})
            for path in PATHS:
                assert page.goto(BASE + path).status == 200
                page.wait_for_timeout(200)
                page.locator("[data-size-selector], [data-format-selector]").first.evaluate(
                    "e=>scrollTo(0,e.getBoundingClientRect().bottom+scrollY+80)"
                )
                page.wait_for_timeout(350)
                bar = page.locator(".format-sticky")
                assert "is-visible" in bar.get_attribute("class")
                assert not bar.evaluate("e=>e.inert")
                chips = bar.locator(".format-sticky-chips")
                if width <= 1280:
                    assert abs(bar.bounding_box()["y"]) < 1
                    toggle = page.locator("#sidebar .toggle")
                    first_chip = chips.bounding_box()
                    toggle_box = toggle.bounding_box()
                    assert first_chip["x"] >= toggle_box["x"] + toggle_box["width"]
                    assert bar.bounding_box()["height"] <= 65
                    active = chips.locator(".is-active").first
                    assert active.evaluate("""e=>{
                        const r=e.getBoundingClientRect(), p=e.parentElement.getBoundingClientRect();
                        return r.left>=p.left-1 && r.right<=p.right+1;
                    }"""), (width, path, "active size clipped")
                    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
                    buttons = bar.locator(".format-scroll-button")
                    visible = [b for b in buttons.all() if b.is_visible()]
                    if visible:
                        for button in visible:
                            assert button.bounding_box()["height"] >= 44
                            assert button.get_attribute("aria-label")
                        next_button = buttons.nth(1)
                        if next_button.is_enabled():
                            before = chips.evaluate("e=>e.scrollLeft")
                            next_button.focus()
                            page.keyboard.press("Enter")
                            page.wait_for_timeout(120)
                            assert chips.evaluate("e=>e.scrollLeft") > before
                        chips.evaluate("e=>e.scrollLeft=e.scrollWidth")
                        page.wait_for_timeout(100)
                        assert next_button.is_disabled()
                        previous = buttons.first
                        previous.focus()
                        page.keyboard.press("Space")
                        page.wait_for_timeout(120)
                        assert not next_button.is_disabled()
                    if path == PATHS[0]:
                        page.screenshot(path=str(OUT / f"toolbar-{width}x{height}.jpg"))
                        toggle.click()
                        page.wait_for_timeout(550)
                        assert not bar.is_visible()
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(550)
                        assert bar.is_visible()
                else:
                    assert not bar.locator(".format-scroll-button").first.is_visible()
                results["matrix"].append([width, height, path, "pass"])
            print(f"{width}x{height}: seven format selectors passed", flush=True)

        # Pick another size through the fixed bar; use the existing real URL.
        page.set_viewport_size({"width": 844, "height": 390})
        page.goto(BASE + PATHS[0])
        page.locator("[data-size-selector]").evaluate(
            "e=>scrollTo(0,e.getBoundingClientRect().bottom+scrollY+80)"
        )
        page.wait_for_timeout(400)
        link = page.locator(".format-sticky a[href='?size=28']")
        link.click()
        page.wait_for_url("**/?size=28")
        assert page.locator("[data-size-selector] .is-active").inner_text().strip() == "28 cm"
        browser.close()
    assert not results["errors"], results["errors"]
    (OUT / "results.json").write_text(json.dumps(results, indent=2))
    print(f"{len(results['matrix'])} layout checks; keyboard arrows, menu and filtering passed")


if __name__ == "__main__":
    run()
