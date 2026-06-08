---
name: Product color variants
description: Conventions for the optional product-card color-swatch feature (template + variants.js).
---

# Product color variants

Optional `variants` list on a product dict drives circular color swatches in the product card. Reusable across all categories.

**Rules / decisions:**
- Variants are **card-only and client-side**. Never create per-color URLs/pages, and never expand canonical or Schema.org structured data per color — those stay tied to the single base `product.image`.
  - **Why:** the explicit SEO requirement was to keep one canonical product page per product; per-color URLs would fragment ranking signals.
- All variant images for a given product **must share the same aspect ratio** (example GreenPan uses 1200×800).
  - **Why:** the card image is `width:100%` with auto height; mismatched ratios cause visible layout shift on swatch click. When sourcing real images from the web, flatten to white + autocrop + pad onto a fixed canvas to normalize.
- Affiliate fallback: a swatch without its own `affiliate_url` falls back to the button's `data-base-affiliate` (product-level URL), not the previously-selected variant's URL.
- JS is scoped per card (`[data-variant-card]`) so multiple cards on one page operate independently; swatches are native `<button>`s for free keyboard support; a `requestId` token guards against stale preload callbacks on rapid clicks.

**How to apply:** to add variants to another product, add a `variants` list (`name`, `image`, `hex`, optional `affiliate_url`) and ensure all variant images match aspect ratio. No view or URL changes needed.
