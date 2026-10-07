from django.test import TestCase

from products.content_koekenpannen import CONTENT as CERAMIC_CONTENT
from products.content_rvs_koekenpannen import CONTENT as RVS_CONTENT


class PanSetConclusionTests(TestCase):
    def test_all_set_pages_show_their_own_conclusion(self):
        for path, content in (
            ("/koekenpannen/", CERAMIC_CONTENT),
            ("/rvs-koekenpannen/", RVS_CONTENT),
        ):
            for size in ("20_28", "24_28", "20_24_28"):
                with self.subTest(path=path, size=size):
                    response = self.client.get(path, {"size": size})
                    expected = content["conclusies"][size]
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context["selected_size"], size)
                    self.assertGreater(response.context["product_count"], 0)
                    self.assertEqual(response.context["conclusie"], expected)
                    self.assertContains(response, f"<h2>{expected['title']}</h2>", html=True)
                    self.assertContains(response, f"<p>{expected['text']}</p>", html=True)

    def test_single_pan_conclusions_are_unchanged(self):
        for path, content in (
            ("/koekenpannen/", CERAMIC_CONTENT),
            ("/rvs-koekenpannen/", RVS_CONTENT),
        ):
            with self.subTest(path=path):
                response = self.client.get(path, {"size": "28"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["conclusie"], content["conclusies"][28])
