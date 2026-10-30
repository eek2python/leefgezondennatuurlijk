"""Desktop menu persistence, first-paint stability and mobile isolation."""
import json
from pathlib import Path

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright


OUT = Path("generated-artifacts/pannen-menu")


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))

        def ready(path):
            assert page.goto(BASE + path).status == 200
            page.wait_for_function("!!document.querySelector('#sidebar .toggle')")
            page.wait_for_timeout(650)

        def state(sidebar, pannen):
            assert page.locator("#sidebar .toggle").get_attribute("aria-expanded") == str(sidebar).lower()
            assert page.locator("#menu .opener").get_attribute("aria-expanded") == str(pannen).lower()
            assert page.locator("#sidebar > .inner").evaluate("e=>e.inert") == (not sidebar)
            assert page.locator("#menu-pannen").evaluate("e=>e.inert") == (not pannen)

        ready("/koekenpannen/")
        state(True, False)
        page.locator("#menu .opener").click()
        state(True, True)
        page.locator("#menu-pannen a[href='/rvs-koekenpannen/']").click()
        page.wait_for_url(BASE + "/rvs-koekenpannen/")
        page.wait_for_timeout(650)
        state(True, True)
        page.reload()
        page.wait_for_timeout(650)
        state(True, True)
        page.go_back()
        page.wait_for_timeout(650)
        state(True, True)
        results.append("Open sidebar and submenu persist on navigation, reload and back")

        page.locator("#menu .opener").click()
        ready("/pannensets/")
        state(True, False)
        page.locator("#menu .opener").click()
        page.locator("#sidebar .toggle").click()
        page.wait_for_timeout(650)
        state(False, True)
        ready("/wokpannen/")
        state(False, True)
        page.locator("#sidebar .toggle").click()
        page.wait_for_timeout(650)
        state(True, True)
        results.append("Explicit collapse persists; reopening sidebar retains submenu")

        # Capture the layout before main.js is loaded, then after initialization.
        for width in (1440, 1920):
            page.set_viewport_size({"width": width, "height": 1000})
            for sidebar in (True, False):
                page.evaluate("(open)=>navigationState.set('sidebar',open)", sidebar)
                before = []

                def delayed_main(route):
                    before.append(page.locator("#main").bounding_box())
                    assert page.locator("#menu-pannen").is_visible()
                    route.continue_()

                page.route("**/assets/js/main.js*", delayed_main)
                ready("/bak-braadsets/")
                page.unroute("**/assets/js/main.js*", delayed_main)
                after = page.locator("#main").bounding_box()
                assert before
                for key in ("x", "width"):
                    assert abs(before[0][key] - after[key]) < 1, (width, sidebar, before, after)
                state(sidebar, True)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        results.append("No main-content width or position shift between early render and initialization")

        page.evaluate("navigationState.set('sidebar',true)")
        ready("/koekenpannen/")
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(650)
        state(False, False)
        page.locator("#sidebar .toggle").click()
        page.wait_for_timeout(550)
        page.locator("#menu .opener").click()
        page.locator("#menu-pannen a[href='/pannensets/']").click()
        page.wait_for_url(BASE + "/pannensets/")
        page.wait_for_timeout(650)
        state(False, False)
        assert not page.locator("#main").evaluate("e=>e.inert")
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.wait_for_timeout(650)
        state(True, True)
        page.screenshot(path=str(OUT / "desktop-persistent-menu.jpg"))
        results.append("Mobile closes after navigation and does not overwrite desktop preferences")

        blocked = browser.new_context(viewport={"width": 1440, "height": 1000})
        blocked.add_init_script("""Object.defineProperty(window, 'localStorage', {
            get() { throw new DOMException('Disabled', 'SecurityError'); }
        });""")
        fallback = blocked.new_page()
        fallback.on("pageerror", lambda error: errors.append(str(error)))
        fallback.goto(BASE + "/koekenpannen/")
        fallback.wait_for_timeout(650)
        fallback.locator("#menu .opener").click()
        assert fallback.locator("#menu .opener").get_attribute("aria-expanded") == "true"
        fallback.locator("#sidebar .toggle").click()
        assert fallback.locator("#sidebar .toggle").get_attribute("aria-expanded") == "false"
        results.append("Navigation remains usable when browser storage is blocked")
        browser.close()
    assert not errors, errors
    output = {"checks": results, "page_errors": errors}
    (OUT / "persistence-results.json").write_text(json.dumps(output, indent=2))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    run()
