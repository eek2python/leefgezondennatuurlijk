"""Verify shared responsive button colours and white award text."""
import re

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright


def contrast(foreground, background):
    def luminance(color):
        channels = [int(n) / 255 for n in re.findall(r"\d+", color)[:3]]
        linear = [n / 12.92 if n <= 0.04045 else ((n + 0.055) / 1.055) ** 2.4
                  for n in channels]
        return sum(n * weight for n, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    values = sorted((luminance(foreground), luminance(background)))
    return (values[1] + 0.05) / (values[0] + 0.05)


def run():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), args=["--no-sandbox"])
        page = browser.new_page(reduced_motion="reduce")
        page.on("pageerror", lambda error: errors.append(str(error)))
        for path in ("/koekenpannen/", "/vershoudcontainers/", "/airfryers/"):
            samples = []
            for width, height in ((1440, 1000), (390, 844), (844, 390)):
                page.set_viewport_size({"width": width, "height": height})
                assert page.goto(BASE + path).status == 200
                page.wait_for_timeout(400)
                page.mouse.move(0, 0)
                sample = page.evaluate("""() => {
                    const colors = e => {
                        const s = getComputedStyle(e);
                        return [s.color, s.backgroundColor, s.borderColor];
                    };
                    const buttons = [...document.querySelectorAll(
                        '#main .button:not(.disabled):not([aria-disabled="true"]), ' +
                        '#main .product-variant-button:not(:disabled), #main .format-pill'
                    )];
                    return {
                        buttons: buttons.map(colors),
                        sizes: buttons.filter(e => e.getClientRects().length).map(e => {
                            const s = getComputedStyle(e);
                            return [parseFloat(s.fontSize), e.getBoundingClientRect().height];
                        }),
                        awards: [...document.querySelectorAll('.product-badge')].map(colors),
                        overflow: document.documentElement.scrollWidth > innerWidth + 1
                    };
                }""")
                assert sample["buttons"], path
                assert sample["awards"], path
                assert not sample["overflow"], (path, width, "page overflow")
                for foreground, background, _ in sample["buttons"]:
                    if background == "rgb(98, 212, 229)":
                        assert foreground == "rgb(255, 255, 255)", (path, width, "filled text must be white")
                        continue
                    if background == "rgba(0, 0, 0, 0)":
                        background = "rgb(255, 255, 255)"
                    assert contrast(foreground, background) >= 4.5, (path, width, foreground, background)
                assert all(award[0] == "rgb(255, 255, 255)" for award in sample["awards"])
                if width == 390:
                    assert all(font >= 14 for font, _ in sample["sizes"])
                    assert all(height >= 44 for _, height in sample["sizes"])
                samples.append(sample)
            for sample in samples[1:]:
                assert sample["buttons"] == samples[0]["buttons"], (path, "button colour mismatch")
                assert sample["awards"] == samples[0]["awards"], (path, "award colour mismatch")
            print(f"{path}: desktop, portrait and landscape match; filled button text and awards white")
        # Check generic button states without changing any live product data.
        page.evaluate("""() => {
            const box = document.createElement('div');
            box.style.cssText = 'position:fixed;right:20px;top:100px;z-index:10000;background:white';
            box.innerHTML = '<a class="button" href="#test">Test</a>' +
                            '<button class="button primary">Test</button>';
            box.id = 'colour-test';
            document.body.prepend(box);
        }""")
        states = {}
        for width in (1440, 390, 844):
            page.set_viewport_size({"width": width, "height": 1000})
            for selector in ("#colour-test a", "#colour-test button"):
                for state in ("normal", "hover", "active"):
                    page.mouse.move(0, 0)
                    element = page.locator(selector)
                    if state != "normal":
                        element.hover()
                    if state == "active":
                        page.mouse.down()
                    page.wait_for_timeout(250)
                    colors = element.evaluate("""e => {
                        const s = getComputedStyle(e);
                        return [s.color, s.backgroundColor, s.boxShadow];
                    }""")
                    if state == "active":
                        page.mouse.up()
                    key = (selector, state)
                    if width == 1440:
                        states[key] = colors
                    else:
                        assert colors == states[key], (width, key, colors, states[key])
        browser.close()
    assert not errors, errors
    print("Normal, hover and pressed button states match; no JavaScript errors.")


if __name__ == "__main__":
    run()
