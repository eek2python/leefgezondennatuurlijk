---
name: Two product variant systems
description: How colour-swatch vs shape-button variants are distinguished on product cards
---

The site has two variant systems that share the `variants` key on product dicts:
- Colour swatches (airfryers): variant dicts have `name`/`hex`, no `id`.
- Shape/format buttons (vershoudcontainers): variant dicts have `id`/`label`/`is_default`.

**Rule:** the presence of an `id` key decides which system applies. `prepare_product_variants` ignores non-`id` variants; the product card template branches on `shape_variants` before legacy `variants`.

**Why:** reusing the same key avoided touching airfryer data, but any new variant type must keep this discriminator consistent or both UIs render at once.

**How to apply:** when adding variants to a product, include `id` for shape/format-style button selectors, omit it (use `hex`) for colour swatches. Never mix both styles in one product.
