RULES = {
    "category_key": "gietijzeren_koekenpannen",
    "description": (
        "Traditionele en geëmailleerde gietijzeren koekenpannen voor "
        "fornuis, oven en buitengebruik."
    ),
    "allowed_material_keywords": [
        "gietijzer",
        "cast iron",
        "geëmailleerd gietijzer",
        "emailliertem gusseisen",
    ],
    "forbidden_material_keywords": [
        "aluminium",
        "ptfe",
        "teflon",
    ],
    "pfas_free_required": False,
    "pfas_free_keywords": [],
    "product_type_keywords": [
        "koekenpan",
        "skillet",
        "frying pan",
        "braadpan",
    ],
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
        "budget_max": 35.0,
        "premium_min": 90.0,
    },
    "badge_policy": {
        "core": ["Beste keuze", "Budget keuze", "Premium keuze"],
        "optional": ["Beste voor barbecue", "Beste geëmailleerde keuze"],
        "max_total": 4,
    },
    "preferred_criteria": [
        "gietijzeren constructie",
        "geschikt voor inductie",
        "geschikt voor oven of barbecue",
        "vooringebrand of duidelijk inbrandadvies",
        "duurzame handgreepconstructie",
    ],
    "exclusion_criteria": [
        {
            "field": "material",
            "keyword": "aluminium",
            "severity": "error",
            "message": "Aluminium pannen horen niet in de gietijzercategorie.",
        },
        {
            "field": "material",
            "keyword": "ptfe",
            "severity": "error",
            "message": "PTFE-coating is niet toegestaan in deze categorie.",
        },
        {
            "field": "material",
            "keyword": "teflon",
            "severity": "error",
            "message": "Teflon-coating is niet toegestaan in deze categorie.",
        },
    ],
    "replacement_rules": {
        "must_match_category": True,
        "must_match_material": True,
        "must_match_size": True,
        "must_match_price_segment": True,
        "require_pfas_free": False,
        "forbidden_materials": ["aluminium", "ptfe", "teflon"],
        "notes": (
            "Vervang alleen door een echte gietijzeren koekenpan of skillet "
            "in hetzelfde formaat en vergelijkbare afwerking."
        ),
    },
    "field_aliases": {
        "diameter": "diameter_cm",
        "price_range": "price_segment",
        "features": "key_features",
    },
    "notes": (
        "Maak in redactionele teksten onderscheid tussen traditioneel "
        "vooringebrand en geëmailleerd gietijzer."
    ),
}