"""Server-rendered accessibility contract; interaction checks live in scripts/."""
from django.test import TestCase


class MobileMarkupTests(TestCase):
    def test_zoom_allowed_and_shared_helpers_loaded(self):
        response = self.client.get("/")
        self.assertContains(response, 'content="width=device-width, initial-scale=1"')
        self.assertNotContains(response, "user-scalable=no")
        self.assertContains(response, "assets/js/mobile-accessibility.js")

    def test_submenu_uses_native_button_and_closed_content_is_inert(self):
        response = self.client.get("/")
        self.assertContains(
            response,
            '<button type="button" class="opener" aria-expanded="false" '
            'aria-controls="menu-pannen">Pannen</button>',
        )
        self.assertContains(response, '<ul id="menu-pannen" inert>')

    def test_detail_variants_use_same_payload_and_controls_as_listing(self):
        response = self.client.get("/product/ikea-365-plus-enkel/")
        self.assertContains(response, "data-shape-page")
        self.assertContains(response, "data-variant-option")
        self.assertContains(response, 'id="variant-data-ikea-365-plus-enkel"')
        self.assertContains(response, '"resolved_url"')
        self.assertNotContains(response, "data-shape-option")
