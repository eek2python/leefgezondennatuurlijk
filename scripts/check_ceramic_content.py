"""Responsive checks for all ceramic category selections and colour controls."""
from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright


SIZES = ("20", "24", "26", "28", "30", "32", "20_28", "24_28", "20_24_28")


def run():
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(CHROME), args=["--no-sandbox"],
        )
        page = browser.new_page(reduced_motion="reduce")
        page.on("pageerror", lambda error: errors.append(str(error)))
        for width, height in ((375, 844), (430, 932), (768, 1024), (1440, 1000)):
            page.set_viewport_size({"width": width, "height": height})
            for size in SIZES:
                response = page.goto(BASE + "/koekenpannen/?size=" + size)
                assert response.status == 200, (width, size)
                page.wait_for_selector(".compact-comparison-table", state="attached")
                assert not page.evaluate(
                    "document.documentElement.scrollWidth > innerWidth"
                ), (width, size, "page overflow")
                assert page.locator("h1").inner_text().endswith(
                    "van " + " + ".join(size.split("_")) + " cm (2026)"
                ), (width, size)
                # All four price levels are visible, never an accordion/table.
                assert page.locator(".ceramic-price-levels li").count() == 4
                assert page.locator(".ceramic-price-levels").is_visible()
                mobile = width <= 736
                assert page.locator(".compact-comparison-scroll").is_visible() == mobile
                assert page.locator(".table-wrapper").is_visible() != mobile
                assert page.locator(".ceramic-assessment").get_attribute("open") == (
                    None if mobile else ""
                )
                order = page.locator(
                    ".ceramic-category-page > section, "
                    ".ceramic-category-page > details"
                ).evaluate_all("els => els.map(el => el.querySelector('h2,h1')?.textContent.trim())")
                assert order.index("Prijsniveaus binnen deze vergelijking") < order.index(
                    "Zo beoordelen we keramische koekenpannen"
                )
            print(f"{width}px: all nine selections, price levels, disclosures and widths passed")

        page.set_viewport_size({"width": 375, "height": 844})
        page.goto(BASE + "/koekenpannen/?size=28")
        page.locator(".ceramic-assessment summary").click()
        assert page.locator(".ceramic-score-weights strong").all_text_contents() == [
            "25%", "25%", "20%", "15%", "15%",
        ]
        compact = page.locator(".compact-comparison-scroll")
        first_name = compact.locator("tbody th").first
        compact.scroll_into_view_if_needed()
        name_left = first_name.bounding_box()["x"]
        compact.evaluate("el => el.scrollLeft = el.scrollWidth")
        assert abs(first_name.bounding_box()["x"] - name_left) < 3, "name not pinned"

        # Follow a real selector link rather than inventing a separate mobile route.
        page.locator('a[href*="size=20_24_28"]').first.click()
        page.wait_for_url("**size=20_24_28*")
        swatch = page.locator("[data-variant-swatch]").first
        card = swatch.locator("xpath=ancestor::*[contains(@class,'product-block')][1]")
        second = card.locator("[data-variant-swatch]").nth(1)
        second.click()
        assert second.get_attribute("aria-pressed") == "true"
        assert swatch.get_attribute("aria-pressed") == "false"
        # The existing swatch contract determines price/image/destination.
        expected_price = second.get_attribute("data-price")
        expected_image = second.get_attribute("data-image")
        expected_url = second.get_attribute("data-url")
        if expected_image:
            assert card.locator("img").first.get_attribute("src") == expected_image
        if expected_url:
            assert card.locator(f'a[href="{expected_url}"]').count() > 0
        if expected_price:
            assert expected_price in card.inner_text()
        assert not errors, errors
        print("Assessment disclosure, pinned product names, selector and colour switch passed")
        browser.close()


if __name__ == "__main__":
    run()
