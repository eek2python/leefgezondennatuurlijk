"""Centrale auditrunner.

Voert geregistreerde audits synchroon uit (het project heeft bewust geen
achtergrondtaakinfrastructuur), bewaart runs en issues, en beschermt tegen
dubbele gelijktijdige uitvoering. Alle audits zijn read-only: er wordt
nooit productdata gewijzigd.
"""

import logging

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from audits.models import ProductAuditIssue, ProductAuditRun
from audits.registry import get_audit

logger = logging.getLogger(__name__)

#: Sleutel van de volledige projectaudit (batch met kinderen).
FULL_AUDIT_KEY = "full_project"


class AuditAlreadyRunning(Exception):
    pass


class UnknownAudit(Exception):
    pass


def _validate(key, category):
    definition = get_audit(key)
    if definition is None:
        raise UnknownAudit(f"Onbekende audit: {key!r}")
    if category and definition.categories and category not in definition.categories:
        raise ValueError(f"Ongeldige categorie: {category!r}")
    return definition


def _claim_run(key, title, category, user, params, parent=None):
    """Maak atomisch een 'running'-rij aan; weiger als er al één draait."""
    try:
        with transaction.atomic():
            return ProductAuditRun.objects.create(
                audit_key=key,
                title=title,
                status="running",
                requested_by=user if getattr(user, "pk", None) else None,
                category=category or "",
                parameters=params or {},
                parent=parent,
                started_at=timezone.now(),
            )
    except IntegrityError:
        # DB-constraint unique_running_audit_per_key: er draait er al één.
        raise AuditAlreadyRunning(f"Audit '{key}' draait al.")


def _finish(run, issues, metadata, failure=None):
    run.finished_at = timezone.now()
    if run.started_at:
        run.duration_ms = int(
            (run.finished_at - run.started_at).total_seconds() * 1000
        )
    if failure is not None:
        run.status = "failed"
        # Beperkte melding; volledige traceback alleen in serverlog.
        run.failure_message = str(failure)[:1000]
    else:
        run.status = "completed"
        run.metadata = metadata or {}
        run.issue_count = len(issues)
        run.error_count = sum(
            1 for i in issues if i.severity in ("error", "critical")
        )
        run.warning_count = sum(1 for i in issues if i.severity == "warning")
        ProductAuditIssue.objects.bulk_create(
            [
                ProductAuditIssue(
                    run=run,
                    code=i.code,
                    severity=i.severity,
                    category=i.category or "",
                    product_slug=i.product_slug or "",
                    variant_id=i.variant_id or "",
                    field=i.field or "",
                    message=i.message,
                    expected=i.expected or "",
                    actual=i.actual or "",
                    file_path=i.file_path or "",
                )
                for i in issues
            ]
        )
    run.save()
    _apply_retention(run.audit_key)
    return run


def _apply_retention(audit_key):
    """Retentie is opt-in via settings.AUDIT_RUN_RETENTION_PER_KEY.

    Standaard (None) wordt niets automatisch verwijderd — er is nog geen
    expliciet projectbeleid."""
    keep = getattr(settings, "AUDIT_RUN_RETENTION_PER_KEY", None)
    if not keep:
        return
    stale_ids = list(
        ProductAuditRun.objects.filter(audit_key=audit_key, parent__isnull=True)
        .order_by("-created_at")
        .values_list("id", flat=True)[int(keep):]
    )
    if stale_ids:
        ProductAuditRun.objects.filter(id__in=stale_ids).delete()


def run_audit(key, category=None, user=None, params=None, parent=None):
    """Voer één geregistreerde audit uit en bewaar het resultaat."""
    definition = _validate(key, category)
    if not definition.admin_runnable:
        raise ValueError(
            f"Audit '{key}' is netwerkafhankelijk en niet geschikt voor "
            f"directe uitvoering. Gebruik: {definition.cli_hint}"
        )
    run = _claim_run(key, definition.title, category, user, params, parent)
    try:
        issues, metadata = definition.runner(category=category, params=params or {})
    except Exception as exc:
        logger.exception("Audit '%s' is mislukt", key)
        return _finish(run, [], {}, failure=exc)
    return _finish(run, issues, metadata)


def run_full_audit(category=None, user=None, params=None):
    """Volledige projectaudit: alle veilige lokale audits na elkaar in één
    batch. Gaat door wanneer één niet-kritieke audit faalt; failures worden
    per kind apart gerapporteerd. Netwerkaudits blijven uit."""
    from audits.registry import all_audits

    parent = _claim_run(
        FULL_AUDIT_KEY, "Volledige productaudit", category, user, params
    )
    total_issues = errors = warnings = 0
    failed_children = []
    try:
        for definition in all_audits():
            if not definition.admin_runnable:
                continue
            child_category = category if definition.supports_category else None
            try:
                child = run_audit(
                    definition.key,
                    category=child_category,
                    user=user,
                    params=params,
                    parent=parent,
                )
            except AuditAlreadyRunning:
                failed_children.append((definition.key, "draait al"))
                continue
            if child.status == "failed":
                failed_children.append((definition.key, child.failure_message))
            total_issues += child.issue_count
            errors += child.error_count
            warnings += child.warning_count
    except Exception as exc:  # onverwachte batchfout
        logger.exception("Volledige audit is mislukt")
        return _finish(parent, [], {}, failure=exc)

    parent.issue_count = total_issues
    parent.error_count = errors
    parent.warning_count = warnings
    parent.metadata = {
        "failed_children": [
            {"audit_key": k, "failure": m} for k, m in failed_children
        ],
    }
    parent.finished_at = timezone.now()
    parent.duration_ms = int(
        (parent.finished_at - parent.started_at).total_seconds() * 1000
    )
    parent.status = "completed"
    parent.save()
    return parent
