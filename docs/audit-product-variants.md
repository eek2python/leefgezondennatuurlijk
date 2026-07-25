# Projectbrede audit productvarianten

## Samenvatting

- Categorieën gecontroleerd: 7
- Categorieën met varianten: 2
- Variantproducten (knoppen): 8
- Variantproducten (kleurswatches): 3
- Structurele fouten: 0
- Waarschuwingen: 1
- Handmatige controles: zie tabel onderaan

## Gedeelde infrastructuur

| Helper | Gebruikt door | Mutatie | Commerciële fallback | Status |
|---|---|---|---|---|
| utils/variant_helpers.py (prepare_product_variants, set_display_variant, resolve_commercial_fields, _apply_display_variant_fields) | vershoudbakjes (knopvarianten) | alleen op deep copies in views | geen — velden worden expliciet gezet of gewist; familie-afbeelding als gedocumenteerde fallback | OK |
| static/assets/js/variant-selector.js | vershoudbakjes-productkaarten | n.v.t. (DOM) | geen — set-or-clear per veld | OK |
| static/assets/js/variants.js | airfryers-kleurswatches | n.v.t. (DOM) | bewuste familiefallback naar data-base-* (gedocumenteerd beleid) | OK |

## Categorieoverzicht

| Categorie | Producten | Knopvarianten | Swatchvarianten | Productkaart | Tabel | JSON-LD | Risico |
|---|---|---|---|---|---|---|---|
| koekenpannen | 58 | 0 | 0 | productniveau | productniveau | productniveau | laag |
| hapjespannen | 16 | 0 | 0 | productniveau | productniveau | productniveau | laag |
| wokpannen | 17 | 0 | 0 | productniveau | productniveau | productniveau | laag |
| rvs-koekenpannen | 21 | 0 | 0 | productniveau | productniveau | productniveau | laag |
| snijplanken | 10 | 0 | 0 | productniveau | productniveau | productniveau | laag |
| airfryers | 17 | 0 | 3 | productniveau | productniveau | productniveau | middel |
| vershoudbakjes | 18 | 8 | 0 | displayvariant | expliciete rijvelden | displayvariant (default of filtermatch) | laag |

## Structurele fouten

Geen.

## Waarschuwingen

| Code | Categorie | Product/bestand | Probleem |
|---|---|---|---|
| inconsistent_jsonld_variant | airfryers | greenpan_silhouette_xl_5l | JSON-LD gebruikt productniveauprijs 129.9 maar de getoonde defaultswatch 'Moroccan Green' kost 116.0 |

## Handmatige controle

| Categorie | Probleem | Waarom niet automatisch opgelost |
|---|---|---|
| airfryers | greenpan_silhouette_xl_5l: productniveauprijs (129,90) wijkt af van de getoonde defaultswatch Moroccan Green (116,00); JSON-LD gebruikt productniveau | Prijscorrectie is een redactionele/datakeuze; de audit mag geen prijzen wijzigen |
| vershoudbakjes | Eerder gemarkeerde TODO-varianten (Igluu vierkant, Lock&Lock 630 ml / 1 L) hebben inmiddels prijs en URL; periodieke prijsverificatie blijft handwerk | price_last_checked bijwerken is een redactionele taak; de audit mag geen prijzen wijzigen |
