"""One public origin for canonical, sitemap and structured-data URLs."""

from urllib.parse import urljoin

from django.conf import settings


def absolute_site_url(path="/"):
    """Resolve an internal path against the public origin, not the request host.

    Absolute external URLs (e.g. a future image CDN) remain external.
    """
    return urljoin(settings.SITE_URL.rstrip("/") + "/", path)
