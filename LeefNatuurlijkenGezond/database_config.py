"""Deterministic database selection for Django settings."""

from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured


POSTGRES_ENGINE = "django.db.backends.postgresql"
POSTGRES_CONNECTION_MAX_AGE = 600


def build_database_config(
    *,
    base_dir: Path,
    django_env: str,
    database_backend: str,
    database_url: str | None,
) -> dict:
    """Build ``DATABASES`` without inferring a backend from ``DATABASE_URL``.

    SQLite remains the explicit development default. PostgreSQL is only
    selected through ``DJANGO_DB_BACKEND=postgres``; production additionally
    requires that selection and a valid PostgreSQL URL.
    """

    environment = (django_env or "development").strip().lower()
    backend = (database_backend or "sqlite").strip().lower()
    is_production = environment == "production"

    if is_production and backend != "postgres":
        raise ImproperlyConfigured(
            "DJANGO_DB_BACKEND must be 'postgres' when DJANGO_ENV is "
            "'production'."
        )

    if backend == "sqlite":
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": base_dir / "db.sqlite3",
            }
        }

    if backend != "postgres":
        raise ImproperlyConfigured(
            f"Unsupported DJANGO_DB_BACKEND: {database_backend}"
        )

    if not database_url or not database_url.strip():
        if is_production:
            message = "DATABASE_URL must be configured in production."
        else:
            message = "DATABASE_URL is required when PostgreSQL is selected."
        raise ImproperlyConfigured(message)

    try:
        postgres_config = dj_database_url.parse(
            database_url.strip(),
            conn_max_age=POSTGRES_CONNECTION_MAX_AGE,
            conn_health_checks=True,
            ssl_require=is_production,
        )
    except Exception as exc:
        raise ImproperlyConfigured(
            "DATABASE_URL must be a valid PostgreSQL database URL."
        ) from exc

    if (
        postgres_config.get("ENGINE") != POSTGRES_ENGINE
        or not str(postgres_config.get("NAME") or "").strip()
    ):
        raise ImproperlyConfigured(
            "DATABASE_URL must be a valid PostgreSQL database URL."
        )

    return {"default": postgres_config}