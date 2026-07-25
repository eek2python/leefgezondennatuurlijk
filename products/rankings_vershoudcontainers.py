# Rankings per uitvoering (paginaselector: Enkel / 3-delig / 5-delig).
# Keys verwijzen naar product keys in products_vershoudcontainers.py.
RANKINGS = {
    "single": [
        "pyrex_cook_store_enkel",
        "ikea_365+_enkel",
        "mepal_easyclip_glass_enkel",
        "locknlock_enkel",
        "luminarc_purebox_enkel",
        "berghoff_perfect_seal",
    ],
    "set_3": [
        "mepal_easyclip_glass_3delig",
        "igluu_meal_prep_3delig",
        "pyrex_cook_heat_3delig",
        "bormioli_frigoverre_3delig",
        "luminarc_purebox_3delig",
        "glasslock_3delig",
    ],
    "set_5": [
        "pyrex_cook_heat_5delig",
        "bormioli_frigoverre_5delig",
        "igluu_meal_prep_5delig",
        "kitchenbrothers_5delig",
        "luminarc_purebox_5delig",
        # "oxo_good_grips_smart_seal_6delig" is bewust niet gerankt: de entry bevat
        # nog gekopieerde Glasslock-data (beschrijving, inhoud, afbeelding) en wacht
        # op echte OXO-productgegevens.
    ],
}
