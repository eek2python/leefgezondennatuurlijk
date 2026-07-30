"""Tests voor het centrale auditdashboard (spec §18)."""

import copy
import json

from django.contrib.auth.models import Permission, User
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from audits import runner as audit_runner
from audits.checks.links import run_product_link_check
from audits.checks.variants import run_price_level_check, run_variant_check
from audits.models import ProductAuditIssue, ProductAuditRun
from audits.registry import all_audits, get_audit
from audits.result import SEVERITY_ERROR, SEVERITY_WARNING, AuditIssue


def _perm(codename):
    return Permission.objects.get(
        codename=codename, content_type__app_label="audits"
    )


class AccessControlTests(TestCase):
    def setUp(self):
        self.dashboard_url = reverse("audit_dashboard")
        self.run_url = reverse("audit_run")

    def test_anonymous_user_denied(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response["Location"])

    def test_staff_without_permission_cannot_run(self):
        staff = User.objects.create_user("staff", password="x", is_staff=True)
        staff.user_permissions.add(_perm("view_product_audits"))
        self.client.force_login(staff)
        response = self.client.post(
            self.run_url, {"audit_key": "price_levels"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ProductAuditRun.objects.count(), 0)

    def test_staff_without_view_permission_denied_dashboard(self):
        staff = User.objects.create_user("staff2", password="x", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.dashboard_url).status_code, 403)

    def test_superuser_can_open_dashboard(self):
        admin = User.objects.create_superuser("admin", "a@a.nl", "x")
        self.client.force_login(admin)
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Productaudits")
        self.assertContains(response, "Volledige productaudit uitvoeren")

    def test_run_requires_post(self):
        admin = User.objects.create_superuser("admin2", "a@a.nl", "x")
        self.client.force_login(admin)
        response = self.client.get(self.run_url)
        self.assertEqual(response.status_code, 405)

    def test_csrf_enforced(self):
        admin = User.objects.create_superuser("admin3", "a@a.nl", "x")
        client = Client(enforce_csrf_checks=True)
        client.force_login(admin)
        response = client.post(self.run_url, {"audit_key": "price_levels"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ProductAuditRun.objects.count(), 0)


class RunnerTests(TestCase):
    def test_invalid_audit_key_rejected(self):
        with self.assertRaises(audit_runner.UnknownAudit):
            audit_runner.run_audit("rm -rf /")
        self.assertEqual(ProductAuditRun.objects.count(), 0)

    def test_invalid_category_rejected(self):
        with self.assertRaises(ValueError):
            audit_runner.run_audit("price_levels", category="nep-categorie")
        self.assertEqual(ProductAuditRun.objects.count(), 0)

    def test_run_and_issues_saved_with_counts(self):
        run = audit_runner.run_audit("price_levels", category="koekenpannen")
        self.assertEqual(run.status, "completed")
        self.assertGreater(run.issue_count, 0)
        self.assertEqual(run.issue_count, run.issues.count())
        self.assertEqual(
            run.error_count,
            run.issues.filter(severity__in=["error", "critical"]).count(),
        )
        self.assertEqual(
            run.warning_count, run.issues.filter(severity="warning").count()
        )

    def test_price_level_audit_reports_mismatch(self):
        issues, meta = run_price_level_check(category="koekenpannen")
        codes = {i.code for i in issues}
        self.assertIn("price_range_mismatch", codes)
        self.assertTrue(meta["price_table"])

    def test_price_level_audit_covers_hapjespannen_with_own_thresholds(self):
        issues, meta = run_price_level_check(category="hapjespannen")
        rows = [
            r for r in meta["price_table"] if r["category"] == "hapjespannen"
        ]
        self.assertTrue(rows)
        # Grenzen €40/€70/€110: verwachte niveaus in de tabel moeten met de
        # centrale helper overeenkomen (geen koekenpangrenzen).
        from utils.pricing import get_price_range
        for row in rows:
            expected = get_price_range(row["price"], "hapjespannen") or "—"
            self.assertEqual(
                row["computed"], expected,
                (row["product"], row["variant"], row["price"]),
            )

    def test_failed_audit_gets_failed_status(self):
        from audits import registry

        definition = registry.AuditDefinition(
            key="_kapot", title="Kapot", description="", runner=lambda **kw: 1 / 0,
        )
        registry._REGISTRY["_kapot"] = definition
        try:
            run = audit_runner.run_audit("_kapot")
        finally:
            del registry._REGISTRY["_kapot"]
        self.assertEqual(run.status, "failed")
        self.assertIn("division", run.failure_message)

    def test_duplicate_concurrent_run_prevented(self):
        ProductAuditRun.objects.create(
            audit_key="price_levels", title="x", status="running"
        )
        with self.assertRaises(audit_runner.AuditAlreadyRunning):
            audit_runner.run_audit("price_levels")

    def test_duplicate_running_row_blocked_by_db_constraint(self):
        """Race-scenario: ook wie de Python-check omzeilt, botst op de
        DB-constraint unique_running_audit_per_key."""
        from django.db import IntegrityError, transaction

        ProductAuditRun.objects.create(
            audit_key="price_levels", title="x", status="running"
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProductAuditRun.objects.create(
                audit_key="price_levels", title="y", status="running"
            )

    def test_network_audit_not_runnable(self):
        with self.assertRaises(ValueError):
            audit_runner.run_audit("live_links")

    def test_full_audit_combines_children(self):
        parent = audit_runner.run_full_audit(category="koekenpannen")
        self.assertEqual(parent.audit_key, audit_runner.FULL_AUDIT_KEY)
        self.assertEqual(parent.status, "completed")
        children = list(parent.children.all())
        self.assertGreaterEqual(len(children), 3)
        self.assertEqual(
            parent.issue_count, sum(c.issue_count for c in children)
        )
        # netwerkaudit is geen kind
        self.assertNotIn("live_links", {c.audit_key for c in children})

    def test_audit_does_not_modify_product_data(self):
        from products.products_koekenpannen import PRODUCTS

        before = copy.deepcopy(PRODUCTS)
        audit_runner.run_full_audit(category="koekenpannen")
        self.assertEqual(PRODUCTS, before)


class SharedLogicTests(TestCase):
    def test_admin_and_command_share_same_function(self):
        """Het registry-runnerpad en het managementcommand gebruiken
        dezelfde modules uit audits/checks/."""
        from audits.checks import variants as shared
        from products.management.commands import audit_product_variants as cmd

        self.assertIs(cmd.run_variant_audit, shared.run_variant_audit)
        definition = get_audit("product_variants")
        self.assertIs(definition.runner, shared.run_variant_check)
        self.assertIs(
            get_audit("price_levels").runner, shared.run_price_level_check
        )

    def test_existing_management_command_still_works(self):
        from io import StringIO

        out = StringIO()
        call_command("audit_product_variants", "--category", "koekenpannen", stdout=out)
        self.assertIn("Projectbrede audit productvarianten", out.getvalue())

    def test_audit_products_command_uses_runner(self):
        from io import StringIO

        out = StringIO()
        call_command(
            "audit_products", "--audit", "price_levels",
            "--category", "koekenpannen", stdout=out,
        )
        self.assertIn("price_levels", out.getvalue())
        self.assertEqual(
            ProductAuditRun.objects.filter(audit_key="price_levels").count(), 1
        )


class DetailAndExportTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "a@a.nl", "x")
        self.client.force_login(self.admin)
        self.run = audit_runner.run_audit(
            "price_levels", category="koekenpannen", user=self.admin
        )

    def test_detail_page_filterable(self):
        url = reverse("audit_run_detail", args=[self.run.pk])
        response = self.client.get(url, {"severity": "warning"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "price_range_mismatch")
        response = self.client.get(url, {"severity": "critical"})
        self.assertContains(response, "Geen issues.")
        response = self.client.get(url, {"code": "price_range_mismatch"})
        self.assertContains(response, "price_range_mismatch")

    def test_issue_messages_escaped(self):
        evil = ProductAuditIssue.objects.create(
            run=self.run,
            code="x",
            severity="error",
            message="<script>alert(1)</script>",
        )
        url = reverse("audit_run_detail", args=[self.run.pk])
        response = self.client.get(url)
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;")
        evil.delete()

    def test_export_csv_and_json(self):
        csv_resp = self.client.get(
            reverse("audit_run_export", args=[self.run.pk, "csv"])
        )
        self.assertEqual(csv_resp.status_code, 200)
        self.assertIn("text/csv", csv_resp["Content-Type"])
        json_resp = self.client.get(
            reverse("audit_run_export", args=[self.run.pk, "json"])
        )
        payload = json.loads(json_resp.content)
        self.assertEqual(payload["run"]["audit_key"], "price_levels")
        self.assertEqual(len(payload["issues"]), self.run.issue_count)

    def test_run_via_post_creates_run_and_redirects(self):
        response = self.client.post(
            reverse("audit_run"),
            {"audit_key": "brand_diversity", "category": "koekenpannen"},
        )
        self.assertEqual(response.status_code, 302)
        run = ProductAuditRun.objects.get(audit_key="brand_diversity")
        self.assertEqual(run.requested_by, self.admin)
        self.assertEqual(run.category, "koekenpannen")

    def test_unknown_key_via_post_rejected(self):
        response = self.client.post(
            reverse("audit_run"), {"audit_key": "does_not_exist"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            ProductAuditRun.objects.filter(audit_key="does_not_exist").count(), 0
        )


class RegistryTests(TestCase):
    def test_only_real_audits_registered(self):
        keys = {d.key for d in all_audits()}
        self.assertEqual(
            keys,
            {"product_variants", "price_levels", "product_links",
             "product_data", "brand_diversity", "live_links"},
        )

    def test_retention_opt_in(self):
        for _ in range(3):
            audit_runner.run_audit("brand_diversity", category="koekenpannen")
        self.assertEqual(
            ProductAuditRun.objects.filter(audit_key="brand_diversity").count(), 3
        )
        with self.settings(AUDIT_RUN_RETENTION_PER_KEY=2):
            audit_runner.run_audit("brand_diversity", category="koekenpannen")
        self.assertEqual(
            ProductAuditRun.objects.filter(audit_key="brand_diversity").count(), 2
        )


class ProductLinkAuditTests(TestCase):
    """Auditregels voor het onderscheid affiliate/retailer/official."""

    def test_runner_registered_and_runs(self):
        issues, metadata = run_product_link_check(category="snijplanken")
        self.assertIn("products_checked", metadata)
        self.assertGreater(metadata["products_checked"], 0)
        # Geen enkele niet-affiliatelink mag sponsored-rel opleveren en
        # er mag geen variant-fallback optreden in bestaande data.
        codes = {i.code for i in issues}
        self.assertNotIn("retailer_url_with_sponsored_rel", codes)
        self.assertNotIn("official_url_with_sponsored_rel", codes)
        self.assertNotIn("variant_link_fallback_to_other_variant", codes)
        self.assertNotIn("stale_variant_link", codes)

    def test_unconfirmed_affiliate_urls_are_info_only(self):
        issues, metadata = run_product_link_check(category="snijplanken")
        review = [
            i for i in issues
            if i.code == "affiliate_url_without_affiliate_confirmation"
        ]
        self.assertEqual(len(review), metadata["manual_review_affiliate_urls"])
        for issue in review:
            self.assertEqual(issue.severity, "info")

    def test_full_run_over_all_categories(self):
        result = audit_runner.run_audit("product_links")
        self.assertEqual(result.status, "completed")
