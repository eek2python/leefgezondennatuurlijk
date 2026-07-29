from django.apps import AppConfig


class AuditsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "audits"
    verbose_name = "Productaudits"

    def ready(self):
        # Registreer alle beschikbare audits bij het opstarten.
        from audits import checks  # noqa: F401
