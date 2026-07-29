from django.contrib import admin

from audits.models import ProductAuditIssue, ProductAuditRun


@admin.register(ProductAuditRun)
class ProductAuditRunAdmin(admin.ModelAdmin):
    list_display = (
        "id", "audit_key", "title", "status", "category",
        "error_count", "warning_count", "requested_by", "created_at",
    )
    list_filter = ("audit_key", "status")
    readonly_fields = [f.name for f in ProductAuditRun._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ProductAuditIssue)
class ProductAuditIssueAdmin(admin.ModelAdmin):
    list_display = ("id", "run", "severity", "code", "category", "product_slug")
    list_filter = ("severity", "code", "category")
    search_fields = ("product_slug", "message")
    readonly_fields = [f.name for f in ProductAuditIssue._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
