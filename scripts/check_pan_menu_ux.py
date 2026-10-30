"""Focused checks for the shared Pannen menu (optional browser dependencies)."""
import json
from pathlib import Path

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright


OUT = Path("generated-artifacts/pannen-menu")
PATHS = [
    "/pannen/", "/koekenpannen/", "/koekenpannen/", "/rvs-koekenpannen/",
    "/koolstofstalen-koekenpannen/", "/gietijzeren-koekenpannen/",
    "/hapjespannen/", "/wokpannen/", "/pannensets/",
    "/pannensets/koekenpannensets/", "/bak-braadsets/",
    "/kookpannensets/", "/complete-pannensets/",
]


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {"viewports": [], "navigation": [], "errors": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=str(CHROME), args=["--no-sandbox"],
        )
        page = browser.new_page()
        page.on("pageerror", lambda error: results["errors"].append(str(error)))

        def open_menu():
            page.wait_for_function("typeof jQuery !== 'undefined' && !!document.querySelector('#sidebar .toggle')")
            page.wait_for_timeout(200)
            toggle = page.locator("#sidebar .toggle")
            if toggle.get_attribute("aria-expanded") != "true":
                toggle.focus()
                page.keyboard.press("Enter")
                page.wait_for_timeout(550)
            opener = page.locator("#menu button.opener")
            opener.focus()
            if opener.get_attribute("aria-expanded") != "true":
                page.keyboard.press("Space")
            page.wait_for_timeout(550)
            assert opener.get_attribute("aria-expanded") == "true"
            assert not page.locator("#menu-pannen").evaluate("e => e.inert")
            return opener

        for width in (320, 390, 768, 1024, 1280, 1440, 1920):
            print(f"Checking {width}px", flush=True)
            page.set_viewport_size({"width": width, "height": 900})
            assert page.goto(BASE + "/bak-braadsets/").status == 200
            opener = open_menu()
            links = page.locator("#menu-pannen a")
            assert links.count() == len(PATHS)
            assert links.evaluate_all(
                "ls => new Set(ls.map(l => l.textContent.trim())).size === ls.length"
            )
            assert page.locator("#menu-pannen button").count() == 0
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert page.locator("#menu-pannen .pan-overview-link").evaluate(
                "e => getComputedStyle(e, '::after').content.includes('→')"
            )
            for index, link in enumerate(links.all()):
                assert link.get_attribute("href") == PATHS[index]
                link.focus()
                link.scroll_into_view_if_needed()
                bounds = link.bounding_box()
                assert bounds["height"] >= 44, (width, index, bounds)
                assert 0 <= bounds["x"] < bounds["x"] + bounds["width"] <= width
                # The anchor covers the full parent width and its padded top.
                assert link.evaluate("""e => {
                    const r = e.getBoundingClientRect(), p = e.parentElement.getBoundingClientRect();
                    return Math.abs(r.width - p.width) < 1 &&
                        document.elementFromPoint(r.right - 2, r.top + 2)?.closest('a') === e;
                }"""), (width, index, "non-clickable row area")
                assert link.evaluate(
                    "e => getComputedStyle(e).outlineStyle !== 'none'"
                ), (width, index, "missing keyboard focus")
            regular = links.nth(2).locator("..").evaluate(
                "e => parseFloat(getComputedStyle(e).marginTop)"
            )
            compact = page.locator(".pan-set-item").first.evaluate(
                "e => parseFloat(getComputedStyle(e).marginTop)"
            )
            assert abs(compact / regular - 0.8) < 0.02
            opener.focus()
            page.screenshot(path=str(OUT / f"menu-{width}.jpg"))
            opener.press("Enter")
            assert opener.get_attribute("aria-expanded") == "false"
            assert page.locator("#menu-pannen").evaluate("e => e.inert")
            opener.press("Enter")
            if width <= 1280:
                for _ in range(20):
                    page.keyboard.press("Tab")
                    assert page.evaluate(
                        "document.querySelector('#sidebar').contains(document.activeElement)"
                    )
                page.keyboard.press("Escape")
                assert page.locator("#sidebar .toggle").get_attribute("aria-expanded") == "false"
            results["viewports"].append({"width": width, "status": "pass"})

        # Follow each destination by clicking near the right edge, not the text.
        for width in (390, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            for index, path in enumerate(PATHS):
                assert page.goto(BASE + "/bak-braadsets/").status == 200
                open_menu()
                link = page.locator("#menu-pannen a").nth(index)
                link.scroll_into_view_if_needed()
                bounds = link.bounding_box()
                link.click(position={"x": bounds["width"] - 3, "y": bounds["height"] / 2})
                page.wait_for_url(BASE + path)
                assert page.locator("h1").count() == 1
                results["navigation"].append([width, index, path, "pass"])
        browser.close()
    assert not results["errors"], results["errors"]
    (OUT / "results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    run()
