"""Template tag voor automatische cache-busting van statische bestanden.

Gebruik in templates:

    {% load static_version %}
    <link rel="stylesheet" href="{% static_v 'assets/css/main.css' %}" />

In productie (ManifestStaticFilesStorage via WhiteNoise) krijgt het bestand al
een content-hash in de bestandsnaam; dan geeft deze tag gewoon de standaard
static-URL terug. In development (DEBUG) wordt automatisch een
``?v=<content-hash>`` toegevoegd op basis van de bestandsinhoud, zodat
bezoekers na elke wijziging altijd de nieuwste versie krijgen — zonder
handmatige versienummers.
"""
import hashlib

from django import template
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import ManifestFilesMixin, staticfiles_storage
from django.templatetags.static import static

register = template.Library()

# Cache van berekende hashes per (pad, mtime) zodat we niet bij elke request
# het bestand opnieuw hoeven te lezen.
_hash_cache = {}


def _file_version(path):
    """Korte content-hash van een statisch bestand, of None indien onvindbaar."""
    file_path = finders.find(path)
    if not file_path:
        return None
    try:
        import os
        mtime = os.path.getmtime(file_path)
    except OSError:
        return None
    cache_key = (file_path, mtime)
    if cache_key not in _hash_cache:
        try:
            with open(file_path, "rb") as f:
                digest = hashlib.md5(f.read()).hexdigest()[:12]
        except OSError:
            return None
        _hash_cache[cache_key] = digest
    return _hash_cache[cache_key]


@register.simple_tag
def static_v(path):
    """Zoals {% static %}, maar met automatische versie-parameter."""
    url = static(path)
    # Manifest-storage hasht de bestandsnaam zelf al (productie/collectstatic).
    if isinstance(staticfiles_storage, ManifestFilesMixin):
        return url
    version = _file_version(path)
    if version:
        return f"{url}?v={version}"
    return url
