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
- `templates/partials/product_block.html` — renders one product card
- `templates/partials/related_categories.html` — "Ontdek andere categorieën" section, included at bottom of all 6 category pages

### Sitemap
`LeefNatuurlijkenGezond/sitemap_views.py` generates sitemap.xml dynamically:
- Static URLs: 8 pages using `reverse()` (homepage, 6 categories, blogs overview)
- Dynamic blog URLs: filesystem scan of `blogs/templates/blogs/*.html` (excludes `blogoverzicht.html`)

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
