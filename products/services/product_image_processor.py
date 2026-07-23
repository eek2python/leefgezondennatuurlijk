"""Reusable product image processing service.

Standardizes product images onto a square white canvas and saves them as
optimized WebP files. The service is deliberately independent of the
management command so a future custom admin page can call the same
functions, e.g.::

    result = process_manifest_entry(entry, config, force=True)

All values are configured centrally via :class:`ProcessingConfig` and
:class:`PipelinePaths`. Originals are never modified.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
import unicodedata
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageChops, ImageOps, UnidentifiedImageError

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

STATUS_PROCESSED = "processed"
STATUS_UNCHANGED = "unchanged"
STATUS_SKIPPED = "skipped"
STATUS_WARNING = "warning"
STATUS_FAILED = "failed"

# Manifest processing overrides that are allowed and their expected types.
ALLOWED_OVERRIDES = {
    "content_fill_ratio": (int, float),
    "auto_crop": bool,
    "background_color": (list, tuple),
    "vertical_offset": int,
    "horizontal_offset": int,
    "max_upscale_factor": (int, float),
}

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CATEGORY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ManifestError(Exception):
    """Raised when the manifest is invalid or contains unsafe paths."""


@dataclass(frozen=True)
class ProcessingConfig:
    """Central image-processing configuration (see docs/product-image-pipeline.md)."""

    canvas_width: int = 800
    canvas_height: int = 800
    background_color: tuple = (255, 255, 255)
    content_fill_ratio: float = 0.78
    webp_quality: int = 85
    webp_method: int = 6
    min_recommended_source_width: int = 600
    min_recommended_source_height: int = 600
    max_upscale_factor: float = 1.5
    auto_crop: bool = True
    overwrite_existing: bool = False
    # Conservative border-crop heuristics (opaque images).
    border_tolerance: int = 12
    border_lightness_min: int = 235
    # Safety margin retained around the cropped product (fraction of size).
    safety_margin_ratio: float = 0.02
    vertical_offset: int = 0
    horizontal_offset: int = 0

    def merged_with(self, overrides: dict | None) -> "ProcessingConfig":
        if not overrides:
            return self
        values = asdict(self)
        for key, value in overrides.items():
            if key not in ALLOWED_OVERRIDES:
                raise ManifestError(f"Unknown processing override: {key!r}")
            expected = ALLOWED_OVERRIDES[key]
            if not isinstance(value, expected) or isinstance(value, bool) and expected is not bool:
                raise ManifestError(
                    f"Invalid type for processing override {key!r}: {value!r}"
                )
            if key == "background_color":
                if len(value) != 3 or not all(
                    isinstance(c, int) and 0 <= c <= 255 for c in value
                ):
                    raise ManifestError(f"Invalid background_color: {value!r}")
                value = tuple(value)
            if key == "content_fill_ratio" and not 0.1 <= float(value) <= 1.0:
                raise ManifestError(f"content_fill_ratio out of range: {value!r}")
            if key == "max_upscale_factor" and not 1.0 <= float(value) <= 4.0:
                raise ManifestError(f"max_upscale_factor out of range: {value!r}")
            values[key] = value
        values["background_color"] = tuple(values["background_color"])
        return ProcessingConfig(**values)


@dataclass(frozen=True)
class PipelinePaths:
    """Filesystem layout for the pipeline. Override in tests with tmp dirs."""

    base_dir: Path = field(default_factory=lambda: Path(settings.BASE_DIR))

    @property
    def originals_dir(self) -> Path:
        return self.base_dir / "assets" / "product_images" / "originals"

    @property
    def output_dir(self) -> Path:
        return self.base_dir / "static" / "images" / "products"

    @property
    def manifest_path(self) -> Path:
        return self.base_dir / "assets" / "product_images" / "manifest.json"

    @property
    def reports_dir(self) -> Path:
        return self.base_dir / "assets" / "product_images" / "reports"

    @property
    def state_path(self) -> Path:
        return self.reports_dir / "processing-state.json"


@dataclass
class ProcessingResult:
    """Structured result for one manifest entry (admin-page friendly)."""

    product_key: str = ""
    variant_id: str | None = None
    slug: str = ""
    category: str = ""
    source: str = ""
    output: str = ""
    source_format: str = ""
    original_size: tuple | None = None
    cropped_size: tuple | None = None
    resized_size: tuple | None = None
    canvas_size: tuple | None = None
    original_bytes: int = 0
    processed_bytes: int = 0
    saving_percent: float = 0.0
    source_checksum: str = ""
    config_fingerprint: str = ""
    duration_seconds: float = 0.0
    status: str = STATUS_SKIPPED
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    processed_at: str = ""

    @property
    def success(self) -> bool:
        return self.status in (STATUS_PROCESSED, STATUS_UNCHANGED, STATUS_WARNING)

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("original_size", "cropped_size", "resized_size", "canvas_size"):
            if data[key] is not None:
                data[key] = list(data[key])
        return data


# --------------------------------------------------------------------------
# Slug and path helpers
# --------------------------------------------------------------------------

def normalize_slug(text: str) -> str:
    """Normalize arbitrary text into a safe hyphenated slug."""
    text = unicodedata.normalize("NFKD", str(text))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("_", "-").replace(" ", "-")
    text = re.sub(r"[^a-z0-9-]", "", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def _safe_relative(base: Path, relative: str) -> Path:
    """Resolve ``relative`` under ``base`` and refuse escapes."""
    if not relative or Path(relative).is_absolute():
        raise ManifestError(f"Unsafe path: {relative!r}")
    resolved = (base / relative).resolve()
    if not str(resolved).startswith(str(base.resolve()) + os.sep):
        raise ManifestError(f"Path escapes allowed directory: {relative!r}")
    return resolved


def build_output_path(entry: dict, paths: PipelinePaths) -> Path:
    category = entry["category"]
    slug = normalize_slug(entry["slug"])
    return _safe_relative(paths.output_dir, f"{category}/{slug}.webp")


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------

def load_manifest(paths: PipelinePaths) -> list:
    try:
        with open(paths.manifest_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise ManifestError(f"Manifest not found: {paths.manifest_path}")
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Manifest is not valid JSON: {exc}")
    if not isinstance(data, list):
        raise ManifestError("Manifest root must be a JSON list")
    return data


def validate_manifest(entries: list, paths: PipelinePaths,
                      config: ProcessingConfig | None = None) -> list:
    """Validate all entries. Raises ManifestError on the first hard failure.

    Returns a list of warning strings (e.g. missing source files are hard
    errors; low-severity issues become warnings).
    """
    config = config or ProcessingConfig()
    warnings: list = []
    seen_outputs: dict = {}
    seen_keys: dict = {}
    for i, entry in enumerate(entries):
        label = f"manifest entry #{i + 1}"
        if not isinstance(entry, dict):
            raise ManifestError(f"{label}: entry must be an object")
        for required in ("source", "slug", "category", "product_key"):
            if not entry.get(required) or not isinstance(entry[required], str):
                raise ManifestError(f"{label}: missing or invalid '{required}'")
        if "enabled" in entry and not isinstance(entry["enabled"], bool):
            raise ManifestError(f"{label}: 'enabled' must be a boolean")
        category = entry["category"]
        if not _CATEGORY_RE.match(category):
            raise ManifestError(f"{label}: invalid category {category!r}")
        slug = normalize_slug(entry["slug"])
        if not slug or not _SLUG_RE.match(slug):
            raise ManifestError(f"{label}: invalid slug {entry['slug']!r}")

        source_path = _safe_relative(paths.originals_dir, entry["source"])
        if source_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ManifestError(
                f"{label}: unsupported source format {source_path.suffix!r}"
            )
        if not source_path.exists():
            raise ManifestError(f"{label}: source file not found: {entry['source']}")

        output_path = build_output_path(entry, paths)
        if output_path in seen_outputs:
            raise ManifestError(
                f"{label}: duplicate output path {output_path.name!r} "
                f"(also produced by {seen_outputs[output_path]})"
            )
        seen_outputs[output_path] = label

        key = (entry["product_key"], entry.get("variant_id"))
        if key in seen_keys:
            raise ManifestError(
                f"{label}: duplicate product_key/variant_id combination {key!r} "
                f"(also used by {seen_keys[key]})"
            )
        seen_keys[key] = label

        overrides = entry.get("processing")
        if overrides is not None:
            if not isinstance(overrides, dict):
                raise ManifestError(f"{label}: 'processing' must be an object")
            try:
                config.merged_with(overrides)
            except ManifestError as exc:
                raise ManifestError(f"{label}: {exc}")
    return warnings


# --------------------------------------------------------------------------
# Fingerprints / change detection
# --------------------------------------------------------------------------

def _file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def calculate_processing_fingerprint(entry: dict, config: ProcessingConfig) -> str:
    effective = config.merged_with(entry.get("processing"))
    payload = json.dumps(
        {"config": asdict(effective), "slug": normalize_slug(entry["slug"]),
         "category": entry["category"]},
        sort_keys=True, default=list,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_state(paths: PipelinePaths) -> dict:
    try:
        with open(paths.state_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_state(paths: PipelinePaths, state: dict) -> None:
    paths.reports_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(paths.state_path, state)


def _atomic_write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


# --------------------------------------------------------------------------
# Image processing
# --------------------------------------------------------------------------

def _detect_crop_box(image: Image.Image, config: ProcessingConfig, warnings: list):
    """Return a conservative crop box or None (keep the full image)."""
    width, height = image.size
    alpha = image.getchannel("A")
    lo, hi = alpha.getextrema()
    has_transparency = lo < 250

    if has_transparency:
        # Almost fully transparent?
        mask = alpha.point(lambda a: 255 if a > 8 else 0)
        bbox = mask.getbbox()
        if bbox is None:
            warnings.append("image is fully transparent; no crop applied")
            return None
        visible = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if visible < 0.005 * width * height:
            warnings.append("image is almost fully transparent")
        return bbox

    # Opaque image: only crop when the border is demonstrably uniform + light.
    rgb = image.convert("RGB")
    border_pixels = []
    px = rgb.load()
    step = max(1, min(width, height) // 64)
    for x in range(0, width, step):
        border_pixels.append(px[x, 0])
        border_pixels.append(px[x, height - 1])
    for y in range(0, height, step):
        border_pixels.append(px[0, y])
        border_pixels.append(px[width - 1, y])
    avg = tuple(
        sum(p[c] for p in border_pixels) // len(border_pixels) for c in range(3)
    )
    max_dev = max(
        max(abs(p[c] - avg[c]) for c in range(3)) for p in border_pixels
    )
    if max_dev > config.border_tolerance or min(avg) < config.border_lightness_min:
        warnings.append(
            "auto-crop skipped: border background not sufficiently uniform and light"
        )
        return None

    background = Image.new("RGB", rgb.size, avg)
    diff = ImageChops.difference(rgb, background)
    threshold = config.border_tolerance
    mask = diff.convert("L").point(lambda v: 255 if v > threshold else 0)
    bbox = mask.getbbox()
    if bbox is None:
        warnings.append("no content found inside uniform background; no crop applied")
        return None
    return bbox


def _apply_safety_margin(bbox, size, config: ProcessingConfig):
    width, height = size
    margin = max(4, int(round(max(width, height) * config.safety_margin_ratio)))
    left = max(0, bbox[0] - margin)
    top = max(0, bbox[1] - margin)
    right = min(width, bbox[2] + margin)
    bottom = min(height, bbox[3] + margin)
    return (left, top, right, bottom)


def process_product_image(source_path: Path, output_path: Path,
                          config: ProcessingConfig) -> dict:
    """Process one image file. Returns a dict with sizes and warnings.

    Never modifies the source. Writes the output atomically.
    """
    warnings: list = []
    if source_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported source format: {source_path.suffix}")

    try:
        with Image.open(source_path) as opened:
            opened = ImageOps.exif_transpose(opened)
            image = opened.convert("RGBA")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Cannot read image {source_path.name}: {exc}")

    original_size = image.size
    if (original_size[0] < config.min_recommended_source_width
            or original_size[1] < config.min_recommended_source_height):
        warnings.append(
            f"source resolution {original_size[0]}×{original_size[1]} is below the "
            f"recommended {config.min_recommended_source_width}×"
            f"{config.min_recommended_source_height}"
        )

    # Crop
    cropped = image
    if config.auto_crop:
        bbox = _detect_crop_box(image, config, warnings)
        if bbox:
            bbox = _apply_safety_margin(bbox, image.size, config)
            if bbox != (0, 0, image.size[0], image.size[1]):
                cropped = image.crop(bbox)
    cropped_size = cropped.size

    if cropped_size[0] * cropped_size[1] < 0.02 * original_size[0] * original_size[1]:
        warnings.append("cropped product area is very small relative to the source")

    ratio = cropped_size[0] / cropped_size[1]
    if ratio > 4 or ratio < 0.25:
        warnings.append(f"extreme aspect ratio ({ratio:.2f})")

    # Resize into the content box
    content_w = int(config.canvas_width * config.content_fill_ratio)
    content_h = int(config.canvas_height * config.content_fill_ratio)
    scale = min(content_w / cropped_size[0], content_h / cropped_size[1])
    if scale > config.max_upscale_factor:
        warnings.append(
            f"source too small for preferred display size; upscale capped at "
            f"{config.max_upscale_factor}× (needed {scale:.2f}×)"
        )
        scale = config.max_upscale_factor
    resized_size = (
        max(1, int(round(cropped_size[0] * scale))),
        max(1, int(round(cropped_size[1] * scale))),
    )
    resized = cropped.resize(resized_size, Image.Resampling.LANCZOS)

    # Position on the canvas (offsets clamped so the image stays on canvas)
    canvas = Image.new(
        "RGBA",
        (config.canvas_width, config.canvas_height),
        tuple(config.background_color) + (255,),
    )
    base_x = (config.canvas_width - resized_size[0]) // 2
    base_y = (config.canvas_height - resized_size[1]) // 2
    x = min(max(base_x + config.horizontal_offset, 0),
            max(0, config.canvas_width - resized_size[0]))
    y = min(max(base_y + config.vertical_offset, 0),
            max(0, config.canvas_height - resized_size[1]))
    canvas.paste(resized, (x, y), resized)

    final = canvas.convert("RGB")

    # Atomic save as WebP (no EXIF / metadata carried over)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(output_path.parent), suffix=".webp.tmp")
    os.close(fd)
    try:
        final.save(
            tmp_name,
            format="WEBP",
            quality=config.webp_quality,
            method=config.webp_method,
        )
        os.replace(tmp_name, output_path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise

    original_bytes = source_path.stat().st_size
    processed_bytes = output_path.stat().st_size
    if processed_bytes > original_bytes:
        warnings.append("processed file is larger than the original")

    return {
        "source_format": source_path.suffix.lstrip(".").upper(),
        "original_size": original_size,
        "cropped_size": cropped_size,
        "resized_size": resized_size,
        "canvas_size": (config.canvas_width, config.canvas_height),
        "original_bytes": original_bytes,
        "processed_bytes": processed_bytes,
        "warnings": warnings,
    }


# --------------------------------------------------------------------------
# Entry-level processing (used by command, tests and future admin page)
# --------------------------------------------------------------------------

def process_manifest_entry(entry: dict, config: ProcessingConfig | None = None,
                           paths: PipelinePaths | None = None,
                           force: bool = False,
                           dry_run: bool = False) -> ProcessingResult:
    config = config or ProcessingConfig()
    paths = paths or PipelinePaths()
    started = time.monotonic()
    result = ProcessingResult(
        product_key=entry.get("product_key", ""),
        variant_id=entry.get("variant_id"),
        slug=normalize_slug(entry.get("slug", "")),
        category=entry.get("category", ""),
        source=entry.get("source", ""),
        processed_at=datetime.now().isoformat(timespec="seconds"),
    )
    try:
        source_path = _safe_relative(paths.originals_dir, entry["source"])
        output_path = build_output_path(entry, paths)
        result.output = str(output_path.relative_to(paths.base_dir))
        result.source_format = source_path.suffix.lstrip(".").upper()
        result.source_checksum = _file_checksum(source_path)
        result.config_fingerprint = calculate_processing_fingerprint(entry, config)

        if not entry.get("enabled", True):
            result.status = STATUS_SKIPPED
            result.warnings.append("entry disabled in manifest")
            return result

        state = _load_state(paths)
        previous = state.get(result.output, {})
        unchanged = (
            output_path.exists()
            and previous.get("source_checksum") == result.source_checksum
            and previous.get("config_fingerprint") == result.config_fingerprint
        )
        if unchanged and not force:
            result.status = STATUS_UNCHANGED
            result.original_bytes = source_path.stat().st_size
            result.processed_bytes = output_path.stat().st_size
            return result

        if output_path.exists() and not force and not unchanged \
                and not config.overwrite_existing and previous == {}:
            result.status = STATUS_SKIPPED
            result.warnings.append(
                "output already exists and was not created by this pipeline; "
                "use --force to overwrite"
            )
            return result

        if dry_run:
            result.status = STATUS_PROCESSED
            result.warnings.append("dry-run: no files written")
            return result

        effective = config.merged_with(entry.get("processing"))
        info = process_product_image(source_path, output_path, effective)
        result.source_format = info["source_format"]
        result.original_size = info["original_size"]
        result.cropped_size = info["cropped_size"]
        result.resized_size = info["resized_size"]
        result.canvas_size = info["canvas_size"]
        result.original_bytes = info["original_bytes"]
        result.processed_bytes = info["processed_bytes"]
        if result.original_bytes:
            result.saving_percent = round(
                100.0 * (1 - result.processed_bytes / result.original_bytes), 1
            )
        result.warnings.extend(info["warnings"])
        result.status = STATUS_WARNING if result.warnings else STATUS_PROCESSED

        state[result.output] = {
            "source": result.source,
            "source_checksum": result.source_checksum,
            "config_fingerprint": result.config_fingerprint,
            "processed_at": result.processed_at,
        }
        _save_state(paths, state)
    except (ManifestError, ValueError, KeyError, OSError) as exc:
        result.status = STATUS_FAILED
        result.errors.append(str(exc))
    finally:
        result.duration_seconds = round(time.monotonic() - started, 3)
    return result


def write_processing_report(results: list, paths: PipelinePaths) -> Path:
    """Write a timestamped JSON report plus latest.json (both atomic)."""
    paths.reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    report_path = paths.reports_dir / f"product-image-report-{timestamp}.json"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summarize_results(results),
        "images": [r.to_dict() for r in results],
    }
    _atomic_write_json(report_path, payload)
    _atomic_write_json(paths.reports_dir / "latest.json", payload)
    return report_path


def summarize_results(results: list) -> dict:
    original = sum(r.original_bytes for r in results)
    processed = sum(r.processed_bytes for r in results if r.processed_bytes)
    return {
        "processed": sum(
            1 for r in results if r.status in (STATUS_PROCESSED, STATUS_WARNING)
        ),
        "unchanged": sum(1 for r in results if r.status == STATUS_UNCHANGED),
        "skipped": sum(1 for r in results if r.status == STATUS_SKIPPED),
        "warnings": sum(1 for r in results if r.warnings),
        "failed": sum(1 for r in results if r.status == STATUS_FAILED),
        "original_bytes": original,
        "processed_bytes": processed,
        "saving_percent": round(100.0 * (1 - processed / original), 1)
        if original and processed else 0.0,
    }


def filter_entries(entries: list, category: str | None = None,
                   product: str | None = None, source: str | None = None) -> list:
    selected = entries
    if category:
        selected = [e for e in selected if e.get("category") == category]
    if product:
        selected = [e for e in selected if e.get("product_key") == product]
    if source:
        selected = [e for e in selected if e.get("source") == source]
    return selected
