---
name: Affiliate product maintenance admin
description: Architecture decisions for the AffiliateProductState model, runtime overlay, sync command, and admin changelist.
---

## Model
- `AffiliateProductState` (products/models.py) — slug (unique, max_length=200), price (Decimal null), availability (CharField blank), price_last_checked (DateField null).
- No FK to the existing `Product` model (which has 0 DB records and must stay untouched).
- AVAILABILITY_CHOICES defined in models.py and imported by admin.py.

## Runtime overlay order (per spec)
`deepcopy → prepare_product_variants() → _apply_affiliate_maintenance_override() → apply_resolved_link() → derive_price_levels()`

**Why:** `prepare_product_variants()` projects default-variant commercial fields onto product level. DB override must happen AFTER so variants can't overwrite it.

**How to apply:** In `_enrich_products()` (products/views.py), bulk-load states with `AffiliateProductState.objects.in_bulk(slugs, field_name="slug")` before the loop.

## availability_label consistency
After DB override, both `product["availability_label"]` AND `product["default_variant"]["availability_label"]` AND `product["_family_links"]["availability_label"]` must be set to the canonical label, then `apply_resolved_link(product, default_variant)` re-called.

`_CANONICAL_AVAILABILITY_LABELS` dict in views.py maps InStock→"", OutOfStock→"Tijdelijk uitverkocht", etc.

## sync_affiliate_product_states command
- Idempotent `get_or_create` per slug from ALL_PRODUCTS_BY_SLUG.
- Variant products: finds default variant (is_default=True or first) for effective price/availability.
- Invalid dates (e.g. "2026-06-31") caught and set to None to avoid DateField validation error.
- `--force` flag overwrites existing DB values (dev/test only).
- Sets price_last_checked=None (not today) when Python data has no date.

## Admin changelist
- `change_list_template` attribute points to custom template.
- Default filter `needs_review=1` set in `changelist_view` when not in GET.
- `cl.result_list` (paginated slice) used to build rows, not `cl.queryset` (full).
- One-POST confirmation: intercepted BEFORE super() call in `changelist_view`.
- Blank price input = keep existing price (never erase).
- Only selected_ids rows are updated; unselected rows are completely untouched.
- Template: `templates/admin/products/affiliateproductstate/change_list.html`

## Tests
28 tests in `products/tests_maintenance.py`:
- SyncCommandTests (9 tests, test_01–test_08b)
- RuntimeOverrideTests (8 tests, test_09–test_16)
- AdminMaintenanceTests (11 tests, test_17–test_27)

## Quirk: product_detail template does not render numeric price
The product_detail.html only shows `display_price_range` (a label like "€60-€100"), not the raw numeric price. Tests for DB price in rendered HTML must check `product["price"]` after `_enrich_products()`, not the HTTP response body.
