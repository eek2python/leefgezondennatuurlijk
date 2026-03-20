# LeefNatuurlijkenGezond

A Django-based website for natural and healthy living product comparisons (Dutch: "Live Naturally and Healthy").

## Architecture

- **Framework**: Django 5.2.6
- **Database**: SQLite (db.sqlite3)
- **Static files**: WhiteNoise for serving static assets
- **Production server**: Gunicorn

## Project Structure

- `LeefNatuurlijkenGezond/` - Django project settings, URLs, WSGI/ASGI
- `products/` - Products app (airfryers, pans, woks, etc.)
- `blogs/` - Blogs app
- `templates/` - HTML templates
- `static/` - Static assets (CSS, images)

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
