"""Responsive and anchor regression checks for compact ceramic quick picks."""
import os
import sys
from pathlib import Path

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright


SIZES = ("20", "24", "26", "28", "30", "32", "20_28", "24_28", "20_24_28")
VIEWPORTS = ((375, 844), (430, 932), (768, 1024), (1024, 768), (1440, 1000))


def fixture_html(count):
    """Render real component with isolated input; never edit the live catalogue."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LeefNatuurlijkenGezond.settings")
    import django
    django.setup()
    from django.template.loader import render_to_string
    from utils.quick_picks import AWARD_ORDER, build_quick_picks

    products = [{
        "slug": f"fixture-{index}", "name": "Een lange maar volledige productnaam voor deze pan",
        "rating": 4.5, "rating_display": "4,5", "rating_class": "4-5",
        "award": award, "award_class": ("best-choice", "budget-choice", "premium-choice")[index],
        "comparison_features": ["Een zorgvuldig gekozen constructiekenmerk", "Oven tot 230 °C"],
    } for index, award in enumerate(list(AWARD_ORDER)[:count])]
    partial = render_to_string("partials/ceramic_quick_picks.html", {
        "quick_picks": build_quick_picks(products),
    })
    styles = "".join(
        f'<link rel="stylesheet" href="{BASE}/static/assets/css/{name}.css">'
        for name in ("main", "category-mobile")
    )
    return (
        '<!doctype html><html lang="nl"><head><meta name="viewport" '
        'content="width=device-width, initial-scale=1">' + styles +
        '</head><body><div id="wrapper"><div id="main"><div class="inner">'
        '<div class="ceramic-category-page">' + partial +
        "</div></div></div></div></body></html>"
    )


def run():
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(CHROME), args=["--no-sandbox"],
        )
        page = browser.new_page(reduced_motion="reduce")
        page.on("pageerror", lambda error: errors.append(str(error)))
        for width, height in VIEWPORTS:
            page.set_viewport_size({"width": width, "height": height})
            for size in SIZES:
                response = page.goto(BASE + "/koekenpannen/?size=" + size)
                assert response.status == 200, (width, size)
                section = page.locator("#snel-kiezen")
                assert section.is_visible(), (width, size)
                assert not page.evaluate(
                    "document.documentElement.scrollWidth > innerWidth"
                ), (width, size, "page overflow")
                assert section.locator("img").count() == 0
                links = section.locator("a")
                for index in range(links.count()):
                    link = links.nth(index)
                    target = link.get_attribute("href")
                    assert target.startswith("#product-"), target
                    assert page.locator(target).count() == 1
                    link.click()
                    page.wait_for_timeout(250)
                    assert page.evaluate("location.hash") == target
                    assert page.evaluate("document.activeElement.id") == target[1:]
                    top = page.locator(target).bounding_box()["y"]
                    assert 40 <= top <= 180, (width, size, target, top)
                if width <= 430 and links.count() == 2:
                    assert section.bounding_box()["height"] < height * 0.8
            print(f"{width}px: all nine selections, correct review links and focus passed")

        # Zero/one/three are not all guaranteed to occur in the changing catalogue.
        for width, height in VIEWPORTS:
            page.set_viewport_size({"width": width, "height": height})
            for count in range(4):
                page.set_content(fixture_html(count), wait_until="networkidle")
                section = page.locator("#snel-kiezen")
                assert section.count() == bool(count)
                assert page.locator(".ceramic-quick-pick").count() == count
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
                if width > 736 and count == 1:
                    assert page.locator(".ceramic-quick-pick").bounding_box()["width"] <= 385
                if width == 1440 and count == 3:
                    tops = page.locator(".ceramic-quick-pick").evaluate_all(
                        "els => els.map(el => el.getBoundingClientRect().top)"
                    )
                    assert max(tops) - min(tops) < 2, "three picks should fit side by side"
        assert not errors, errors
        print("Zero, one, two and three recommendations passed at all five widths")
        browser.close()


if __name__ == "__main__":
    run()
