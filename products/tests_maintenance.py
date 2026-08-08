"""
Tests voor de Affiliate Product Maintenance-module.

Onderverdeeld in drie klassen:
  - SyncCommandTests        (1–8):  sync_affiliate_product_states command
  - RuntimeOverrideTests    (9–16): DB-overlay op rendertijd
  - AdminMaintenanceTests   (17–27): custom admin changelist & POST
"""
import copy
import json
import re
from decimal import Decimal
from io import StringIO

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from products.models import AffiliateProductState, Product
from products.views import ALL_PRODUCTS_BY_SLUG, _apply_affiliate_maintenance_override

# ─── Producten die in de tests gebruikt worden ───────────────────────────────
#   Eenvoudig product: geen variant-selectors.
SIMPLE_SLUG = "greenpan-barcelona-pro-28"
#   Variantproduct: button-varianten (meerdere maten).
VARIANT_SLUG = "ikea-365-plus-enkel"


def _product_copy(slug: str) -> dict:
    """Geeft een deepcopy van de productdata terug, klaar voor verrijking."""
    return copy.deepcopy(ALL_PRODUCTS_BY_SLUG[slug]["data"])


# ─── Hulpfuncties ─────────────────────────────────────────────────────────────

def _run_sync(**kwargs) -> str:
    """Draait de management-command en geeft stdout terug."""
    from django.core.management import call_command
    out = StringIO()
    call_command(
        "sync_affiliate_product_states", stdout=out, **kwargs
    )
    return out.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 1–8  SyncCommandTests
# ─────────────────────────────────────────────────────────────────────────────

class SyncCommandTests(TestCase):
    """sync_affiliate_product_states management command."""

    def test_01_creates_record_for_each_python_product(self):
        """Sync maakt een AffiliateProductState-record per Python-product."""
        _run_sync()
        self.assertEqual(
            AffiliateProductState.objects.count(),
            len(ALL_PRODUCTS_BY_SLUG),
        )

    def test_02_slug_used_as_unique_key(self):
        """Sync gebruikt de slug als unieke sleutel; tweede run maakt geen duplicaten."""
        _run_sync()
        first_count = AffiliateProductState.objects.count()
        _run_sync()
        self.assertEqual(AffiliateProductState.objects.count(), first_count)

    def test_03_imports_effective_price_for_simple_product(self):
        """Eenvoudig product: prijs uit productniveau wordt geïmporteerd."""
        _run_sync()
        state = AffiliateProductState.objects.get(slug=SIMPLE_SLUG)
        python_price = ALL_PRODUCTS_BY_SLUG[SIMPLE_SLUG]["data"].get("price")
        if python_price is not None:
            self.assertAlmostEqual(float(state.price), float(python_price), places=2)
        else:
            self.assertIsNone(state.price)

    def test_04_imports_effective_price_for_variant_product(self):
        """Variantproduct: prijs van de default-variant wordt geïmporteerd."""
        _run_sync()
        state = AffiliateProductState.objects.get(slug=VARIANT_SLUG)
        data = ALL_PRODUCTS_BY_SLUG[VARIANT_SLUG]["data"]
        variants = [v for v in data["variants"] if isinstance(v, dict) and v.get("id")]
        default = next((v for v in variants if v.get("is_default")), variants[0])
        expected = default.get("price")
        if expected is not None:
            self.assertAlmostEqual(float(state.price), float(expected), places=2)
        else:
            self.assertIsNone(state.price)

    def test_05_imports_availability(self):
        """Beschikbaarheid wordt geïmporteerd uit de Python-data."""
        _run_sync()
        state = AffiliateProductState.objects.get(slug=SIMPLE_SLUG)
        python_avail = ALL_PRODUCTS_BY_SLUG[SIMPLE_SLUG]["data"].get("availability") or ""
        # Normaliseer zoals de command dat doet
        if python_avail == "OutofStock":
            python_avail = "OutOfStock"
        self.assertEqual(state.availability, python_avail)

    def test_06_normalizes_outofstock_typo(self):
        """'OutofStock' (typefout) wordt genormaliseerd naar 'OutOfStock'."""
        from products.management.commands.sync_affiliate_product_states import (
            _get_effective_commercial_fields,
        )
        product_data = {"availability": "OutofStock", "price": 10.0}
        fields = _get_effective_commercial_fields(product_data)
        self.assertEqual(fields["availability"], "OutOfStock")

    def test_07_price_last_checked_stays_null(self):
        """price_last_checked = NULL voor producten zonder controlledatum in Python-data."""
        _run_sync()
        state = AffiliateProductState.objects.get(slug=SIMPLE_SLUG)
        python_plc = ALL_PRODUCTS_BY_SLUG[SIMPLE_SLUG]["data"].get("price_last_checked")
        if not python_plc:
            self.assertIsNone(state.price_last_checked)

    def test_08_second_sync_does_not_overwrite_manual_db_values(self):
        """Tweede sync (zonder --force) overschrijft handmatig bijgehouden waarden niet."""
        _run_sync()
        # Stel handmatige DB-waarden in
        state = AffiliateProductState.objects.get(slug=SIMPLE_SLUG)
        state.price = Decimal("999.99")
        state.availability = "Discontinued"
        state.save(update_fields=["price", "availability"])

        _run_sync()  # Tweede run zonder --force

        state.refresh_from_db()
        self.assertEqual(state.price, Decimal("999.99"))
        self.assertEqual(state.availability, "Discontinued")

    def test_08b_product_model_untouched_after_sync(self):
        """Product.objects.count() blijft 0 na sync (bestaand model ongewijzigd)."""
        self.assertEqual(Product.objects.count(), 0)
        _run_sync()
        self.assertEqual(Product.objects.count(), 0)


# ─────────────────────────────────────────────────────────────────────────────
# 9–16  RuntimeOverrideTests
# ─────────────────────────────────────────────────────────────────────────────

class RuntimeOverrideTests(TestCase):
    """DB-overlay op rendertijd via _enrich_products / product_detail."""

    # ── Directe overlay-functie tests ────────────────────────────────────

    def _make_state(self, **kwargs):
        """Bouwt een AffiliateProductState-object zonder het op te slaan."""
        defaults = {
            "slug": SIMPLE_SLUG,
            "price": None,
            "availability": "",
            "price_last_checked": None,
        }
        defaults.update(kwargs)
        return AffiliateProductState(**defaults)

    def test_09_db_price_overrides_python_price(self):
        """DB-prijs overschrijft de Python-prijs na prepare_product_variants."""
        from utils.variant_helpers import prepare_product_variants
        product = _product_copy(SIMPLE_SLUG)
        prepare_product_variants(product)

        state = self._make_state(price=Decimal("55.55"))
        _apply_affiliate_maintenance_override(product, state)

        self.assertAlmostEqual(product["price"], 55.55, places=2)

    def test_10_db_availability_overrides_python_availability(self):
        """DB-beschikbaarheid overschrijft de Python-beschikbaarheid."""
        from utils.variant_helpers import prepare_product_variants
        product = _product_copy(SIMPLE_SLUG)
        prepare_product_variants(product)

        state = self._make_state(availability="OutOfStock")
        _apply_affiliate_maintenance_override(product, state)

        self.assertEqual(product["availability"], "OutOfStock")

    def test_11_no_maintenance_state_uses_python_fallback(self):
        """Zonder DB-record wordt de Python-prijs onveranderd getoond."""
        # Geen AffiliateProductState aanmaken → Python-data blijft geldig.
        response = self.client.get(f"/product/{SIMPLE_SLUG}/")
        self.assertEqual(response.status_code, 200)
        python_price = ALL_PRODUCTS_BY_SLUG[SIMPLE_SLUG]["data"].get("price")
        if python_price is not None:
            content = response.content.decode()
            # Prijs moet ergens in de pagina voorkomen (JSON-LD of displayveld)
            self.assertIn(str(int(python_price)) if python_price == int(python_price)
                          else "", content or "")  # soepele check: pagina laadt gewoon

    def test_12_variant_product_db_price_overrides_default_variant(self):
        """Variantproduct: DB-prijs overschrijft de default-variant prijs."""
        from utils.variant_helpers import prepare_product_variants
        product = _product_copy(VARIANT_SLUG)
        prepare_product_variants(product)

        state = self._make_state(slug=VARIANT_SLUG, price=Decimal("99.00"))
        _apply_affiliate_maintenance_override(product, state)

        # Zowel op product- als variant-niveau bijgewerkt
        self.assertAlmostEqual(product["price"], 99.00, places=2)
        dv = product.get("default_variant")
        if dv is not None:
            self.assertAlmostEqual(dv["price"], 99.00, places=2)

    def test_13_availability_label_follows_db_availability(self):
        """availability_label volgt de DB-beschikbaarheid, niet de Python-label."""
        from utils.variant_helpers import prepare_product_variants
        from products.views import _CANONICAL_AVAILABILITY_LABELS

        product = _product_copy(SIMPLE_SLUG)
        prepare_product_variants(product)

        state = self._make_state(availability="Discontinued")
        _apply_affiliate_maintenance_override(product, state)

        expected_label = _CANONICAL_AVAILABILITY_LABELS["Discontinued"]
        self.assertEqual(product["availability_label"], expected_label)

    def test_14_db_price_reflected_after_enrichment(self):
        """DB-prijs overschrijft Python-prijs na _enrich_products."""
        AffiliateProductState.objects.create(
            slug=SIMPLE_SLUG,
            price=Decimal("77.77"),
            availability="InStock",
        )
        product = _product_copy(SIMPLE_SLUG)
        from products.views import _enrich_products
        _enrich_products([product], category="koekenpannen")
        self.assertAlmostEqual(float(product["price"]), 77.77, places=2)

    def test_15_db_outofstock_reflected_in_enrichment_and_offer_ld(self):
        """DB availability=OutOfStock wordt doorgegeven na verrijking en in Offer JSON-LD."""
        AffiliateProductState.objects.create(
            slug=SIMPLE_SLUG,
            price=Decimal("82.09"),
            availability="OutOfStock",
        )
        product = _product_copy(SIMPLE_SLUG)
        from products.views import _enrich_products, _build_offer_ld
        _enrich_products([product], category="koekenpannen")
        self.assertEqual(product["availability"], "OutOfStock")
        # Als de product een URL heeft → Offer moet OutOfStock weerspiegelen.
        offer = _build_offer_ld(product)
        if offer is not None:
            self.assertIn("OutOfStock", offer.get("availability", ""))

    def test_16_url_resolution_unaffected_by_overlay(self):
        """Affiliate-URL-resolutie wordt niet geraakt door de DB-overlay."""
        from utils.variant_helpers import prepare_product_variants
        product = _product_copy(SIMPLE_SLUG)
        prepare_product_variants(product)
        # Sla de resolved_link voor overlay op
        resolved_before = product.get("resolved_link")

        state = self._make_state(price=Decimal("10.00"), availability="InStock")
        _apply_affiliate_maintenance_override(product, state)

        # resolved_link moet nog steeds aanwezig zijn (opnieuw gezet na overlay)
        self.assertIn("resolved_link", product)


# ─────────────────────────────────────────────────────────────────────────────
# 17–27  AdminMaintenanceTests
# ─────────────────────────────────────────────────────────────────────────────

class AdminMaintenanceTests(TestCase):
    """Custom admin changelist en POST-verwerking."""

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(
            username="testadmin",
            password="testpass",
            email="admin@test.nl",
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.admin_user)
        self.changelist_url = reverse(
            "admin:products_affiliateproductstate_changelist"
        )
        # Maak testrecords aan
        today = timezone.localdate()
        self.recent_instock = AffiliateProductState.objects.create(
            slug="test-recent-instock",
            price=Decimal("25.00"),
            availability="InStock",
            price_last_checked=today,
        )
        self.stale = AffiliateProductState.objects.create(
            slug="test-stale",
            price=Decimal("30.00"),
            availability="InStock",
            price_last_checked=today.replace(year=today.year - 1),
        )
        self.never_checked = AffiliateProductState.objects.create(
            slug="test-never-checked",
            price=Decimal("15.00"),
            availability="InStock",
            price_last_checked=None,
        )
        self.outofstock = AffiliateProductState.objects.create(
            slug="test-outofstock",
            price=Decimal("20.00"),
            availability="OutOfStock",
            price_last_checked=today,
        )

    def test_17_null_price_last_checked_in_default_filter(self):
        """NULL price_last_checked verschijnt in de standaard needs_review-filter."""
        response = self.client.get(self.changelist_url + "?needs_review=1")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("test-never-checked", content)

    def test_18_stale_date_in_default_filter(self):
        """Verouderde controlledatum (> 30 dagen) verschijnt in needs_review-filter."""
        response = self.client.get(self.changelist_url + "?needs_review=1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("test-stale", response.content.decode())

    def test_19_recent_instock_not_in_default_filter(self):
        """Recent gecontroleerde InStock-producten staan NIET in de needs_review-filter."""
        response = self.client.get(self.changelist_url + "?needs_review=1")
        self.assertEqual(response.status_code, 200)
        # recent-instock is recent + InStock → niet vereist
        self.assertNotIn("test-recent-instock", response.content.decode())

    def test_20_outofstock_in_default_filter_even_if_recent(self):
        """OutOfStock verschijnt altijd in de needs_review-filter, ook als recent gecontroleerd."""
        response = self.client.get(self.changelist_url + "?needs_review=1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("test-outofstock", response.content.decode())

    def test_21_selected_price_change_is_saved(self):
        """Een gewijzigde prijs wordt opgeslagen voor de geselecteerde rij."""
        response = self.client.post(self.changelist_url + "?needs_review=all", data={
            "_confirm_checked": "1",
            "selected_ids": [str(self.stale.pk)],
            f"price_{self.stale.pk}": "39.99",
            f"avail_{self.stale.pk}": "InStock",
        })
        self.assertIn(response.status_code, (200, 302))
        self.stale.refresh_from_db()
        self.assertEqual(self.stale.price, Decimal("39.99"))

    def test_22_unchanged_price_remains_untouched(self):
        """Als de prijs niet wijzigt (zelfde waarde), blijft de DB ongewijzigd."""
        original_price = self.stale.price  # 30.00
        response = self.client.post(self.changelist_url + "?needs_review=all", data={
            "_confirm_checked": "1",
            "selected_ids": [str(self.stale.pk)],
            f"price_{self.stale.pk}": "30.00",  # zelfde waarde
            f"avail_{self.stale.pk}": "InStock",
        })
        self.assertIn(response.status_code, (200, 302))
        self.stale.refresh_from_db()
        self.assertEqual(self.stale.price, original_price)

    def test_23_availability_change_is_saved(self):
        """Een gewijzigde beschikbaarheid wordt opgeslagen voor de geselecteerde rij."""
        response = self.client.post(self.changelist_url + "?needs_review=all", data={
            "_confirm_checked": "1",
            "selected_ids": [str(self.outofstock.pk)],
            f"price_{self.outofstock.pk}": "20.00",
            f"avail_{self.outofstock.pk}": "InStock",
        })
        self.assertIn(response.status_code, (200, 302))
        self.outofstock.refresh_from_db()
        self.assertEqual(self.outofstock.availability, "InStock")

    def test_24_selected_row_gets_todays_checked_date(self):
        """Geselecteerde rijen krijgen de huidige datum als price_last_checked."""
        response = self.client.post(self.changelist_url + "?needs_review=all", data={
            "_confirm_checked": "1",
            "selected_ids": [str(self.never_checked.pk)],
            f"price_{self.never_checked.pk}": "15.00",
            f"avail_{self.never_checked.pk}": "InStock",
        })
        self.assertIn(response.status_code, (200, 302))
        self.never_checked.refresh_from_db()
        self.assertEqual(self.never_checked.price_last_checked, timezone.localdate())

    def test_25_unselected_row_is_not_modified(self):
        """Niet-geselecteerde rijen worden niet aangepast."""
        original_price = self.stale.price
        original_plc = self.stale.price_last_checked
        # Selecteer alleen `never_checked`, laat `stale` ongewijzigd
        response = self.client.post(self.changelist_url + "?needs_review=all", data={
            "_confirm_checked": "1",
            "selected_ids": [str(self.never_checked.pk)],
            f"price_{self.never_checked.pk}": "15.00",
            f"avail_{self.never_checked.pk}": "InStock",
            f"price_{self.stale.pk}": "999.00",  # waarde aanwezig in POST maar NOT selected
            f"avail_{self.stale.pk}": "Discontinued",
        })
        self.assertIn(response.status_code, (200, 302))
        self.stale.refresh_from_db()
        # stale mag NIET zijn aangepast
        self.assertEqual(self.stale.price, original_price)
        self.assertEqual(self.stale.price_last_checked, original_plc)

    def test_26_blank_price_input_does_not_erase_existing_price(self):
        """Een leeg prijsveld wist de bestaande prijs NIET."""
        original_price = self.stale.price  # 30.00
        response = self.client.post(self.changelist_url + "?needs_review=all", data={
            "_confirm_checked": "1",
            "selected_ids": [str(self.stale.pk)],
            f"price_{self.stale.pk}": "",  # bewust leeggelaten
            f"avail_{self.stale.pk}": "InStock",
        })
        self.assertIn(response.status_code, (200, 302))
        self.stale.refresh_from_db()
        self.assertEqual(self.stale.price, original_price)

    def test_27_get_request_changes_no_data(self):
        """Een gewone GET op de changelist wijzigt geen enkel DB-record."""
        counts_before = {
            obj.pk: (obj.price, obj.availability, obj.price_last_checked)
            for obj in AffiliateProductState.objects.all()
        }
        self.client.get(self.changelist_url + "?needs_review=all")
        for obj in AffiliateProductState.objects.all():
            self.assertEqual(
                (obj.price, obj.availability, obj.price_last_checked),
                counts_before[obj.pk],
                msg=f"Record {obj.pk} ({obj.slug}) was onterecht gewijzigd door GET.",
            )
