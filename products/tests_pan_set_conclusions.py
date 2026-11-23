import copy
from unittest.mock import patch

from django.test import TestCase

from products.content_koekenpannen import CONTENT as CERAMIC_CONTENT
from products.content_rvs_koekenpannen import CONTENT as RVS_CONTENT


class PanSetConclusionTests(TestCase):
    def test_all_set_pages_show_their_own_conclusion(self):
        legacy_content = copy.deepcopy(RVS_CONTENT)
        legacy_content["conclusies"] = {
            size: {"title": f"Keuze voor {size}", "text": f"Bestaand advies voor {size}."}
            for size in ("20_28", "24_28", "20_24_28")
        }
        for path, content in (
            ("/rvs-koekenpannen/", legacy_content),
        ):
            for size in ("20_28", "24_28", "20_24_28"):
                with self.subTest(path=path, size=size):
                    with patch("products.views.RVS_KOEKENPANNEN_CONTENT", content):
                        response = self.client.get(path, {"size": size})
                    expected = content["conclusies"][size]
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context["selected_size"], size)
                    self.assertGreater(response.context["product_count"], 0)
                    self.assertEqual(response.context["conclusie"], expected)
                    self.assertContains(response, f"<h2>{expected['title']}</h2>", html=True)
                    self.assertContains(response, f"<p>{expected['text']}</p>", html=True)

    def test_rvs_formats_use_general_guidance_without_invented_conclusions(self):
        for path, content in (
            ("/rvs-koekenpannen/", RVS_CONTENT),
        ):
            with self.subTest(path=path):
                response = self.client.get(path, {"size": "28"})
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("conclusies", content)
                self.assertEqual(response.context["conclusie"], {})
                self.assertContains(response, content["how_we_assess"]["title"])

    def test_ceramic_formats_use_the_general_guidance_without_conclusions(self):
        self.assertNotIn("conclusies", CERAMIC_CONTENT)
        for size in ("28", "20_28", "24_28", "20_24_28"):
            with self.subTest(size=size):
                response = self.client.get("/koekenpannen/", {"size": size})
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("conclusie", response.context)
                self.assertNotContains(response, "Conclusie voor")
                self.assertContains(response, "Prijsniveaus binnen deze vergelijking")
