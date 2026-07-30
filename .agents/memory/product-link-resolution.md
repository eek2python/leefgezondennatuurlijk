---
name: Product link resolution
description: Rules for affiliate/retailer/official link handling and the central resolver
---

# Productlink-resolutie

**Regel:** alle productlinks lopen via de centrale resolver
`utils/variant_helpers.py::resolve_product_link` met vaste prioriteit
affiliate_url → retailer_url → official_url → availability_label → niets.
Templates renderen alleen resolved resultaten (partial
`templates/includes/product_link.html`); JS krijgt door Django resolved
velden in de variantpayload — nooit eigen linkprioriteit in templates of JS.

**Why:** juridisch/SEO-onderscheid: alleen echte affiliatelinks mogen
`rel="sponsored"`; fabrikantpagina's mogen nooit als kooplink worden
gepresenteerd; varianten mogen nooit een link van een andere variant tonen.

**How to apply:**
- Nieuwe weergaven: altijd de partial of `product.resolved_link` gebruiken,
  nooit rechtstreeks een URL-veld kiezen in een template.
- Bestaande `affiliate_url`-waarden nooit automatisch herclassificeren of
  "opschonen"; de audit `product_links` levert de handmatige-reviewlijst
  (`affiliate_url_without_affiliate_confirmation`, INFO). Bevestigde
  affiliatelinks kunnen `affiliate_confirmed: True` krijgen.
- Kleurswatch-uitzondering (varianten zonder `id`): affiliate-only met
  gedocumenteerde familie-fallback naar productniveau; retailer/official op
  swatch-varianten wordt niet gerenderd (audit waarschuwt).
- JSON-LD Offer alleen uit affiliate_url; nooit uit retailer/official.

Volledige regels: `docs/product-links.md`.
