---
name: Display-variant strictness (vershoudbakjes)
description: No cross-variant fallback for commercial fields; deep-copy source PRODUCTS before enrichment.
---
Rule: for products with button variants, commercial fields (affiliate_url, price, currency, availability, price_last_checked, capacities) come ONLY from the selected display variant; missing values are explicitly cleared, never inherited from another variant or stale product-level data. Image is the one exception: family-level original image is the documented fallback. JSON-LD emits no Offer without valid price+URL+currency+availability.
**Why:** shallow `dict()` copies of PRODUCTS share nested variant dicts, and copy-only-when-present logic let a previous variant's URL/price leak to another variant — a trust/affiliate-correctness bug.
**How to apply:** deep-copy catalog entries before enrichment (listing AND detail views); client-side variant switch must set-or-clear every field (no `if` without `else`, remove stale `href`). Tests guard source non-mutation.

For ceramic frying-pan colour variants only, the user explicitly allows the
shared product-level regular reference price when a colour lacks its own
reference price, solely to derive the €/€€/€€€/€€€€ comparison level.
**Why:** the shared regular price applies to all colours; temporary offers
must not set the comparison level.
**How to apply:** an own colour reference wins. Never copy family current
prices or links, borrow another colour's reference, or extend this exception
to button/shape variants.
