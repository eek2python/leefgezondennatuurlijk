"""Tests for the staff-only product image admin page."""

import io
import json
import shutil
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from products.services import product_image_processor as pipeline

URL = reverse("admin_product_images")


def _png_bytes(size=(700, 700), color=(200, 40, 40)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


class AdminImagePageTestCase(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.paths = pipeline.PipelinePaths(base_dir=self.tmp)
        self.paths.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.paths.manifest_path.write_text("[]", encoding="utf-8")
        patcher = mock.patch(
            "products.admin_views.pipeline.PipelinePaths",
            return_value=self.paths,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.staff = User.objects.create_user(
            "staff", "s@example.com", "pw", is_staff=True
        )
        self.client.force_login(self.staff)

    def _manifest(self):
        return json.loads(self.paths.manifest_path.read_text(encoding="utf-8"))


class AccessTests(AdminImagePageTestCase):
    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_non_staff_redirected(self):
        user = User.objects.create_user("plain", "p@example.com", "pw")
        self.client.force_login(user)
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 302)

    def test_staff_sees_page(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Productafbeeldingen")


class UploadTests(AdminImagePageTestCase):
    def _upload(self, **overrides):
        data = {
            "action": "upload",
            "image": SimpleUploadedFile("Test Photo.png", _png_bytes(),
                                        content_type="image/png"),
            "new_category": "vershoudbakjes",
            "product_key": "test_product",
            "slug": "test-product-enkel",
        }
        data.update(overrides)
        return self.client.post(URL, data, follow=True)

    def test_upload_registers_and_processes(self):
        response = self._upload()
        self.assertEqual(response.status_code, 200)
        manifest = self._manifest()
        self.assertEqual(len(manifest), 1)
        entry = manifest[0]
        self.assertEqual(entry["slug"], "test-product-enkel")
        self.assertEqual(entry["category"], "vershoudbakjes")
        self.assertEqual(entry["source"], "vershoudbakjes/test-photo.png")
        original = self.paths.originals_dir / "vershoudbakjes" / "test-photo.png"
        self.assertTrue(original.exists())
        output = self.paths.output_dir / "vershoudbakjes" / "test-product-enkel.webp"
        self.assertTrue(output.exists())
        with Image.open(output) as img:
            self.assertEqual(img.size, (800, 800))
            self.assertEqual(img.format, "WEBP")

    def test_upload_with_variant_id(self):
        self._upload(variant_id="round")
        self.assertEqual(self._manifest()[0]["variant_id"], "round")

    def test_unsupported_extension_rejected(self):
        response = self._upload(
            image=SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain")
        )
        self.assertContains(response, "wordt niet ondersteund")
        self.assertEqual(self._manifest(), [])

    def test_missing_category_rejected(self):
        response = self._upload(new_category="", category="")
        self.assertContains(response, "categorie")
        self.assertEqual(self._manifest(), [])

    def test_duplicate_original_filename_rejected(self):
        self._upload()
        response = self._upload(slug="ander-product", product_key="ander_product")
        self.assertContains(response, "bestaat al een origineel")
        self.assertEqual(len(self._manifest()), 1)

    def test_duplicate_slug_rejected_and_original_cleaned_up(self):
        self._upload()
        response = self._upload(
            image=SimpleUploadedFile("other.png", _png_bytes(),
                                     content_type="image/png"),
            product_key="ander_product",
        )
        self.assertContains(response, "duplicate")
        self.assertEqual(len(self._manifest()), 1)
        self.assertFalse(
            (self.paths.originals_dir / "vershoudbakjes" / "other.png").exists()
        )

    def test_corrupt_image_reports_failure_and_rolls_back(self):
        response = self._upload(
            image=SimpleUploadedFile("broken.png", b"not-an-image",
                                     content_type="image/png")
        )
        self.assertContains(response, "mislukt")
        self.assertEqual(self._manifest(), [])
        self.assertFalse(
            (self.paths.originals_dir / "vershoudbakjes" / "broken.png").exists()
        )


class ProcessActionTests(AdminImagePageTestCase):
    def _register(self):
        src_dir = self.paths.originals_dir / "vershoudbakjes"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "sample.png").write_bytes(_png_bytes())
        entry = {
            "source": "vershoudbakjes/sample.png",
            "slug": "sample-product",
            "category": "vershoudbakjes",
            "product_key": "sample_product",
            "enabled": True,
        }
        self.paths.manifest_path.write_text(
            json.dumps([entry]), encoding="utf-8"
        )
        return entry

    def test_process_one(self):
        self._register()
        response = self.client.post(URL, {
            "action": "process_one",
            "source": "vershoudbakjes/sample.png",
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        output = self.paths.output_dir / "vershoudbakjes" / "sample-product.webp"
        self.assertTrue(output.exists())

    def test_process_one_unknown_source(self):
        response = self.client.post(URL, {
            "action": "process_one",
            "source": "does/not-exist.png",
        }, follow=True)
        self.assertContains(response, "Geen manifest-entry")

    def test_process_all(self):
        self._register()
        response = self.client.post(URL, {"action": "process_all"}, follow=True)
        self.assertEqual(response.status_code, 200)
        output = self.paths.output_dir / "vershoudbakjes" / "sample-product.webp"
        self.assertTrue(output.exists())

    def test_manifest_row_listed_on_page(self):
        self._register()
        response = self.client.get(URL)
        self.assertContains(response, "sample_product")
        self.assertContains(response, "vershoudbakjes/sample.png")
