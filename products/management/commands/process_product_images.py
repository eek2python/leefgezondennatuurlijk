"""Management command for the product image processing pipeline.

All business logic lives in products/services/product_image_processor.py so a
future custom admin page can reuse it. This command only handles CLI parsing,
progress output and exit codes.
"""

from django.core.management.base import BaseCommand, CommandError

from products.services import product_image_processor as pipeline


def _fmt_bytes(num):
    if num >= 1024 * 1024:
        return f"{num / (1024 * 1024):.1f} MB"
    return f"{num / 1024:.0f} KB"


class Command(BaseCommand):
    help = "Process product images from assets/product_images/ into static/images/products/"

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true",
                            help="Process all enabled manifest entries")
        parser.add_argument("--category", help="Process one category")
        parser.add_argument("--product", help="Process one product family (product_key)")
        parser.add_argument("--source", help="Process one manifest entry by source path")
        parser.add_argument("--dry-run", action="store_true",
                            help="Validate and show intended actions without writing files")
        parser.add_argument("--force", action="store_true",
                            help="Reprocess files even when unchanged")
        parser.add_argument("--check", action="store_true",
                            help="Only validate manifest, originals and existing outputs")
        parser.add_argument("--report", action="store_true",
                            help="Write a detailed JSON report")

    def handle(self, *args, **options):
        paths = pipeline.PipelinePaths()
        config = pipeline.ProcessingConfig()

        selectors = [bool(options["all"]), bool(options["category"]),
                     bool(options["product"]), bool(options["source"])]
        if sum(selectors) > 1:
            raise CommandError(
                "Use only one of --all, --category, --product or --source."
            )
        if not any(selectors) and not options["check"]:
            raise CommandError(
                "Choose a selection: --all, --category, --product or --source "
                "(or use --check to only validate)."
            )

        try:
            entries = pipeline.load_manifest(paths)
            pipeline.validate_manifest(entries, paths, config)
        except pipeline.ManifestError as exc:
            raise CommandError(f"Manifest validation failed: {exc}")

        if options["check"]:
            missing_outputs = [
                str(pipeline.build_output_path(e, paths).name)
                for e in entries
                if e.get("enabled", True)
                and not pipeline.build_output_path(e, paths).exists()
            ]
            self.stdout.write(self.style.SUCCESS(
                f"Manifest OK: {len(entries)} entries, all source files present."
            ))
            if missing_outputs:
                self.stdout.write(
                    "Not yet processed: " + ", ".join(missing_outputs)
                )
            if not any(selectors):
                return

        selected = pipeline.filter_entries(
            [e for e in entries if e.get("enabled", True)],
            category=options["category"],
            product=options["product"],
            source=options["source"],
        )
        if not selected and (options["category"] or options["product"]
                             or options["source"]):
            raise CommandError("No manifest entries match the given selection.")
        if not selected:
            self.stdout.write("Manifest is empty; nothing to process.")
            return

        results = []
        total = len(selected)
        for index, entry in enumerate(selected, start=1):
            result = pipeline.process_manifest_entry(
                entry, config, paths,
                force=options["force"], dry_run=options["dry_run"],
            )
            results.append(result)
            label = result.product_key + (
                f" ({result.variant_id})" if result.variant_id else ""
            )
            self.stdout.write(f"[{index}/{total}] {label}")
            self.stdout.write(f"      source: {result.source}")
            self.stdout.write(f"      output: {result.output}")
            self.stdout.write(f"      status: {result.status}")
            if result.original_size and result.resized_size:
                o, c, r = result.original_size, result.cropped_size, result.resized_size
                self.stdout.write(
                    f"      dimensions: {o[0]}×{o[1]} → crop {c[0]}×{c[1]} → "
                    f"{r[0]}×{r[1]} on {result.canvas_size[0]}×{result.canvas_size[1]}"
                )
            if result.processed_bytes:
                self.stdout.write(
                    f"      file size: {_fmt_bytes(result.original_bytes)} → "
                    f"{_fmt_bytes(result.processed_bytes)}"
                )
                if result.saving_percent:
                    self.stdout.write(f"      saving: {result.saving_percent}%")
            for warning in result.warnings:
                self.stdout.write(self.style.WARNING(f"      warning: {warning}"))
            for error in result.errors:
                self.stdout.write(self.style.ERROR(f"      error: {error}"))

        summary = pipeline.summarize_results(results)
        self.stdout.write("")
        self.stdout.write(f"Processed: {summary['processed']}")
        self.stdout.write(f"Unchanged: {summary['unchanged']}")
        self.stdout.write(f"Skipped: {summary['skipped']}")
        self.stdout.write(f"Warnings: {summary['warnings']}")
        self.stdout.write(f"Failed: {summary['failed']}")
        if summary["original_bytes"]:
            self.stdout.write(f"Original size: {_fmt_bytes(summary['original_bytes'])}")
            self.stdout.write(f"Processed size: {_fmt_bytes(summary['processed_bytes'])}")
            self.stdout.write(f"Total saving: {summary['saving_percent']}%")

        if options["report"] and not options["dry_run"]:
            report_path = pipeline.write_processing_report(results, paths)
            self.stdout.write(f"Report written: {report_path}")
        elif options["report"] and options["dry_run"]:
            report_path = pipeline.write_processing_report(results, paths)
            self.stdout.write(f"Dry-run report written: {report_path}")

        if summary["failed"]:
            raise CommandError(f"{summary['failed']} image(s) failed processing.")
