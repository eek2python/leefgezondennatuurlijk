"""Admin-only views voor het productauditdashboard.

Bevat geen auditlogica: alle uitvoering loopt via audits.runner en de
registry-allowlist. Read-only voor productdata; geen subprocess of
shellcommando's.
"""

import csv
import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from audits import runner as audit_runner
from audits.models import ProductAuditRun
from audits.registry import all_audits, get_audit

VIEW_PERM = "audits.view_product_audits"
RUN_PERM = "audits.run_product_audits"
HISTORY_PERM = "audits.view_product_audit_history"


def _check(request, perm):
    if not request.user.has_perm(perm):
        raise PermissionDenied


@staff_member_required
def dashboard(request):
    _check(request, VIEW_PERM)
    latest_by_key = {}
    for run in (
        ProductAuditRun.objects.filter(parent__isnull=True)
        .order_by("audit_key", "-created_at")
        .distinct()
    ):
        latest_by_key.setdefault(run.audit_key, run)

    rows = []
    for definition in all_audits():
        latest = latest_by_key.get(definition.key)
        rows.append({"definition": definition, "latest": latest})

    full_latest = latest_by_key.get(audit_runner.FULL_AUDIT_KEY)
    open_runs = [r for r in latest_by_key.values() if r.status == "completed"]
    context = {
        "title": "Productaudits",
        "rows": rows,
        "full_latest": full_latest,
        "open_errors": sum(r.error_count for r in open_runs),
        "open_warnings": sum(r.warning_count for r in open_runs),
        "failed_audits": [r for r in latest_by_key.values() if r.status == "failed"],
        "can_run": request.user.has_perm(RUN_PERM),
        "can_history": request.user.has_perm(HISTORY_PERM),
        "full_audit_key": audit_runner.FULL_AUDIT_KEY,
    }
    return render(request, "admin/audits/dashboard.html", context)


@staff_member_required
@require_POST
def run_audit_view(request):
    _check(request, RUN_PERM)
    key = request.POST.get("audit_key", "")
    category = (request.POST.get("category") or "").strip() or None
    params = {
        "strict": request.POST.get("strict") == "on",
        "network_checks": False,  # netwerkchecks staan vanuit admin altijd uit
    }
    try:
        if key == audit_runner.FULL_AUDIT_KEY:
            run = audit_runner.run_full_audit(
                category=category, user=request.user, params=params
            )
        else:
            definition = get_audit(key)
            if definition is None:
                messages.error(request, "Onbekende audit.")
                return redirect("audit_dashboard")
            run = audit_runner.run_audit(
                key, category=category, user=request.user, params=params
            )
    except audit_runner.AuditAlreadyRunning:
        messages.error(request, "Deze audit draait al; dubbele start voorkomen.")
        return redirect("audit_dashboard")
    except (ValueError, audit_runner.UnknownAudit) as exc:
        messages.error(request, str(exc))
        return redirect("audit_dashboard")

    if run.status == "failed":
        messages.error(
            request,
            f"Audit '{run.title}' is mislukt: {run.failure_message[:200]}",
        )
    else:
        messages.success(
            request,
            f"Audit '{run.title}' voltooid: {run.error_count} fouten, "
            f"{run.warning_count} waarschuwingen.",
        )
    return redirect("audit_run_detail", run_id=run.pk)


@staff_member_required
def run_detail(request, run_id):
    _check(request, VIEW_PERM)
    run = get_object_or_404(ProductAuditRun, pk=run_id)
    issues = run.issues.all()
    filters = {
        "severity": request.GET.get("severity", ""),
        "category": request.GET.get("category", ""),
        "product": request.GET.get("product", ""),
        "code": request.GET.get("code", ""),
    }
    if filters["severity"]:
        issues = issues.filter(severity=filters["severity"])
    if filters["category"]:
        issues = issues.filter(category=filters["category"])
    if filters["product"]:
        issues = issues.filter(product_slug__icontains=filters["product"])
    if filters["code"]:
        issues = issues.filter(code=filters["code"])

    context = {
        "title": f"Auditrun #{run.pk} — {run.title}",
        "run": run,
        "children": run.children.all(),
        "issues": issues[:1000],
        "filters": filters,
        "severities": ["info", "warning", "error", "critical"],
        "categories": sorted(
            set(run.issues.values_list("category", flat=True)) - {""}
        ),
        "codes": sorted(set(run.issues.values_list("code", flat=True))),
        "price_table": (run.metadata or {}).get("price_table"),
    }
    return render(request, "admin/audits/run_detail.html", context)


@staff_member_required
def run_history(request, audit_key):
    _check(request, HISTORY_PERM)
    runs = ProductAuditRun.objects.filter(audit_key=audit_key)[:100]
    return render(
        request,
        "admin/audits/history.html",
        {"title": f"Historie — {audit_key}", "audit_key": audit_key, "runs": runs},
    )


@staff_member_required
def export_run(request, run_id, fmt):
    _check(request, VIEW_PERM)
    run = get_object_or_404(ProductAuditRun, pk=run_id)
    if fmt == "json":
        payload = {
            "run": {
                "id": run.pk,
                "audit_key": run.audit_key,
                "title": run.title,
                "status": run.status,
                "category": run.category,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                "duration_ms": run.duration_ms,
                "issue_count": run.issue_count,
                "error_count": run.error_count,
                "warning_count": run.warning_count,
            },
            "issues": [
                {
                    "code": i.code,
                    "severity": i.severity,
                    "category": i.category,
                    "product_slug": i.product_slug,
                    "variant_id": i.variant_id,
                    "field": i.field,
                    "message": i.message,
                    "expected": i.expected,
                    "actual": i.actual,
                    "file_path": i.file_path,
                }
                for i in run.issues.all()
            ],
        }
        response = JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
        response["Content-Disposition"] = (
            f'attachment; filename="audit-run-{run.pk}.json"'
        )
        return response
    if fmt == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="audit-run-{run.pk}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            ["severity", "code", "category", "product_slug", "variant_id",
             "field", "message", "expected", "actual", "file_path"]
        )
        for i in run.issues.all():
            writer.writerow(
                [i.severity, i.code, i.category, i.product_slug, i.variant_id,
                 i.field, i.message, i.expected, i.actual, i.file_path]
            )
        return response
    return HttpResponse(status=404)
