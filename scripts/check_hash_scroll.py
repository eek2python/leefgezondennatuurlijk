"""Regression checks for hash links and mobile browser-height changes."""
from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright


def run():
    errors = []
    cases = (
        (390, "/koekenpannen/?size=24#productlijst"),
        (390, "/koekenpannen/?size=28#productlijst"),
        (390, "/koekenpannen/?size=30#productlijst"),
        (390, "/koekenpannen/?size=28"),
        (390, "/airfryers/xl/#productlijst"),
        (390, "/vershoudcontainers/?uitvoering=3-delig#productlijst"),
        (390, "/pannensets/koekenpannensets/?materiaal=keramisch#productlijst"),
        (1440, "/koekenpannen/?size=28#productlijst"),
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        for width, path in cases:
            page = browser.new_page(viewport={"width": width, "height": 844},
                                    is_mobile=width < 736, has_touch=width < 736,
                                    reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            assert page.goto(BASE + path).status == 200, path
            page.wait_for_timeout(350)
            if "#productlijst" in path:
                assert abs(page.locator("#productlijst").bounding_box()["y"]) < 180, path
            comparison = page.locator(
                ".compact-comparison-scroll" if width < 736 else ".table-wrapper"
            ).first
            comparison.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            top = page.evaluate("scrollY")
            for height in (760, 844):
                page.set_viewport_size({"width": width, "height": height})
                page.wait_for_timeout(350)
                assert abs(page.evaluate("scrollY") - top) < 3, (path, "resize reset scroll")

            # A load event after user scrolling must not revisit the old hash.
            page.dispatch_event("body", "wheel", {"deltaY": 1})
            page.evaluate("window.dispatchEvent(new Event('load'))")
            page.wait_for_timeout(250)
            assert abs(page.evaluate("scrollY") - top) < 3, (path, "late load reset scroll")

            # New, intentional hash navigation still reaches the requested target.
            page.evaluate("""() => {
                history.replaceState(null, '', location.pathname + location.search);
                location.hash = 'productlijst';
            }""")
            page.wait_for_timeout(350)
            assert abs(page.locator("#productlijst").bounding_box()["y"]) < 180, path
            print(f"{width}px {path}: height changes, late load and new hash link passed")
            page.close()
        assert not errors, errors
        browser.close()


if __name__ == "__main__":
    run()
