---
name: Display-variant strictness (vershoudbakjes)
description: No cross-variant fallback for commercial fields; deep-copy source PRODUCTS before enrichment.
---
Rule: for products with button variants, commercial fields (affiliate_url, price, currency, availability, price_last_checked, capacities) come ONLY from the selected display variant; missing values are explicitly cleared, never inherited from another variant or stale product-level data. Image is the one exception: family-level original image is the documented fallback. JSON-LD emits no Offer without valid price+URL+currency+availability.
**Why:** shallow `dict()` copies of PRODUCTS share nested variant dicts, and copy-only-when-present logic let a previous variant's URL/price leak to another variant — a trust/affiliate-correctness bug.
**How to apply:** deep-copy catalog entries before enrichment (listing AND detail views); client-side variant switch must set-or-clear every field (no `if` without `else`, remove stale `href`). Tests guard source non-mutation.
