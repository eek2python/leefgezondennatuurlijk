"""Browser regression checks. See reports/mobile-ux.md for setup and limitations."""
import json
import re
import sys
from mobile_capture import BASE, CHROME, OUT, snapshot
from playwright.sync_api import sync_playwright


def check(page, expression, message):
    assert page.evaluate(expression), message + " (" + page.url + ")"


def ready(page, path):
    response = page.goto(BASE + path)
    assert response.status == 200, (path, response.status)
    page.wait_for_timeout(260)


def check_unavailable(browser):
    """Exercise a missing-link state in an isolated response, never in catalogue data."""
    page = browser.new_page(viewport={"width": 390, "height": 844})
    variant_data = {}

    def without_link(route):
        response = route.fetch()
        body = response.text()
        pattern = r'(<script[^>]*id="variant-data-ikea-365-plus-enkel"[^>]*>)(.*?)(</script>)'

        def replace(match):
            data = json.loads(match.group(2))
            default = next(v for v in data["variants"] if v["id"] == data["default_id"])
            missing = next(v for v in data["variants"] if v["id"] != data["default_id"])
            missing["resolved_url"] = ""
            missing["affiliate_url"] = ""
            missing["availability_label"] = "Link voor deze uitvoering nog niet beschikbaar"
            variant_data.update(default=default, missing=missing)
            return match.group(1) + json.dumps(data).replace("<", "\\u003c") + match.group(3)

        body, count = re.subn(pattern, replace, body, flags=re.S)
        assert count == 1
        route.fulfill(response=response, body=body)

    page.route("**/vershoudcontainers/", without_link)
    ready(page, "/vershoudcontainers/")
    card = page.locator("[data-product-slug='ikea-365-plus-enkel']")
    missing_capacity = variant_data["missing"]["options"]["capacity"]
    card.locator(f"[data-option-value='{missing_capacity}']").click()
    link = card.locator("[data-shape-affiliate]")
    assert not link.is_visible()
    assert link.get_attribute("href") is None
    assert link.get_attribute("rel") is None
    assert card.locator("[data-shape-affiliate-disabled]").is_visible()
    page.screenshot(path=str(OUT / "after-unavailable-fixture.jpg"))
    default_capacity = variant_data["default"]["options"]["capacity"]
    card.locator(f"[data-option-value='{default_capacity}']").click()
    assert link.is_visible()
    assert link.get_attribute("href") == variant_data["default"]["resolved_url"]
    assert not card.locator("[data-shape-affiliate-disabled]").is_visible()
    page.close()
    return "isolated missing-link fixture: unavailable message, stale href/rel cleared, available choice restored"


def run():
    results = {"matrix": [], "interactions": [], "errors": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        page = browser.new_page()
        page.on("pageerror", lambda error: results["errors"].append(str(error)))
        ready(page, "/koekenpannen/")
        detail = page.locator(".product-block h3 a").first.get_attribute("href")
        ready(page, "/blogs/")
        blog = page.locator("#main a[href^='/blogs/']").first.get_attribute("href")
        paths = ["/", "/koekenpannen/", "/koekenpannen/?size=24", "/koekenpannen/?size=20_28",
                 "/airfryers/", "/airfryers/xl/", "/airfryers/dual/", "/vershoudcontainers/",
                 "/vershoudcontainers/?uitvoering=3-delig", "/vershoudcontainers/?uitvoering=5-delig",
                 detail, "/product/ikea-365-plus-enkel/", blog]
        for width in (320, 360, 390, 430, 768, 1024, 1440, 1920):
            page.set_viewport_size({"width": width, "height": 844 if width < 768 else 1000})
            for path in paths:
                ready(page, path)
                check(page, "document.documentElement.scrollWidth <= innerWidth + 1", "Page overflows")
                if width <= 736:
                    check(page, "parseFloat(getComputedStyle(document.body).fontSize) >= 16", "Small base text")
                    check(page, """Array.from(document.querySelectorAll('.format-pill, .variant-swatch, .product-variant-button'))
                      .filter(e=>e.getBoundingClientRect().width && !e.closest('[inert]'))
                      .every(e=>e.getBoundingClientRect().height>=43.9)""", "Small touch target")
                results["matrix"].append([width, path, "pass"])
            print(f"Matrix {width}px: {len(paths)} pages passed", flush=True)
        # Menu: native Enter/Space, submenu state, focus containment and Escape restoration.
        page.set_viewport_size({"width": 390, "height": 844})
        ready(page, "/koekenpannen/")
        toggle = page.locator("#sidebar .toggle")
        toggle.focus()
        page.keyboard.press("Enter")
        assert toggle.get_attribute("aria-expanded") == "true"
        check(page, "document.querySelector('#main').inert", "Covered main remains focusable")
        page.keyboard.press("Escape")
        check(page, "document.activeElement.matches('#sidebar .toggle')", "Escape from menu link loses focus")
        page.keyboard.press("Enter")
        page.locator("#menu a").first.focus()
        page.keyboard.press("Shift+Tab")
        check(page, "document.activeElement.matches('#sidebar .toggle')", "Reverse Tab escapes overlay")
        opener = page.locator("#menu .opener")
        opener.focus()
        page.keyboard.press("Space")
        assert opener.get_attribute("aria-expanded") == "true"
        assert page.locator("#menu-pannen a").first.is_visible()
        for _ in range(25):
            page.keyboard.press("Tab")
            check(page, "document.querySelector('#sidebar').contains(document.activeElement)", "Focus escapes overlay")
        page.keyboard.press("Escape")
        assert toggle.get_attribute("aria-expanded") == "false"
        check(page, "document.activeElement.matches('#sidebar .toggle')", "Focus not restored")
        check(page, "document.querySelector('#sidebar > .inner').inert", "Hidden menu remains focusable")
        toggle.click()
        page.locator("#menu a[href='/airfryers/']").click()
        page.wait_for_url("**/airfryers/")
        results["interactions"].append("menu keyboard, submenu, Tab containment, Escape, navigation")

        # Desktop retains visible sidebar and open/close state.
        page.set_viewport_size({"width": 1440, "height": 1000})
        ready(page, "/")
        assert toggle.get_attribute("aria-expanded") == "true"
        check(page, "!document.querySelector('#main').inert && !document.querySelector('#sidebar > .inner').inert",
              "Desktop navigation inaccessible")
        results["interactions"].append("desktop persistent menu")

        page.set_viewport_size({"width": 390, "height": 844})
        ready(page, "/koekenpannen/")
        page.locator("[data-size-selector] a").filter(has_text="24").first.click()
        page.wait_for_url("**/?size=24")
        assert "24 cm" in page.locator("h1").inner_text()
        page.locator("[data-size-selector] a[href='?size=20_28']").click()
        page.wait_for_url("**/?size=20_28")
        assert page.locator(".product-block").count()
        ready(page, "/airfryers/")
        page.locator("[data-format-selector] a").filter(has_text="XL").first.click()
        page.wait_for_url("**/airfryers/xl/")
        assert page.locator("[data-format-selector] [aria-current='page']").count() == 1
        results["interactions"].append("size and airfryer format links")

        # Color selectors: verify each rendered swatch uses exactly its existing destination.
        ready(page, "/airfryers/xl/")
        swatch_count = 0
        for card in page.locator("[data-variant-card]").all():
            for swatch in card.locator("[data-variant-swatch]").all():
                swatch.click()
                assert swatch.get_attribute("aria-pressed") == "true"
                link = card.locator("[data-variant-affiliate]")
                if link.count():
                    assert (link.get_attribute("href") or "") == (swatch.get_attribute("data-url") or "")
                swatch_count += 1
        assert swatch_count > 0
        results["interactions"].append(f"{swatch_count} color selections and exact destinations")

        # Storage variants: every reachable visible option, grouped options and unavailable CTAs.
        variant_count = 0
        disabled_count = 0
        for path in ("/vershoudcontainers/", "/vershoudcontainers/?uitvoering=3-delig", "/vershoudcontainers/?uitvoering=5-delig"):
            ready(page, path)
            for card in page.locator("[data-shape-card]").all():
                for option in card.locator("[data-variant-option]").all():
                    if not option.is_visible():
                        continue
                    option.click()
                    assert option.get_attribute("aria-pressed") == "true"
                    assert card.locator("[data-shape-summary]").inner_text().strip()
                    data = card.locator("script[type='application/json']")
                    if data.count():
                        check_data = json.loads(data.inner_text())
                        # Compare the selected option tuple to server-rendered variant projection.
                        selections = card.locator("[data-variant-option][aria-pressed='true']").evaluate_all(
                            "(els)=>Object.fromEntries(els.map(e=>[e.dataset.selectorKey,e.dataset.optionValue]))")
                        variants = check_data if isinstance(check_data, list) else check_data["variants"]
                        selected = next(v for v in variants if all(str(v["options"][k]) == val for k, val in selections.items()))
                        link = card.locator("[data-shape-affiliate]")
                        expected = selected["resolved_url"]
                        if expected:
                            assert link.get_attribute("href") == expected
                        if not link.is_visible():
                            assert card.locator("[data-shape-affiliate-disabled]").is_visible()
                            disabled_count += 1
                    variant_count += 1
            # Filter type and size controls remain real navigable links.
            for selector in ("[data-storage-type-selector]", "[data-storage-size-filter]"):
                links = page.locator(selector + " a:not([aria-current])")
                if links.count():
                    destination = links.first.get_attribute("href")
                    links.first.click()
                    page.wait_for_timeout(400)
                    assert destination in page.url
                    ready(page, path)
        assert variant_count > 0
        results["interactions"].append(f"{variant_count} storage selections, {disabled_count} unavailable states, type/size filters")
        ready(page, "/product/ikea-365-plus-enkel/")
        options = page.locator("[data-variant-option]")
        detail_data = json.loads(page.locator("script[id^='variant-data-']").inner_text())
        for option in options.all():
            if not option.is_visible():
                continue
            option.click()
            assert option.get_attribute("aria-pressed") == "true"
            selections = page.locator("[data-variant-option][aria-pressed='true']").evaluate_all(
                "(els)=>Object.fromEntries(els.map(e=>[e.dataset.selectorKey,e.dataset.optionValue]))")
            selected = next(v for v in detail_data["variants"] if all(str(v["options"][k]) == val for k, val in selections.items()))
            assert page.locator("[data-shape-affiliate]").get_attribute("href") == selected["resolved_url"]
            assert selected["summary"] == page.locator("[data-shape-summary]").inner_text()
        results["interactions"].append(f"{options.count()} detail-page variant choices")

        # Horizontal table browsing, product-name association, and all columns remain present.
        ready(page, "/vershoudcontainers/")
        table = page.locator(".table-wrapper").first
        table.scroll_into_view_if_needed()
        table.focus()
        before = table.evaluate("(e)=>e.scrollLeft")
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
        assert table.evaluate("(e)=>e.scrollLeft") > before
        check(page, "getComputedStyle(document.querySelector('.product-table tbody tr > :first-child')).position === 'sticky'",
              "Product column does not follow scroll")
        assert page.locator(".table-scroll-hint").first.is_visible()
        page.screenshot(path=str(OUT / "after-table.jpg"))
        results["interactions"].append("horizontal keyboard scroll, visible hint, sticky product column")

        # Anchor offset adapts to filter height, orientation, and 200% text enlargement.
        for path, target in (("/koekenpannen/", "productlijst"), ("/vershoudcontainers/", "producten")):
            for width, height, text_zoom in ((390, 844, False), (844, 390, False), (320, 844, True), (390, 422, True)):
                page.set_viewport_size({"width": width, "height": height})
                ready(page, path)
                if text_zoom:
                    page.add_style_tag(content="html { font-size: 200% !important; } body { font-size: 32px !important; }")
                page.evaluate("(id)=>{location.hash=id}", target)
                page.wait_for_timeout(700)
                check(page, """(() => {
                  const t=document.getElementById(location.hash.slice(1)).getBoundingClientRect();
                  const bars=[...document.querySelectorAll('.format-sticky.is-visible:not(.is-too-tall),.storage-filters-sticky.is-stuck:not(.is-too-tall)')];
                  const bottom=Math.max(56,...bars.map(e=>e.getBoundingClientRect().bottom));
                  return t.top >= bottom - 2;
                })()""", "Anchor covered")
                check(page, "document.documentElement.scrollWidth <= innerWidth + 1", "Zoom/landscape overflow")
        results["interactions"].append("anchors after dynamic filters in portrait, landscape and 200% text")

        # 200% page layout zoom via half-size CSS viewport at deviceScaleFactor=2.
        zoom = browser.new_context(viewport={"width": 320, "height": 422}, device_scale_factor=2)
        zoom_page = zoom.new_page()
        ready(zoom_page, "/koekenpannen/")
        check(zoom_page, "document.documentElement.scrollWidth <= innerWidth + 1", "200% equivalent reflow")
        zoom_page.locator("#sidebar .toggle").click()
        assert zoom_page.locator("#menu a").first.is_visible()
        check(zoom_page, "document.querySelector('#sidebar > .inner').getBoundingClientRect().right <= innerWidth + 1",
              "Narrow menu is clipped")
        zoom.close()
        results["interactions"].append("200% equivalent reflow and menu at 320 CSS pixels")
        touch = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        touch_page = touch.new_page()
        ready(touch_page, "/airfryers/xl/")
        touch_page.locator("#sidebar .toggle").tap()
        assert touch_page.locator("#sidebar .toggle").get_attribute("aria-expanded") == "true"
        touch_page.locator("#sidebar .toggle").tap()
        swatch = touch_page.locator("[data-variant-swatch]").last
        swatch.tap()
        assert swatch.get_attribute("aria-pressed") == "true"
        touch.close()
        results["interactions"].append("emulated mobile touch: menu and color swatch taps")
        for path in ("/product/bestaat-niet/", "/airfryers/bestaat-niet/"):
            response = page.goto(BASE + path)
            assert response.status == 404
        assert not results["errors"], results["errors"]
        results["interactions"].append(check_unavailable(browser))
        browser.close()
    (OUT / "checks.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(json.dumps({"matrix_checks": len(results["matrix"]), "interactions": results["interactions"], "errors": results["errors"]}, indent=2))


if __name__ == "__main__":
    if "--unavailable-only" in sys.argv:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
            message = check_unavailable(browser)
            browser.close()
        results = json.loads((OUT / "checks.json").read_text())
        if message not in results["interactions"]:
            results["interactions"].append(message)
        (OUT / "checks.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
        print(message)
    else:
        run()
