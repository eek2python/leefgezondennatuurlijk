"""Tests for the product image processing pipeline.

Uses temporary directories and programmatically generated images only —
no dependency on real production images.
"""

import io
import json
import shutil
import tempfile
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase
from PIL import Image

from products.services import product_image_processor as pipeline


def make_image(path, size=(1000, 800), color=(200, 30, 30), mode="RGB",
               fmt=None, background=None, product_box=None, exif_orientation=None):
    """Create a test image. Optionally a product rectangle on a background."""
    if background is not None:
        img = Image.new(mode, size, background)
        if product_box:
            for x in range(product_box[0], product_box[2]):
                for y in range(product_box[1], product_box[3]):
                    img.putpixel((x, y), color)
    else:
        img = Image.new(mode, size, color)
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {}
    if exif_orientation:
        exif = Image.Exif()
        exif[274] = exif_orientation
        kwargs["exif"] = exif
    img.save(path, format=fmt, **kwargs)
    return path


class PipelineTestCase(SimpleTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.paths = pipeline.PipelinePaths(base_dir=self.tmp)
        self.paths.originals_dir.mkdir(parents=True)
        self.paths.output_dir.mkdir(parents=True)
        self.config = pipeline.ProcessingConfig()

    def write_manifest(self, entries):
        self.paths.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.paths.manifest_path.write_text(json.dumps(entries))

    def entry(self, source="cat/test.jpg", slug="test-product",
              category="cat", product_key="test_product", **extra):
        return {"source": source, "slug": slug, "category": category,
                "product_key": product_key, "enabled": True, **extra}

    def source(self, name="cat/test.jpg", **kwargs):
        kwargs.setdefault("background", (255, 255, 255))
        if kwargs["background"] is not None:
            w, h = kwargs.get("size", (1000, 800))
            kwargs.setdefault("product_box",
                              (w // 4, h // 4, 3 * w // 4, 3 * h // 4))
        return make_image(self.paths.originals_dir / name, **kwargs)

    def process(self, entry, **kwargs):
        return pipeline.process_manifest_entry(entry, self.config, self.paths, **kwargs)


class SlugTests(SimpleTestCase):
    def test_slug_normalization(self):
        self.assertEqual(pipeline.normalize_slug("GreenPan Bistro XL"),
                         "greenpan-bistro-xl")
        self.assertEqual(pipeline.normalize_slug("Igluu Meal Prep – Rond"),
                         "igluu-meal-prep-rond")
        self.assertEqual(pipeline.normalize_slug("Crème_brûlée  --  pan"),
                         "creme-brulee-pan")
        self.assertEqual(pipeline.normalize_slug("--weird--"), "weird")


class FormatTests(PipelineTestCase):
    def test_jpeg_becomes_webp(self):
        self.source()
        result = self.process(self.entry())
        self.assertTrue(result.success)
        out = self.tmp / result.output
        self.assertEqual(out.suffix, ".webp")
        with Image.open(out) as img:
            self.assertEqual(img.format, "WEBP")

    def test_png_transparency_flattened_onto_white(self):
        self.source("cat/t.png", size=(700, 700), mode="RGBA",
                    color=(255, 0, 0, 0))
        # red square in centre, transparent border
        path = self.paths.originals_dir / "cat/t.png"
        img = Image.new("RGBA", (700, 700), (0, 0, 0, 0))
        for x in range(200, 500):
            for y in range(200, 500):
                img.putpixel((x, y), (200, 0, 0, 255))
        img.save(path)
        result = self.process(self.entry(source="cat/t.png"))
        self.assertTrue(result.success)
        with Image.open(self.tmp / result.output) as out:
            self.assertEqual(out.mode, "RGB")
            self.assertEqual(out.getpixel((5, 5)), (255, 255, 255))

    def test_webp_input_processed_directly(self):
        self.source("cat/t.webp", fmt="WEBP")
        result = self.process(self.entry(source="cat/t.webp"))
        self.assertTrue(result.success)
        self.assertEqual(result.source_format, "WEBP")

    def test_exif_orientation_applied(self):
        # 600x900 with orientation 6 (90° CW) → effective 900x600
        self.source("cat/t.jpg", size=(600, 900), exif_orientation=6)
        result = self.process(self.entry(source="cat/t.jpg"))
        self.assertEqual(result.original_size, (900, 600))


class GeometryTests(PipelineTestCase):
    def test_canvas_exactly_800x800_and_aspect_preserved(self):
        self.source(size=(1600, 800))
        result = self.process(self.entry())
        with Image.open(self.tmp / result.output) as out:
            self.assertEqual(out.size, (800, 800))
        w, h = result.resized_size
        cw, ch = result.cropped_size
        self.assertAlmostEqual(w / h, cw / ch, places=1)

    def test_content_within_content_area(self):
        self.source(size=(2000, 2000))
        result = self.process(self.entry())
        limit = int(800 * self.config.content_fill_ratio)
        self.assertLessEqual(result.resized_size[0], limit)
        self.assertLessEqual(result.resized_size[1], limit)

    def test_transparent_borders_cropped(self):
        path = self.paths.originals_dir / "cat/t.png"
        img = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
        for x in range(400, 600):
            for y in range(400, 600):
                img.putpixel((x, y), (10, 10, 200, 255))
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        result = self.process(self.entry(source="cat/t.png"))
        self.assertTrue(result.success)
        self.assertLess(result.cropped_size[0], 400)

    def test_uniform_white_border_cropped_conservatively(self):
        self.source(size=(1000, 1000), background=(255, 255, 255),
                    color=(30, 30, 30), product_box=(300, 300, 700, 700))
        result = self.process(self.entry())
        self.assertLess(result.cropped_size[0], 1000)
        self.assertGreaterEqual(result.cropped_size[0], 400)  # margin kept

    def test_non_uniform_background_not_cropped(self):
        path = self.paths.originals_dir / "cat/photo.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (800, 800))
        for x in range(800):
            for y in range(800):
                img.putpixel((x, y), (x % 256, y % 256, 120))
        img.save(path)
        result = self.process(self.entry(source="cat/photo.jpg"))
        self.assertEqual(result.cropped_size, result.original_size)
        self.assertTrue(any("auto-crop skipped" in w for w in result.warnings))

    def test_fully_white_image_does_not_crash(self):
        self.source(size=(700, 700), color=(255, 255, 255))
        result = self.process(self.entry())
        self.assertNotEqual(result.status, pipeline.STATUS_FAILED)

    def test_fully_transparent_image_warns(self):
        path = self.paths.originals_dir / "cat/t.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (700, 700), (0, 0, 0, 0)).save(path)
        result = self.process(self.entry(source="cat/t.png"))
        self.assertTrue(result.warnings)
        self.assertTrue(any("transparent" in w for w in result.warnings))

    def test_small_image_not_upscaled_beyond_max(self):
        self.source(size=(200, 200))
        result = self.process(self.entry())
        self.assertLessEqual(result.resized_size[0],
                             int(200 * self.config.max_upscale_factor) + 1)
        self.assertTrue(any("upscale" in w for w in result.warnings))


class ManifestValidationTests(PipelineTestCase):
    def test_duplicate_output_names_rejected(self):
        self.source("cat/a.jpg")
        self.source("cat/b.jpg")
        entries = [
            self.entry(source="cat/a.jpg", slug="Same Name", product_key="a"),
            self.entry(source="cat/b.jpg", slug="same-name", product_key="b"),
        ]
        with self.assertRaisesMessage(pipeline.ManifestError, "duplicate output"):
            pipeline.validate_manifest(entries, self.paths)

    def test_duplicate_product_key_variant_rejected(self):
        self.source("cat/a.jpg")
        self.source("cat/b.jpg")
        entries = [
            self.entry(source="cat/a.jpg", slug="a", variant_id="round"),
            self.entry(source="cat/b.jpg", slug="b", variant_id="round"),
        ]
        with self.assertRaisesMessage(pipeline.ManifestError, "duplicate product_key"):
            pipeline.validate_manifest(entries, self.paths)

    def test_unsafe_relative_paths_rejected(self):
        entries = [self.entry(source="../../etc/passwd.png")]
        with self.assertRaises(pipeline.ManifestError):
            pipeline.validate_manifest(entries, self.paths)

    def test_missing_source_rejected(self):
        entries = [self.entry(source="cat/missing.jpg")]
        with self.assertRaisesMessage(pipeline.ManifestError, "not found"):
            pipeline.validate_manifest(entries, self.paths)

    def test_missing_required_field_rejected(self):
        with self.assertRaises(pipeline.ManifestError):
            pipeline.validate_manifest([{"source": "cat/a.jpg"}], self.paths)

    def test_invalid_processing_override_rejected(self):
        self.source("cat/a.jpg")
        entries = [self.entry(source="cat/a.jpg",
                              processing={"content_fill_ratio": "big"})]
        with self.assertRaises(pipeline.ManifestError):
            pipeline.validate_manifest(entries, self.paths)

    def test_variants_optional(self):
        self.source("cat/a.jpg")
        self.source("cat/b.jpg")
        entries = [
            self.entry(source="cat/a.jpg", slug="a", product_key="pa"),
            self.entry(source="cat/b.jpg", slug="b", product_key="pb",
                       variant_id="round"),
        ]
        pipeline.validate_manifest(entries, self.paths)  # no exception


class ChangeDetectionTests(PipelineTestCase):
    def test_unchanged_skipped_and_force_reprocesses(self):
        self.source()
        entry = self.entry()
        first = self.process(entry)
        self.assertEqual(first.status, pipeline.STATUS_PROCESSED)
        second = self.process(entry)
        self.assertEqual(second.status, pipeline.STATUS_UNCHANGED)
        third = self.process(entry, force=True)
        self.assertEqual(third.status, pipeline.STATUS_PROCESSED)

    def test_config_change_causes_reprocessing(self):
        self.source()
        entry = self.entry()
        self.process(entry)
        changed = dict(entry, processing={"content_fill_ratio": 0.6})
        result = self.process(changed)
        self.assertEqual(result.status, pipeline.STATUS_PROCESSED)

    def test_source_change_causes_reprocessing(self):
        self.source()
        entry = self.entry()
        self.process(entry)
        self.source(color=(0, 200, 0))
        result = self.process(entry)
        self.assertEqual(result.status, pipeline.STATUS_PROCESSED)

    def test_existing_foreign_output_not_overwritten_without_force(self):
        self.source()
        entry = self.entry()
        out = pipeline.build_output_path(entry, self.paths)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"pre-existing")
        result = self.process(entry)
        self.assertEqual(result.status, pipeline.STATUS_SKIPPED)
        self.assertEqual(out.read_bytes(), b"pre-existing")
        forced = self.process(entry, force=True)
        self.assertEqual(forced.status, pipeline.STATUS_PROCESSED)
        self.assertNotEqual(out.read_bytes(), b"pre-existing")

    def test_dry_run_writes_no_files(self):
        self.source()
        entry = self.entry()
        result = self.process(entry, dry_run=True)
        self.assertTrue(result.success)
        self.assertFalse(pipeline.build_output_path(entry, self.paths).exists())


class ReportTests(PipelineTestCase):
    def test_report_contains_required_fields(self):
        self.source()
        result = self.process(self.entry())
        report_path = pipeline.write_processing_report([result], self.paths)
        data = json.loads(report_path.read_text())
        self.assertIn("summary", data)
        image = data["images"][0]
        for key in ("product_key", "variant_id", "source", "output",
                    "source_format", "original_size", "cropped_size",
                    "resized_size", "canvas_size", "original_bytes",
                    "processed_bytes", "saving_percent", "source_checksum",
                    "config_fingerprint", "duration_seconds", "status",
                    "warnings", "errors", "processed_at"):
            self.assertIn(key, image)
        self.assertTrue((self.paths.reports_dir / "latest.json").exists())

    def test_failure_does_not_block_other_entries(self):
        self.source("cat/good.jpg")
        bad = self.paths.originals_dir / "cat/bad.jpg"
        bad.write_bytes(b"not an image")
        entries = [
            self.entry(source="cat/bad.jpg", slug="bad", product_key="bad"),
            self.entry(source="cat/good.jpg", slug="good", product_key="good"),
        ]
        results = [self.process(e) for e in entries]
        self.assertEqual(results[0].status, pipeline.STATUS_FAILED)
        self.assertEqual(results[1].status, pipeline.STATUS_PROCESSED)


class CommandTests(PipelineTestCase):
    def call(self, *args, **kwargs):
        out = io.StringIO()
        with mock.patch.object(pipeline, "PipelinePaths", return_value=self.paths):
            call_command("process_product_images", *args, stdout=out, **kwargs)
        return out.getvalue()

    def test_command_requires_selection(self):
        self.write_manifest([])
        with self.assertRaises(CommandError):
            self.call()

    def test_command_check_valid_empty_manifest(self):
        self.write_manifest([])
        output = self.call("--check")
        self.assertIn("Manifest OK", output)

    def test_command_all_processes_and_reports(self):
        self.source()
        self.write_manifest([self.entry()])
        output = self.call("--all", "--report")
        self.assertIn("Processed: 1", output)
        self.assertIn("Failed: 0", output)
        self.assertTrue(list(self.paths.reports_dir.glob("product-image-report-*.json")))

    def test_command_nonzero_exit_on_invalid_manifest(self):
        self.write_manifest([{"source": "cat/x.jpg"}])
        with self.assertRaises(CommandError):
            self.call("--all")

    def test_command_nonzero_exit_on_processing_failure(self):
        bad = self.paths.originals_dir / "cat/bad.jpg"
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_bytes(b"not an image")
        self.write_manifest([self.entry(source="cat/bad.jpg")])
        with self.assertRaises(CommandError):
            self.call("--all")

    def test_command_warning_only_is_not_failure(self):
        self.source(size=(300, 300))  # low resolution → warning
        self.write_manifest([self.entry()])
        output = self.call("--all")
        self.assertIn("Failed: 0", output)

    def test_command_rejects_ambiguous_selectors(self):
        self.write_manifest([])
        with self.assertRaises(CommandError):
            self.call("--all", "--category", "cat")


class RegisterCommandTests(PipelineTestCase):
    def test_register_appends_and_rejects_duplicates(self):
        self.source("cat/new.jpg")
        self.write_manifest([])
        with mock.patch.object(pipeline, "PipelinePaths", return_value=self.paths):
            call_command(
                "register_product_image", "--source", "cat/new.jpg",
                "--product", "new_product", "--category", "cat",
                "--slug", "new-product", stdout=io.StringIO(),
            )
            entries = pipeline.load_manifest(self.paths)
            self.assertEqual(len(entries), 1)
            with self.assertRaises(CommandError):
                call_command(
                    "register_product_image", "--source", "cat/new.jpg",
                    "--product", "new_product", "--category", "cat",
                    "--slug", "new-product", stdout=io.StringIO(),
                )
