RULES = {
    "category_key": "glazen_vershoudbakjes",
    "description": "Glazen vershoudbakjes voor voedselbewaring. Geen volledig kunststof sets.",

    "allowed_material_keywords": ["glas", "glass", "borosilicaat", "borosilicate", "gehard glas", "tempered glass"],
    "forbidden_material_keywords": ["kunststof", "plastic", "melamine"],

    "pfas_free_required": False,
    "pfas_free_keywords": [],

    "product_type_keywords": ["vershoudbakje", "bewaarbakje", "lunchbox", "voorraadpot", "bewaarcontainer", "meal prep"],

    "size_sensitive": False,
    "size_field": None,
    "capacity_sensitive": True,
    "capacity_field": "features",

    "price_segments": {
        "budget": ["€"],
        "middenklasse": ["€€", "€€€"],
        "premium": ["€€€€"],
    },
    "price_thresholds": {
        "budget_max": 20.0,
        "premium_min": 50.0,
    },

    "badge_policy": {
        "core": ["Beste keuze", "Budget keuze", "Premium keuze"],
        "optional": ["Beste lekdicht"],
        "max_total": 4,
    },

    "preferred_criteria": [
        "lekdicht",
        "geschikt voor oven / magnetron / vriezer",
        "praktisch dekselsysteem",
        "goede set-opbouw voor dagelijks gebruik",
        "duidelijke voedselveilige positionering",
    ],

    "exclusion_criteria": [
        {"field": "material", "keyword": "kunststof", "severity": "error", "message": "Volledig kunststof vershoudbakjes zijn uitgesloten van deze categorie."},
        {"field": "material", "keyword": "plastic", "severity": "error", "message": "Volledig plastic vershoudbakjes zijn uitgesloten van deze categorie."},
        {"field": "material", "keyword": "melamine", "severity": "error", "message": "Melaminen producten zijn uitgesloten van deze categorie."},
        {"field": "description", "keyword": "decoratief", "severity": "warning", "message": "Decoratieve glazen schaaltjes zonder echte vershoudfunctie controleren."},
    ],

    "replacement_rules": {
        "must_match_category": True,
        "must_match_material": True,
        "must_match_size": False,
        "must_match_price_segment": True,
        "require_pfas_free": False,
        "forbidden_materials": ["kunststof", "plastic", "melamine"],
        "notes": "Vervang alleen door glazen vershoudbakjes. Vergelijkbare setgrootte, gebruiksprofiel en prijsklasse.",
    },

    "notes": "Deksel mag kunststof zijn als de bak zelf glas is. Zeer dun glas zonder duidelijke kwaliteitsaanduiding kritisch beoordelen.",
}
