RULES = {
    "category_key": "koolstofstalen_koekenpannen",
    "description": (
        "Koolstofstalen en plaatstalen koekenpannen zonder synthetische "
        "antiaanbaklaag."
    ),
    "allowed_material_keywords": [
        "koolstofstaal",
        "carbonstaal",
        "carbon steel",
        "plaatstaal",
        "black steel",
    ],
    "forbidden_material_keywords": [
        "keramisch",
        "ceramic",
        "ptfe",
        "teflon",
    ],
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
        "budget_max": 35.0,
        "premium_min": 80.0,
    },
    "badge_policy": {
        "core": ["Beste keuze", "Budget keuze", "Premium keuze"],
        "optional": ["Beste voor inductie", "Beste voor ovengebruik"],
        "max_total": 4,
    },
    "preferred_criteria": [
        "koolstofstalen of plaatstalen constructie",
        "geschikt voor inductie",
        "geschikt om in te branden",
        "duidelijke informatie over ovengebruik",
        "duurzame handgreepconstructie",
    ],
    "exclusion_criteria": [
        {
            "field": "material",
            "keyword": "keramisch",
            "severity": "error",
            "message": "Keramische pannen horen niet in de koolstofstaalcategorie.",
        },
        {
            "field": "material",
            "keyword": "ceramic",
            "severity": "error",
            "message": "Ceramic pannen horen niet in de koolstofstaalcategorie.",
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
        "forbidden_materials": ["keramisch", "ceramic", "ptfe", "teflon"],
        "notes": (
            "Vervang alleen door een koolstofstalen of plaatstalen koekenpan "
            "zonder synthetische antiaanbaklaag en in hetzelfde formaat."
        ),
    },
    "field_aliases": {
        "diameter": "diameter_cm",
        "price_range": "price_segment",
        "features": "key_features",
    },
    "notes": (
        "Controleer handmatig of beschermende was of fabrieksolie geen "
        "synthetische antiaanbaklaag is en of ovenlimieten correct zijn."
    ),
}