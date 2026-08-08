"""
Django Admin — Affiliate Product Maintenance
============================================
Enkel model: AffiliateProductState.

Custom single-POST changelist: elke rij heeft een prijs-input en
beschikbaarheids-select; één submit-knop slaat wijzigingen op en markeert
geselecteerde producten als gecontroleerd in één atomaire transactie.
"""
from __future__ import annotations

import copy
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Case, F, IntegerField, Q, Value, When
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.html import format_html

from .models import AffiliateProductState, AVAILABILITY_CHOICES

NEEDS_REVIEW_DAYS = 30  # Drempel voor "verlopen" controlestatus


# ──────────────────────────────────────────────────────────────────────────────
# Filters
# ──────────────────────────────────────────────────────────────────────────────

class NeedsReviewFilter(admin.SimpleListFilter):
    title = "Vereist review"
    parameter_name = "needs_review"

    def _needs_review_q(self):
        threshold = timezone.localdate() - timedelta(days=NEEDS_REVIEW_DAYS)
        return (
            Q(price_last_checked__isnull=True)
            | Q(price_last_checked__lt=threshold)
            | Q(availability="OutOfStock")
        )

    def lookups(self, request, model_admin):
        return [
            ("1", "Ja — controleer vereist"),
            ("0", "Nee — recent gecontroleerd"),
            ("all", "Alle producten"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(self._needs_review_q())
        if self.value() == "0":
            return queryset.exclude(self._needs_review_q())
        # "all" of geen waarde → teruggeven ongewijzigd
        return queryset


class AvailabilityFilter(admin.SimpleListFilter):
    title = "Beschikbaarheid"
    parameter_name = "avail"

    def lookups(self, request, model_admin):
        return list(AVAILABILITY_CHOICES) + [("", "Onbekend / leeg")]

    def queryset(self, request, queryset):
        v = self.value()
        if v is not None:
            return queryset.filter(availability=v)
        return queryset


class PriceAgeFilter(admin.SimpleListFilter):
    title = "Controlestatus prijs"
    parameter_name = "price_age"

    def lookups(self, request, model_admin):
        return [
            ("missing", "Nooit gecontroleerd"),
            ("stale", f"Verlopen (> {NEEDS_REVIEW_DAYS} dagen)"),
            ("recent", "Recent gecontroleerd"),
        ]

    def queryset(self, request, queryset):
        threshold = timezone.localdate() - timedelta(days=NEEDS_REVIEW_DAYS)
        if self.value() == "missing":
            return queryset.filter(price_last_checked__isnull=True)
        if self.value() == "stale":
            return queryset.filter(
                price_last_checked__isnull=False,
                price_last_checked__lt=threshold,
            )
        if self.value() == "recent":
            return queryset.filter(price_last_checked__gte=threshold)
        return queryset


# ──────────────────────────────────────────────────────────────────────────────
# Admin
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(AffiliateProductState)
class AffiliateProductStateAdmin(admin.ModelAdmin):
    # Standaard list_display alleen voor Django's eigen changelist-machinerie
    # (wordt niet getoond — onze custom template vervangt result_list).
    list_display = ["slug", "price", "availability", "price_last_checked"]
    list_filter = [NeedsReviewFilter, AvailabilityFilter, PriceAgeFilter]
    search_fields = ["slug"]
    list_per_page = 50

    # Verwijst naar onze custom changelist-template.
    change_list_template = (
        "admin/products/affiliateproductstate/change_list.html"
    )

    # ── Queryset & volgorde ────────────────────────────────────────────────

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by(
            # OutOfStock als eerste
            Case(
                When(availability="OutOfStock", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            # NULL price_last_checked vóór elke datum
            F("price_last_checked").asc(nulls_first=True),
        )

    # ── changelist_view ────────────────────────────────────────────────────

    def changelist_view(self, request, extra_context=None):
        # 1) Intercept onze custom one-POST bevestiging.
        if request.method == "POST" and "_confirm_checked" in request.POST:
            return self._handle_confirmation(request)

        # 2) Standaard-filter: toon needs_review=1 als er geen filter is.
        if "needs_review" not in request.GET:
            q = request.GET.copy()
            q["needs_review"] = "1"
            request.GET = q
            request.META["QUERY_STRING"] = q.urlencode()

        # 3) Roep de standaard Django changelist-view aan (regelt filters,
        #    zoeken, paginatie en admin-chrome).
        response = super().changelist_view(request, extra_context)

        # 4) Injecteer extra context in de TemplateResponse voor onze template.
        if hasattr(response, "context_data"):
            cl = response.context_data.get("cl")
            if cl is not None:
                # cl.result_list = gepagineerde, gefilterde queryset
                response.context_data["maintenance_rows"] = (
                    self._build_maintenance_rows(cl.result_list)
                )
                response.context_data["availability_choices"] = AVAILABILITY_CHOICES

        return response

    # ── Helper: bouw rijen voor de template ───────────────────────────────

    def _build_maintenance_rows(self, result_list) -> list[dict]:
        from products.views import ALL_PRODUCTS_BY_SLUG
        from utils.variant_helpers import resolve_product_link

        today = timezone.localdate()
        threshold = today - timedelta(days=NEEDS_REVIEW_DAYS)
        rows = []

        for state in result_list:
            entry = ALL_PRODUCTS_BY_SLUG.get(state.slug)
            missing = entry is None

            if entry:
                data = entry["data"]
                product_name = data.get("name", state.slug)
                category_label = entry["category"]
                # Effectieve URL: zelfde prioriteit als publieke site
                # (affiliate → retailer → official).
                link = resolve_product_link(copy.copy(data))
                url = link.url if link and link.url else ""
            else:
                product_name = state.slug
                category_label = "—"
                url = ""

            # Prijs voor het formulierveld
            price_display = (
                f"{float(state.price):.2f}" if state.price is not None else ""
            )

            # Datum-stijl
            if state.price_last_checked is None:
                date_display = "—"
                date_class = "plc-missing"
            elif state.price_last_checked < threshold:
                date_display = str(state.price_last_checked)
                date_class = "plc-stale"
            else:
                date_display = str(state.price_last_checked)
                date_class = "plc-ok"

            # Beschikbaarheid-stijl
            avail_class = (
                "avail-outofstock" if state.availability == "OutOfStock" else ""
            )

            # URL-link
            if url:
                url_html = format_html(
                    '<a href="{}" target="_blank" rel="noopener noreferrer"'
                    ' title="{}" class="url-link">🔗 Bekijk</a>',
                    url,
                    url,
                )
            else:
                url_html = format_html('<span class="no-url">—</span>')

            rows.append({
                "pk": state.pk,
                "slug": state.slug,
                "product_name": product_name,
                "category": category_label,
                "price": state.price,
                "price_display": price_display,
                "availability": state.availability or "",
                "price_last_checked": state.price_last_checked,
                "date_display": date_display,
                "date_class": date_class,
                "avail_class": avail_class,
                "url_html": url_html,
                "missing_python": missing,
                "needs_review": (
                    state.price_last_checked is None
                    or state.price_last_checked < threshold
                    or state.availability == "OutOfStock"
                ),
            })

        return rows

    # ── Handler: verwerk de bevestigings-POST atomair ─────────────────────

    def _handle_confirmation(self, request):
        # Verzamel geselecteerde IDs.
        selected_ids = []
        for raw in request.POST.getlist("selected_ids"):
            try:
                selected_ids.append(int(raw))
            except (ValueError, TypeError):
                pass

        if not selected_ids:
            self.message_user(
                request, "Geen producten geselecteerd.", messages.WARNING
            )
            return redirect(request.get_full_path())

        today = timezone.localdate()
        price_changes = 0
        avail_changes = 0
        confirmed = 0
        errors = []

        with transaction.atomic():
            qs = (
                AffiliateProductState.objects.filter(pk__in=selected_ids)
                .select_for_update()
            )
            for state in qs:
                price_raw = (
                    request.POST.get(f"price_{state.pk}") or ""
                ).strip()
                avail_new = (
                    request.POST.get(f"avail_{state.pk}") or ""
                ).strip()

                updated_fields = ["price_last_checked"]

                # Prijs: alleen bijwerken als het veld niet leeg is.
                # Een leeg veld = ongewijzigd laten (nooit bestaande prijs wissen).
                if price_raw:
                    try:
                        new_price = Decimal(price_raw.replace(",", "."))
                        if state.price != new_price:
                            state.price = new_price
                            updated_fields.append("price")
                            price_changes += 1
                    except (InvalidOperation, ArithmeticError):
                        errors.append(
                            f"Ongeldige prijs voor {state.slug!r}: {price_raw!r}"
                        )
                        continue

                # Beschikbaarheid: alleen bijwerken als gewijzigd.
                if avail_new and avail_new != state.availability:
                    state.availability = avail_new
                    updated_fields.append("availability")
                    avail_changes += 1

                state.price_last_checked = today
                state.save(update_fields=updated_fields)
                confirmed += 1

        # Foutmeldingen
        for e in errors:
            self.message_user(request, e, messages.ERROR)

        # Succesbericht
        msg = f"{confirmed} product(en) gemarkeerd als gecontroleerd."
        if price_changes:
            msg += f" {price_changes} prijswijziging(en) opgeslagen."
        if avail_changes:
            msg += f" {avail_changes} beschikbaarheidswijziging(en) opgeslagen."
        self.message_user(request, msg, messages.SUCCESS)

        # Redirect terug naar changelist (filterstatus behouden).
        qs_str = request.META.get("QUERY_STRING", "")
        base = request.path
        return redirect(f"{base}?{qs_str}" if qs_str else base)
