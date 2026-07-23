# Product Image Pipeline

Standardizes product images onto an 800×800 white canvas and saves them as
optimized WebP files for consistent product cards and fast loading. Originals
are always preserved and never modified.

## Directory layout

| Purpose | Location |
|---|---|
| Original source images (never served publicly) | `assets/product_images/originals/<category>/` |
| Manifest (maps sources → outputs) | `assets/product_images/manifest.json` |
| JSON reports + `latest.json` | `assets/product_images/reports/` |
| Processed website images | `static/images/products/<category>/<slug>.webp` |

Categories: `airfryers`, `keramische-koekenpannen`, `rvs-koekenpannen`,
`hapjespannen`, `wokpannen`, `snijplanken`, `vershoudbakjes`.

## Supported formats

Sources: `.jpg`, `.jpeg`, `.png`, `.webp`. Output is always WebP (quality 85,
method 6, no metadata). AVIF is not supported. Unsupported or corrupt files
are reported as `failed`; remaining files are still processed.

## Configuration defaults

Central config: `ProcessingConfig` in
`products/services/product_image_processor.py`.

- Canvas: 800×800, white background `(255, 255, 255)`
- Content fill ratio: 0.78 (product fits within 624×624)
- WebP: quality 85, method 6
- Minimum recommended source size: 600×600 (warning below)
- Maximum upscale: 1.5×
- Auto-crop: on (conservative — only uniform, light borders or transparency)
- Existing outputs not created by the pipeline are never overwritten without `--force`

## Adding a manifest entry

Either edit `assets/product_images/manifest.json` (a JSON list) by hand:

```json
[
  {
    "source": "vershoudbakjes/igluu-meal-prep-round.webp",
    "slug": "igluu-meal-prep-3delig-rond",
    "category": "vershoudbakjes",
    "product_key": "igluu_meal_prep_3delig",
    "variant_id": "round",
    "enabled": true
  },
  {
    "source": "vershoudbakjes/igluu-meal-prep-square.jpg",
    "slug": "igluu-meal-prep-3delig-vierkant",
    "category": "vershoudbakjes",
    "product_key": "igluu_meal_prep_3delig",
    "variant_id": "square",
    "enabled": true,
    "processing": { "content_fill_ratio": 0.74, "vertical_offset": 0 }
  }
]
```

`variant_id` is optional — products without variants simply omit it.

Or use the helper command (validates, backs up the manifest, writes atomically):

```
python manage.py register_product_image \
    --source vershoudbakjes/igluu-original.webp \
    --product igluu_meal_prep_3delig \
    --category vershoudbakjes \
    --slug igluu-meal-prep-3delig-rond \
    --variant round
```

## Output naming

The output name comes from the manifest `slug`, normalized: lowercase, spaces
and underscores → hyphens, accents transliterated, punctuation removed,
repeated hyphens collapsed. `"GreenPan Bistro XL"` → `greenpan-bistro-xl.webp`.
Duplicate output paths are a validation error — nothing is silently
overwritten.

## Commands (run in the Replit Shell from the project root)

```
python manage.py process_product_images --check              # validate only
python manage.py process_product_images --all --dry-run      # show intended actions
python manage.py process_product_images --all                # process everything
python manage.py process_product_images --category vershoudbakjes
python manage.py process_product_images --product igluu_meal_prep_3delig
python manage.py process_product_images --source vershoudbakjes/example.jpg
python manage.py process_product_images --all --force        # reprocess unchanged
python manage.py process_product_images --all --report       # write JSON report
```

Use exactly one of `--all` / `--category` / `--product` / `--source`.
Unchanged files (same source checksum + same configuration) are skipped as
`unchanged`; `--force` reprocesses them. Changing a relevant configuration
value also triggers reprocessing automatically.

## Warnings

Warnings are printed per image and included in reports. They cover: low
source resolution, capped upscaling, skipped auto-crop (background not
uniform/light enough), extreme aspect ratios, near-transparent images, output
larger than the original, very small cropped areas. Warnings do **not** cause
a failing exit status — only validation errors and processing failures do.

## Fixing one problematic image

Add a `processing` object to that entry only, e.g.:

```json
"processing": {
  "auto_crop": false,
  "content_fill_ratio": 0.70,
  "vertical_offset": -20,
  "background_color": [250, 250, 250],
  "max_upscale_factor": 1.2
}
```

## Why originals must never be manually overwritten

The pipeline detects changes via checksums. Overwriting an original destroys
the ability to reprocess with better settings later and breaks change
detection. Always add new files under new names instead.

## Recommended first migration (five test images)

1. Place five originals with different characteristics in
   `assets/product_images/originals/<category>/`:
   a JPG with white background, a transparent PNG, an existing WebP, an image
   with excessive white space, and a low-resolution image.
2. Add the five entries to `manifest.json`.
3. `python manage.py process_product_images --dry-run --report`
4. `python manage.py process_product_images --all --report`
5. Visually inspect the five outputs in `static/images/products/`.
6. Adjust global defaults or per-image `processing` overrides if needed.
7. Only after approval, add the remaining originals.

## Future admin page

All logic lives in `products/services/product_image_processor.py` and is
CLI-independent:

```python
from products.services import product_image_processor as pipeline

entry = {...}  # a manifest entry dict
result = pipeline.process_manifest_entry(entry, pipeline.ProcessingConfig(), force=True)
result.success, result.output, result.resized_size, result.processed_bytes,
result.warnings, result.errors
```
