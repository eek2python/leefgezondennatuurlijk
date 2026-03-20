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

All 6 category pages use the same pattern:

1. **Data file** (`products/data_<category>.py`) — list of product dicts with: `slug`, `name`, `brand`, `material`, `image`, `image_path`, `description`, `pros`, `cons`, `rating`, `rating_count`, `price`, `currency`, `availability`, `affiliate_url`, `price_range`, `verdict`, `award`
2. **Conclusie file** (`products/data_conclusies_<category>.py`) — a single `{title, text}` dict
3. **View** (`products/views.py`) — enriches products with `rating_class` and `award_class`, generates `json_ld` (Schema.org ItemList), passes `products`, `product_count`, `conclusie`, `json_ld` to template
4. **Template** (`templates/<category>.html`) — uses `{% for product in products %}{% include "partials/product_block.html" %}{% endfor %}` for product cards; `{{ json_ld|safe }}` for structured data

### Categories

| Category | Data file | Products | Notes |
|---|---|---|---|
| koekenpannen | data_koekenpannen.py | 10 per size | Size-based (24/26/28 cm) |
| hapjespannen | data_hapjespannen.py | 10 per size | Size-based (24/26/28 cm) |
| wokpannen | data_wokpannen.py | 10 per size | Size-based (28/30/32 cm) |
| snijplanken | data_snijplanken.py | 10 | image_path: "images" |
| airfryers | data_airfryers.py | 6 | image_path: "images" |
| vershoudcontainers | data_vershoudcontainers.py | 5 | image_path: "images/vershoudbakjes" |

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
