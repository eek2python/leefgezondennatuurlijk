"""Regression checks for curated feature lists in compact comparisons."""
from pathlib import Path

from mobile_capture import BASE, CHROME
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent.parent


def run():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(CHROME), args=["--no-sandbox"]
        )
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        for path in ("/koekenpannen/?size=30", "/snijplanken/",
                     "/airfryers/", "/vershoudcontainers/"):
            assert page.goto(BASE + path).status == 200, path
            page.wait_for_selector(".compact-comparison-table")
            source = page.locator(".product-table").first
            original_text = source.text_content()
            expected = source.locator("tbody tr").evaluate_all("""rows => rows.map(row =>
                [...row.querySelectorAll('[data-comparison-feature]')]
                    .map(el => el.textContent.trim()).filter(Boolean).slice(0, 4))""")
            for index, features in enumerate(expected):
                if features:
                    actual = page.locator(".compact-comparison-table tbody tr").nth(index)
                    assert actual.locator("li").all_text_contents() == features, path
            for width, height in ((390, 844), (844, 390), (1440, 1000)):
                page.set_viewport_size({"width": width, "height": height})
                page.wait_for_timeout(100)
                assert source.text_content() == original_text, path
                assert source.is_visible() == (width > 736), path
                assert not page.evaluate(
                    "document.documentElement.scrollWidth > innerWidth"
                ), (path, width, "page overflow")
            page.set_viewport_size({"width": 390, "height": 844})
            print(path, "curated lists, rotation, desktop and page width passed")

        # Browser-only fixtures never change catalogue data. Cover mixed rollout,
        # equal values, >64-character text, four-item cap and reserved characters.
        curated = ["Hetzelfde", ("Een bewust langer kenmerk " * 4).strip(), "<veilig> · intact",
                   "Vierde", "Vijfde niet mobiel"]
        from html import escape
        markup = "".join(
            '<span data-comparison-feature>' + escape(value) + "</span>"
            for value in curated
        )
        page.set_content(
            '<div class="table-wrapper"><table class="product-table">'
            "<thead><tr><th>Product</th><th>Kenmerken</th></tr></thead><tbody>"
            "<tr><td>A</td><td>" + markup + "</td></tr>"
            "<tr><td>B</td><td>" + markup + "</td></tr>"
            "<tr><td>C</td><td>Terugval · Tweede niet mobiel</td></tr>"
            "<tr><td>D</td><td>—</td></tr></tbody></table></div>"
        )
        page.add_script_tag(path=str(ROOT / "static/assets/js/category-experience.js"))
        rows = page.locator(".compact-comparison-table tbody tr")
        for index in (0, 1):
            assert rows.nth(index).locator("li").all_text_contents() == curated[:4]
        assert rows.nth(2).locator("td").inner_text() == "Terugval"
        assert rows.nth(3).locator("td").inner_text() == "—"
        print("Mixed rollout, identical and long features, escaping and four-item cap passed")
        assert not errors, errors
        browser.close()


if __name__ == "__main__":
    run()
