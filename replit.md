# LeefNatuurlijkenGezond

A Django-based website for natural and healthy living product comparisons (Dutch: "Live Naturally and Healthy").

## Architecture

- **Framework**: Django 5.2.6
- **Database**: SQLite (db.sqlite3)
- **Static files**: WhiteNoise for serving static assets
- **Production server**: Gunicorn

## Project Structure

- `LeefNatuurlijkenGezond/` - Django project settings, URLs, WSGI/ASGI, sitemap view
- `products/` - Products app with data-driven category pages
- `blogs/` - Blogs app with filesystem-template-based blog detail pages
- `templates/` - HTML templates (category pages + partials)
- `static/` - Static assets (CSS, images)

## Data-driven Architecture

All 6 category pages use a standardised three-file content architecture per category:

1. **Products file** (`products/products_<category>.py`) — dict of product dicts keyed by slug. Each product has: `slug`, `name`, `brand`, `material`, `features` (list), `image`, `image_path`, `description`, `pros`, `cons`, `rating`, `rating_count`, `price`, `currency`, `availability`, `affiliate_url`, `price_range`, `verdict`, `award`
2. **Rankings file** (`products/rankings_<category>.py`) — maps size (or `"default"`) → ordered list of product slugs
3. **Content file** (`products/content_<category>.py`) — `CONTENT` dict with schema: `hero`, `why_choose`, `size_guide` (None for flat cats), `products_section`, `tips`, `conclusies`, `faq`
4. **View** (`products/views.py`) — enriches products with `rating_class` and `award_class`; generates `json_ld` (Schema.org ItemList) and `faq_ld` (FAQPage); passes `products`, `product_count`, `content`, `faq_ld`, `hero_h1`, `products_h2`, `comparison_title`, `conclusie`, `json_ld` to template
5. **Template** (`templates/<category>.html`) — data-driven via context vars; `{% for product in products %}{% include "partials/product_block.html" %}{% endfor %}`; `{{ faq_ld|safe }}` for FAQ structured data

### Categories

| Category | Type | Rankings key | image_path |
|---|---|---|---|
| koekenpannen | size-based | 24/26/28 cm | `images/koekenpannen` |
| hapjespannen | size-based | 24/26/28 cm | `images/hapjespannen` |
| wokpannen | size-based | 28/30/32 cm | `images/wokpannen` |
| snijplanken | flat | `"default"` | `images` |
| airfryers | flat | `"default"` | `images` |
| vershoudcontainers | flat | `"default"` | `images/vershoudbakjes` |

### Key Partials
- `templates/partials/product_block.html` — renders one product card; image and title link to `/product/<slug>/` detail page
- `templates/partials/related_categories.html` — "Ontdek andere categorieën" section, included at bottom of all 6 category pages
- `templates/partials/breadcrumbs.html` — breadcrumb navigation with JSON-LD BreadcrumbList structured data
- `templates/partials/affiliate_disclosure.html` — transparency disclosure for affiliate links
- `templates/partials/author_byline.html` — author/editorial team byline
- `templates/partials/newsletter_signup.html` — newsletter signup placeholder (sidebar, no backend integration yet)

### Product Color Variants (optional, reusable)
- Add an optional `variants` list to any product dict. Each variant: `name`, `image` (filename in the product's `image_path`), `hex` (swatch colour), and optional `affiliate_url` and `price_range` (displayed price string).
- When `variants` is present, `templates/partials/product_block.html` renders the first variant as the default image plus circular colour swatches; products without `variants` render unchanged.
- `static/assets/js/variants.js` (loaded site-wide in base.html) handles swatch clicks: per-card scoped vanilla JS, lazy preload + fade swap, alt-text update, active-state toggle, affiliate-button URL swap, and price-text swap. Swatches without `affiliate_url` / `price_range` fall back to the product-level value (`data-base-affiliate` / `data-base-price`).
- Swatch / media CSS lives near `.product-block` in `static/assets/css/main.css`.
- SEO: variants are card-only and client-side. No new URLs/pages per colour; canonical and Schema.org structured data stay tied to the single base `product.image`.
- **Important**: all variant images for a product must share the same aspect ratio (the example GreenPan airfryer uses 1200×800) to avoid layout shift when switching.
- Example wired on the GreenPan Silhouette airfryer (`products/products_airfryers.py`): Moroccan Green / Crème / Smokey Blue.

### Product Shape/Format Variants (optional, reusable)
- Distinct from the colour-swatch system: shape variants have an `id` key (colour swatches don't) and render as labelled buttons instead of swatches
- Product dict gets `variant_label` (e.g. "Vorm") + `variants` list; each variant: `id` (unique), `label`, `shape`, `capacities` (ml), `image`, `image_path`, `price`, `price_last_checked`, `currency`, `availability`, `affiliate_url`, `is_default` (exactly one True)
- Shared editorial data (name, description, pros/cons, rating, verdict, award, price_range) stays at family level; the product stays ONE ranked card / table row
- `utils/variant_helpers.py::prepare_product_variants` (called from `_enrich_products`): validates unique ids (ValueError), enriches variants with formatted capacity fields + `image_url` + `alt_text` + `selected_summary`, sets `shape_variants` / `default_variant`, copies default variant's commercial fields to product level (keeps detail page, JSON-LD, no-JS rendering working), sets `capacity_summary` for comparison tables ("Afhankelijk van uitvoering" unless all variants share capacities)
- Template: shape branch in `templates/partials/product_block.html` (semantic buttons, aria-pressed, selected-summary line, affiliate link + hidden disabled span toggled by JS)
- JS: `static/assets/js/variant-selector.js` (card-scoped, data attributes, GA4 `select_product_variant` event when gtag present); CSS: `.product-variant-selector` / `.product-variant-button` in main.css
- First use: Igluu Meal Prep 3-delig (Rond = verified default; Vierkant variant has TODOs awaiting real data)
- **Selector order = priority**: in `variant_selectors` the first selector always shows all its options; later selectors only show options that exist within the earlier choice. For shape+capacity products, put `shape` ("Vorm") first, `capacity` ("Inhoud") second — otherwise shapes get hidden by the selected capacity.
- Second use: Lock&Lock enkel (`locknlock_enkel`, variant_label "Inhoud"): 630 ml / 740 ml / 1 L capacity options. 740 ml = verified default (real product is 740 ml, NOT 750 — user explicitly chose to keep the true capacity; do not "normalize" to 750). 630 ml and 1 L variants have TODOs awaiting real data (no image/price/link yet — CTA shows disabled state per convention)
- `selected_summary` skips the capacity suffix when it equals the variant label (avoids "740 ml · 740 ml")

### Product Detail Pages
- URL: `/product/<slug>/` — dict-based product detail view
- View: `products/views.py::product_detail` — looks up product by slug from `ALL_PRODUCTS_BY_SLUG` dict (simple 1:1 mapping, enforced unique at startup), falls back to DB model
- Template: `templates/product_detail.html` — breadcrumbs, disclosure, image, description, features, pros/cons, verdict, affiliate CTA, back-to-category link
- `CATEGORY_MAP` in views.py maps category keys → (label, url) for breadcrumb generation
- All product slugs are globally unique across categories; duplicate slugs raise `ValueError` at startup
- All product slugs use hyphens (no underscores). Old underscore slugs are 301-redirected to the new hyphen versions via `products/slug_redirects.py` (`SLUG_REDIRECTS` map)

### Trust & Legal Pages
- `/over-ons/` — About page (templates/over_ons.html)
- `/hoe-wij-beoordelen/` — Methodology page (templates/hoe_wij_beoordelen.html)
- `/privacy/` — Privacy policy (templates/privacy.html)
- Views in `products/views.py` (over_ons, hoe_wij_beoordelen, privacy)

### Capacity System (generic, reusable)
- `utils/product_helpers.py` — category-agnostic helpers for products with one or more containers (values in ml): `format_capacities` ([700,700,1500] → "2 × 700 ml + 1,5 L"; sorts, groups equals, ≥1000 ml as liters with comma decimals), `calculate_total_capacity`, `format_total_capacity`, `get_capacity_display(product)`
- Product dicts may have optional `capacities` list (ml); legacy `capacity` field supported as fallback; invalid entries (None/0/negative/strings) are ignored
- `_enrich_products` (views.py) sets `formatted_capacity` / `formatted_total_capacity` on every product (empty strings when absent)
- Display: product detail shows "Inhoud" + "Totale inhoud" (total only for multi-container sets); vershoudcontainers comparison table has an "Inhoud" column (no totals)
- Tests: `products/tests.py` (run with `python manage.py test products`)

### Product Image Pipeline
- Originals in `assets/product_images/originals/<category>/` (not publicly served); manifest at `assets/product_images/manifest.json`; reports in `assets/product_images/reports/`
- Output: `static/images/products/<category>/<slug>.webp` (800×800 white canvas, fill 0.78, WebP q85 m6)
- Service (CLI-independent, admin-page ready): `products/services/product_image_processor.py` — `ProcessingConfig` dataclass, `load_manifest`, `validate_manifest`, `process_manifest_entry`, `write_processing_report`
- Commands: `python manage.py process_product_images` (--all/--category/--product/--source/--dry-run/--force/--check/--report) and `register_product_image` (appends validated manifest entry with backup + atomic write)
- Change detection via source checksum + config fingerprint (state in `reports/processing-state.json`); conservative auto-crop (transparent or uniform light borders only); atomic writes; per-entry `processing` overrides
- Docs: `docs/product-image-pipeline.md`; tests: `products/test_product_image_processor.py` (35 tests)
- Admin page: `/admin/product-images/` (staff-only, `products/admin_views.py` + `templates/admin/product_images.html`) — upload original + category/product_key/slug/variant → registers manifest entry (backup + atomic write) and processes to WebP in one step; per-entry "Verwerk opnieuw" and "Alle entries verwerken" (force) actions; failed uploads roll back manifest entry + saved original; tests: `products/test_admin_image_page.py`

### Vershoudcontainers Uitvoering Selector (page-level)
- `/vershoudcontainers/?uitvoering=enkel|3-delig|5-delig` — server-side selector (no JS), default `enkel`, invalid values fall back to single
- `rankings_vershoudcontainers.py` maps `single` / `set_3` / `set_5` → ordered slug-key lists; `content_vershoudcontainers.py` has a `types` dict with per-type heading/intro/comparison_title/itemlist name+description/conclusie
- View builds per-type JSON-LD ItemList, comparison rows, and shows "Totale inhoud" column only for sets; import-time `_validate_vershoudbakjes_awards` enforces max one of each award per group
- Selector partial: `templates/partials/storage_type_selector.html` (format-pill links, aria-current)
- Canonical stays on base `/vershoudcontainers/` URL for all selector states
- `oxo_good_grips_smart_seal_6delig` is intentionally unranked (entry still contains copy-pasted Glasslock placeholder data)
- Tests: `StorageTypeSelectorTests` in `products/tests.py`
- Second page-level filter: `?formaat=alle|klein|middel|groot` (default `alle`, invalid falls back); classification by LARGEST container (small ≤600 ml, medium ≤1200 ml, large >1200 ml) via `STORAGE_SIZE_THRESHOLDS`/`STORAGE_SIZE_LABELS`/`classify_storage_size`/`get_product_size_categories`/`filter_products_by_storage_size` in `utils/product_helpers.py`
- View helpers: `get_selected_storage_size`, `prepare_storage_product` (sets size_categories/size_labels; under active filter picks matching default variant for shape families and recomputes formatted capacity + size label); both query params preserved in all selector/filter links
- Filter partial: `templates/partials/storage_size_filter.html` (`.storage-size-filter*` classes); product count line, empty state with reset link to `formaat=alle`, "Formaat" column in comparison table, `.product-size-info` line on cards
- Products without valid numeric capacity: shown only under "Alle" + logged warning
- Tests: `StorageSizeClassificationTests`, `StorageSizeFilterPageTests`

### Vershoudbakjes Usage Info ("Geschikt voor")
- Optional `usage` dict per product (and per variant, partial override): keys `oven`/`microwave`/`freezer`/`dishwasher`, each `{container, lid, note}` with True/False/None; None = unknown and is NEVER rendered as "Nee" (row hidden; `container=True, lid=None` renders "Bakje: ja")
- Helpers: `utils/usage_helpers.py` (`merge_usage`, `build_usage_display`, `validate_usage`); wired via `prepare_product_variants` (per-variant `usage_display` + JSON payload rows) and `_enrich_products` fallback; template block `data-shape-usage` in `partials/product_block.html`; variant switch updates rows client-side (`variant-selector.js`)
- Import-time validator `products/validators_vershoudbakjes.py::validate_vershoudbakjes` (called from views.py): raises on structural errors (dup variant ids/option combos, ≠1 default, bad award/usage schema, unknown ranking keys); logs report-only warnings (copied texts between brands, missing images, etc.). Known-suspect copied records (BergHOFF, Glasslock, KitchenBrothers, OXO) intentionally have NO usage data — report only, never invent facts
- Editorial rules for this category: max 3 pros / 2 cons; generic usage claims live in `usage`, not pros/cons
- IKEA 365+ & Mepal EasyClip enkel migrated from legacy shape-as-capacity variants to `variant_selectors` capacity selectors; `pyrex_cook_store_3delig` renamed to `pyrex_cook_store_enkel` (single 800 ml container)
- Full audit + open verification items: `docs/audit-vershoudbakjes.md`; tests: `products/test_usage_vershoudbakjes.py`

### Comparison Template
- `templates/comparison.html` — reusable comparison table template (not yet wired to a URL)

### SEO & Trust Features
- Breadcrumbs with JSON-LD on all category, blog, product detail, and info pages
- Affiliate disclosure on all category and product pages
- Author byline at bottom of all category and blog pages
- GA4 analytics placeholder: renders `<script>` tag when `GA_MEASUREMENT_ID` env var is set
- Context processor: `LeefNatuurlijkenGezond/context_processors.py` passes `GA_MEASUREMENT_ID` to all templates
- Footer links to Over ons, Hoe wij beoordelen, Privacyverklaring
- Footer-level affiliate disclosure
- `lang="nl"` on `<html>` tag

### RVS Koekenpannen (sub-category)
- URL: `/rvs-koekenpannen/` — stainless steel frying pans
- Breadcrumbs: Home › Koekenpannen › RVS

### Sitemap
`LeefNatuurlijkenGezond/sitemap_views.py` generates sitemap.xml dynamically:
- Static URLs: 12 pages using `reverse()` (homepage, 6 categories, rvs-koekenpannen sub-category, blogs overview, over-ons, hoe-wij-beoordelen, privacy)
- Dynamic blog URLs: filesystem scan of `blogs/templates/blogs/*.html` (excludes `blogoverzicht.html`)
- Product detail URLs: all 125 products from `ALL_PRODUCTS_BY_SLUG` (priority 0.6, monthly changefreq)
- Total: 139 URLs (0 duplicates)

### Canonical Host
- Single canonical host: `https://www.leefnatuurlijkengezond.nl` (with `www.`)
- Used consistently in: all `<link rel="canonical">` tags, all `og:url` meta tags, sitemap.xml (`BASE_URL`), and robots.txt (`Sitemap:` directive)
- Non-www → www redirect should be configured at the web server / deployment level

### URL Routing
- All public routes are defined in `LeefNatuurlijkenGezond/urls.py` (project-level URLconf)
- `products/urls.py` is intentionally empty and **not** included anywhere — kept only to avoid accidental re-inclusion
- Blog routes live in `blogs/urls.py` (included at `/blogs/`)

### Future URL Structure (planned, NOT yet implemented)
The current flat `/product/<slug>/` namespace will eventually move to a categorised structure for better SEO. See `.local/url-structure-audit.md` for the full audit and 10-step migration plan. Target structure:

```
/<category>/                        # category landing (unchanged)
/<category>/<product-slug>/         # categorised product detail (new)
/koekenpannen/rvs/                  # RVS moves under koekenpannen
/koekenpannen/rvs/<product-slug>/
/vershoudbakjes/                    # rename of /vershoudcontainers/ (Dutch consistency)
/blog/<slug>/                       # optional: singular blog path
/gids/<slug>/                       # RESERVED for future buyers' guides
/vergelijk/<slug>/                  # RESERVED for future head-to-head comparisons
```

Reserved namespaces `/gids/` and `/vergelijk/` must NOT be used for anything else. Disambiguator suffixes in current slugs (`-hapjespan-`, `-wok-`) will be dropped once the category is in the URL path. All migrations will use HTTP 301 redirects with no chains.

## Running the App

Development:
```
python manage.py runserver 0.0.0.0:5000
```

Production (Gunicorn):
```
gunicorn --bind=0.0.0.0:5000 --reuse-port LeefNatuurlijkenGezond.wsgi:application
```

## Configuration

- `ALLOWED_HOSTS = ['*']` - Already set for Replit proxy compatibility
- `DEBUG` - Controlled via `DEBUG` environment variable (defaults to `True`)
- `SECRET_KEY` - Set via `SECRET_KEY` environment variable

## Dependencies

Managed via `requirements.txt`. Install with:
```
pip install -r requirements.txt
```
