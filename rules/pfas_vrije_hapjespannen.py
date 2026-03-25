RULES = {
    "category_key": "pfas_vrije_hapjespannen",
    "description": "PFAS-vrije hapjespannen / sautépannen voor dagelijks gebruik. Geen gewone koekenpannen als vervanger.",

    "allowed_material_keywords": ["keramisch", "ceramic", "thermolon", "ceraforce", "greblon", "siliconenhars"],
    "forbidden_material_keywords": ["ptfe", "teflon", "rvs", "stainless"],

    "pfas_free_required": True,
    "pfas_free_keywords": [
        "pfas-vrij", "pfas vrij", "pfas-free", "pfas free",
        "thermolon", "ceraforce", "greblon", "keramisch", "ceramic",
    ],

    "product_type_keywords": ["hapjespan", "sautépan", "sauteerpan", "sauteuse", "hapjes", "sauté"],

    "size_sensitive": True,
    "size_field": "diameter",
    "capacity_sensitive": False,

    "price_segments": {
        "budget": ["€"],
        "middenklasse": ["€€", "€€€"],
        "premium": ["€€€€"],
    },
    "price_thresholds": {
        "budget_max": 25.0,
        "premium_min": 70.0,
    },

    "badge_policy": {
        "core": ["Beste keuze", "Budget keuze", "Premium keuze"],
        "optional": ["Beste voor ovengebruik"],
        "max_total": 4,
    },

    "preferred_criteria": [
        "deksel inbegrepen of beschikbaar",
        "geschikt voor inductie",
        "ovenbestendig",
        "goede diepte voor dagelijks koken",
        "goede balans gewicht en warmteverdeling",
    ],

    "exclusion_criteria": [
        {"field": "material", "keyword": "ptfe", "severity": "error", "message": "PTFE-coating is niet toegestaan in de PFAS-vrije hapjespannen categorie."},
        {"field": "material", "keyword": "teflon", "severity": "error", "message": "Teflon is niet toegestaan in de PFAS-vrije hapjespannen categorie."},
        {"field": "material", "keyword": "bevat pfas", "severity": "error", "message": "Product bevat PFAS-claim die strijdig is met categorie-eis."},
        {"field": "name", "keyword": "koekenpan", "severity": "warning", "message": "Product is mogelijk een gewone koekenpan in plaats van hapjespan. Controleer producttype."},
        {"field": "name", "keyword": "wokpan", "severity": "warning", "message": "Wokpan is geen hapjespan. Controleer producttype."},
    ],

    "replacement_rules": {
        "must_match_category": True,
        "must_match_material": True,
        "must_match_size": True,
        "must_match_price_segment": True,
        "require_pfas_free": True,
        "forbidden_materials": ["ptfe", "teflon"],
        "notes": "Vervang alleen door PFAS-vrije hapjespan. Geen gewone koekenpan als vervanger. Zelfde diameter en prijsklasse.",
    },

    "notes": "Wokachtige vormen zonder hapjespanfunctie uitsluiten. Onduidelijke coating altijd markeren voor handmatige beoordeling.",
}
