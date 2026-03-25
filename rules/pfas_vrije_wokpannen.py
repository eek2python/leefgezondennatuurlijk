RULES = {
    "category_key": "pfas_vrije_wokpannen",
    "description": "PFAS-vrije wokpannen voor dagelijks gebruik bij hoge temperaturen. Geen gewone koekenpannen of hapjespannen.",

    "allowed_material_keywords": ["keramisch", "ceramic", "thermolon", "ceraforce", "greblon", "stratanium"],
    "forbidden_material_keywords": ["ptfe", "teflon"],

    "pfas_free_required": True,
    "pfas_free_keywords": [
        "pfas-vrij", "pfas vrij", "pfas-free", "pfas free",
        "thermolon", "ceraforce", "greblon", "keramisch", "ceramic",
    ],

    "product_type_keywords": ["wokpan", "wok"],

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
        "optional": ["Beste voor hoge temperatuur"],
        "max_total": 4,
    },

    "preferred_criteria": [
        "geschikt voor hoge hitte",
        "geschikt voor inductie",
        "goede wokachtige vorm en diepte",
        "goede handgreep / hulpgreep",
        "robuust voor dagelijks gebruik",
    ],

    "exclusion_criteria": [
        {"field": "material", "keyword": "ptfe", "severity": "error", "message": "PTFE-coating is niet toegestaan in de PFAS-vrije wokpannen categorie."},
        {"field": "material", "keyword": "teflon", "severity": "error", "message": "Teflon is niet toegestaan in de PFAS-vrije wokpannen categorie."},
        {"field": "material", "keyword": "bevat pfas", "severity": "error", "message": "Product bevat PFAS-claim die strijdig is met categorie-eis."},
        {"field": "name", "keyword": "koekenpan", "severity": "warning", "message": "Product is mogelijk een gewone koekenpan in plaats van wokpan. Controleer producttype."},
        {"field": "name", "keyword": "hapjespan", "severity": "warning", "message": "Hapjespan is geen wokpan. Controleer producttype."},
    ],

    "replacement_rules": {
        "must_match_category": True,
        "must_match_material": True,
        "must_match_size": True,
        "must_match_price_segment": True,
        "require_pfas_free": True,
        "forbidden_materials": ["ptfe", "teflon"],
        "notes": "Vervang alleen door PFAS-vrije wokpan. Geen koekenpan of hapjespan als vervanger. Vergelijkbare diameter.",
    },

    "notes": "Te vlakke modellen die feitelijk geen wok zijn uitsluiten. Juist formaat voor de lijst controleren.",
}
