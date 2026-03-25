RULES = {
    "category_key": "pfas_vrije_airfryers",
    "description": "PFAS-vrije airfryers met duidelijke materiaalveiligheidspositionering.",

    "allowed_material_keywords": [],
    "forbidden_material_keywords": ["ptfe", "teflon"],

    "pfas_free_required": True,
    "pfas_free_keywords": [
        "pfas-vrij", "pfas vrij", "pfas-free", "pfas free",
        "keramisch", "ceramic", "rvs mand", "stainless basket",
        "bpa-vrij", "bpa free",
    ],

    "product_type_keywords": ["airfryer", "air fryer", "hetelucht", "heteluchtfriteuse", "friteuse"],

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
        "budget_max": 60.0,
        "premium_min": 150.0,
    },

    "badge_policy": {
        "core": ["Beste keuze", "Budget keuze", "Premium keuze"],
        "optional": ["Stilste model", "Beste gebruiksgemak", "PFAS-vrije keuze"],
        "max_total": 4,
    },

    "preferred_criteria": [
        "capaciteit passend bij de lijst",
        "makkelijk schoon te maken",
        "praktische bediening",
        "betrouwbare mand / binnenwerk materialen",
        "goede prijs-kwaliteit",
    ],

    "exclusion_criteria": [
        {"field": "material", "keyword": "ptfe", "severity": "error", "message": "PTFE-coating is niet toegestaan in de PFAS-vrije airfryers categorie."},
        {"field": "material", "keyword": "teflon", "severity": "error", "message": "Teflon is niet toegestaan in de PFAS-vrije airfryers categorie."},
        {"field": "name", "keyword": "private label", "severity": "warning", "message": "Generiek private-label product zonder betrouwbare onderbouwing kritisch beoordelen."},
    ],

    "replacement_rules": {
        "must_match_category": True,
        "must_match_material": False,
        "must_match_size": False,
        "must_match_price_segment": True,
        "require_pfas_free": True,
        "forbidden_materials": ["ptfe", "teflon"],
        "notes": "Vervang alleen door airfryer met voldoende duidelijke PFAS-vrije of materiaalveilige positionering. Vergelijkbare inhoud en prijsklasse.",
    },

    "pfas_uncertainty_check": True,
    "notes": "Onduidelijke of tegenstrijdige materiaalclaims altijd markeren. Generieke private-label producten zonder betrouwbare basis kritisch behandelen.",
}
