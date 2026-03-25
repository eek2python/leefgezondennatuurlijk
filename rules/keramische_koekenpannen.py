RULES = {
    "category_key": "keramische_koekenpannen",
    "description": "Keramisch gecoate, PFAS-vrije koekenpannen voor dagelijks gebruik. Geen PTFE/Teflon, geen pure RVS.",

    "allowed_material_keywords": ["keramisch", "ceramic", "ceraforce", "thermolon", "greblon"],
    "forbidden_material_keywords": ["rvs", "stainless", "ptfe", "teflon", "pfas"],

    "pfas_free_required": True,
    "pfas_free_keywords": [
        "pfas-vrij", "pfas vrij", "pfas-free", "pfas free",
        "thermolon", "ceraforce", "greblon", "keramisch",
        "ceramic", "siliconenhars", "sol-gel",
    ],

    "product_type_keywords": ["koekenpan", "frying pan", "bakpan"],

    "size_sensitive": True,
    "size_field": "diameter",
    "capacity_sensitive": False,

    "price_segments": {
        "budget": ["€"],
        "middenklasse": ["€€", "€€€"],
        "premium": ["€€€€"],
    },
    "price_thresholds": {
        "budget_max": 20.0,
        "premium_min": 60.0,
    },

    "badge_policy": {
        "core": ["Beste keuze", "Budget keuze", "Premium keuze"],
        "optional": ["Meest gekozen"],
        "max_total": 4,
    },

    "preferred_criteria": [
        "geschikt voor inductie",
        "ovenbestendig",
        "goede reputatie qua coating en gebruiksgemak",
        "goede balans gewicht, warmteverdeling en onderhoud",
        "beschikbaar in relevante maat",
    ],

    "exclusion_criteria": [
        {"field": "material", "keyword": "ptfe", "severity": "error", "message": "PTFE-coating is niet toegestaan in de keramische koekenpannen categorie."},
        {"field": "material", "keyword": "teflon", "severity": "error", "message": "Teflon-coating is niet toegestaan in de keramische koekenpannen categorie."},
        {"field": "material", "keyword": "pfas", "severity": "error", "message": "Product bevat PFAS-claim die strijdig is met categorie-eis."},
        {"field": "material", "keyword": "rvs", "severity": "error", "message": "Pure RVS-pannen zijn uitgesloten van de keramische koekenpannen categorie."},
        {"field": "material", "keyword": "stainless", "severity": "error", "message": "Pure RVS/stainless steel pannen zijn uitgesloten van de keramische koekenpannen categorie."},
        {"field": "name", "keyword": "triply", "severity": "warning", "message": "Triply-constructie zonder keramische laag past mogelijk niet in deze categorie. Controleer materiaalclaim."},
        {"field": "name", "keyword": "hybrid", "severity": "warning", "message": "Hybride materiaalclaim vereist handmatige beoordeling."},
    ],

    "replacement_rules": {
        "must_match_category": True,
        "must_match_material": True,
        "must_match_size": True,
        "must_match_price_segment": True,
        "require_pfas_free": True,
        "forbidden_materials": ["ptfe", "teflon", "rvs", "stainless"],
        "notes": "Vervang alleen door keramische koekenpan met PFAS-vrije positionering en zelfde formaat.",
    },

    "notes": "Hybride of onduidelijke materiaalclaims altijd markeren voor handmatige beoordeling. PTFE/Teflon altijd uitsluiten.",
}
