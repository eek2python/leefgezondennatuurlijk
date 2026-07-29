"""Volledige productaudit vanaf de commandline.

Gebruik:
    python manage.py audit_products
    python manage.py audit_products --audit price_levels
    python manage.py audit_products --category koekenpannen
    python manage.py audit_products --strict
    python manage.py audit_products --no-save   (zonder DB-opslag)

Gebruikt exact dezelfde registry en runner als het admindashboard
(/admin/product-audits/). Console-output wordt opgebouwd uit hetzelfde
gestructureerde resultaat; netwerkafhankelijke audits blijven uit.
"""

from django.core.management.base import BaseCommand, CommandError

from audits import runner as audit_runner
from audits.registry import all_audits, get_audit


class Command(BaseCommand):
    help = "Voer geregistreerde productaudits uit via de centrale runner."

    def add_arguments(self, parser):
        parser.add_argument(
            "--audit", help="Eén specifieke audit-key (standaard: alle veilige audits)."
        )
        parser.add_argument("--category", help="Beperk tot één categorie.")
        parser.add_argument(
            "--strict", action="store_true",
            help="Exit met foutcode bij warnings én errors.",
        )
        parser.add_argument(
            "--no-save", action="store_true",
            help="Voer audits uit zonder runs in de database te bewaren.",
        )

    def handle(self, *args, **options):
        category = options.get("category") or None
        key = options.get("audit")
        errors = warnings = 0

        if options.get("no_save"):
            errors, warnings = self._run_without_persist(key, category)
        elif key:
            run = audit_runner.run_audit(key, category=category)
            self._print_run(run)
            errors, warnings = run.error_count, run.warning_count
        else:
            parent = audit_runner.run_full_audit(category=category)
            self._print_run(parent)
            for child in parent.children.all():
                self._print_run(child, indent="  ")
            errors, warnings = parent.error_count, parent.warning_count

        if errors or (options.get("strict") and warnings):
            raise CommandError(
                f"Audit: {errors} fout(en), {warnings} waarschuwing(en)"
            )

    def _run_without_persist(self, key, category):
        definitions = (
            [get_audit(key)] if key else
            [d for d in all_audits() if d.admin_runnable]
        )
        if key and (definitions[0] is None or not definitions[0].admin_runnable):
            raise CommandError(f"Onbekende of niet-lokale audit: {key!r}")
        errors = warnings = 0
        for definition in definitions:
            cat = category if definition.supports_category else None
            issues, _meta = definition.runner(category=cat, params={})
            e = sum(1 for i in issues if i.severity in ("error", "critical"))
            w = sum(1 for i in issues if i.severity == "warning")
            errors += e
            warnings += w
            self.stdout.write(
                f"{definition.key}: {len(issues)} issues ({e} fouten, {w} waarschuwingen)"
            )
            for issue in issues:
                self.stdout.write(
                    f"  [{issue.severity}] {issue.code} | {issue.category or '-'} | "
                    f"{issue.product_slug or '-'} | {issue.message}"
                )
        return errors, warnings

    def _print_run(self, run, indent=""):
        self.stdout.write(
            f"{indent}{run.audit_key} (run #{run.pk}): {run.status} — "
            f"{run.error_count} fouten, {run.warning_count} waarschuwingen"
            + (f" — {run.failure_message}" if run.failure_message else "")
        )
        for issue in run.issues.all():
            self.stdout.write(
                f"{indent}  [{issue.severity}] {issue.code} | {issue.category or '-'} | "
                f"{issue.product_slug or '-'} | {issue.message}"
            )
