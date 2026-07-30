# Productlinks: affiliate, retailer en fabrikant

## Drie URL-velden (alle optioneel, per product én per variant)

| Veld | Doel | Knop | Label | rel |
|---|---|---|---|---|
| `affiliate_url` | Uitsluitend échte affiliatelinks | primair | "Bekijk prijs & reviews →" | `nofollow sponsored noopener` |
| `retailer_url` | Gewone winkelproductpagina's zonder actieve affiliatecode | primair | "Bekijk prijs & reviews →" | `nofollow noopener` (nooit `sponsored`) |
| `official_url` | Informatieve fabrikantpagina's | secundair (informatief) | "Bekijk productspecificaties →" | `noopener` (nooit `sponsored`) |

Aanvullend: `availability_label` — niet-klikbare statustekst (bijv. "Nog niet
algemeen verkrijgbaar") die alleen wordt getoond wanneer geen enkele URL
beschikbaar is. Geen URL en geen label → geen knop (nooit `href=""`/`href="#"`).

## Prioriteit

`affiliate_url` → `retailer_url` → `official_url` → `availability_label` → niets.

## Centrale resolver

Alle weergaven (productkaarten, detailpagina's, vergelijkingstabellen,
top-picks, variantwissels) gebruiken één resolver:

- `utils/variant_helpers.py::resolve_product_link(product, selected_variant)`
  → frozen dataclass `ProductLink(url, link_type, label, rel, is_commercial)`.
- Templates renderen uitsluitend het reeds bepaalde resultaat, bij voorkeur
  via de partial `templates/includes/product_link.html`
  (context: `resolved_link`, `availability_label`, `link_product`, `link_small`).
- Views zetten `product["resolved_link"]`/`product["availability_label"]`
  via `apply_resolved_link()`; vergelijkingsrijen krijgen `row["resolved_link"]`.
- JavaScript (`static/assets/js/variant-selector.js`) dupliceert de logica
  niet: de variantpayload bevat door Django resolved velden
  (`resolved_url`, `resolved_link_type`, `resolved_label`, `resolved_rel`).

## Variantregels

- Varianten slaan hun eigen `affiliate_url`/`retailer_url`/`official_url`/
  `availability_label` op in hun eigen dict.
- Bij een geselecteerde variant worden UITSLUITEND de URL-velden van die
  variant gebruikt; een lege URL valt nooit terug op een andere variant of
  op verouderde productniveau-data (zelfde strengheid als
  `resolve_commercial_fields`).
- Enige gedocumenteerde productniveau-fallback: producten zónder
  button-varianten resolven op productniveau. De afbeelding kent een aparte
  familie-fallback; links niet.
- **Kleurswatch-uitzondering** (airfryers e.d., varianten zonder `id`): het
  bestaande swatchsysteem (`static/assets/js/variants.js`) toont uitsluitend
  affiliatelinks en mag per gedocumenteerd familiebeleid terugvallen op de
  productniveau-`affiliate_url` (`data-base-affiliate`) — kleurvarianten
  verwijzen naar dezelfde productfamilie. `retailer_url`/`official_url` op
  een swatch-variant wordt niet gerenderd; de audit `product_links`
  waarschuwt hiervoor (`swatch_variant_link_field_unsupported`).
- Bij een variantwissel veranderen href, label, rel, class, `data-link-type`,
  zichtbaarheid en `availability_label` mee (en verdwijnt een oude href
  volledig uit de DOM).

## JSON-LD

- Alleen `affiliate_url` (met prijs, valuta en beschikbaarheid) levert een
  schema.org `Offer` op. `retailer_url` en `official_url` worden nooit
  automatisch als Offer-URL gebruikt; een fabrikantpagina is geen
  verkooppagina. `availability_label` is presentatietekst en gaat nooit als
  schema.org-waarde naar buiten.

## Beheerregels

- Affiliate-URL's nooit automatisch "opschonen": trackingparameters kunnen
  de affiliatecode zijn.
- `retailer_url` en `official_url` bij voorkeur zónder trackingparameters
  opslaan (de audit waarschuwt hiervoor).
- Verplaats bestaande `affiliate_url`-waarden niet automatisch naar
  `retailer_url`; of een link echt affiliate is, is niet technisch
  vaststelbaar. Markeer bevestigde affiliatelinks optioneel met
  `"affiliate_confirmed": True`; onbevestigde worden door de audit
  `product_links` als handmatige-reviewmelding (INFO) gerapporteerd.
- Audit draaien: dashboard `/admin/product-audits/` of
  `python manage.py audit_products --audit product_links`.
