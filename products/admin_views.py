"""Staff-only admin page for the product image pipeline.

Reuses products/services/product_image_processor.py — the same logic as the
management commands, but driven from the browser: upload an original,
register it in the manifest and process it to the final WebP in one step.
"""

import shutil
from datetime import datetime
from pathlib import Path

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.urls import reverse

from products.services import product_image_processor as pipeline

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


def _backup_and_write_manifest(paths, entries):
    backup = paths.manifest_path.with_suffix(
        f".json.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    shutil.copy2(paths.manifest_path, backup)
    pipeline._atomic_write_json(paths.manifest_path, entries)
    try:
        pipeline.validate_manifest(pipeline.load_manifest(paths), paths)
    except pipeline.ManifestError:
        shutil.copy2(backup, paths.manifest_path)
        raise


def _known_categories(paths):
    if not paths.originals_dir.exists():
        return []
    return sorted(p.name for p in paths.originals_dir.iterdir() if p.is_dir())


def _handle_upload(request, paths, config):
    upload = request.FILES.get("image")
    category = (request.POST.get("category") or "").strip()
    new_category = (request.POST.get("new_category") or "").strip()
    if new_category:
        category = pipeline.normalize_slug(new_category)
    product_key = (request.POST.get("product_key") or "").strip()
    slug = pipeline.normalize_slug(request.POST.get("slug") or "")
    variant_id = (request.POST.get("variant_id") or "").strip()

    if not upload:
        raise pipeline.ManifestError("Geen bestand gekozen.")
    if upload.size > MAX_UPLOAD_BYTES:
        raise pipeline.ManifestError("Bestand is groter dan 20 MB.")
    suffix = Path(upload.name).suffix.lower()
    if suffix not in pipeline.SUPPORTED_EXTENSIONS:
        raise pipeline.ManifestError(
            f"Bestandstype {suffix or '(geen)'} wordt niet ondersteund "
            f"(wel: {', '.join(sorted(pipeline.SUPPORTED_EXTENSIONS))})."
        )
    if not category or not pipeline._CATEGORY_RE.match(category):
        raise pipeline.ManifestError("Kies of vul een geldige categorie in.")
    if not product_key:
        raise pipeline.ManifestError("Vul de product key in (bijv. igluu_meal_prep_3delig).")
    if not slug:
        raise pipeline.ManifestError("Vul een geldige slug in (kleine letters en koppeltekens).")

    filename = pipeline.normalize_slug(Path(upload.name).stem) or slug
    source_rel = f"{category}/{filename}{suffix}"
    source_path = pipeline._safe_relative(paths.originals_dir, source_rel)
    if source_path.exists():
        raise pipeline.ManifestError(
            f"Er bestaat al een origineel met de naam {source_rel!r}. "
            "Hernoem het bestand en probeer opnieuw."
        )

    entries = pipeline.load_manifest(paths)
    entry = {
        "source": source_rel,
        "slug": slug,
        "category": category,
        "product_key": product_key,
        "enabled": True,
    }
    if variant_id:
        entry["variant_id"] = variant_id

    # Save the original first so validation can see the file.
    source_path.parent.mkdir(parents=True, exist_ok=True)
    with open(source_path, "wb") as fh:
        for chunk in upload.chunks():
            fh.write(chunk)

    try:
        candidate = entries + [entry]
        pipeline.validate_manifest(candidate, paths)
        _backup_and_write_manifest(paths, candidate)
    except pipeline.ManifestError:
        source_path.unlink(missing_ok=True)
        raise

    result = pipeline.process_manifest_entry(entry, config, paths, force=True)
    pipeline.write_processing_report([result], paths)

    if result.status == pipeline.STATUS_FAILED:
        # Transactional upload: roll back the manifest entry and the saved
        # original so a failed upload leaves nothing behind.
        remaining = [
            e for e in pipeline.load_manifest(paths)
            if e.get("source") != source_rel
        ]
        _backup_and_write_manifest(paths, remaining)
        source_path.unlink(missing_ok=True)
    return result


def _process_entries(entries, config, paths, force):
    results = [
        pipeline.process_manifest_entry(e, config, paths, force=force)
        for e in entries
    ]
    if results:
        pipeline.write_processing_report(results, paths)
    return results


def _report_results(request, results):
    for r in results:
        label = f"{r.product_key}{f' ({r.variant_id})' if r.variant_id else ''}"
        if r.status == pipeline.STATUS_FAILED:
            messages.error(request, f"{label}: mislukt — {'; '.join(r.errors)}")
        elif r.warnings:
            messages.warning(
                request,
                f"{label}: {r.status} met waarschuwingen — {'; '.join(r.warnings)}",
            )
        else:
            messages.success(request, f"{label}: {r.status} → {r.output}")


@staff_member_required
def product_images_admin(request):
    paths = pipeline.PipelinePaths()
    config = pipeline.ProcessingConfig()

    if request.method == "POST":
        action = request.POST.get("action")
        force = request.POST.get("force") == "on"
        try:
            if action == "upload":
                result = _handle_upload(request, paths, config)
                _report_results(request, [result])
            elif action == "process_one":
                source = request.POST.get("source") or ""
                entries = pipeline.filter_entries(
                    pipeline.load_manifest(paths), source=source
                )
                if not entries:
                    messages.error(request, f"Geen manifest-entry voor {source!r}.")
                else:
                    _report_results(
                        request, _process_entries(entries, config, paths, force=True)
                    )
            elif action == "process_all":
                entries = pipeline.load_manifest(paths)
                pipeline.validate_manifest(entries, paths)
                _report_results(
                    request, _process_entries(entries, config, paths, force=force)
                )
            else:
                messages.error(request, "Onbekende actie.")
        except pipeline.ManifestError as exc:
            messages.error(request, str(exc))
        return redirect(reverse("admin_product_images"))

    manifest_error = None
    rows = []
    try:
        entries = pipeline.load_manifest(paths)
    except pipeline.ManifestError as exc:
        entries = []
        manifest_error = str(exc)

    state = pipeline._load_state(paths)
    for entry in entries:
        output_url = ""
        try:
            output_path = pipeline.build_output_path(entry, paths)
            output_rel = str(output_path.relative_to(paths.base_dir))
            output_exists = output_path.exists()
            if output_exists:
                output_url = "/" + str(
                    output_path.relative_to(paths.base_dir / "static" / "images")
                )
                output_url = f"/static/images{output_url}"
        except (pipeline.ManifestError, ValueError, KeyError):
            output_rel, output_exists = "(ongeldig pad)", False
        source_exists = False
        try:
            source_exists = pipeline._safe_relative(
                paths.originals_dir, entry.get("source", "")
            ).exists()
        except pipeline.ManifestError:
            pass
        rows.append({
            "entry": entry,
            "source_exists": source_exists,
            "output": output_rel,
            "output_exists": output_exists,
            "output_url": output_url,
            "processed_at": state.get(output_rel, {}).get("processed_at", ""),
        })

    return render(request, "admin/product_images.html", {
        "title": "Productafbeeldingen",
        "rows": rows,
        "categories": _known_categories(paths),
        "manifest_error": manifest_error,
        "config": config,
    })
