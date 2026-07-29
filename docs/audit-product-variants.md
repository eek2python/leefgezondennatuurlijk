# Projectbrede audit productvarianten

## Samenvatting

- Categorieën gecontroleerd: 7
- Categorieën met varianten: 3
- Variantproducten (knoppen): 8
- Variantproducten (kleurswatches): 7
- Structurele fouten: 0
- Waarschuwingen: 19
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
| koekenpannen | 57 | 0 | 4 | productniveau | productniveau | productniveau | laag |
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
| inconsistent_jsonld_variant | koekenpannen | greenpan_mayflower_28 | Default-swatch-URL wijkt af van productniveau-URL (JSON-LD-basis) |
| inconsistent_jsonld_variant | koekenpannen | kochstar_essenz_24 | Default-swatch-URL wijkt af van productniveau-URL (JSON-LD-basis) |
| inconsistent_jsonld_variant | koekenpannen | kochstar_essenz_20 | Default-swatch-URL wijkt af van productniveau-URL (JSON-LD-basis) |
| inconsistent_jsonld_variant | airfryers | greenpan_silhouette_xl_5l | JSON-LD gebruikt productniveauprijs 129.9 maar de getoonde defaultswatch 'Moroccan Green' kost 116.0 |
| price_range_mismatch | koekenpannen | greenpan_barcelona_pro_28 | product: handmatig '€€€' ≠ berekend '€€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | habonne_hybrid_28 | product: handmatig '€€€€' ≠ berekend '€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | demeyere_alu_pro_5_28 | product: handmatig '€€€€' ≠ berekend '€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | demeyere_alu_pro_5_ceraforce_24 | product: handmatig '€€€€' ≠ berekend '€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | greenchef_diamond_24 | product: handmatig '€€' ≠ berekend '€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | berndes_b_green_24 | product: handmatig '€€' ≠ berekend '€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | demeyere_alu_pro_5_ceraforce_26 | product: handmatig '€€€€' ≠ berekend '€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | greenpan_venice_pro_26 | product: handmatig '€€€' ≠ berekend '€€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | demeyere_alu_pro_5_ceraforce_20 | product: handmatig '€€€€' ≠ berekend '€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | greenchef_diamond_20 | product: handmatig '€€' ≠ berekend '€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | bk_enjoy_20 | product: handmatig '€€' ≠ berekend '€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | hema_milano_20 | product: handmatig '€' ≠ berekend '€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | greenpan_barcelona_pro_30 | product: handmatig '€€€' ≠ berekend '€€€€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | kochstar_stein_30 | product: handmatig '€€' ≠ berekend '€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |
| price_range_mismatch | koekenpannen | brabantia_indu_plus_r_30 | product: handmatig '€€€' ≠ berekend '€' (berekend niveau is leidend bij rendering; brondata blijft ongewijzigd) |

## Prijsniveau-audit (interne prijzen; niet publiek)

| Categorie | Product | Variant | Interne prijs | Handmatig niveau | Berekend niveau |
|---|---|---|---|---|---|
| koekenpannen | greenpan_barcelona_pro_28 | — | 91.03 | €€€ | €€€€ |
| koekenpannen | kochstar_essenz_28 | Zwart | 13.99 | — | € |
| koekenpannen | kochstar_essenz_28 | Taupe | 14.99 | — | € |
| koekenpannen | habonne_hybrid_28 | — | 75.0 | €€€€ | €€€ |
| koekenpannen | greenchef_diamond_28 | — | 26.99 | €€ | €€ |
| koekenpannen | bk_easy_induction_28 | — | 39.99 | €€ | €€ |
| koekenpannen | brabantia_dusk_28 | — | 30.0 | €€ | €€ |
| koekenpannen | tefal_renew_28 | — | 38.99 | €€ | €€ |
| koekenpannen | bk_enjoy_28 | — | 34.9 | €€ | €€ |
| koekenpannen | demeyere_alu_pro_5_28 | — | 85.0 | €€€€ | €€€ |
| koekenpannen | debuyer_ceranoa_28 | — | 105.0 | €€€€ | €€€€ |
| koekenpannen | greenpan_mayflower_28 | Grijs | 59.9 | €€€ | €€€ |
| koekenpannen | greenpan_mayflower_28 | Blauw | 42.99 | €€ | €€ |
| koekenpannen | greenpan_barcelona_pro_24 | — | 79.29 | €€€ | €€€ |
| koekenpannen | kochstar_essenz_24 | Zwart | 11.99 | — | € |
| koekenpannen | kochstar_essenz_24 | Taupe | 11.99 | — | € |
| koekenpannen | demeyere_alu_pro_5_ceraforce_24 | — | 77.0 | €€€€ | €€€ |
| koekenpannen | greenchef_diamond_24 | — | 23.99 | €€ | € |
| koekenpannen | bk_easy_induction_24 | — | 33.95 | €€ | €€ |
| koekenpannen | greenpan_torino_24 | — | 39.6 | €€ | €€ |
| koekenpannen | tefal_renew_24 | — | 35.99 | €€ | €€ |
| koekenpannen | bk_enjoy_24 | — | 29.9 | €€ | €€ |
| koekenpannen | ikea_hemlagad_keramisch_24 | — | 9.99 | € | € |
| koekenpannen | berndes_b_green_24 | — | 64.99 | €€ | €€€ |
| koekenpannen | greenpan_barcelona_pro_26 | — | 79.9 | €€€ | €€€ |
| koekenpannen | greenchef_vintage_26 | — | 42.9 | €€ | €€ |
| koekenpannen | demeyere_alu_pro_5_ceraforce_26 | — | 83.0 | €€€€ | €€€ |
| koekenpannen | bk_easy_induction_26 | — | 37.95 | €€ | €€ |
| koekenpannen | fissler_cenit_ceramic_26 | — | 54.99 | €€€ | €€€ |
| koekenpannen | greenpan_venice_pro_26 | — | 99.9 | €€€ | €€€€ |
| koekenpannen | scanpan_ceramic_26 | — | 175.0 | €€€€ | €€€€ |
| koekenpannen | greenpan_barcelona_pro_20 | — | 69.06 | €€€ | €€€ |
| koekenpannen | kochstar_essenz_20 | Zwart | 8.99 | — | € |
| koekenpannen | kochstar_essenz_20 | Taupe | 8.99 | — | € |
| koekenpannen | demeyere_alu_pro_5_ceraforce_20 | — | 72.25 | €€€€ | €€€ |
| koekenpannen | greenchef_diamond_20 | — | 23.39 | €€ | € |
| koekenpannen | bk_easy_induction_20 | — | 28.95 | €€ | €€ |
| koekenpannen | greenpan_mayflower_20 | — | 41.99 | €€ | €€ |
| koekenpannen | tefal_renew_20 | — | 30.99 | €€ | €€ |
| koekenpannen | bk_enjoy_20 | — | 24.9 | €€ | € |
| koekenpannen | hema_milano_20 | — | 26.99 | € | €€ |
| koekenpannen | berndes_b_green_20 | — | 40.0 | €€ | €€ |
| koekenpannen | greenpan_barcelona_pro_30 | — | 98.31 | €€€ | €€€€ |
| koekenpannen | kochstar_stein_30 | — | 15.33 | €€ | € |
| koekenpannen | demeyere_alu_pro_5_ceraforce_30 | — | 95.98 | €€€€ | €€€€ |
| koekenpannen | greenchef_diamond_30 | — | 39.9 | €€ | €€ |
| koekenpannen | bk_easy_induction_30 | — | 44.95 | €€ | €€ |
| koekenpannen | greenpan_torino_30 | — | 39.0 | €€ | €€ |
| koekenpannen | tefal_renew_30 | — | 43.99 | €€ | €€ |
| koekenpannen | brabantia_indu_plus_r_30 | — | 15.09 | €€€ | € |
| koekenpannen | scanpan_techniq_30 | — | 152.0 | €€€€ | €€€€ |
| koekenpannen | greenpan_barcelona_pro_32 | — | 80.0 | €€€ | €€€ |
| koekenpannen | demeyere_alu_pro_5_ceraforce_32 | — | 99.5 | €€€€ | €€€€ |
| koekenpannen | combekk_ceramic_pro_32 | — | 57.99 | €€€ | €€€ |
| koekenpannen | bk_easy_induction_32 | — | 49.91 | €€ | €€ |
| koekenpannen | greenpan_torino_32 | — | 44.89 | €€ | €€ |
| koekenpannen | tefal_renew_32 | — | 36.79 | €€ | €€ |
| koekenpannen | primecook_32 | — | 81.9 | €€€ | €€€ |
| koekenpannen | blue_diamond_32 | — | 82.41 | €€€ | €€€ |
| koekenpannen | ikea_hemlagad_keramisch_32 | — | 17.99 | € | € |
| koekenpannen | scanpan_ceramic_32 | — | 198.49 | €€€€ | €€€€ |
| hapjespannen | greenpan_barcelona_pro_28 | — | 159.9 | €€€€ | — |
| hapjespannen | bk_enjoy_28 | — | 41.93 | € | — |
| hapjespannen | woll_ecolite_qxr_28 | — | 104.9 | €€€ | — |
| hapjespannen | greenchef_diamond_28 | — | 52.5 | €€ | — |
| hapjespannen | bk_easy_induction_28 | — | 71.35 | € | — |
| hapjespannen | be_living_28 | — | 46.95 | €€ | — |
| hapjespannen | greenpan_torino_28 | — | 54.0 | €€ | — |
| hapjespannen | beka_cicla_28 | — | 85.0 | €€ | — |
| hapjespannen | greenpan_barcelona_pro_24 | — | 149.9 | €€€€ | — |
| hapjespannen | bk_brilliant_24 | — | 44.64 | €€ | — |
| hapjespannen | woll_ecolite_qxr_24 | — | 81.0 | €€€ | — |
| hapjespannen | greenchef_prime_24 | — | 49.9 | €€ | — |
| hapjespannen | bk_balans_plus_24 | — | 49.9 | €€ | — |
| hapjespannen | kochstar_essenz_24 | — | 19.99 | € | — |
| hapjespannen | beka_cicla_24 | — | 74.95 | €€ | — |
| hapjespannen | greenpan_barcelona_pro_30 | — | 59.9 | €€ | — |
| wokpannen | greenpan_torino_wok_28 | — | 47.51 | €€ | — |
| wokpannen | hema_milano_wok_28 | — | 26.59 | € | — |
| wokpannen | wmf_durado_wok_28 | — | 52.59 | €€€ | — |
| wokpannen | greenchef_diamond_wok_28 | — | 27.89 | €€ | — |
| wokpannen | primecook_wok_28 | — | 69.6 | €€€ | — |
| wokpannen | bk_blue_label_granite_wok_28 | — | 47.99 | €€ | — |
| wokpannen | brabantia_futura_green_wok_28 | — | 48.5 | €€ | — |
| wokpannen | greenpan_cambridge_wok_28 | — | 54.9 | €€€ | — |
| wokpannen | bk_easy_induction_wok_28 | — | 39.9 | €€ | — |
| wokpannen | berghoff_leo_recycled_wok_28 | — | 69.0 | €€€ | — |
| wokpannen | greenpan_barcelona_evershine_wok_30 | — | 87.45 | €€€ | — |
| wokpannen | bk_easy_induction_wok_30 | — | 70.0 | € | — |
| wokpannen | scanpan_techniq_wok_30 | — | 276.95 | €€€€ | — |
| wokpannen | bk_superior_ceramic_wok_30 | — | 74.99 | €€ | — |
| wokpannen | bk_balans_wok_30 | — | 99.95 | €€€ | — |
| wokpannen | greenpan_copenhagen_wok_30 | — | 62.49 | €€ | — |
| wokpannen | berghoff_phantom_wok_30 | — | 74.0 | €€€ | — |
| rvs-koekenpannen | demeyere_industry_5_24 | — | 149.0 | €€€ | — |
| rvs-koekenpannen | demeyere_multiline_7_24 | — | 123.0 | €€€ | — |
| rvs-koekenpannen | bk_superior_tri_ply_24 | — | 65.0 | €€ | — |
| rvs-koekenpannen | debuyer_affinity_24 | — | 126.51 | €€€ | — |
| rvs-koekenpannen | wmf_profi_24 | — | 58.02 | €€ | — |
| rvs-koekenpannen | demeyere_silverline_7_nanotouch_24 | — | 209.0 | €€€€ | — |
| rvs-koekenpannen | bk_bright_24 | — | 40.29 | € | — |
| rvs-koekenpannen | demeyere_industry_5_28 | — | 145.0 | €€€ | — |
| rvs-koekenpannen | demeyere_silverline_7_nanotouch_28 | — | 229.0 | €€€€ | — |
| rvs-koekenpannen | demeyere_multiline_7_28 | — | 169.0 | €€€ | — |
| rvs-koekenpannen | debuyer_affinity_28 | — | 165.95 | €€€ | — |
| rvs-koekenpannen | wmf_profi_28 | — | 63.59 | €€ | — |
| rvs-koekenpannen | bk_superior_tri_ply_28 | — | 89.9 | €€ | — |
| rvs-koekenpannen | bk_bright_28 | — | 36.48 | € | — |
| rvs-koekenpannen | demeyere_industry_5_20 | — | 115.99 | €€€ | — |
| rvs-koekenpannen | bk_superior_tri_ply_20 | — | 55.29 | €€ | — |
| rvs-koekenpannen | sola_green_cooking_plus_20 | — | 41.0 | € | — |
| rvs-koekenpannen | demeyere_multiline_7_20 | — | 145.0 | €€€ | — |
| rvs-koekenpannen | wmf_profi_20 | — | 40.54 | €€ | — |
| rvs-koekenpannen | debuyer_affinity_20 | — | 110.0 | €€€ | — |
| rvs-koekenpannen | demeyere_silverline_7_nanotouch_20 | — | 189.0 | €€€€ | — |
| snijplanken | boosblocks_pro_maple | — | 323.64 | €€€€ | — |
| snijplanken | ikea_aptitlig_bamboe | — | 6.99 | € | — |
| snijplanken | kaamut_walnoot_endgrain | — | 129.0 | €€€€ | — |
| snijplanken | zwilling_beukenhout_60x40 | — | 53.99 | €€€ | — |
| snijplanken | wmf_acacia_40x32 | — | 40.66 | €€ | — |
| snijplanken | namture_premium_olie_45x30 | — | 69.99 | €€€ | — |
| snijplanken | wooden_amsterdam_walnoot_40x30 | — | 219.0 | €€€€ | — |
| snijplanken | hema_beukenhout_24x35 | — | 9.99 | € | — |
| snijplanken | continenta_rubberwood_30x25 | — | 29.95 | €€ | — |
| snijplanken | pointvirgule_bamboe_40x30 | — | 17.95 | €€ | — |
| airfryers | inventum_gf500hld_5l | — | 89.0 | €€ | — |
| airfryers | bourgini_slimfit_xl_5l | — | 52.0 | € | — |
| airfryers | greenpan_silhouette_xl_5l | Moroccan Green | 116.0 | — | — |
| airfryers | greenpan_silhouette_xl_5l | Crème | 139.9 | — | — |
| airfryers | greenpan_silhouette_xl_5l | Smokey Blue | 129.9 | — | — |
| airfryers | masterpro_rocket_cyclone_5l | — | 127.26 | €€ | — |
| airfryers | wartmann_wm2312af_5l | — | 109.0 | €€ | — |
| airfryers | maison_kitchen_5l | — | 69.95 | €€ | — |
| airfryers | princess_182244_6l | — | 44.99 | € | — |
| airfryers | inventum_gf730hldb_7_3l | — | 109.0 | €€ | — |
| airfryers | bourgini_slimfit_pure_8l | Zwart | 113.99 | — | — |
| airfryers | bourgini_slimfit_pure_8l | Blauw | 139.99 | — | — |
| airfryers | bourgini_slimfit_pure_8l | Beige | 139.99 | — | — |
| airfryers | greenpan_bistro_xl_7_2l | — | 136.0 | €€€ | — |
| airfryers | greenpan_bistro_xxl_7_2l | Black | 159.9 | — | — |
| airfryers | greenpan_bistro_xxl_7_2l | Pine Green | 129.08 | — | — |
| airfryers | greenpan_bistro_xxl_7_2l | Smokey Blue | 159.9 | — | — |
| airfryers | maison_kitchen_8l | — | 59.95 | € | — |
| airfryers | princess_182280_8l | — | 53.99 | €€ | — |
| airfryers | inventum_gf800hld_dual_8l | — | 84.49 | €€ | — |
| airfryers | bourgini_duo_8l | — | 89.0 | €€ | — |
| airfryers | greenpan_bistro_dual_8l | — | 143.0 | €€€ | — |
| airfryers | wartmann_wm2511af_11l | — | 195.0 | €€€€ | — |
| vershoudbakjes | pyrex_cook_store_enkel | — | 23.21 | €€ | — |
| vershoudbakjes | ikea_365+_enkel | 600-ml | 3.49 | — | — |
| vershoudbakjes | ikea_365+_enkel | 1000-ml | 4.49 | — | — |
| vershoudbakjes | ikea_365+_enkel | 1200-ml | 4.99 | — | — |
| vershoudbakjes | mepal_easyclip_glass_enkel | 450-ml | 9.99 | — | — |
| vershoudbakjes | mepal_easyclip_glass_enkel | 700-ml | 9.94 | — | — |
| vershoudbakjes | mepal_easyclip_glass_enkel | 1500-ml | 15.69 | — | — |
| vershoudbakjes | mepal_easyclip_glass_enkel | 2250-ml | 24.19 | — | — |
| vershoudbakjes | locknlock_enkel | 630-ml | 9.95 | — | — |
| vershoudbakjes | locknlock_enkel | 740-ml | 12.95 | — | — |
| vershoudbakjes | locknlock_enkel | 1000-ml | 15.95 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 820-ml-rectangle | 9.14 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 380-ml-rectangle | 10.06 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 1220-ml-rectangle | 10.58 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 1970-ml-rectangle | 28.9 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 1220-ml-square | 12.68 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 760-ml-square | 11.72 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 420-ml-round | 7.95 | — | — |
| vershoudbakjes | luminarc_purebox_enkel | 920-ml-round | 11.45 | — | — |
| vershoudbakjes | berghoff_perfect_seal | 500-ml-square | 21.95 | — | — |
| vershoudbakjes | berghoff_perfect_seal | 1100-ml-square | 29.95 | — | — |
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
| vershoudbakjes | kitchenbrothers_5delig | — | 25.0 | €€ | — |
| vershoudbakjes | luminarc_purebox_5delig | — | 49.63 | €€ | — |
| vershoudbakjes | oxo_good_grips_smart_seal_6delig | — | 41.29 | €€€ | — |

## Handmatige controle

| Categorie | Probleem | Waarom niet automatisch opgelost |
|---|---|---|
| airfryers | greenpan_silhouette_xl_5l: productniveauprijs (129,90) wijkt af van de getoonde defaultswatch Moroccan Green (116,00); JSON-LD gebruikt productniveau | Prijscorrectie is een redactionele/datakeuze; de audit mag geen prijzen wijzigen |
| vershoudbakjes | Eerder gemarkeerde TODO-varianten (Igluu vierkant, Lock&Lock 630 ml / 1 L) hebben inmiddels prijs en URL; periodieke prijsverificatie blijft handwerk | price_last_checked bijwerken is een redactionele taak; de audit mag geen prijzen wijzigen |
