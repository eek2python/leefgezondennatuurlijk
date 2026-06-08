---
name: Product color variants
description: Conventions for the optional product-card color-swatch feature.
---

# Product color variants

Optional `variants` list on a product dict drives circular color swatches in the product card. Reusable across all categories. Each variant: `name`, `image`, `hex`, optional `affiliate_url`, optional `price_range`.

**Rules / decisions:**
- Variants are **card-only and client-side**. Never create per-color URLs/pages, and never expand canonical or Schema.org structured data per color — those stay tied to the single base `product.image`/base price.
  - **Why:** the explicit SEO requirement was one canonical product page per product; per-color URLs would fragment ranking signals.
- All variant images for a given product **must share the same aspect ratio** (example GreenPan uses 1200×800).
  - **Why:** the card image is `width:100%` with auto height; mismatched ratios cause visible layout shift on swatch click. When sourcing real images from the web, flatten to white + autocrop + pad onto a fixed canvas to normalize.
- Per-variant `affiliate_url` and `price_range` are optional; a swatch missing either **falls back to the product-level value**, not to the previously-selected variant's value.

**How to apply:** to add variants to another product, add a `variants` list and ensure all variant images match aspect ratio. No view or URL changes needed. Do NOT fabricate per-color prices or affiliate links — they are real commercial data; ask the user or source them with approval.
