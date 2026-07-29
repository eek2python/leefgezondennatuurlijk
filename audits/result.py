"""Centrale resultaattypes voor alle productaudits.

Zowel managementcommands als Django Admin bouwen hun output op uit deze
structuren; console-output wordt nooit geparsed om resultaten te
reconstrueren.
"""

from dataclasses import dataclass, field
from datetime import datetime

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_ERROR = "error"
SEVERITY_CRITICAL = "critical"
SEVERITIES = (SEVERITY_INFO, SEVERITY_WARNING, SEVERITY_ERROR, SEVERITY_CRITICAL)

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUSES = (STATUS_PENDING, STATUS_RUNNING, STATUS_COMPLETED, STATUS_FAILED)


@dataclass
class AuditIssue:
    code: str
    severity: str
    message: str
    category: str | None = None
    product_slug: str | None = None
    variant_id: str | None = None
    file_path: str | None = None
    field: str | None = None
    expected: str | None = None
    actual: str | None = None


@dataclass
class AuditResult:
    audit_key: str
    title: str
    started_at: datetime
    finished_at: datetime
    status: str
    issues: list[AuditIssue] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def error_count(self):
        return sum(
            1 for i in self.issues
            if i.severity in (SEVERITY_ERROR, SEVERITY_CRITICAL)
        )

    @property
    def warning_count(self):
        return sum(1 for i in self.issues if i.severity == SEVERITY_WARNING)
