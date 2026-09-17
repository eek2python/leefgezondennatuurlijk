# Projectbrede audit productvarianten

## Samenvatting

- Categorieën gecontroleerd: 9
- Categorieën met varianten: 5
- Variantproducten (knoppen): 8
- Variantproducten (kleurswatches): 11
- Structurele fouten: 0
- Waarschuwingen: 23
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
| koekenpannen | 53 | 0 | 4 | productniveau | productniveau | productniveau | laag |
| hapjespannen | 13 | 0 | 1 | productniveau | productniveau | productniveau | laag |
| wokpannen | 15 | 0 | 0 | productniveau | productniveau | productniveau | laag |
| rvs-koekenpannen | 35 | 0 | 0 | productniveau | productniveau | productniveau | laag |
| koolstofstalen-koekenpannen | 29 | 0 | 0 | productniveau | productniveau | productniveau | laag |
| gietijzeren-koekenpannen | 30 | 0 | 2 | productniveau | productniveau | productniveau | laag |
| snijplanken | 8 | 0 | 0 | productniveau | productniveau | productniveau | laag |
| airfryers | 16 | 0 | 4 | productniveau | productniveau | productniveau | middel |
| vershoudbakjes | 18 | 8 | 0 | displayvariant | expliciete rijvelden | displayvariant (default of filtermatch) | laag |

## Structurele fouten

Geen.

## Waarschuwingen

| Code | Categorie | Product/bestand | Probleem |
|---|---|---|---|
| price_range_mismatch | koekenpannen | bk_infinity_28 | product: handmatig '€€' ≠ berekend '€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | demeyere_alu_pro_5_28 | product: handmatig '€€€€' ≠ berekend '€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | greenchef_diamond_24 | product: handmatig '€' ≠ berekend '€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | greenpan_apex_hybrid_24 | product: handmatig '€€€' ≠ berekend '€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | bk_infinity_24 | product: handmatig '€€' ≠ berekend '€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| missing_price | koekenpannen | scanpan_nura_26 | product: geen numerieke prijs |
| price_range_mismatch | koekenpannen | kochstar_stein_30 | product: handmatig '€' ≠ berekend '€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | greenpan_barcelona_pro_32 | product: handmatig '€€€' ≠ berekend '€€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| missing_price | koekenpannen | scanpan_nura_32 | product: geen numerieke prijs |
| price_range_mismatch | hapjespannen | greenchef_diamond_28 | product: handmatig '€€' ≠ berekend '€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | hapjespannen | bk_easy_induction_28 | product: handmatig '€€€' ≠ berekend '€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| missing_variant_url | vershoudbakjes | ikea_365+_enkel | Variant '600-ml' zonder eigen affiliate-URL (CTA toont bewust de uitgeschakelde staat) |
| missing_variant_url | vershoudbakjes | ikea_365+_enkel | Variant '1000-ml' zonder eigen affiliate-URL (CTA toont bewust de uitgeschakelde staat) |
| missing_variant_url | vershoudbakjes | ikea_365+_enkel | Variant '1200-ml' zonder eigen affiliate-URL (CTA toont bewust de uitgeschakelde staat) |
| missing_variant_url | vershoudbakjes | locknlock_enkel | Variant '630-ml' zonder eigen affiliate-URL (CTA toont bewust de uitgeschakelde staat) |
| missing_variant_url | vershoudbakjes | locknlock_enkel | Variant '740-ml' zonder eigen affiliate-URL (CTA toont bewust de uitgeschakelde staat) |
| missing_variant_url | vershoudbakjes | locknlock_enkel | Variant '1000-ml' zonder eigen affiliate-URL (CTA toont bewust de uitgeschakelde staat) |
| missing_variant_url | vershoudbakjes | igluu_meal_prep_3delig | Variant 'round' zonder eigen affiliate-URL (CTA toont bewust de uitgeschakelde staat) |
| missing_variant_url | vershoudbakjes | igluu_meal_prep_3delig | Variant 'square' zonder eigen affiliate-URL (CTA toont bewust de uitgeschakelde staat) |
| missing_variant_url | vershoudbakjes | pyrex_cook_heat_3delig | Variant 'round' zonder eigen affiliate-URL (CTA toont bewust de uitgeschakelde staat) |
| missing_variant_url | vershoudbakjes | pyrex_cook_heat_3delig | Variant 'square' zonder eigen affiliate-URL (CTA toont bewust de uitgeschakelde staat) |
| missing_variant_url | vershoudbakjes | igluu_meal_prep_5delig | Variant 'set-5x950-round' zonder eigen affiliate-URL (CTA toont bewust de uitgeschakelde staat) |
| missing_variant_url | vershoudbakjes | igluu_meal_prep_5delig | Variant 'set-5x950-rectangle' zonder eigen affiliate-URL (CTA toont bewust de uitgeschakelde staat) |

## Prijsniveau-audit (interne prijzen; niet publiek)

| Categorie | Product | Variant | Interne prijs | Handmatig niveau | Berekend niveau |
|---|---|---|---|---|---|
| koekenpannen | greenpan_barcelona_pro_28 | — | 82.09 | €€€ | €€€ |
| koekenpannen | kochstar_essenz_28 | Zwart | 13.99 | — | € |
| koekenpannen | kochstar_essenz_28 | Taupe | 14.99 | — | € |
| koekenpannen | fissler_essential_28 | — | 49.0 | €€ | €€ |
| koekenpannen | bk_easy_induction_28 | — | 39.99 | €€ | €€ |
| koekenpannen | brabantia_dusk_28 | — | 30.0 | €€ | €€ |
| koekenpannen | tefal_renew_28 | — | 38.99 | €€ | €€ |
| koekenpannen | bk_infinity_28 | — | 69.9 | €€ | €€€ |
| koekenpannen | demeyere_alu_pro_5_28 | — | 86.0 | €€€€ | €€€ |
| koekenpannen | debuyer_ceranoa_28 | — | 84.78 | €€€ | €€€ |
| koekenpannen | greenpan_mayflower_28 | Grijs | 59.9 | €€€ | €€€ |
| koekenpannen | greenpan_mayflower_28 | Blauw | 42.99 | €€ | €€ |
| koekenpannen | greenpan_apex_hybrid_28 | — | 65.95 | €€€ | €€€ |
| koekenpannen | greenpan_barcelona_pro_24 | — | 75.99 | €€€ | €€€ |
| koekenpannen | kochstar_essenz_24 | Zwart | 11.99 | — | € |
| koekenpannen | kochstar_essenz_24 | Taupe | 11.99 | — | € |
| koekenpannen | demeyere_alu_pro_5_ceraforce_24 | — | 78.5 | €€€ | €€€ |
| koekenpannen | greenchef_diamond_24 | — | 26.99 | € | €€ |
| koekenpannen | bk_easy_induction_24 | — | 33.95 | €€ | €€ |
| koekenpannen | greenpan_apex_hybrid_24 | — | 47.99 | €€€ | €€ |
| koekenpannen | tefal_renew_24 | — | 34.99 | €€ | €€ |
| koekenpannen | bk_infinity_24 | — | 59.9 | €€ | €€€ |
| koekenpannen | ikea_hemlagad_keramisch_24 | — | 9.99 | € | € |
| koekenpannen | berndes_b_green_24 | — | 64.99 | €€€ | €€€ |
| koekenpannen | greenpan_barcelona_pro_26 | — | 79.9 | €€€ | €€€ |
| koekenpannen | greenchef_vintage_26 | — | 42.9 | €€ | €€ |
| koekenpannen | demeyere_alu_pro_5_ceraforce_26 | — | 83.0 | €€€ | €€€ |
| koekenpannen | bk_easy_induction_26 | — | 37.95 | €€ | €€ |
| koekenpannen | fissler_essential_26 | — | 53.99 | €€€ | €€€ |
| koekenpannen | greenpan_venice_pro_26 | — | 99.9 | €€€€ | €€€€ |
| koekenpannen | scanpan_nura_26 | — | — | — | — |
| koekenpannen | greenpan_barcelona_pro_20 | — | 69.06 | €€€ | €€€ |
| koekenpannen | kochstar_essenz_20 | Zwart | 8.99 | — | € |
| koekenpannen | kochstar_essenz_20 | Taupe | 8.99 | — | € |
| koekenpannen | demeyere_alu_pro_5_ceraforce_20 | — | 71.0 | €€€ | €€€ |
| koekenpannen | greenchef_diamond_20 | — | 23.39 | € | € |
| koekenpannen | bk_easy_induction_20 | — | 28.95 | €€ | €€ |
| koekenpannen | greenpan_mayflower_20 | — | 49.9 | €€ | €€ |
| koekenpannen | tefal_renew_20 | — | 30.99 | €€ | €€ |
| koekenpannen | bk_enjoy_20 | — | 24.9 | € | € |
| koekenpannen | hema_milano_20 | — | 26.99 | €€ | €€ |
| koekenpannen | berndes_b_green_20 | — | 40.0 | €€ | €€ |
| koekenpannen | greenpan_barcelona_pro_30 | — | 88.09 | €€€ | €€€ |
| koekenpannen | kochstar_stein_30 | — | 27.9 | € | €€ |
| koekenpannen | demeyere_alu_pro_5_ceraforce_30 | — | 92.0 | €€€€ | €€€€ |
| koekenpannen | greenchef_diamond_30 | — | 32.32 | €€ | €€ |
| koekenpannen | bk_easy_induction_30 | — | 44.95 | €€ | €€ |
| koekenpannen | greenpan_torino_30 | — | 39.0 | €€ | €€ |
| koekenpannen | tefal_renew_30 | — | 41.99 | €€ | €€ |
| koekenpannen | brabantia_indu_plus_r_30 | — | 15.09 | € | € |
| koekenpannen | greenpan_barcelona_pro_32 | — | 91.99 | €€€ | €€€€ |
| koekenpannen | demeyere_alu_pro_5_ceraforce_32 | — | 99.5 | €€€€ | €€€€ |
| koekenpannen | combekk_forest_easy_32 | — | 59.0 | €€€ | €€€ |
| koekenpannen | tefal_renew_32 | — | 36.79 | €€ | €€ |
| koekenpannen | primecook_32 | — | 81.9 | €€€ | €€€ |
| koekenpannen | ikea_hemlagad_keramisch_32 | — | 17.99 | € | € |
| koekenpannen | scanpan_nura_32 | — | — | — | — |
| hapjespannen | greenpan_barcelona_pro_28 | — | 105.9 | €€€ | €€€ |
| hapjespannen | bk_enjoy_28 | Zwart | 59.9 | — | €€ |
| hapjespannen | bk_enjoy_28 | Licht Blauw | 59.9 | — | €€ |
| hapjespannen | bk_enjoy_28 | Oxford Blauw | 59.9 | — | €€ |
| hapjespannen | bk_enjoy_28 | Olijf Groen | 47.45 | — | €€ |
| hapjespannen | woll_ecolite_qxr_28 | — | 104.9 | €€€ | €€€ |
| hapjespannen | greenchef_diamond_28 | — | 39.99 | €€ | € |
| hapjespannen | bk_easy_induction_28 | — | 63.58 | €€€ | €€ |
| hapjespannen | be_living_28 | — | 44.95 | €€ | €€ |
| hapjespannen | greenpan_torino_28 | — | 54.01 | €€ | €€ |
| hapjespannen | greenpan_barcelona_pro_24 | — | 149.9 | €€€€ | €€€€ |
| hapjespannen | bk_brilliant_24 | — | 55.99 | €€ | €€ |
| hapjespannen | woll_ecolite_qxr_24 | — | 81.0 | €€€ | €€€ |
| hapjespannen | greenchef_prime_24 | — | 43.38 | €€ | €€ |
| hapjespannen | kochstar_essenz_24 | — | 19.99 | € | € |
| hapjespannen | greenpan_barcelona_pro_30 | — | 59.9 | €€ | €€ |
| wokpannen | greenpan_torino_wok_28 | — | 46.88 | €€ | — |
| wokpannen | hema_milano_wok_28 | — | 37.99 | €€ | — |
| wokpannen | wmf_durado_wok_28 | — | 61.11 | €€ | — |
| wokpannen | greenchef_diamond_wok_28 | — | 39.9 | €€ | — |
| wokpannen | primecook_wok_28 | — | 69.6 | €€€ | — |
| wokpannen | bk_granite_wok_28 | — | 49.99 | €€ | — |
| wokpannen | brabantia_indu_plus_wok_28 | — | 40.0 | €€ | — |
| wokpannen | greenpan_cambridge_wok_28 | — | 49.82 | €€€ | — |
| wokpannen | bk_easy_basic_ceramic_wok_28 | — | 49.9 | €€ | — |
| wokpannen | berghoff_leo_phantom_wok_28 | — | 59.95 | €€€ | — |
| wokpannen | greenpan_barcelona_evershine_wok_30 | — | 149.9 | €€€€ | — |
| wokpannen | bk_easy_induction_wok_30 | — | 66.17 | €€€ | — |
| wokpannen | bk_superior_ceramic_wok_30 | — | 73.87 | €€€ | — |
| wokpannen | greenpan_copenhagen_wok_30 | — | 68.2 | €€€ | — |
| wokpannen | berghoff_phantom_wok_30 | — | 74.95 | €€€ | — |
| rvs-koekenpannen | demeyere_industry_5_24 | — | 117.0 | €€€ | — |
| rvs-koekenpannen | bk_superior_tri_ply_24 | — | 65.0 | €€ | — |
| rvs-koekenpannen | debuyer_affinity_24 | — | 125.32 | €€€ | — |
| rvs-koekenpannen | wmf_profi_24 | — | 54.18 | €€ | — |
| rvs-koekenpannen | demeyere_silverline_7_nanotouch_24 | — | 209.0 | €€€€ | — |
| rvs-koekenpannen | bk_bright_24 | — | 35.26 | € | — |
| rvs-koekenpannen | demeyere_industry_5_28 | — | 139.0 | €€€ | — |
| rvs-koekenpannen | demeyere_silverline_7_nanotouch_28 | — | 189.0 | €€€€ | — |
| rvs-koekenpannen | debuyer_affinity_28 | — | 141.0 | €€€ | — |
| rvs-koekenpannen | wmf_profi_28 | — | 63.99 | €€ | — |
| rvs-koekenpannen | bk_superior_tri_ply_28 | — | 89.9 | €€ | — |
| rvs-koekenpannen | bk_bright_28 | — | 38.81 | € | — |
| rvs-koekenpannen | demeyere_industry_5_20 | — | 132.4 | €€€ | — |
| rvs-koekenpannen | bk_superior_tri_ply_20 | — | 59.95 | €€ | — |
| rvs-koekenpannen | sola_green_cooking_plus_20 | — | 42.95 | € | — |
| rvs-koekenpannen | wmf_profi_20 | — | 41.99 | € | — |
| rvs-koekenpannen | debuyer_affinity_20 | — | 110.0 | €€€ | — |
| rvs-koekenpannen | demeyere_silverline_7_nanotouch_20 | — | 189.0 | €€€€ | — |
| rvs-koekenpannen | bk_maestro_rvs_30 | — | 109.9 | €€€ | — |
| rvs-koekenpannen | le_creuset_3ply_classic_30 | — | 139.0 | €€€ | — |
| rvs-koekenpannen | cristel_1826_30 | — | 134.9 | €€€ | — |
| rvs-koekenpannen | beka_chef_30 | — | 90.6 | €€ | — |
| rvs-koekenpannen | mauviel_mcook_30 | — | 280.0 | €€€€ | — |
| rvs-koekenpannen | oz_home_bavary_30 | — | 37.95 | € | — |
| rvs-koekenpannen | demeyere_industry_5_32 | — | 195.0 | €€€ | — |
| rvs-koekenpannen | spring_brigade_premium_32 | — | 129.0 | €€€ | — |
| rvs-koekenpannen | debuyer_affinity_32 | — | 188.0 | €€€ | — |
| rvs-koekenpannen | cristel_castel_pro_32 | — | 169.0 | €€€ | — |
| rvs-koekenpannen | demeyere_silverline_7_nanotouch_32 | — | 269.0 | €€€€ | — |
| rvs-koekenpannen | debuyer_prim_appety_32 | — | 54.99 | €€ | — |
| rvs-koekenpannen | fissler_m5_pro_ply_26 | — | 169.0 | €€€ | — |
| rvs-koekenpannen | cristel_castel_pro_26 | — | 144.0 | €€€ | — |
| rvs-koekenpannen | le_creuset_signature_rvs_26 | — | 149.0 | €€€ | — |
| rvs-koekenpannen | habonne_queen_26 | — | 59.99 | €€ | — |
| rvs-koekenpannen | scanpan_impact_26 | — | 51.9 | € | — |
| koolstofstalen-koekenpannen | debuyer_mineral_b_20 | — | 36.95 | €€ | — |
| koolstofstalen-koekenpannen | debuyer_mineral_b_pro_20 | — | 46.99 | €€ | — |
| koolstofstalen-koekenpannen | skottsberg_carbon_steel_20 | — | 49.99 | €€ | — |
| koolstofstalen-koekenpannen | bk_black_steel_20 | — | 32.9 | €€ | — |
| koolstofstalen-koekenpannen | forged_essentials_20 | — | 45.0 | €€ | — |
| koolstofstalen-koekenpannen | blackwell_carbon_steel_20 | — | 29.99 | €€ | — |
| koolstofstalen-koekenpannen | debuyer_mineral_b_24 | — | 32.3 | €€ | — |
| koolstofstalen-koekenpannen | debuyer_mineral_b_pro_24 | — | 58.0 | €€€ | — |
| koolstofstalen-koekenpannen | skottsberg_carbon_steel_24 | — | 59.99 | €€€ | — |
| koolstofstalen-koekenpannen | forged_essentials_24 | — | 64.95 | €€€ | — |
| koolstofstalen-koekenpannen | blackwell_carbon_steel_24 | — | 34.99 | €€ | — |
| koolstofstalen-koekenpannen | hendi_traditioneel_24 | — | 24.95 | € | — |
| koolstofstalen-koekenpannen | debuyer_mineral_b_28 | — | 41.79 | €€ | — |
| koolstofstalen-koekenpannen | skottsberg_carbon_steel_28 | — | 69.99 | €€€ | — |
| koolstofstalen-koekenpannen | debuyer_mineral_b_pro_28 | — | 54.49 | €€€ | — |
| koolstofstalen-koekenpannen | beka_nomad_28 | — | 45.0 | €€ | — |
| koolstofstalen-koekenpannen | forged_essentials_28 | — | 74.95 | €€€ | — |
| koolstofstalen-koekenpannen | bk_black_steel_28 | — | 43.9 | €€ | — |
| koolstofstalen-koekenpannen | ikea_vardagen_28 | — | 29.99 | € | — |
| koolstofstalen-koekenpannen | debuyer_carbone_plus_30 | — | 59.99 | €€ | — |
| koolstofstalen-koekenpannen | netherton_foundry_induction_30 | — | 119.95 | €€€€ | — |
| koolstofstalen-koekenpannen | bk_black_steel_30 | — | 43.95 | €€ | — |
| koolstofstalen-koekenpannen | blackwell_carbon_steel_30 | — | 44.99 | €€ | — |
| koolstofstalen-koekenpannen | bk_solid_steel_30 | — | 29.59 | € | — |
| koolstofstalen-koekenpannen | hendi_traditioneel_30 | — | 25.66 | € | — |
| koolstofstalen-koekenpannen | debuyer_mineral_b_32 | — | 44.89 | €€ | — |
| koolstofstalen-koekenpannen | debuyer_mineral_b_pro_32 | — | 95.49 | €€€ | — |
| koolstofstalen-koekenpannen | blackwell_carbon_steel_32 | — | 49.99 | €€ | — |
| koolstofstalen-koekenpannen | hendi_traditioneel_32 | — | 23.47 | € | — |
| gietijzeren-koekenpannen | petromax_fp20_20 | — | 34.64 | €€ | — |
| gietijzeren-koekenpannen | le_creuset_signature_skillet_20 | — | 119.95 | €€€€ | — |
| gietijzeren-koekenpannen | hendi_cast_iron_skillet_20 | — | 18.5 | € | — |
| gietijzeren-koekenpannen | ronneby_bruk_ultra_light_pro_20 | — | 79.95 | €€€ | — |
| gietijzeren-koekenpannen | lava_cast_iron_20 | — | 59.95 | €€€ | — |
| gietijzeren-koekenpannen | blackwell_cast_iron_20 | — | 17.99 | € | — |
| gietijzeren-koekenpannen | skottsberg_cast_iron_24 | — | 59.99 | €€ | — |
| gietijzeren-koekenpannen | combekk_cast_iron_24 | — | 66.95 | €€€ | — |
| gietijzeren-koekenpannen | ronneby_bruk_maestro_24 | — | 85.0 | €€€ | — |
| gietijzeren-koekenpannen | skeppshult_walnut_24 | — | 149.0 | €€€€ | — |
| gietijzeren-koekenpannen | staub_cast_iron_24 | — | 108.99 | €€€€ | — |
| gietijzeren-koekenpannen | maysternya_cast_iron_24 | — | 37.5 | €€ | — |
| gietijzeren-koekenpannen | lodge_logic_26 | — | 59.99 | €€ | — |
| gietijzeren-koekenpannen | maysternya_cast_iron_26 | — | 38.95 | €€ | — |
| gietijzeren-koekenpannen | combekk_classic_skillet_26 | — | 73.09 | €€€ | — |
| gietijzeren-koekenpannen | fissler_moments_26 | Ivory White | 59.0 | — | — |
| gietijzeren-koekenpannen | fissler_moments_26 | Burgundy Red | 55.0 | — | — |
| gietijzeren-koekenpannen | staub_cast_iron_26 | — | 149.0 | €€€€ | — |
| gietijzeren-koekenpannen | le_creuset_signature_skillet_26 | Zwart | 160.99 | — | — |
| gietijzeren-koekenpannen | le_creuset_signature_skillet_26 | Kersenrood | 154.0 | — | — |
| gietijzeren-koekenpannen | le_creuset_signature_skillet_26 | Nectar | 164.95 | — | — |
| gietijzeren-koekenpannen | skottsberg_cast_iron_28 | — | 69.99 | €€€ | — |
| gietijzeren-koekenpannen | kela_calido_28 | — | 59.95 | €€ | — |
| gietijzeren-koekenpannen | beka_stark_28 | — | 69.0 | €€€ | — |
| gietijzeren-koekenpannen | wmf_flavour_28 | — | 68.0 | €€€ | — |
| gietijzeren-koekenpannen | lava_cast_iron_28 | — | 79.95 | €€€ | — |
| gietijzeren-koekenpannen | skeppshult_traditional_28 | — | 195.0 | €€€€ | — |
| gietijzeren-koekenpannen | lodge_logic_30 | — | 69.95 | €€€ | — |
| gietijzeren-koekenpannen | valhal_outdoor_vh30_30 | — | 41.95 | €€ | — |
| gietijzeren-koekenpannen | petromax_fp30_30 | — | 44.99 | €€ | — |
| gietijzeren-koekenpannen | beka_stark_30 | — | 75.0 | €€€ | — |
| gietijzeren-koekenpannen | koock_amsterdam_skillet_30 | — | 44.95 | €€ | — |
| gietijzeren-koekenpannen | victoria_signature_polished_30 | — | 184.0 | €€€€ | — |
| snijplanken | kaamut_walnoot_endgrain | — | 129.0 | €€€€ | — |
| snijplanken | ikea_aptitlig_bamboe | — | 6.99 | € | — |
| snijplanken | boosblocks_pro_maple | — | 323.64 | €€€€ | — |
| snijplanken | zwilling_beukenhout_60x40 | — | 54.99 | €€€ | — |
| snijplanken | namture_premium_olie_45x30 | — | 69.99 | €€€ | — |
| snijplanken | wmf_acacia_40x32 | — | 36.59 | €€ | — |
| snijplanken | continenta_rubberwood_35x25 | — | 26.96 | €€ | — |
| snijplanken | hema_beukenhout_24x35 | — | 9.99 | € | — |
| airfryers | inventum_gf500hld_5l | — | 79.0 | €€ | — |
| airfryers | bourgini_slimfit_xl_5l | — | 99.99 | €€ | — |
| airfryers | masterpro_rocket_cyclone_5l | — | 125.73 | €€€ | — |
| airfryers | wartmann_wm2312af_5l | — | 119.95 | €€ | — |
| airfryers | maison_kitchen_5l | — | 69.95 | € | — |
| airfryers | ninja_crispi_4in1 | Marineblauw | 109.0 | — | — |
| airfryers | ninja_crispi_4in1 | Groen | 109.0 | — | — |
| airfryers | ninja_crispi_4in1 | Stone | 109.0 | — | — |
| airfryers | inventum_gf730hldb_7_3l | — | 109.0 | €€ | — |
| airfryers | princess_182280_8l | — | 54.99 | € | — |
| airfryers | greenpan_bistro_xxl_7_2l | Zwart | 126.99 | — | — |
| airfryers | greenpan_bistro_xxl_7_2l | Pine Green | 150.99 | — | — |
| airfryers | greenpan_bistro_xxl_7_2l | Smokey Blue | 124.9 | — | — |
| airfryers | bourgini_slimfit_pure_8l | Zwart | 129.99 | — | — |
| airfryers | bourgini_slimfit_pure_8l | Beige | 129.99 | — | — |
| airfryers | maison_kitchen_8l | — | 79.95 | €€ | — |
| airfryers | ninja_crispi_pro_xl_5_7l | Asgrijs | 249.0 | — | — |
| airfryers | ninja_crispi_pro_xl_5_7l | Marineblauw | 219.0 | — | — |
| airfryers | ninja_crispi_pro_xl_5_7l | Gebroken Wit | 249.0 | — | — |
| airfryers | ninja_crispi_pro_xl_5_7l | Rose | 249.0 | — | — |
| airfryers | inventum_gf800hld_dual_8l | — | 89.99 | €€ | — |
| airfryers | bourgini_duo_8l | — | 105.0 | € | — |
| airfryers | greenpan_bistro_dual_8l | — | 129.99 | €€€ | — |
| airfryers | wartmann_wm2511af_11l | — | 195.0 | €€€€ | — |
| vershoudbakjes | pyrex_cook_store_enkel | — | 24.99 | €€ | — |
| vershoudbakjes | ikea_365+_enkel | 600-ml | 3.49 | — | — |
| vershoudbakjes | ikea_365+_enkel | 1000-ml | 4.49 | — | — |
| vershoudbakjes | ikea_365+_enkel | 1200-ml | 4.99 | — | — |
| vershoudbakjes | mepal_easyclip_glass_enkel | 450-ml | 9.44 | — | — |
| vershoudbakjes | mepal_easyclip_glass_enkel | 700-ml | 12.59 | — | — |
| vershoudbakjes | mepal_easyclip_glass_enkel | 1500-ml | 21.99 | — | — |
| vershoudbakjes | mepal_easyclip_glass_enkel | 2250-ml | 24.19 | — | — |
| vershoudbakjes | locknlock_enkel | 630-ml | 9.95 | — | — |
| vershoudbakjes | locknlock_enkel | 740-ml | 12.95 | — | — |
| vershoudbakjes | locknlock_enkel | 1000-ml | 15.95 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 820-ml-rectangle | 9.14 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 380-ml-rectangle | 10.06 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 1220-ml-rectangle | 10.58 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 1970-ml-rectangle | 28.9 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 1220-ml-square | 12.68 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 760-ml-square | 9.99 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 420-ml-round | 7.95 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 920-ml-round | 11.3 | — | — |
| vershoudbakjes | berghoff_perfect_seal | 500-ml-square | 16.47 | — | — |
| vershoudbakjes | berghoff_perfect_seal | 1100-ml-square | 22.47 | — | — |
| vershoudbakjes | mepal_easyclip_glass_3delig | — | 49.97 | €€€ | — |
| vershoudbakjes | igluu_meal_prep_3delig | round | 24.95 | — | — |
| vershoudbakjes | igluu_meal_prep_3delig | square | 24.95 | — | — |
| vershoudbakjes | pyrex_cook_heat_3delig | round | 61.84 | — | — |
| vershoudbakjes | pyrex_cook_heat_3delig | square | 39.87 | — | — |
| vershoudbakjes | bormioli_frigoverre_3delig | — | 27.99 | €€ | — |
| vershoudbakjes | luminarc_purebox_3delig | — | 26.61 | €€ | — |
| vershoudbakjes | glasslock_3delig | — | 41.29 | €€€ | — |
| vershoudbakjes | pyrex_cook_heat_5delig | — | 65.0 | €€€ | — |
| vershoudbakjes | bormioli_frigoverre_5delig | — | 44.99 | €€ | — |
| vershoudbakjes | igluu_meal_prep_5delig | set-5x950-round | 33.95 | — | — |
| vershoudbakjes | igluu_meal_prep_5delig | set-5x950-rectangle | 38.95 | — | — |
| vershoudbakjes | kitchenbrothers_5delig | — | 27.99 | €€ | — |
| vershoudbakjes | luminarc_purebox_5delig | — | 49.63 | €€ | — |
| vershoudbakjes | oxo_good_grips_smart_seal_4delig | — | 41.29 | €€€ | — |

## Handmatige controle

| Categorie | Probleem | Waarom niet automatisch opgelost |
|---|---|---|
| vershoudbakjes | Eerder gemarkeerde TODO-varianten (Igluu vierkant, Lock&Lock 630 ml / 1 L) hebben inmiddels prijs en URL; periodieke prijsverificatie blijft handwerk | price_last_checked bijwerken is een redactionele taak; de audit mag geen prijzen wijzigen |
