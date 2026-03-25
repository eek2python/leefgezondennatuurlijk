RULES = {
    "category_key": "rvs_koekenpannen",
    "description": "RVS koekenpannen voor serieus gebruik. Geen coating, geen keramische pannen.",

    "allowed_material_keywords": ["rvs", "stainless", "inox", "roestvrij", "18/10", "18/8", "chromagan", "cromargan"],
    "forbidden_material_keywords": ["keramisch", "ceramic", "ptfe", "teflon", "antikleef", "antiaanbak"],

    "pfas_free_required": False,
    "pfas_free_keywords": [],

    "product_type_keywords": ["koekenpan", "frying pan", "bakpan"],

    "size_sensitive": True,
    "size_field": "diameter_cm",
    "capacity_sensitive": False,

    "price_segments": {
        "budget": ["budget"],
        "middenklasse": ["mid"],
        "premium": ["premium"],
    },
    "price_range_field": "price_segment",

    "price_thresholds": {
        "budget_max": 40.0,
        "premium_min": 80.0,
    },

    "badge_policy": {
        "core": ["Beste keuze", "Budget keuze", "Premium keuze"],
        "optional": ["Beste voor inductie"],
        "max_total": 4,
    },

    "preferred_criteria": [
        "meerlagenbodem of meerlagenconstructie",
        "geschikt voor inductie",
        "ovenbestendig",
        "goede warmteverdeling en bouwkwaliteit",
        "reputatie voor duurzaamheid",
    ],

    "exclusion_criteria": [
        {"field": "material", "keyword": "keramisch", "severity": "error", "message": "Keramische pannen zijn uitgesloten van de RVS koekenpannen categorie."},
        {"field": "material", "keyword": "ceramic", "severity": "error", "message": "Keramische pannen zijn uitgesloten van de RVS koekenpannen categorie."},
        {"field": "material", "keyword": "ptfe", "severity": "error", "message": "PTFE-coating is niet toegestaan in de RVS categorie."},
        {"field": "material", "keyword": "teflon", "severity": "error", "message": "Teflon-coating is niet toegestaan in de RVS categorie."},
        {"field": "material", "keyword": "antikleef", "severity": "error", "message": "Klassieke antikleef-coating is niet toegestaan in de RVS categorie."},
        {"field": "material", "keyword": "antiaanbak", "severity": "error", "message": "Klassieke antiaanbak-coating is niet toegestaan in de RVS categorie."},
        {"field": "name", "keyword": "hybrid", "severity": "warning", "message": "Hybride claim vereist handmatige beoordeling op RVS-positionering."},
    ],

    "replacement_rules": {
        "must_match_category": True,
        "must_match_material": True,
        "must_match_size": True,
        "must_match_price_segment": True,
        "require_pfas_free": False,
        "forbidden_materials": ["keramisch", "ceramic", "ptfe", "teflon"],
        "notes": "Vervang alleen door echte RVS koekenpan zonder klassieke antiaanbaklaag. Zelfde formaat en constructiekwaliteit.",
    },

    "field_aliases": {
        "diameter": "diameter_cm",
        "price_range": "price_segment",
        "features": "key_features",
    },

    "notes": "Lichte budget-RVS-pannen zonder duidelijke kwaliteitsbasis kritisch beoordelen. Altijd onderscheid maken tussen echte RVS en hybride/coating varianten.",
}
