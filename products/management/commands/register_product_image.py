"""Append a validated entry to the product image manifest.

Example:
    python manage.py register_product_image \
        --source vershoudbakjes/igluu-original.webp \
        --product igluu_meal_prep_3delig \
        --category vershoudbakjes \
        --slug igluu-meal-prep-3delig-rond \
        --variant round
"""

import json
import shutil
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from products.services import product_image_processor as pipeline


class Command(BaseCommand):
    help = "Add a validated entry to assets/product_images/manifest.json"

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True,
                            help="Path relative to the originals directory")
        parser.add_argument("--product", required=True, help="product_key")
        parser.add_argument("--category", required=True)
        parser.add_argument("--slug", required=True)
        parser.add_argument("--variant", help="Optional variant id")

    def handle(self, *args, **options):
        paths = pipeline.PipelinePaths()
        try:
            entries = pipeline.load_manifest(paths)
        except pipeline.ManifestError as exc:
            raise CommandError(str(exc))

        entry = {
            "source": options["source"],
            "slug": options["slug"],
            "category": options["category"],
            "product_key": options["product"],
            "enabled": True,
        }
        if options["variant"]:
            entry["variant_id"] = options["variant"]

        for existing in entries:
            if existing.get("source") == entry["source"]:
                raise CommandError(
                    f"An entry for source {entry['source']!r} already exists."
                )

        candidate = entries + [entry]
        try:
            pipeline.validate_manifest(candidate, paths)
        except pipeline.ManifestError as exc:
            raise CommandError(f"New entry is invalid: {exc}")

        backup = paths.manifest_path.with_suffix(
            f".json.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        shutil.copy2(paths.manifest_path, backup)
        pipeline._atomic_write_json(paths.manifest_path, candidate)

        try:
            pipeline.validate_manifest(pipeline.load_manifest(paths), paths)
        except pipeline.ManifestError as exc:
            shutil.copy2(backup, paths.manifest_path)
            raise CommandError(f"Manifest invalid after update, restored backup: {exc}")

        self.stdout.write(self.style.SUCCESS(
            f"Entry added for {entry['product_key']} "
            f"({entry.get('variant_id') or 'no variant'}). Backup: {backup.name}"
        ))
