from django.conf import settings
from django.db import models


class ProductAuditRun(models.Model):
    STATUS_CHOICES = [
        ("pending", "pending"),
        ("running", "running"),
        ("completed", "completed"),
        ("failed", "failed"),
    ]

    audit_key = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=200)
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="product_audit_runs",
    )
    category = models.CharField(max_length=64, blank=True, default="")
    parameters = models.JSONField(default=dict, blank=True)
    #: Batch: kinderen van een volledige projectaudit wijzen naar de parent.
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    issue_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    failure_message = models.TextField(blank=True, default="")
    #: Niet-gevoelige metadata (samenvattingen, prijstabel). Nooit secrets.
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["audit_key", "-created_at"]),
        ]
        constraints = [
            # DB-afgedwongen bescherming tegen dubbele gelijktijdige runs.
            models.UniqueConstraint(
                fields=["audit_key"],
                condition=models.Q(status="running"),
                name="unique_running_audit_per_key",
            ),
        ]
        permissions = [
            ("view_product_audits", "Kan het productauditdashboard bekijken"),
            ("run_product_audits", "Kan productaudits uitvoeren"),
            ("view_product_audit_history", "Kan audithistorie bekijken"),
        ]

    def __str__(self):
        return f"{self.audit_key} #{self.pk} ({self.status})"


class ProductAuditIssue(models.Model):
    SEVERITY_CHOICES = [
        ("info", "info"),
        ("warning", "warning"),
        ("error", "error"),
        ("critical", "critical"),
    ]

    run = models.ForeignKey(
        ProductAuditRun, on_delete=models.CASCADE, related_name="issues"
    )
    code = models.CharField(max_length=80, db_index=True)
    severity = models.CharField(
        max_length=16, choices=SEVERITY_CHOICES, db_index=True
    )
    category = models.CharField(max_length=64, blank=True, default="", db_index=True)
    product_slug = models.CharField(
        max_length=200, blank=True, default="", db_index=True
    )
    variant_id = models.CharField(max_length=120, blank=True, default="")
    field = models.CharField(max_length=120, blank=True, default="")
    message = models.TextField()
    expected = models.TextField(blank=True, default="")
    actual = models.TextField(blank=True, default="")
    file_path = models.CharField(max_length=300, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["severity", "code", "id"]

    def __str__(self):
        return f"{self.severity}:{self.code}"
