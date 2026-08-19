from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from .database_config import (
    POSTGRES_CONNECTION_MAX_AGE,
    POSTGRES_ENGINE,
    build_database_config,
)


class DatabaseConfigTests(SimpleTestCase):
    base_dir = Path("/app")
    postgres_url = "postgresql://app_user:secret@db.example.test:5432/app_db"

    def build_config(
        self,
        *,
        django_env="development",
        database_backend="sqlite",
        database_url=None,
    ):
        return build_database_config(
            base_dir=self.base_dir,
            django_env=django_env,
            database_backend=database_backend,
            database_url=database_url,
        )

    def test_development_sqlite_ignores_unrelated_database_url(self):
        config = self.build_config(
            database_url=self.postgres_url,
        )

        self.assertEqual(
            config,
            {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": self.base_dir / "db.sqlite3",
                }
            },
        )

    def test_development_postgres_uses_database_url_without_connecting(self):
        config = self.build_config(
            database_backend="postgres",
            database_url=self.postgres_url,
        )["default"]

        self.assertEqual(config["ENGINE"], POSTGRES_ENGINE)
        self.assertEqual(config["NAME"], "app_db")
        self.assertEqual(config["HOST"], "db.example.test")
        self.assertEqual(config["CONN_MAX_AGE"], POSTGRES_CONNECTION_MAX_AGE)
        self.assertTrue(config["CONN_HEALTH_CHECKS"])
        self.assertNotIn("sslmode", config.get("OPTIONS", {}))

    def test_production_postgres_requires_ssl(self):
        config = self.build_config(
            django_env="production",
            database_backend="postgres",
            database_url=self.postgres_url,
        )["default"]

        self.assertEqual(config["ENGINE"], POSTGRES_ENGINE)
        self.assertEqual(config["OPTIONS"]["sslmode"], "require")
        self.assertTrue(config["CONN_HEALTH_CHECKS"])

    def test_production_postgres_without_database_url_fails(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "DATABASE_URL must be configured in production.",
        ):
            self.build_config(
                django_env="production",
                database_backend="postgres",
            )

    def test_production_never_falls_back_to_sqlite(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "DJANGO_DB_BACKEND must be 'postgres'",
        ):
            self.build_config(django_env="production")

    def test_malformed_database_url_fails(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "DATABASE_URL must be a valid PostgreSQL database URL.",
        ):
            self.build_config(
                database_backend="postgres",
                database_url="not-a-database-url",
            )

    def test_empty_postgres_database_name_fails(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "DATABASE_URL must be a valid PostgreSQL database URL.",
        ):
            self.build_config(
                database_backend="postgres",
                database_url="postgresql://",
            )

    def test_non_postgres_database_url_fails(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "DATABASE_URL must be a valid PostgreSQL database URL.",
        ):
            self.build_config(
                database_backend="postgres",
                database_url="mysql://user:secret@db.example.test/app_db",
            )

    def test_unsupported_backend_fails(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "Unsupported DJANGO_DB_BACKEND: mysql",
        ):
            self.build_config(database_backend="mysql")